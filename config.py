"""
学霸帝AI - 配置
"""
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_DIR = os.path.join(BASE_DIR, "models")
LLAMA_DIR = os.path.join(BASE_DIR, "llama.cpp")

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
        "size_mb": "~1100",
        "fallback": "https://huggingface.co/unsloth/DeepSeek-R1-Distill-Qwen-1.5B-GGUF/resolve/main/DeepSeek-R1-Distill-Qwen-1.5B-Q4_K_M.gguf",
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
