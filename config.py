"""
学霸帝AI - 配置
"""
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# 优先从 dist/ 读取（打包后），没有则用根目录
_DIST_MODEL = os.path.join(BASE_DIR, "dist", "models")
_DIST_LLAMA = os.path.join(BASE_DIR, "dist", "llama.cpp")
MODEL_DIR = _DIST_MODEL if os.path.exists(_DIST_MODEL) else os.path.join(BASE_DIR, "models")
LLAMA_DIR = _DIST_LLAMA if os.path.exists(_DIST_LLAMA) else os.path.join(BASE_DIR, "llama.cpp")

# 模型列表
MODELS = {
    "gemma-4-E2B": {
        "name": "Gemma-4-2B-IT Q4_K_M",
        "url": "https://www.modelscope.cn/models/unsloth/gemma-4-E2B-it-GGUF/resolve/master/gemma-4-E2B-it-Q4_K_M.gguf",
        "filename": "gemma-4-E2B-it-Q4_K_M.gguf",
        "size_mb": "~3000",
        "fallback": "https://huggingface.co/unsloth/gemma-4-E2B-it-GGUF/resolve/main/gemma-4-E2B-it-Q4_K_M.gguf",
    },
    "qwen-0.5B": {
        "name": "Qwen2.5-0.5B-IT Q4_K_M",
        "url": "https://www.modelscope.cn/models/Qwen/Qwen2.5-0.5B-Instruct-GGUF/resolve/master/qwen2.5-0.5b-instruct-q4_k_m.gguf",
        "filename": "qwen2.5-0.5b-instruct-q4_k_m.gguf",
        "size_mb": "~400",
    },
    "deepseek-1.5B": {
        "name": "DeepSeek-R1-Distill-Qwen-1.5B Q4_K_M",
        "url": "https://www.modelscope.cn/models/unsloth/DeepSeek-R1-Distill-Qwen-1.5B-GGUF/resolve/master/DeepSeek-R1-Distill-Qwen-1.5B-Q4_K_M.gguf",
        "filename": "DeepSeek-R1-Distill-Qwen-1.5B-Q4_K_M.gguf",
        "size_mb": "~900",
    },
    # ── Ollama vision 模型（本地推理，自动下载）─────────────
    "ollama-moondream": {
        "name": "Moondream2（Ollama·多模态·医图）",
        "url": "ollama:pull moondream",  # Ollama 自动管理
        "size_mb": "~830",
        "manual_only": False,
        "vision": True,
        "backend": "ollama",     # llama-server vs ollama
        "ollama_model": "moondream",
        "ollama_base": "http://127.0.0.1:11434",
    },
    "ollama-llava": {
        "name": "LLaVA 1.6（Ollama·多模态·通用图）",
        "url": "ollama:pull llava",
        "size_mb": "~4100",
        "manual_only": False,
        "vision": True,
        "backend": "ollama",
        "ollama_model": "llava",
        "ollama_base": "http://127.0.0.1:11434",
    },
    # ── GGUF vision 模型（手动下载）─────────────
    "qwen2-vl-7B": {
        "name": "Qwen2-VL-7B Q4_K_M（GGUF·手动下载）",
        "url": "",   # 手动下载
        "filename": "qwen2-vl-7b-instruct-q4_k_m.gguf",
        "size_mb": "~4700",
        "manual_only": True,
        "vision": True,
        "mmproj": "qwen2-vl-7b-mmproj-q4_k_m.gguf",
        "manual_url": (
            "https://www.modelscope.cn/models/Qwen/Qwen2-VL-7B-Instruct-GGUF/"
            "resolve/master/qwen2-vl-7b-instruct-q4_k_m.gguf\n"
            "https://www.modelscope.cn/models/Qwen/Qwen2-VL-7B-Instruct-GGUF/"
            "resolve/master/qwen2-vl-7b-mmproj-q4_k_m.gguf"
        ),
    },
}

DEFAULT_MODEL_KEY = "deepseek-1.5B"

# llama-server 默认参数
LLAMA_PORT = 8080
LLAMA_CTX_SIZE = 8192
LLAMA_THREADS = 4
LLAMA_NGL = 0  # CPU模式

# 推理参数
DEFAULT_MAX_TOKENS = 512
DEFAULT_TEMPERATURE = 0.7
DEFAULT_TOP_P = 0.9

# UI
WINDOW_W = 720
WINDOW_H = 860
THEME_BG = "#0f1117"
THEME_SURFACE = "#1a1d27"
THEME_BORDER = "#2d3148"
THEME_TEXT = "#e8eaf0"
THEME_TEXT_DIM = "#7a7f99"
THEME_ACCENT = "#7c6af7"
THEME_ACCENT2 = "#5eead4"
THEME_USER = "#7c6af7"
THEME_ASSISTANT = "#1e2130"
