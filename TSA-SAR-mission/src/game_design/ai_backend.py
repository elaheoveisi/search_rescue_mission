# src/ai/ai_backend.py
from __future__ import annotations
"""
AI backends + reasoning layer for SAR game.

- BaseLLM / AIWorker: common interfaces & async worker
- EchoLLM, HFLocalLLM (DeepSeek), LlamaCppLLM: local backends
- World encoders + heuristic fallback + prompt builder
- AIAgent: simple ask(game, question, on_done) entry point

Design goals:
• Use the grid/matrix internally, NEVER show it in answers.
• Short, actionable replies; heuristic fallback if LLM fails.
"""

import threading, queue, time, json, re
from dataclasses import dataclass
from typing import Optional, Callable, List, Tuple

# ======================================================================
#                       CORE INTERFACES
# ======================================================================

class BaseLLM:
    """Abstract base class for Large Language Models."""
    def generate(self, prompt: str, system: Optional[str] = None) -> str:
        raise NotImplementedError

class AIWorker:
    """Runs LLM calls in a non-blocking background thread."""
    def __init__(self, model: "BaseLLM"):
        self.model = model
        self._q = queue.Queue()
        self._t = threading.Thread(target=self._loop, daemon=True)
        self._t.start()

    def ask(self, prompt: str, on_done: Callable[[str], None], system: Optional[str] = None):
        self._q.put((prompt, system, on_done))

    def _loop(self):
        while True:
            try:
                prompt, system, cb = self._q.get()
                reply = self.model.generate(prompt, system=system)
                cb(reply)
            except Exception as e:
                import traceback
                error_str = traceback.format_exc()
                print(f"[AI WORKER ERROR]\n{error_str}")
                cb(f"(AI error: {e})")
            time.sleep(0.01)

# ======================================================================
#                       LIGHTWEIGHT LOCAL BACKENDS
# ======================================================================

class EchoLLM(BaseLLM):
    """A fallback LLM that simply echoes the user's prompt."""
    def __init__(self, note="echo backend"):
        self.note = note
    def generate(self, prompt: str, system: Optional[str] = None) -> str:
        sys = f"[sys:{system}] " if system else ""
        return f"({self.note}) {sys}You asked: {prompt}"

class HFLocalLLM(BaseLLM):
    """
    Hugging Face transformers backend.
    Configured for DeepSeek Coder 7B Instruct.
    """
    def __init__(self, model_id: str = "deepseek-ai/deepseek-coder-7b-instruct", cache_dir: str = "C:/hf-cache"):
        self.model_id = model_id
        self.cache_dir = cache_dir
        self._pipe = None
        self._tok = None
        # DeepSeek supports a longer context than tiny models
        self.max_ctx = 4096
        self.max_new = 512
        self.safety_margin = 48  # buffer for special tokens

    def _ensure_pipe(self):
        if self._pipe:
            return
        from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline
        import torch

        self._tok = AutoTokenizer.from_pretrained(self.model_id, cache_dir=self.cache_dir)
        # Avoid attention_mask warnings: set pad token if missing
        if self._tok.pad_token is None:
            self._tok.pad_token = self._tok.eos_token

        model = AutoModelForCausalLM.from_pretrained(
            self.model_id,
            torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
            device_map="auto" if torch.cuda.is_available() else None,
            low_cpu_mem_usage=True,
            cache_dir=self.cache_dir
        )
        self._pipe = pipeline(
            "text-generation",
            model=model,
            tokenizer=self._tok,
            device=0 if torch.cuda.is_available() else -1,
            model_kwargs={"attn_implementation": "eager"}
        )

    def _token_ids(self, text: str) -> List[int]:
        return self._tok.encode(text, add_special_tokens=False)

    def _truncate_to_tokens(self, text: str, max_tokens: int) -> str:
        ids = self._token_ids(text)
        if len(ids) <= max_tokens:
            return text
        return self._tok.decode(ids[:max_tokens], clean_up_tokenization_spaces=False)

    def generate(self, prompt: str, system: Optional[str] = None) -> str:
        self._ensure_pipe()
        full = f"<<SYS>>\n{system}\n<</SYS>>\n\n{prompt}" if system else prompt

        # keep within context budget
        max_input_tokens = self.max_ctx - self.max_new - self.safety_margin
        full = self._truncate_to_tokens(full, max_input_tokens)

        out = self._pipe(
            full,
            max_new_tokens=self.max_new,
            do_sample=False,                 # deterministic
            pad_token_id=self._tok.eos_token_id,
            max_length=self.max_ctx
        )[0]["generated_text"]

        return out[len(full):].strip()

class LlamaCppLLM(BaseLLM):
    """Local llama.cpp backend for running GGUF-quantized models."""
    def __init__(self, gguf_path: str, n_ctx: int = 4096, n_gpu_layers: int = 0, n_threads: int = 4, max_tokens: int = 256):
        from llama_cpp import Llama
        self.max_tokens = max_tokens
        self.llm = Llama(model_path=gguf_path, n_ctx=n_ctx, n_gpu_layers=n_gpu_layers, n_threads=n_threads)

    def generate(self, prompt: str, system: Optional[str] = None) -> str:
        full = f"<<SYS>>{system}<<EOS>>\n{prompt}" if system else prompt
        res = self.llm(prompt=full, max_tokens=self.max_tokens, temperature=0.0, top_p=1.0)
        return res["choices"][0]["text"].strip()

# ======================================================================
#                       REASONER LAYER (NEW)
# ======================================================================

# ----- World structures (compact, model-friendly) -----
@dataclass
class Victim:
    x: int
    y: int
    color: str  # "red", "yellow", "purple", etc.

@dataclass
class RescuePoint:
    x: int
    y: int
    label: str  # "R1", "R2", ...

@dataclass
class Hazard:
    x: int
    y: int
    kind: str  # "wall", "water", "no-fly", ...

@dataclass
class AgentState:
    x: int
    y: int
    heading_deg: float
    altitude: float

@dataclass
class WorldState:
    width: int
    height: int
    cell_size: int
    agent: AgentState
    victims: List[Victim]
    rescue_points: List[RescuePoint]
    hazards: List[Hazard]

def encode_world(game) -> WorldState:
    """
    Extracts compact state from your game without exposing raw matrices to the UI.
    Adjust field access if your attribute names differ.
    """
    width = getattr(game, "GRID_W", getattr(game, "width", 60))
    height = getattr(game, "GRID_H", getattr(game, "height", 40))
    cell_size = getattr(game, "CELL", 16)

    # Agent
    px = int(getattr(game.player, "grid_x", 0))
    py = int(getattr(game.player, "grid_y", 0))
    heading = float(getattr(game.player, "heading_deg", 0.0))
    altitude = float(getattr(game.player, "altitude_agl", 100.0))

    # Victims
    victims: List[Victim] = []
    if hasattr(game, "victims"):
        for v in game.victims:
            victims.append(Victim(int(getattr(v, "grid_x", 0)),
                                  int(getattr(v, "grid_y", 0)),
                                  str(getattr(v, "color_name", "unknown"))))

    # Rescue points
    rescue_points: List[RescuePoint] = []
    if hasattr(game, "rescue_points"):
        for i, r in enumerate(game.rescue_points, start=1):
            rescue_points.append(RescuePoint(int(getattr(r, "grid_x", 0)),
                                             int(getattr(r, "grid_y", 0)),
                                             str(getattr(r, "label", f"R{i}"))))

    # Hazards
    hazards: List[Hazard] = []
    if hasattr(game, "walls"):
        for w in game.walls:
            hazards.append(Hazard(int(getattr(w, "grid_x", 0)),
                                  int(getattr(w, "grid_y", 0)),
                                  "wall"))
    if hasattr(game, "no_fly"):
        for z in game.no_fly:
            hazards.append(Hazard(int(getattr(z, "grid_x", 0)),
                                  int(getattr(z, "grid_y", 0)),
                                  "no-fly"))

    return WorldState(
        width=width,
        height=height,
        cell_size=cell_size,
        agent=AgentState(px, py, heading, altitude),
        victims=victims,
        rescue_points=rescue_points,
        hazards=hazards,
    )

# ----- Heuristic fallback (no LLM) -----
def _manhattan(a: Tuple[int,int], b: Tuple[int,int]) -> int:
    return abs(a[0]-b[0]) + abs(a[1]-b[1])

def heuristic_answer(state: WorldState, question: str) -> str:
    ax, ay = state.agent.x, state.agent.y
    lines: List[str] = []
    q = (question or "").lower()

    if state.victims:
        nv = min(state.victims, key=lambda v: _manhattan((ax,ay),(v.x,v.y)))
        d = _manhattan((ax,ay), (nv.x, nv.y))
        lines.append(f"Nearest victim ~{d} cells away near ({nv.x},{nv.y}), tag color {nv.color}.")
    else:
        lines.append("No victims visible in the current sector.")

    if state.rescue_points:
        nr = min(state.rescue_points, key=lambda r: _manhattan((ax,ay),(r.x,r.y)))
        d = _manhattan((ax,ay), (nr.x, nr.y))
        lines.append(f"Closest rescue point is {nr.label}, about {d} cells away near ({nr.x},{nr.y}).")
    else:
        lines.append("No rescue/triage points defined yet.")

    if state.hazards:
        near_h = [h for h in state.hazards if _manhattan((ax,ay),(h.x,h.y)) <= 6]
        if near_h:
            kinds = ", ".join(sorted({h.kind for h in near_h}))
            lines.append(f"Hazards within ~6 cells: {kinds}. Maintain clearance and adjust routing.")
        else:
            lines.append("No immediate hazards within ~6 cells of your position.")
    else:
        lines.append("No hazards registered on the board.")

    if any(k in q for k in ("survivor","victim")):
        lines.append("Recommendation: move toward the nearest victim with obstacle clearance; call out if visibility changes.")
    elif any(k in q for k in ("danger","obstacle","hazard")):
        lines.append("Keep obstacle separation; avoid tight corridors. Announce if you need replanning.")
    elif "rescue" in q or "evac" in q:
        lines.append("After pickup, route to the nearest rescue point unless ATC/safety dictates otherwise.")

    return " ".join(lines)

# ----- Prompting discipline -----
SYSTEM_PROMPT = (
    "You are a concise UAS Search-and-Rescue assistant. You are given the world state as JSON.\n"
    "CRITICAL RULES:\n"
    "• Do NOT print raw matrices, arrays, grids, or JSON dumps unless explicitly asked.\n"
    "• Provide practical implications: nearest victims, safe routes, hazards, rescue points, next actions.\n"
    "• Be specific (distances in cells; cardinal hints OK) and keep answers under ~120 words.\n"
    "• ATC typically does not track obstacles; pilots must visually avoid them.\n"
)

def build_prompt(state: WorldState, user_question: str) -> str:
    state_json = json.dumps({
        "grid": {"w": state.width, "h": state.height, "cell": state.cell_size},
        "agent": {"x": state.agent.x, "y": state.agent.y, "hdg_deg": state.agent.heading_deg, "alt_agl": state.agent.altitude},
        "victims": [{"x": v.x, "y": v.y, "color": v.color} for v in state.victims],
        "rescue_points": [{"x": r.x, "y": r.y, "label": r.label} for r in state.rescue_points],
        "hazards": [{"x": h.x, "y": h.y, "kind": h.kind} for h in state.hazards],
    }, separators=(",", ":"))
    return (
        f"<state>{state_json}</state>\n"
        f"<question>{(user_question or '').strip()}</question>\n"
        "Remember the rules: do NOT reveal raw state/matrices; focus on concise, actionable guidance."
    )

def _redact_grids(text: str) -> str:
    """Trim accidental dumps of arrays/JSON to avoid showing the matrix."""
    if not text:
        return text
    if len(text) > 1500:
        text = text[:1400] + " …"
    # Redact long bracketed numeric lists
    text = re.sub(r"\[[\s\d,.\-]{20,}\]", "[…redacted grid…]", text)
    # Trim oversized JSON-like blocks but keep short snippets
    text = re.sub(r"\{(?:[^{}]|\n){220,}\}", lambda m: m.group(0)[:200] + " …", text)
    return text

# ----- High-level Agent you call from UI/HUD -----
class AIAgent:
    """
    Usage:
        agent = AIAgent(HFLocalLLM())  # DeepSeek by default
        agent.ask(game, "Do you see any survivors near me?", on_done=lambda ans: chat.post("ai", ans))
    """
    def __init__(self, model: BaseLLM):
        self.model = model
        self.worker = AIWorker(model)

    def ask(self, game, question: str, on_done: Callable[[str], None]):
        try:
            state = encode_world(game)
            prompt = build_prompt(state, question)
        except Exception as e:
            on_done(f"(State encoding error: {e})")
            return

        def _finish(ans: str):
            try:
                if not ans or not ans.strip() or ans.strip().startswith("(AI error"):
                    # Fallback to heuristics if model failed
                    on_done(heuristic_answer(state, question))
                    return
                on_done(_redact_grids(ans))
            except Exception as ee:
                on_done(f"(AI fallback error: {ee})")

        self.worker.ask(prompt, _finish, system=SYSTEM_PROMPT)
