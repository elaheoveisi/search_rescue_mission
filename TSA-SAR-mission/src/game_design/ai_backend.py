# src/ai/ai_backend.py
import threading, queue, time
from typing import Optional, Callable

# ---------- Base Class and Worker ----------

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
                cb(f"[AI error] {e}")
            time.sleep(0.01)

# ---------- Lightweight Local Backends ----------

class EchoLLM(BaseLLM):
    """A fallback LLM that simply echoes the user's prompt."""
    def __init__(self, note="echo backend"):
        self.note = note
    def generate(self, prompt: str, system: Optional[str] = None) -> str:
        return f"({self.note}) You asked: {prompt}"

class HFLocalLLM(BaseLLM):
    """Local Hugging Face transformers backend."""
    def __init__(self, model_name: str = "deepseek-ai/deepseek-llm-7b-chat"):
        try:
            from transformers import AutoModelForCausalLM, AutoTokenizer, pipeline
            import torch

            self.model_name = model_name
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            
            use_cuda = torch.cuda.is_available()
            torch_dtype = torch.float16 if use_cuda else torch.float32

            self.pipe = pipeline(
                "text-generation",
                model=AutoModelForCausalLM.from_pretrained(
                    self.model_name,
                    device_map="auto",
                    torch_dtype=torch_dtype,
                ),
                tokenizer=self.tokenizer,
                return_full_text=False,
                max_new_tokens=256,
                # The 'device' argument is removed here to fix the conflict with 'device_map'
            )
            print(f"HFLocalLLM: Successfully loaded '{self.model_name}' on {'GPU' if use_cuda else 'CPU'}.")
        except Exception as e:
            print(f"FATAL: Failed to load Hugging Face model. Using fallback. Error: {e}")
            self.pipe = None
            self.fallback = EchoLLM(note=f"HF model failed to load")

    def generate(self, prompt: str, system: Optional[str] = None) -> str:
        if not self.pipe:
            return self.fallback.generate(prompt, system)

        if hasattr(self.tokenizer, "apply_chat_template"):
            messages = [{"role": "system", "content": system}, {"role": "user", "content": prompt}] if system else [{"role": "user", "content": prompt}]
            text_in = self.tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
        else:
            text_in = (system + "\n\n" if system else "") + prompt
        
        generation_args = {"max_length": 4096}
        out = self.pipe(text_in, **generation_args)
        return out[0]["generated_text"].strip()


class LlamaCppLLM(BaseLLM):
    """Local Llama.cpp backend for running GGUF-quantized models."""
    def __init__(self, gguf_path: str, n_ctx: int = 4096, n_gpu_layers: int = 0, n_threads: int = 4, max_tokens: int = 256):
        from llama_cpp import Llama
        self.max_tokens = max_tokens
        self.llm = Llama(model_path=gguf_path, n_ctx=n_ctx, n_gpu_layers=n_gpu_layers, n_threads=n_threads)

    def generate(self, prompt: str, system: Optional[str] = None) -> str:
        full = f"<<SYS>>{system}<<EOS>>\n{prompt}" if system else prompt
        res = self.llm(prompt=full, max_tokens=self.max_tokens, temperature=0.7, top_p=0.95)
        return res["choices"][0]["text"].strip()