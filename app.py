# -*- coding: utf-8 -*-
"""
学霸帝AI  v1.0
GGUF离线大模型 + llama.cpp + customtkinter
"""
import os, sys, json, time, subprocess, threading, queue, re, base64
import tkinter as tk
import tkinter.ttk as ttk
from tkinter import messagebox, filedialog

# PIL 用于缩略图预览
try:
    from PIL import Image as PILImage, ImageTk
    HAS_PIL = True
except ImportError:
    HAS_PIL = False

try:
    import requests
except ImportError:
    messagebox.showerror("缺少依赖", "请先运行: pip install requests customtkinter")
    sys.exit(1)

try:
    import customtkinter as ctk
    HAS_CTK = True
except ImportError:
    HAS_CTK = False
    tk.messagebox.showwarning("customtkinter未安装", "将使用标准tkinter，功能受限")
    import tkinter as ctk
    class CTkBase:
        def pack(self, **kw): return super().pack(**kw)
        def configure(self, **kw): pass
        def bind(self, *a, **kw): pass
    for cls in (ctk.CTk, ctk.CTkFrame, ctk.CTkLabel, ctk.CTkButton,
                ctk.CTkTextbox, ctk.CTkSlider, ctk.CTkRadioButton,
                ctk.CTkProgressBar, ctk.CTkInputDialog):
        setattr(cls, "pack", lambda self, **kw: tk.Widget.pack(self, **kw))
        setattr(cls, "configure", lambda self, **kw: tk.Widget.configure(self, **kw) or self)
        setattr(cls, "bind", lambda self, *a, **kw: tk.Widget.bind(self, *a, **kw))

import config
from llama_client import LlamaClient


# ══════════════════════════════════════════════
#  状态
# ══════════════════════════════════════════════

class State:
    proc: subprocess.Popen | None = None
    client: LlamaClient | None = None
    loaded = False
    generating = False
    stop_flag = threading.Event()
    reply_queue: queue.Queue = queue.Queue()
    image_path: str | None = None   # 当前附加的图片路径
    ollama_model: str | None = None  # 当前 ollama 模型名（vision 用）
    ollama_base: str = "http://127.0.0.1:11434"


_state = State()

# ══════════════════════════════════════════════
#  工具
# ══════════════════════════════════════════════

def llama_exe() -> str:
    for p in [
        os.path.join(config.LLAMA_DIR, "llama-server.exe"),
        os.path.join(config.LLAMA_DIR, "bin", "llama-server.exe"),
        "llama-server.exe",
    ]:
        if os.path.exists(p):
            return p
    raise FileNotFoundError("未找到 llama-server.exe")

def model_path(key: str) -> str:
    return os.path.join(config.MODEL_DIR, config.MODELS[key]["filename"])

def model_exists(key: str) -> bool:
    info = config.MODELS[key]
    if info.get("backend") == "ollama":
        return _ollama_model_installed(info.get("ollama_model") or key)
    p = model_path(key)
    return os.path.exists(p) and os.path.getsize(p) > 1024 * 1024

def model_size_mb(key: str) -> str:
    p = model_path(key)
    if os.path.exists(p):
        mb = os.path.getsize(p) / 1024 / 1024
        return f"{mb:.0f} MB"
    return "未下载"

def launch_llama(model_key: str, port: int = 8080):
    exe = llama_exe()
    mp = model_path(model_key)
    info = config.MODELS[model_key]
    cmd = [
        exe, "-m", mp,
        "-c", str(config.LLAMA_CTX_SIZE),
        "-t", str(config.LLAMA_THREADS),
        "--port", str(port), "--host", "127.0.0.1",
        "-ngl", str(config.LLAMA_NGL),
        "--log-disable",
    ]
    # VL 视觉投影文件
    mmproj_key = info.get("mmproj") or ""
    if mmproj_key:
        # mmproj 文件应在 models/ 同目录下
        mmproj_path = os.path.join(config.MODEL_DIR, mmproj_key)
        if os.path.exists(mmproj_path):
            cmd += ["--mmproj", mmproj_path]
        else:
            print(f"[warn] mmproj not found: {mmproj_path}")
    print("[llama-server]", " ".join(cmd))
    CREATE_NO_WINDOW = 0x08000000
    return subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        creationflags=CREATE_NO_WINDOW,
    )

def _ensure_ollama_serve():
    """确保 Ollama 服务在运行"""
    import urllib.request, ssl
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    try:
        req = urllib.request.Request("http://127.0.0.1:11434/", headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=3, context=ctx):
            return  # 已在运行
    except Exception:
        pass
    # 启动 ollama serve
    ollama_exe = r"C:\Users\iMac\AppData\Local\Programs\Ollama\ollama.exe"
    subprocess.Popen([ollama_exe, "serve"],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    import time; time.sleep(3)


def _ollama_model_installed(model_name: str) -> bool:
    """检查 Ollama 模型是否已安装"""
    import subprocess
    r = subprocess.run(
        [r"C:\Users\iMac\AppData\Local\Programs\Ollama\ollama.exe", "list"],
        capture_output=True, text=True
    )
    if r.returncode != 0:
        return False
    return any(model_name in line for line in r.stdout.split("\n"))


def download_file(url: str, dest: str, progress_fn=None):
    """带进度的下载，支持断点续传"""
    import urllib.request, urllib.error

    os.makedirs(os.path.dirname(dest), exist_ok=True)
    headers = {}
    mode = "wb"
    if os.path.exists(dest):
        size = os.path.getsize(dest)
        if size > 1024 * 1024:
            headers["Range"] = f"bytes={size}-"
            mode = "ab"

    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=300) as resp:
            total = int(resp.headers.get("Content-Length", 0))
            downloaded = 0 if mode == "wb" else os.path.getsize(dest)
            with open(dest, mode) as f:
                while True:
                    chunk = resp.read(256 * 1024)
                    if not chunk:
                        break
                    f.write(chunk)
                    downloaded += len(chunk)
                    if progress_fn and total:
                        progress_fn(downloaded, total)
    except urllib.error.HTTPError as e:
        if e.code == 416:
            return  # 已是完整文件
        raise


# ══════════════════════════════════════════════
#  主界面
# ══════════════════════════════════════════════

if HAS_CTK:
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("blue")
    FONT = ("Microsoft YaHei UI", 10)
    FONT_B = ("Microsoft YaHei UI", 10, "bold")
    FONT_TITLE = ("Microsoft YaHei UI", 13, "bold")
    FONT_SM = ("Consolas", 9)
else:
    FONT = ("微软雅黑", 10)
    FONT_B = ("微软雅黑", 10, "bold")
    FONT_TITLE = ("微软雅黑", 13, "bold")
    FONT_SM = ("Consolas", 9)

C_BG = "#0d1117"
C_SUR = "#161b22"
C_BOR = "#30363d"
C_TXT = "#e6edf3"
C_DIM = "#8b949e"
C_ACC = "#bc8cff"
C_ACC2 = "#79c0ff"
C_OK = "#3fb950"
C_WN = "#d29922"
C_ER = "#f85149"
C_USR = "#bc8cff"
C_AI = "#1c2128"


class App(ctk.CTk if HAS_CTK else tk.Tk):
    def __init__(self):
        kw = {}
        if HAS_CTK:
            super().__init__()
        else:
            super().__init__()
            self.configure(bg=C_SUR)

        self.title("📚 学霸帝AI  -  离线大模型  GGUF+llama.cpp")
        self.geometry("680x920")
        self.minsize(420, 600)
        self.protocol("WM_DELETE_WINDOW", self._on_close)
        self._build_ui()
        self._refresh_ui()
        self._poll_state()

    # ── UI 构建 ──────────────────────────────────

    def _build_ui(self):
        # 标题栏
        hdr = ctk.CTkFrame(self, fg_color=C_SUR, height=46)
        hdr.pack(fill="x", padx=0, pady=0)
        hdr.pack_propagate(False)

        ctk.CTkLabel(hdr, text="📚 学霸帝AI 离线大模型",
                     font=FONT_TITLE, text_color=C_ACC
                     ).pack(side="left", padx=16, pady=8)

        self._status = ctk.CTkLabel(hdr, text="⚠️ 请下载并加载模型",
                                     font=("微软雅黑", 10), text_color=C_WN)
        self._status.pack(side="right", padx=16, pady=8)

        main = ctk.CTkFrame(self, fg_color="transparent")
        main.pack(fill="both", expand=True, padx=10, pady=(6, 4))

        # ── 模型区 ──
        mdl_f = ctk.CTkFrame(main, fg_color=C_SUR, corner_radius=10)
        mdl_f.pack(fill="x", pady=(0, 5))

        ctk.CTkLabel(mdl_f, text="🤖  模型选择", font=FONT_B,
                     text_color=C_ACC).pack(anchor="w", padx=14, pady=(10, 4))

        self._model_var = ctk.StringVar(value=config.DEFAULT_MODEL_KEY)
        rb_f = ctk.CTkFrame(mdl_f, fg_color="transparent")
        rb_f.pack(fill="x", padx=14, pady=(0, 6))
        for key, info in config.MODELS.items():
            ctk.CTkRadioButton(
                rb_f,
                text=f"{info['name']}  ({info['size_mb']} MB)",
                variable=self._model_var, value=key,
                font=FONT, radiobutton_height=16, radiobutton_width=16,
                command=self._refresh_ui,
            ).pack(side="left", padx=(0, 14))

        btn_f = ctk.CTkFrame(mdl_f, fg_color="transparent")
        btn_f.pack(fill="x", padx=14, pady=(0, 6))

        self._dl_btn = ctk.CTkButton(
            btn_f, text="⬇️  下载模型", width=118, height=32,
            font=FONT_B, corner_radius=8,
            fg_color="#b45309", hover_color="#92400e",
            command=self._on_download,
        )
        self._dl_btn.pack(side="left", padx=(0, 8))

        self._load_btn = ctk.CTkButton(
            btn_f, text="🚀 加载模型", width=118, height=32,
            font=FONT_B, corner_radius=8,
            fg_color=C_ACC, hover_color="#9d6fdd",
            command=self._on_load, state="disabled",
        )
        self._load_btn.pack(side="left", padx=(0, 8))

        self._unload_btn = ctk.CTkButton(
            btn_f, text="⛔ 卸载", width=88, height=32,
            font=FONT, corner_radius=8,
            fg_color="#3d4148", hover_color="#2d3138",
            command=self._on_unload, state="disabled",
        )
        self._unload_btn.pack(side="left")

        self._model_lbl = ctk.CTkLabel(
            mdl_f, text="", font=FONT_SM, text_color=C_DIM, anchor="w",
        )
        self._model_lbl.pack(fill="x", padx=14, pady=(0, 4))

        # 进度条（下载用）
        self._pbar = ctk.CTkProgressBar(mdl_f, height=5, corner_radius=3,
                                         progress_color=C_ACC)
        self._pbar.set(0)
        self._pbar.pack(fill="x", padx=14, pady=(0, 2))
        self._pbar.pack_forget()

        self._pbar_lbl = ctk.CTkLabel(mdl_f, text="", font=FONT_SM,
                                        text_color=C_DIM, anchor="w")
        self._pbar_lbl.pack(fill="x", padx=14, pady=(0, 6))
        self._pbar_lbl.pack_forget()

        # ── 对话区 ──
        chat_f = ctk.CTkFrame(main, fg_color=C_SUR, corner_radius=10)
        chat_f.pack(fill="both", expand=True, pady=(0, 5))

        # 欢迎语
        self._chat = ctk.CTkTextbox(
            chat_f, fg_color=C_BG,
            font=FONT, text_color=C_TXT,
            border_width=0, corner_radius=0,
            state="normal", wrap="word",
        )
        self._chat.pack(fill="both", expand=True, padx=6, pady=(6, 4))
        self._chat.insert("1.0",
            "📖 欢迎使用 学霸帝AI\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "首次使用请先「下载模型」，\n"
            "下载完成后点击「加载模型」启动推理引擎。\n\n"
            "⚡ 支持 GGUF 格式模型，本地离线运行，\n"
            "   无需联网，保护隐私。\n\n"
            "💡 快捷键：Ctrl+Enter 发送\n"
            "━━━━━━━━━━━━━━━━━━━━\n\n"
        )
        self._chat.configure(state="disabled")

        self._chat.tag_config("usr", foreground=C_USR)
        self._chat.tag_config("ai", foreground=C_TXT)
        self._chat.tag_config("sys", foreground=C_DIM)
        self._chat.tag_config("hdr", foreground=C_ACC)

        # ── 输入区 ──
        inp_f = ctk.CTkFrame(main, fg_color=C_SUR, corner_radius=10)
        inp_f.pack(fill="x", pady=0)

        self._inp = ctk.CTkTextbox(
            inp_f, height=76,
            fg_color=C_BG, font=FONT, text_color=C_TXT,
            border_width=1, border_color=C_BOR, corner_radius=8,
        )
        self._inp.pack(fill="x", padx=8, pady=(8, 4))
        self._inp.bind("<Control-Return>", lambda e: self._on_send())

        # ── 图片预览区 ──
        self._img_f = ctk.CTkFrame(inp_f, fg_color="transparent")
        self._img_f.pack(fill="x", padx=8, pady=(0, 2))
        self._img_lbl = ctk.CTkLabel(self._img_f, text="", font=FONT_SM,
                                      text_color=C_DIM, anchor="w")
        self._img_lbl.pack(side="left")
        self._img_canvas = tk.Canvas(
            self._img_f, width=80, height=80,
            bg=C_BG, highlightthickness=0, cursor="hand2"
        )
        self._img_canvas.pack(side="left", padx=(0, 4))
        self._img_canvas.bind("<Button-1>", lambda e: self._on_rmimg())
        self._img_tk = [None]   # keep ref to avoid GC
        self._img_canvas.pack_forget()
        self._rmimg_btn = ctk.CTkButton(
            self._img_f, text="✕ 移除图片", width=90, height=26,
            font=("微软雅黑", 9), corner_radius=6,
            fg_color="#b91c1c", hover_color="#991b1b",
            command=self._on_rmimg,
        )
        self._rmimg_btn.pack(side="right")
        self._rmimg_btn.pack_forget()

        act_f = ctk.CTkFrame(inp_f, fg_color="transparent")
        act_f.pack(fill="x", padx=8, pady=(0, 6))

        self._send_btn = ctk.CTkButton(
            act_f, text="💬 发送", width=100, height=34,
            font=FONT_B, corner_radius=8,
            fg_color=C_ACC, hover_color="#9d6fdd",
            command=self._on_send, state="disabled",
        )
        self._send_btn.pack(side="right")

        self._stop_btn = ctk.CTkButton(
            act_f, text="⏹ 停止", width=80, height=34,
            font=FONT, corner_radius=8,
            fg_color="#b91c1c", hover_color="#991b1b",
            command=self._on_stop, state="disabled",
        )
        self._stop_btn.pack(side="right", padx=(0, 8))

        self._clear_btn = ctk.CTkButton(
            act_f, text="🗑 清空", width=80, height=34,
            font=FONT, corner_radius=8,
            fg_color="#3d4148", hover_color="#2d3138",
            command=self._on_clear,
        )
        self._clear_btn.pack(side="left")

        self._img_btn = ctk.CTkButton(
            act_f, text="📷 上传图片", width=110, height=34,
            font=FONT_B, corner_radius=8,
            fg_color="#1f6feb", hover_color="#1a5bc4",
            command=self._on_img,
        )
        self._img_btn.pack(side="left", padx=(0, 8))

        self._img_note_lbl = ctk.CTkLabel(
            act_f, text="",
            font=FONT_SM, text_color=C_DIM,
        )
        self._img_note_lbl.pack(side="left", padx=(2, 0))

        # 参数滑条
        prm_f = ctk.CTkFrame(inp_f, fg_color="transparent")
        prm_f.pack(fill="x", pady=(0, 4))

        ctk.CTkLabel(prm_f, text="温度", font=FONT_SM, text_color=C_DIM
                     ).pack(side="left")
        self._temp_v = ctk.DoubleVar(value=0.7)
        s = ctk.CTkSlider(prm_f, from_=0.1, to=2.0, number_of_steps=19,
                           variable=self._temp_v, width=110,
                           progress_color=C_ACC)
        s.pack(side="left", padx=(4, 0))
        self._temp_lbl = ctk.CTkLabel(prm_f, text="0.70", font=FONT_SM,
                                        text_color=C_DIM)
        self._temp_lbl.pack(side="left", padx=(4, 12))
        self._temp_v.trace("w", lambda *_: self._temp_lbl.configure(
            text=f"{self._temp_v.get():.2f}"))

        ctk.CTkLabel(prm_f, text="MaxTokens", font=FONT_SM, text_color=C_DIM
                     ).pack(side="left", padx=(8, 0))
        self._mt_v = ctk.IntVar(value=512)
        ms = ctk.CTkSlider(prm_f, from_=64, to=2048, number_of_steps=15,
                            variable=self._mt_v, width=100,
                            progress_color=C_ACC)
        ms.pack(side="left", padx=(4, 0))
        self._mt_lbl = ctk.CTkLabel(prm_f, text="512", font=FONT_SM,
                                      text_color=C_DIM)
        self._mt_lbl.pack(side="left", padx=(4, 0))
        self._mt_v.trace("w", lambda *_: self._mt_lbl.configure(
            text=str(self._mt_v.get())))

    # ── 聊天辅助 ─────────────────────────────────

    def _chat_append(self, role: str, text: str):
        self._chat.configure(state="normal")
        icon = {"usr": "👤", "ai": "🤖", "sys": "ℹ️"}.get(role, "")
        self._chat.insert("end", f"{icon} {text}\n\n")
        self._chat.see("end")
        self._chat.configure(state="disabled")

    def _chat_stream(self, role: str, initial: str = ""):
        """返回上下文管理器，在块内可多次调用更新"""
        class StreamCtx:
            def __init__(ctx, chat_widget, role, icon):
                ctx._c = chat_widget
                ctx._role = role
                ctx._icon = icon
                ctx._buf = ""
                ctx._started = False

            def __enter__(ctx2):
                ctx2._c.configure(state="normal")
                ctx2._c.insert("end", f"{ctx2._icon} {initial}")
                ctx2._c.see("end")
                ctx2._c.configure(state="disabled")
                return ctx2

            def write(ctx2, text: str):
                ctx2._buf += text
                ctx2._c.configure(state="normal")
                ctx2._c.insert("end", text)
                ctx2._c.see("end")
                ctx2._c.configure(state="disabled")

            def __exit__(ctx2, *a):
                pass

        return StreamCtx(self._chat, role, {"usr": "👤", "ai": "🤖", "sys": "ℹ️"}.get(role, ""))

    # ── 状态刷新 ─────────────────────────────────

    def _refresh_ui(self, msg: str = None):
        key = self._model_var.get()
        info = config.MODELS[key]
        has = model_exists(key)
        sz = model_size_mb(key)

        if msg:
            self._status.configure(text=msg)
            return

        is_ollama = info.get("backend") == "ollama"
        if is_ollama:
            self._model_lbl.configure(
                text=f"Ollama 模型: {info.get('ollama_model', key)}  |  {info['size_mb']} MB",
                text_color=C_DIM,
            )
        else:
            self._model_lbl.configure(
                text=f"模型路径: {model_path(key)}  |  {sz}",
                text_color=C_DIM,
            )

        if _state.loaded:
            is_ollama = info.get("backend") == "ollama"
            port_txt = "(Ollama)" if is_ollama else f"http://127.0.0.1:{config.LLAMA_PORT}"
            self._status.configure(text=f"✅ {info['name']} 已加载  {port_txt}",
                                    text_color=C_OK)
            self._load_btn.configure(state="disabled", text="✅ 已加载")
            self._unload_btn.configure(state="normal")
            self._send_btn.configure(state="normal")
        elif has:
            ollama_info = "（Ollama 已安装）" if is_ollama else f"已下载({sz})"
            self._status.configure(text=f"📦 {info['name']} {ollama_info}，点击「加载模型」",
                                    text_color=C_WN)
            dl_text = "⬇️ 已安装" if is_ollama else "⬇️ 已下载"
            dl_hint = "下载" if not is_ollama else "安装"
            self._load_btn.configure(state="normal", text="🚀 加载模型")
            self._dl_btn.configure(text=dl_text)
            self._unload_btn.configure(state="disabled")
            self._send_btn.configure(state="disabled")
        else:
            dl_hint = "安装" if is_ollama else "下载"
            self._status.configure(text=f"⚠️ {info['name']} 未{dl_hint}，点击「下载模型」",
                                    text_color=C_ER)
            self._load_btn.configure(state="disabled", text="🚀 加载模型")
            self._unload_btn.configure(state="disabled")
            self._send_btn.configure(state="disabled")

        self._stop_btn.configure(
            state="normal" if _state.generating else "disabled"
        )

        # 图片按钮提示文字
        if _state.loaded and info.get("backend") == "ollama":
            self._img_note_lbl.configure(text="（视觉模式·上传图片）", text_color=C_ACC2)
        elif _state.loaded and info.get("vision"):
            self._img_note_lbl.configure(text="（需 GGUF vision 模型才可识图）", text_color=C_WN)
        else:
            self._img_note_lbl.configure(text="")

    # ── 图片 ───────────────────────────────────

    def _on_img(self):
        path = filedialog.askopenfilename(
            title="选择图片",
            filetypes=[
                ("图片文件", "*.png *.jpg *.jpeg *.gif *.bmp *.webp"),
                ("所有文件", "*.*"),
            ],
        )
        if not path:
            return
        if not HAS_PIL:
            messagebox.showwarning("缺少 PIL",
                "请安装 Pillow: pip install Pillow")
            return

        try:
            _state.image_path = path
            img = PILImage.open(path)
            img.thumbnail((80, 80))
            tk_img = ImageTk.PhotoImage(img)
            self._img_tk[0] = tk_img
            self._img_canvas.delete("all")
            self._img_canvas.create_image(40, 40, image=tk_img)
            self._img_lbl.configure(
                text=f"📎 {os.path.basename(path)}",
                text_color=C_ACC,
            )
            self._img_canvas.pack(side="left", padx=(0, 4))
            self._rmimg_btn.pack(side="right")
            self._img_f.pack(fill="x", padx=8, pady=(0, 2))
        except Exception as e:
            messagebox.showerror("图片加载失败", str(e))
            _state.image_path = None

    def _on_rmimg(self):
        _state.image_path = None
        self._img_tk[0] = None
        self._img_canvas.delete("all")
        self._img_canvas.pack_forget()
        self._rmimg_btn.pack_forget()
        self._img_lbl.configure(text="", text_color=C_DIM)
        self._img_f.pack_forget()

    def _poll_state(self):
        """定时刷新 UI"""
        self.after(500, self._poll_state)

    # ── 下载 ────────────────────────────────────

    def _on_download(self):
        key = self._model_var.get()
        info = config.MODELS[key]
        dest = model_path(key)

        # ── Ollama 模型：直接 pull ────────────────
        if info.get("backend") == "ollama":
            ollama_name = info.get("ollama_model") or key
            if _ollama_model_installed(ollama_name):
                messagebox.showinfo("模型已安装",
                    f"{info['name']} 已安装，可以直接加载。")
                return
            self._pbar.pack(fill="x", padx=14, pady=(0, 2))
            self._pbar_lbl.pack(fill="x", padx=14, pady=(0, 6))
            self._pbar.configure(progress_color=C_ACC)
            self._pbar.set(0)
            self._dl_btn.configure(state="disabled", text="安装中...")
            self._load_btn.configure(state="disabled")

            def pull_task():
                p = subprocess.Popen(
                    [r"C:\Users\iMac\AppData\Local\Programs\Ollama\ollama.exe", "pull", ollama_name],
                    stdout=subprocess.PIPE, stderr=subprocess.STDOUT
                )
                for raw in iter(p.stdout.readline, b''):
                    line = raw.decode('utf-8', errors='replace').rstrip()
                    if '%' in line:
                        # 解析进度
                        import re
                        m = re.search(r'(\d+)%', line)
                        if m:
                            pct = int(m.group(1)) / 100
                            self.after(0, lambda v=pct, l=line[:60]: (
                                self._pbar.set(v),
                                self._pbar_lbl.configure(text=l[:60])
                            ))
                p.wait()
                if p.returncode == 0:
                    self.after(0, self._dl_done_ollama)
                else:
                    self.after(0, lambda: self._dl_error("Ollama pull 失败"))
            threading.Thread(target=pull_task, daemon=True).start()
            return

        # ── 手动下载模型：只展示下载地址 ────────────────
        if info.get("manual_only"):
            if model_exists(key):
                messagebox.showinfo("模型已存在",
                    f"{info['name']} 已下载，直接加载即可。")
            else:
                msg = f"📥 {info['name']}\n\n" \
                      f"大小: {info['size_mb']}\n\n" \
                      f"请手动下载后放入 models/ 目录:\n{info.get('manual_url', info['url'] or '（无下载地址）')}"
                try:
                    self.clipboard_clear()
                    self.clipboard_append(info.get("manual_url") or "")
                except Exception:
                    pass
                messagebox.showinfo("手动下载", msg + "\n\n（下载地址已复制到剪贴板）")
            return

        if model_exists(key):
            if messagebox.askyesno("模型已存在",
                f"{info['name']} 已存在，可以直接加载。是否重新下载？"):
                os.remove(dest)
            else:
                return

        self._pbar.pack(fill="x", padx=14, pady=(0, 2))
        self._pbar_lbl.pack(fill="x", padx=14, pady=(0, 6))
        self._pbar.set(0)
        self._dl_btn.configure(state="disabled", text="下载中...")

        def dl_task():
            def prog(dl, total):
                pct = dl / total * 100
                self.after(0, lambda: (
                    self._pbar.set(pct / 100),
                    self._pbar_lbl.configure(
                        text=f"下载中: {dl/1024/1024:.1f} / {total/1024/1024:.1f} MB  ({pct:.1f}%)")
                ))
            try:
                download_file(info["url"], dest, progress_fn=prog)
                self.after(0, self._dl_done)
            except Exception as e:
                self.after(0, lambda: self._dl_error(str(e)))

        threading.Thread(target=dl_task, daemon=True).start()

    def _dl_done(self):
        self._pbar.set(1.0)
        self._pbar_lbl.configure(text="下载完成！")
        self._dl_btn.configure(state="normal", text="⬇️ 已下载")
        self._refresh_ui()
        messagebox.showinfo("下载完成", "模型下载成功！\n点击「加载模型」启动推理引擎。")

    def _dl_done_ollama(self):
        self._pbar.set(1.0)
        self._pbar_lbl.configure(text="安装完成！")
        self._dl_btn.configure(state="normal", text="⬇️ 已安装")
        self._refresh_ui()
        messagebox.showinfo("安装完成", "Ollama 视觉模型安装成功！\n点击「加载模型」启动。")

    def _dl_error(self, err: str):
        self._pbar_lbl.configure(text=f"下载失败: {err}", text_color=C_ER)
        self._dl_btn.configure(state="normal", text="⬇️ 重试下载")
        messagebox.showerror("下载失败", err)

    # ── 加载模型 ────────────────────────────────

    def _on_load(self):
        key = self._model_var.get()
        info = config.MODELS[key]

        # ── Ollama vision 模型 ───────────────────
        if info.get("backend") == "ollama":
            ollama_model = info.get("ollama_model") or key
            self._status.configure(text=f"🤖 Ollama 视觉模式: {ollama_model}", text_color=C_WN)
            self._load_btn.configure(state="disabled", text="加载中...")
            self._dl_btn.configure(state="disabled")

            def load_task():
                try:
                    # 确保 ollama serve 在运行
                    _ensure_ollama_serve()
                    _state.ollama_model = ollama_model
                    _state.ollama_base = info.get("ollama_base", "http://127.0.0.1:11434")
                    _state.client = None   # ollama 不走 LlamaClient
                    _state.loaded = True
                    self.after(0, self._load_done_ollama)
                except Exception as e:
                    self.after(0, lambda: self._load_error(str(e)))
            threading.Thread(target=load_task, daemon=True).start()
            return

        # ── GGUF 模型（原有逻辑）──────────────────
        if not model_exists(key):
            messagebox.showwarning("未找到模型", "请先下载模型")
            return

        if info.get("vision") and info.get("mmproj"):
            mmproj_path = os.path.join(config.MODEL_DIR, info["mmproj"])
            if not os.path.exists(mmproj_path):
                self.after(0, lambda: messagebox.showwarning(
                    "缺少 mmproj 文件",
                    f"Qwen2-VL 需要 mmproj 视觉投影文件才能识别图片。\n"
                    f"请将以下文件放入 models/ 目录:\n{info['mmproj']}\n\n"
                    f"下载地址已在上次下载提示中复制到剪贴板。\n"
                    f"如不加载图片，可忽略此警告继续。"))

        self._status.configure(text="🚀 正在启动 llama-server（首次约30秒）...",
                                text_color=C_WN)
        self._load_btn.configure(state="disabled", text="加载中...")
        self._dl_btn.configure(state="disabled")

        def load_task():
            try:
                _state.proc = launch_llama(key, config.LLAMA_PORT)
                _state.client = LlamaClient(
                    model_path(key),
                    port=config.LLAMA_PORT,
                    mmproj=config.MODELS[key].get("mmproj"),
                )
                _state.client.bind_proc(_state.proc)
                ok = _state.client.wait_ready(timeout=180)
                if ok:
                    _state.loaded = True
                    self.after(0, self._load_done)
                else:
                    _state.proc.terminate()
                    self.after(0, lambda: self._load_error("加载超时，模型文件可能损坏"))
            except Exception as e:
                self.after(0, lambda: self._load_error(str(e)))

        threading.Thread(target=load_task, daemon=True).start()

    def _load_done(self):
        self._refresh_ui(f"✅ 模型加载完成！")
        self._chat_append("sys", "🤖 学霸帝AI已就绪！请输入问题。")
        self._dl_btn.configure(state="normal")

    def _load_done_ollama(self):
        key = self._model_var.get()
        info = config.MODELS[key]
        self._status.configure(
            text=f"✅ {info['name']} 已就绪  (Ollama)",
            text_color=C_OK)
        self._load_btn.configure(state="disabled", text="✅ 已加载")
        self._unload_btn.configure(state="normal")
        self._send_btn.configure(state="normal")
        self._dl_btn.configure(state="normal")
        self._chat_append("sys", "📷 视觉模式已就绪！可上传图片。")

    def _load_error(self, err: str):
        self._refresh_ui(f"❌ 加载失败: {err}")
        self._load_btn.configure(state="normal", text="🚀 重新加载")
        self._dl_btn.configure(state="normal")
        messagebox.showerror("加载失败", err)

    # ── 卸载模型 ────────────────────────────────

    def _on_unload(self):
        if _state.proc:
            _state.proc.terminate()
            _state.proc = None
        _state.loaded = False
        _state.client = None
        _state.generating = False
        _state.ollama_model = None
        self._refresh_ui("⚠️ 模型已卸载")
        self._chat_append("sys", "模型已卸载。")

    # ── 发送 ────────────────────────────────────

    def _on_send(self):
        if not _state.loaded or _state.generating:
            return
        text = self._inp.get("1.0", "end").strip()
        if not text:
            return
        self._inp.delete("1.0", "end")

        # 收集图片信息
        img_path = _state.image_path
        img_preview = None
        if img_path:
            # 缩略图用于聊天区展示
            try:
                if HAS_PIL:
                    pil_img = PILImage.open(img_path)
                    pil_img.thumbnail((160, 160))
                    img_preview = ImageTk.PhotoImage(pil_img)
            except Exception:
                pass
            # 清输入区的图片预览
            self._on_rmimg()

        # 追加图片文件名到对话
        img_label = f"\n[📎 图片: {os.path.basename(img_path)}]\n" if img_path else ""
        self._chat_append("usr", text + img_label)

        # 聊天区展示缩略图
        if img_preview:
            self._chat.configure(state="normal")
            lbl = ctk.CTkLabel(self._chat, image=img_preview, text="")
            lbl.image = img_preview  # keep ref
            self._chat.window_create("end", window=lbl)
            self._chat.insert("end", "\n\n")
            self._chat.see("end")
            self._chat.configure(state="disabled")

        _state.generating = True
        _state.stop_flag.clear()
        self._refresh_ui()
        self._send_btn.configure(state="disabled")

        def infer():
            client: LlamaClient = _state.client
            system = (
                "你是「学霸帝」，一个友善、专业的AI学习助手。"
                "请用中文回答，简洁有条理，适当使用列表或分段。\n"
                "回答内容应准确、有帮助，符合学生和老师的使用习惯。"
            )
            buf = []
            ctx = self._chat_stream("ai", "")

            # 如果有图片，Base64 拼入 prompt
            final_text = text
            if img_path:
                try:
                    b64 = base64.b64encode(open(img_path, "rb").read()).decode("ascii")
                    ext = os.path.splitext(img_path)[1].lstrip(".").lower()
                    mime = {"jpg": "jpeg", "png": "png", "gif": "gif",
                            "bmp": "bmp", "webp": "webp"}.get(ext, "jpeg")
                    final_text = (
                        f"[图片(={mime};base64,{b64}=)]\n"
                        f"请描述这张图片，并回答以下问题：\n{text}"
                    )
                except Exception as e:
                    pass

            try:
                with ctx:
                    if _state.client is None:  # ── Ollama vision 模式 ──
                        import urllib.request, ssl, json as json_mod
                        b64_img = None
                        if img_path:
                            try:
                                b64_img = base64.b64encode(open(img_path, "rb").read()).decode("ascii")
                            except Exception:
                                pass
                        payload = {
                            "model": _state.ollama_model,
                            "prompt": text,
                            "stream": True,
                            "options": {
                                "temperature": self._temp_v.get(),
                                "num_predict": self._mt_v.get(),
                            }
                        }
                        if b64_img:
                            payload["images"] = [b64_img]
                        body = json_mod.dumps(payload).encode("utf-8")
                        ssl_ctx = ssl.create_default_context()
                        ssl_ctx.check_hostname = False
                        ssl_ctx.verify_mode = ssl.CERT_NONE
                        req = urllib.request.Request(
                            _state.ollama_base + "/api/generate",
                            data=body,
                            headers={"Content-Type": "application/json"},
                            method="POST"
                        )
                        with urllib.request.urlopen(req, timeout=300, context=ssl_ctx) as resp:
                            for line in resp:
                                line = line.decode("utf-8", errors="replace").strip()
                                if not line:
                                    continue
                                try:
                                    chunk = json_mod.loads(line)
                                    tok = chunk.get("response", "")
                                    if _state.stop_flag.is_set():
                                        break
                                    buf.append(tok)
                                    ctx.write(tok)
                                except Exception:
                                    pass
                    else:  # ── GGUF llama-server 模式 ──
                        for tok in client.infer_stream(
                            prompt=final_text,
                            system=system,
                            max_tokens=self._mt_v.get(),
                            temperature=self._temp_v.get(),
                        ):
                            if _state.stop_flag.is_set():
                                ctx.write("\n\n[已停止]")
                                break
                            buf.append(tok)
                            ctx.write(tok)
            except Exception as e:
                self.after(0, lambda: self._chat_append("sys", f"⚠️ 错误: {e}"))
            finally:
                _state.generating = False
                self.after(0, self._refresh_ui)

        threading.Thread(target=infer, daemon=True).start()

    # ── 停止 / 清空 ─────────────────────────────

    def _on_stop(self):
        _state.stop_flag.set()
        self._chat_append("sys", "⏹ 已发送停止信号")

    def _on_clear(self):
        self._chat.configure(state="normal")
        self._chat.delete("1.0", "end")
        self._chat.configure(state="disabled")

    # ── 关闭 ────────────────────────────────────

    def _on_close(self):
        if _state.proc:
            try:
                _state.proc.terminate()
                _state.proc.wait(timeout=5)
            except Exception:
                pass
        self.destroy()


# ══════════════════════════════════════════════
#  入口
# ══════════════════════════════════════════════

def main():
    # PyInstaller 路径修正
    if getattr(sys, "frozen", False):
        app_dir = os.path.dirname(sys.executable)
        config.LLAMA_DIR = os.path.join(app_dir, "llama.cpp")
        config.MODEL_DIR = os.path.join(app_dir, "models")

    print("=" * 50)
    print(" 学霸帝AI  GGUF离线大模型")
    print("=" * 50)
    print(f"  Python : {sys.version}")
    print(f"  模型目录: {config.MODEL_DIR}")
    print(f"  llama目录: {config.LLAMA_DIR}")
    print(f"  默认模型: {config.MODELS[config.DEFAULT_MODEL_KEY]['name']}")
    print("=" * 50)

    App().mainloop()

if __name__ == "__main__":
    main()
