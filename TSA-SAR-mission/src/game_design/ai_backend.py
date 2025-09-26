# ai_backend.py
from __future__ import annotations
import threading, queue, re
from typing import Optional, Callable, List, Tuple

# ---------- Base Class and Worker ----------

class BaseLLM:
    """Abstract base class for Large Language Models (or stand-ins)."""
    def generate(self, prompt: str, system: Optional[str] = None) -> str:
        raise NotImplementedError

class AIWorker:
    """Runs LLM calls in a non-blocking background thread."""
    def __init__(self, model: "BaseLLM"):
        self.model = model
        self._q: "queue.Queue[Tuple[str, Optional[str], Callable[[str], None]]]" = queue.Queue()
        self._t = threading.Thread(target=self._loop, daemon=True)
        self._t.start()

    def ask(self, prompt: str, on_done: Callable[[str], None], system: Optional[str] = None):
        self._q.put((prompt, system, on_done))

    def _loop(self):
        while True:
            prompt, system, cb = self._q.get()
            try:
                reply = self.model.generate(prompt, system=system)
            except Exception as e:
                reply = f"(AI error: {e})"
            try:
                cb(reply)
            except Exception:
                pass

# ---------- Utilities to parse your prompt text ----------

def _parse_player(prompt: str) -> Optional[Tuple[int,int]]:
    m = re.search(r"My current position is\s*\[(\s*\d+\s*),\s*(\d+)\s*\]", prompt)
    if not m:
        m = re.search(r"My current position is\s*\((\s*\d+\s*),\s*(\d+)\s*\)", prompt)
    return (int(m.group(1)), int(m.group(2))) if m else None

def _parse_rescue_points(prompt: str) -> List[Tuple[int,int]]:
    pts = []
    m = re.search(r"Rescue points are at:\s*([^\n]+)", prompt)
    if not m:
        return pts
    block = m.group(1)
    for x,y in re.findall(r"\(\s*(\d+)\s*,\s*(\d+)\s*\)", block):
        pts.append((int(x), int(y)))
    return pts

def _parse_matrix(prompt: str) -> List[List[int]]:
    rows = []
    for line in prompt.splitlines():
        line = line.strip()
        if line and re.fullmatch(r"[0-9]+", line):
            rows.append([int(ch) for ch in line])
    return rows

def _manhattan(a: Tuple[int,int], b: Tuple[int,int]) -> int:
    return abs(a[0]-b[0]) + abs(a[1]-b[1])

# ---------- Rule-based "LLM" that always works offline ----------

class RuleReasoner(BaseLLM):
    """
    Deterministic analyzer:
      - Reads the matrix & positions from prompt text
      - Computes nearest victim(s), nearest obstacle band, nearest rescue point
      - Writes a clean, pilot-friendly description (no commands)
    """
    def generate(self, prompt: str, system: Optional[str] = None) -> str:
        grid = _parse_matrix(prompt)
        if not grid:
            return "I couldn't read the map grid. Please resend the question."

        H, W = len(grid), len(grid[0])
        me = _parse_player(prompt)
        rescues = _parse_rescue_points(prompt)

        victims = {"red": [], "purple": [], "yellow": []}
        walls_grey, walls_orange = set(), set()
        passable = set()
        me_fallback = None

        for y in range(H):
            for x in range(W):
                v = grid[y][x]
                if v == 9: me_fallback = (x,y)
                if v == 1: passable.add((x,y))
                if v == 0: walls_grey.add((x,y))
                if v == 5: walls_orange.add((x,y))
                if v == 2: victims["red"].append((x,y))
                if v == 3: victims["purple"].append((x,y))
                if v == 4: victims["yellow"].append((x,y))

        if me is None:
            me = me_fallback

        def _sector(p: Tuple[int,int]) -> str:
            x,y = p
            sx = "west" if x < W/3 else ("center" if x < 2*W/3 else "east")
            sy = "south" if y < H/3 else ("center" if y < 2*H/3 else "north")
            return "center" if (sx == "center" and sy == "center") else f"{sy}-{sx}"

        def _nearest(me, pts):
            if me is None or not pts: return None, None
            best = min(pts, key=lambda p: _manhattan(me,p))
            return best, _manhattan(me, best)

        # Nearest per victim type
        nearest_by_kind = {}
        for k in ("red","purple","yellow"):
            p, d = _nearest(me, victims[k])
            if p: nearest_by_kind[k] = (p, d)

        # Orange hazard summary (mode sector)
        orange_summary = ""
        if walls_orange:
            from collections import Counter
            sec, _ = Counter(_sector(p) for p in walls_orange).most_common(1)[0]
            orange_summary = f"Orange hazard clusters are prominent around the {sec}."

        # Rescue nearest
        rescue_nearest, rescue_d = _nearest(me, rescues)

        q = prompt.lower()
        parts = []

        if any(k in q for k in ("hazard", "obstacle", "wall")):
            all_walls = list(walls_grey | walls_orange)
            pw, dw = _nearest(me, all_walls)
            if pw:
                tone = "orange (significant)" if pw in walls_orange else "gray"
                parts.append(f"The nearest obstacle is a {tone} wall near {pw[0]},{pw[1]}, approximately {dw} cells away.")
            if orange_summary: parts.append(orange_summary)
            elif walls_grey: parts.append("Gray walls form corridors in several areas; expect reduced maneuvering room.")

        if "where" in q and "victim" in q:
            if nearest_by_kind:
                triples = sorted([(k, p, d) for k,(p,d) in nearest_by_kind.items()], key=lambda t: t[2])
                k,p,d = triples[0]
                color = {"red":"high-priority red","purple":"purple","yellow":"yellow"}[k]
                parts.append(f"The nearest victim is a {color} at {p[0]},{p[1]}, about {d} cells from your position.")
            all_v = victims["red"] + victims["purple"] + victims["yellow"]
            if all_v:
                from collections import Counter
                sec, _ = Counter(_sector(p) for p in all_v).most_common(1)[0]
                parts.append(f"Victims appear denser toward the {sec} sector.")

        if "nearest rescue" in q or ("rescue" in q and "nearest" in q):
            if rescue_nearest:
                parts.append(f"The closest rescue point is around {rescue_nearest[0]},{rescue_nearest[1]} (~{rescue_d} cells).")
            elif rescues:
                parts.append("Rescue points are listed but I couldn’t determine the closest one.")
            else:
                parts.append("I don’t have rescue-point locations in this map view.")

        if not parts:
            victims_total = sum(len(v) for v in victims.values())
            parts.append(f"The map shows {victims_total} victims distributed across the grid; "
                         f"{len(walls_orange)} orange-wall cells indicate higher-risk structures.")
            if orange_summary: parts.append(orange_summary)
            if me is not None: parts.append(f"Your current cell is {me[0]},{me[1]}.")

        return " ".join(parts)

# ---------- DeepSeek via llama.cpp (NO transformers/torch) ----------

class LlamaCppLLM(BaseLLM):
    """
    Runs a local GGUF with llama.cpp bindings. No API key, no torch/transformers.
    Example model: deepseek-r1-distill-qwen-1.5b-Q4_K_M.gguf
    """
    def __init__(self, model_path: str, n_ctx: int = 4096, n_threads: int = 0):
        try:
            from llama_cpp import Llama
        except Exception as e:
            raise RuntimeError("Please install llama-cpp-python: pip install --upgrade llama-cpp-python") from e
        # n_threads=0 lets it auto-pick your CPU cores
        self.llm = Llama(model_path=model_path, n_ctx=n_ctx, n_threads=n_threads)
        self._fallback = RuleReasoner()

    def generate(self, prompt: str, system: Optional[str] = None) -> str:
        """
        We first compute a deterministic, map-grounded summary (RuleReasoner),
        then ask the model to rewrite/expand it as a clean paragraph with no commands.
        """
        base = self._fallback.generate(prompt, system)
        sys = (system or "").strip()
        composed = (
            (f"<<SYS>>\n{sys}\n<</SYS>>\n" if sys else "") +
            "Context summary (derived from the grid):\n" + base + "\n\n" +
            "User question and map details:\n" + prompt + "\n\n" +
            "Write ONE concise paragraph. No commands. Descriptive only."
        )
        out = self.llm(
            composed,
            max_tokens=200,
            temperature=0.6,
            stop=["</s>", "```"]
        )
        text = out["choices"][0]["text"].strip()
        return text if text else base

# ---------- Optional HF local model (can be any open-source HF model) ----------

class HFLocalLLM(BaseLLM):
    """
    Uses a local HuggingFace model if available; otherwise falls back to RuleReasoner.
    Default kept small; change model_id for DeepSeek HF if you prefer that route.
    """
    def __init__(self, model_id: str = "TinyLlama/TinyLlama-1.1B-Chat-v1.0"):
        self.model_id = model_id
        self._pipe = None
        self._fallback = RuleReasoner()

    def _ensure(self):
        if self._pipe is not None:
            return
        try:
            from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline
            tok = AutoTokenizer.from_pretrained(self.model_id)
            mdl = AutoModelForCausalLM.from_pretrained(self.model_id)
            self._pipe = pipeline("text-generation", model=mdl, tokenizer=tok)
        except Exception:
            self._pipe = None  # stay graceful

    def generate(self, prompt: str, system: Optional[str] = None) -> str:
        base = self._fallback.generate(prompt, system)
        self._ensure()
        if not self._pipe:
            return base
        system_text = (system or "").strip()
        full = (
            f"{system_text}\n\nContext summary:\n{base}\n\n"
            f"User question and map details:\n{prompt}\n\n"
            f"Rewrite a single concise paragraph (no commands, descriptive only)."
        )
        out = self._pipe(full, max_new_tokens=120, do_sample=True, temperature=0.6)
        text = out[0]["generated_text"].strip()
        # A light cleanup in case the model echoes the instruction:
        if "Rewrite a single concise paragraph" in text:
            text = text.split("Rewrite a single concise paragraph", 1)[-1].strip(":.- \n")
        return text if text else base

# ---------- Debug echo ----------

class EchoLLM(BaseLLM):
    def generate(self, prompt: str, system: Optional[str] = None) -> str:
        return "(echo) " + (prompt[-600:] if len(prompt) > 600 else prompt)
