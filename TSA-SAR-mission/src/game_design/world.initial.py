# world.py
import random
from pyglet import shapes
from config import (
    # Grid & colors
    PLAY_W, PLAY_H, CELL_SIZE, START,
    COLOR_WALL, COLOR_RED, COLOR_PURPLE, COLOR_YELLOW, COLOR_RESCUE,
    COLOR_WALL_ORANGE,
    # Victims & difficulties
    NUM_RED, NUM_PURPLE, NUM_YELLOW, DIFFICULTIES,
    # Wall generation knobs (global defaults; can be overridden per difficulty)
    WALL_CLEARANCE, WALL_ORANGE_PCT, MULTI_WALL_PCT, MULTI_WALL_LAYERS,
    MULTI_WALL_GROW_PCT, MIN_PASSABLE_RATIO, WALL_SEGMENT_LEN, WALL_ATTEMPTS_PER_SEG,
    # Red victim distribution knobs
    RED_SEP_CELLS, RED_FAR_QUANTILE, RED_SECTORS_X, RED_SECTORS_Y,
    RED_DIFFICULTY_DIST_WEIGHT, RED_DIFFICULTY_DEADEND_BONUS,
    RED_DIFFICULTY_CORRIDOR_BONUS, RED_DIFFICULTY_NEARWALL_BONUS,
    # Purple/Yellow victim distribution knobs
    PURPLE_SECTORS_X, PURPLE_SECTORS_Y,
    YELLOW_SECTORS_X, YELLOW_SECTORS_Y,
)
from config import PROTECTED_CELLS

# -------- small helpers --------
def victim_color(k): return COLOR_YELLOW if k == "yellow" else (COLOR_PURPLE if k == "purple" else COLOR_RED)
def _in(x, y): return 0 <= x < PLAY_W and 0 <= y < PLAY_H
def _border_cells():
    return {(x, 0) for x in range(PLAY_W)} | {(x, PLAY_H-1) for x in range(PLAY_W)} | \
           {(0, y) for y in range(PLAY_H)} | {(PLAY_W-1, y) for y in range(PLAY_H)}
def _buf(cells, r=WALL_CLEARANCE):
    out = set()
    for x, y in cells:
        for dx in range(-r, r + 1):
            for dy in range(-r, r + 1):
                nx, ny = x + dx, y + dy
                if _in(nx, ny): out.add((nx, ny))
    return out
def _comps(wset):
    vis, comps = set(), []
    for c in wset:
        if c in vis: continue
        st = [c]; comp = set()
        while st:
            x, y = st.pop()
            if (x, y) in vis or (x, y) not in wset: continue
            vis.add((x, y)); comp.add((x, y))
            for nx, ny in ((x+1,y),(x-1,y),(x,y+1),(x,y-1)):
                if (nx, ny) in wset and (nx, ny) not in vis: st.append((nx, ny))
        comps.append(comp)
    return comps

# -------- wall generation --------
def generate_walls(difficulty: str):
    """Generates wall layout and returns two sets: (all_walls, orange_walls)."""
    cfg = DIFFICULTIES[difficulty]
    rng = random.Random(cfg.get("seed", None))

    # per-difficulty overrides (fallback to global config knobs)
    min_passable = float(cfg.get("min_passable_ratio", MIN_PASSABLE_RATIO))
    multi_pct    = float(cfg.get("multi_wall_pct",   MULTI_WALL_PCT))
    layers_min, layers_max = tuple(cfg.get("layers", MULTI_WALL_LAYERS))
    grow_pct     = float(cfg.get("grow_pct",         MULTI_WALL_GROW_PCT))

    walls, reserved = set(), set()
    total = PLAY_W * PLAY_H
    max_walls = int(total * (1.0 - min_passable))
    def can_add(n): return len(walls) + n <= max_walls

    # 1) perimeter
    border = _border_cells()
    walls |= border
    reserved |= _buf(border)
    reserved |= _buf({START}, max(2, WALL_CLEARANCE))
    reserved |= set(PROTECTED_CELLS)

    # 2) random segments with clearance + budget
    segs = int(cfg.get("segments", 120))
    attempts = segs * int(WALL_ATTEMPTS_PER_SEG)
    placed = 0
    dirs = [(1,0), (-1,0), (0,1), (0,-1)] #possible directions
    min_len, max_len = WALL_SEGMENT_LEN

    while placed < segs and attempts > 0 and len(walls) < max_walls:
        attempts -= 1
        sx, sy = rng.randrange(1, PLAY_W-1), rng.randrange(1, PLAY_H-1)
        if (sx, sy) in reserved or (sx, sy) == START: continue
        dx, dy = rng.choice(dirs)
        length = rng.randint(int(min_len), int(max_len))

        prop = []
        x, y = sx, sy
        ok = True
        for _ in range(length):              #ensures only valid, non-overlapping wall segments
            if not _in(x, y) or (x, y) == START or (x, y) in reserved or (x, y) in walls:
                ok = False; break
            prop.append((x, y)); x += dx; y += dy
        if not ok or not prop or any(p in walls for p in _buf(prop)): continue   #buffer overlap

        if not can_add(len(prop)):
            need = max(0, max_walls - len(walls))
            if need == 0: break
            prop = prop[:need]

        walls.update(prop)
        reserved |= _buf(prop)
        placed += 1

    # 3) slim thickening
    comps = _comps(walls)
    if comps:
        k = max(1, int(len(comps) * multi_pct))
        for comp in rng.sample(comps, min(k, len(comps))):
            layers = random.randint(int(layers_min), int(layers_max))
            for _ in range(layers):
                if len(walls) >= max_walls: break
                comp_buf = _buf(comp)  # allow growth inside own buffer
                rim = set()
                for x, y in comp:
                    for nx, ny in ((x+1,y),(x-1,y),(x,y+1),(x,y-1)):
                        if _in(nx,ny): rim.add((nx,ny))
                elig = [c for c in rim if c not in walls and c not in (reserved - comp_buf)]
                if not elig: break
                take = max(1, int(len(elig) * grow_pct))
                rng.shuffle(elig)
                add = set(elig[:take])
                if not can_add(len(add)):
                    need = max(0, max_walls - len(walls))
                    if need <= 0: break
                    add = set(list(add)[:need])
                if not add: break
                walls.update(add); reserved |= _buf(add); comp.update(add)

    # 4) Determine which wall components are orange
    wall_comps = _comps(walls)
    orange_walls = set()
    if wall_comps:
        k = int(len(wall_comps) * float(WALL_ORANGE_PCT))
        if k > 0:
            for comp in rng.sample(wall_comps, k):
                orange_walls.update(comp)
    orange_walls -= _border_cells()

    return walls, orange_walls

# -------- victim placement --------
def place_victims(distmap, start, all_passable=None):  #distmap: how far every cell is from start
    """
    Reds: sector-quota, farthest quantile, spaced.
    Purples & Yellows: also sector-based quotas for better distribution.
    """
    rng = random.Random(99)
    victims = {}

    # Candidate pool (choose which cells get victims, while respecting rules (not on START, not blocked, spread by sector)
    pool = [p for p in distmap.keys() if p != start]  #pool = the initial list of candidate cells where victims could be placed.
    if all_passable is not None:
        extras = list((all_passable - set(pool)) - {start})
        rng.shuffle(extras); pool += extras
    if not pool: return victims

    # ---------------- REDS ----------------
    dists = {p: distmap.get(p, 0) for p in pool}
    scored_linear = sorted(((p, dists[p]) for p in pool), key=lambda t: t[1])
    q_idx = int(len(scored_linear) * float(RED_FAR_QUANTILE))
    cutoff = scored_linear[q_idx][1] if 0 <= q_idx < len(scored_linear) else 0  #cutoff distance
    far = [p for (p, d) in scored_linear if d >= cutoff]
    if len(far) < max(NUM_RED, 8):
        far += [p for p, _ in reversed(scored_linear) if p not in far]

    passable = set(all_passable) if all_passable is not None else set(p for p, _ in scored_linear)
    dirs4 = ((1,0),(-1,0),(0,1),(-1,0))
    def degree(p):
        x,y=p; return sum(((x+dx,y+dy) in passable) for dx,dy in dirs4)
    def is_corridor(p):
        x,y=p; neigh=[(x+dx,y+dy) for dx,dy in dirs4 if (x+dx,y+dy) in passable]
        if len(neigh)!=2: return False
        (x1,y1),(x2,y2)=neigh; return (x1-x)==-(x2-x) and (y1-y)==-(y2-y)
    def blocked_sides(p):
        x,y=p; return 4 - sum(((x+dx,y+dy) in passable) for dx,dy in dirs4)

    maxd = max(dists.values()) if dists else 1
    def hardness_score(p):
        nd = (dists.get(p,0)/maxd) if maxd>0 else 0.0
        s = RED_DIFFICULTY_DIST_WEIGHT * nd
        if degree(p) == 1: s += RED_DIFFICULTY_DEADEND_BONUS
        if is_corridor(p): s += RED_DIFFICULTY_CORRIDOR_BONUS
        if blocked_sides(p) >= 2: s += RED_DIFFICULTY_NEARWALL_BONUS
        return s

    SX, SY = int(RED_SECTORS_X), int(RED_SECTORS_Y)
    def sector_of(p):
        sx = min(SX-1, (p[0] * SX) // max(1, PLAY_W))
        sy = min(SY-1, (p[1] * SY) // max(1, PLAY_H))
        return int(sx), int(sy)
    sector_count = SX * SY
    buckets = {i: [] for i in range(sector_count)}
    for p in far:
        sx, sy = sector_of(p)
        buckets[sy * SX + sx].append(p)
    for i in buckets:
        buckets[i].sort(key=hardness_score, reverse=True)

    base = NUM_RED // sector_count
    rem  = NUM_RED % sector_count
    order = list(range(sector_count)); rng.shuffle(order)
    quotas = {i: base + (1 if idx < rem else 0) for idx, i in enumerate(order)}

    def cheby(a,b): return max(abs(a[0]-b[0]), abs(a[1]-b[1]))
    reds, sep = [], int(RED_SEP_CELLS)
    while len(reds) < NUM_RED and sep >= 2:
        placed_any = False
        for i in order:
            if len(reds) >= NUM_RED or quotas[i] <= 0: continue
            lst = buckets[i]; j = 0
            while j < len(lst):
                p = lst[j]
                if all(cheby(p,q) >= sep for q in reds):
                    reds.append(p); quotas[i] -= 1; lst.pop(j); placed_any = True; break
                j += 1
        if not placed_any: sep -= 1

    if len(reds) < NUM_RED:
        remaining = []
        for i in order: remaining += buckets[i]
        remaining += sorted((set(far) - set(reds)), key=hardness_score, reverse=True)
        for p in remaining:
            if len(reds) >= NUM_RED: break
            if all(cheby(p,q) >= 2 for q in reds): reds.append(p)

    for p in reds[:NUM_RED]: victims[p] = "red"

    # ---------------- PURPLES & YELLOWS ----------------
    def distribute_victims(candidates, num, SX, SY, kind):
        local = {}
        if not candidates or num <= 0: return local
        buckets = {i: [] for i in range(SX * SY)}
        for p in candidates:
            sx = min(SX-1, (p[0] * SX) // max(1, PLAY_W))
            sy = min(SY-1, (p[1] * SY) // max(1, PLAY_H))
            buckets[sy * SX + sx].append(p)

        base = num // (SX * SY)
        rem  = num % (SX * SY)
        order = list(range(SX * SY)); rng.shuffle(order)
        quotas = {i: base + (1 if idx < rem else 0) for idx, i in enumerate(order)}

        placed = 0
        for i in order:
            rng.shuffle(buckets[i])
            for p in buckets[i]:
                if placed >= num: break
                if quotas[i] <= 0: break
                local[p] = kind
                quotas[i] -= 1; placed += 1
        return local

    rest = [p for p in pool if p not in victims and p != start]
    rng.shuffle(rest)

    victims.update(distribute_victims(rest, NUM_PURPLE, PURPLE_SECTORS_X, PURPLE_SECTORS_Y, "purple"))
    rest = [p for p in rest if p not in victims]

    victims.update(distribute_victims(rest, NUM_YELLOW, YELLOW_SECTORS_X, YELLOW_SECTORS_Y, "yellow"))

    return victims

# -------- drawing --------
def draw_world(play_batch, walls, orange_walls, victims):
    """Draws walls (coloring orange ones differently) and victims."""
    wall_shapes = [shapes.Rectangle(x*CELL_SIZE, y*CELL_SIZE, CELL_SIZE, CELL_SIZE,
                                    color=(COLOR_WALL_ORANGE if (x,y) in orange_walls else COLOR_WALL),
                                    batch=play_batch) for (x,y) in walls]
    victim_shapes = {
        p: (shapes.Circle(p[0]*CELL_SIZE + CELL_SIZE/2,
                          p[1]*CELL_SIZE + CELL_SIZE/2,
                          CELL_SIZE/2 - 3,
                          color=victim_color(t), batch=play_batch), t)
        for p, t in victims.items()
    }
    return wall_shapes, victim_shapes

def make_rescue_triangle(play_batch, rescue_pos):
    if not rescue_pos: return None
    gx, gy = rescue_pos
    cx, cy = gx*CELL_SIZE + CELL_SIZE/2, gy*CELL_SIZE + CELL_SIZE/2
    s = CELL_SIZE * 0.9; h = s * 0.5
    return shapes.Triangle(cx, cy + h, cx - s/2, cy - h, cx + s/2, cy - h,
                           color=COLOR_RESCUE, batch=play_batch)