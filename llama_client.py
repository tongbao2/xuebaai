"""
学霸帝AI - llama.cpp HTTP API 客户端
"""
import requests
import json
import time


class LlamaClient:
    """封装 llama-server HTTP API"""

    def __init__(self, model_path: str, port: int = 8080,
                 ctx_size: int = 8192, threads: int = 4, ngl: int = 0,
                 mmproj: str = None):
        self.model_path = model_path
        self.base_url = f"http://127.0.0.1:{port}"
        self.port = port
        self.ctx_size = ctx_size
        self.threads = threads
        self.ngl = ngl
        self.mmproj = mmproj          # vision 投影文件路径（可为空）
        self._proc = None
        self._loaded = False

    @property
    def is_ready(self) -> bool:
        """检测服务器是否就绪（模型加载完成）"""
        try:
            r = requests.get(f"{self.base_url}/v1/models", timeout=3)
            return r.status_code == 200
        except requests.exceptions.ConnectionError:
            return False
        except Exception:
            return False

    def bind_proc(self, proc):
        self._proc = proc

    def wait_ready(self, timeout=180) -> bool:
        """轮询等待服务器就绪"""
        for i in range(timeout):
            if self.is_ready:
                self._loaded = True
                return True
            time.sleep(1)
        return False

    def infer_stream(self, prompt: str, system: str = "",
                     max_tokens: int = 512,
                     temperature: float = 0.7,
                     top_p: float = 0.9,
                     stop: list = None):
        """
        流式推理，yield 每个 token chunk
        """
        if not self._loaded:
            raise RuntimeError("模型未加载")

        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "messages": messages,
            "stream": True,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "top_p": top_p,
            "stop": stop or ["<|im_end|>", "<|end_of_text|>"],
        }

        try:
            with requests.post(
                f"{self.base_url}/v1/chat/completions",
                json=payload,
                stream=True,
                timeout=300,
            ) as resp:
                if resp.status_code != 200:
                    body = resp.text[:500]
                    raise RuntimeError(f"推理失败 HTTP {resp.status_code}: {body}")

                for line in resp.iter_lines():
                    if not line:
                        continue
                    if line.startswith(b"data: "):
                        data = line[6:]
                        if data == b"[DONE]":
                            break
                        try:
                            obj = json.loads(data)
                            choices = obj.get("choices", [])
                            if choices:
                                delta = choices[0].get("delta", {})
                                content = delta.get("content", "")
                                if content:
                                    yield content
                        except json.JSONDecodeError:
                            pass
        except requests.exceptions.Timeout:
            raise RuntimeError("推理超时，请减少 MaxTokens 或使用更小的模型")

    def get_models(self) -> dict:
        try:
            r = requests.get(f"{self.base_url}/v1/models", timeout=3)
            return r.json() if r.status_code == 200 else {}
        except:
            return {}
