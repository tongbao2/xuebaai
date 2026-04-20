# 📚 学霸帝AI - GGUF离线大模型应用

基于 GGUF 格式模型 + llama.cpp 的 Windows 离线 AI 对话应用。

## 功能特性

- 🤖 **离线运行** - 无需网络，本地推理
- 💾 **GGUF 模型** - 支持 Gemma-4-2B-IT、Qwen2.5-0.5B 等主流 GGUF 模型
- ⚡ **llama.cpp 引擎** - 高效 CPU 推理（支持 GPU 加速）
- 🎨 **现代 UI** - customtkinter 深色主题
- ⌨️ **流式输出** - 打字机效果实时显示
- 📥 **内置下载** - 一键下载模型，无需手动操作

## 快速开始

### 方式一：直接运行构建好的 EXE

```bash
cd study-ai/dist
双击 "学霸帝AI.exe"
```

### 方式二：从源码运行

```bash
pip install requests customtkinter

# 首次需要下载 llama-server.exe
# 从 https://github.com/ggml-org/llama.cpp/releases
# 下载 "llama-b8855-bin-win-cpu-x64.zip"
# 解压到 study-ai/llama.cpp/

python app.py
```

### 方式三：重新构建 EXE

```bash
# 双击运行 build.bat
# 或在命令行执行：
build.bat
```

## 首次使用流程

1. 启动应用
2. 选择模型（Gemma-4-2B 或 Qwen-0.5B）
3. 点击「下载模型」⬇️
4. 等待下载完成（约 3GB）
5. 点击「加载模型」🚀
6. 首次加载约 20-60 秒
7. 开始对话 💬

## 模型下载链接

| 模型 | 大小 | 下载地址 |
|------|------|---------|
| Gemma-4-2B-IT Q4_K_M | ~3 GB | https://www.modelscope.cn/models/unsloth/gemma-4-E2B-it-GGUF/resolve/master/gemma-4-E2B-it-Q4_K_M.gguf |
| Qwen2.5-0.5B-IT Q4_K_M | ~400 MB | https://www.modelscope.cn/models/Qwen/Qwen2.5-0.5B-Instruct-GGUF/resolve/master/qwen2.5-0.5b-instruct-q4_k_m.gguf |

备用源: https://huggingface.co

## 目录结构

```
study-ai/
├── app.py              # 主程序
├── config.py           # 配置
├── llama_client.py     # llama.cpp API 封装
├── build.bat           # 构建脚本
├── llama.cpp/          # llama-server.exe（需手动下载）
│   └── llama-server.exe
├── models/             # GGUF 模型文件（下载后存放于此）
│   └── *.gguf
└── dist/               # 构建输出目录
    └── 学霸帝AI.exe
```

## GPU 加速（可选）

已有 NVIDIA 显卡的用户：
1. 从 https://github.com/ggml-org/llama.cpp/releases 下载 `llama-b8855-bin-win-cuda-12.4-x64.zip`
2. 解压覆盖 `llama.cpp/` 目录

## 系统要求

- Windows 10/11 x64
- RAM: 8GB+（推荐 16GB）
- 硬盘: 10GB+（模型文件约 3GB）
- 无需显卡（CPU 模式可用）

## 技术栈

- **前端**: Python 3.12 + customtkinter
- **推理引擎**: llama.cpp (llama-server HTTP API)
- **打包**: PyInstaller
- **模型格式**: GGUF Q4_K_M

## 项目结构

```
用户交互 (customtkinter GUI)
  ↓
app.py (主程序 + UI + 状态管理)
  ↓
llama_client.py (HTTP API 客户端)
  ↓
llama-server.exe (llama.cpp, 独立进程)
  ↓
GGUF 模型文件 (*.gguf)
```
