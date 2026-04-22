# -*- coding: utf-8 -*-
"""
学霸帝AI - 中文 OCR 引擎（RapidOCR / PaddleOCR ONNX）
支持中英混排识别，离线运行
"""
import os
import sys

# Fix console encoding for print with emoji/special chars
if getattr(sys, 'frozen', False):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

_ocr = None
_ocr_available = False
_IMPORT_ERROR = None


def _get_rapidocr_path():
    """获取 rapidocr_onnxruntime 包的根路径（兼容 PyInstaller）"""
    if getattr(sys, 'frozen', False):
        # PyInstaller --onefile: 数据解压到 sys._MEIPASS
        return os.path.join(sys._MEIPASS, 'rapidocr_onnxruntime')
    else:
        import rapidocr_onnxruntime
        return os.path.dirname(rapidocr_onnxruntime.__file__)


def _init_ocr():
    """延迟初始化 OCR 引擎"""
    global _ocr, _ocr_available, _IMPORT_ERROR
    if _ocr is not None or _IMPORT_ERROR is not None:
        return

    try:
        from rapidocr_onnxruntime import RapidOCR
        # 指定模型目录
        rapidocr_root = _get_rapidocr_path()
        config_path = os.path.join(rapidocr_root, 'config.yaml')
        if os.path.exists(config_path):
            _ocr = RapidOCR(config_path)
            _ocr_available = True
            print(f"[OCR] RapidOCR 初始化成功 (config: {config_path})")
        else:
            _ocr = RapidOCR()
            _ocr_available = True
            print("[OCR] RapidOCR 初始化成功 (default config)")
    except ImportError:
        _IMPORT_ERROR = "rapidocr_onnxruntime 未安装，请运行: pip install rapidocr_onnxruntime"
        print("[OCR]", _IMPORT_ERROR)
    except Exception as e:
        _IMPORT_ERROR = f"OCR 初始化失败: {e}"
        print("[OCR] 错误:", e)


def is_available() -> bool:
    """检查 OCR 是否可用"""
    _init_ocr()
    return _ocr_available


def get_error() -> str | None:
    """获取初始化错误信息"""
    _init_ocr()
    return _IMPORT_ERROR


def recognize_file(image_path: str) -> str:
    """
    识别图片文件中的文字
    @param image_path 图片文件路径
    @return 识别到的文字，多行拼接；失败返回空字符串
    """
    if not os.path.exists(image_path):
        return ""
    _init_ocr()
    if not _ocr_available:
        return ""

    try:
        result, _ = _ocr(image_path)
        if result is None or len(result) == 0:
            return ""
        # result: list of [bbox, text, confidence]
        lines = [item[1] for item in result if item[1]]
        return "\n".join(lines)
    except Exception as e:
        print("[OCR] 识别失败:", e)
        return ""


def recognize_image(image) -> str:
    """
    识别 PIL Image 或 numpy array 中的文字
    @param image PIL.Image 或 numpy.ndarray
    @return 识别到的文字
    """
    _init_ocr()
    if not _ocr_available:
        return ""

    try:
        import numpy as np
        if hasattr(image, "convert"):
            # PIL Image -> numpy
            image = np.array(image)
        result, _ = _ocr(image)
        if result is None or len(result) == 0:
            return ""
        lines = [item[1] for item in result if item[1]]
        return "\n".join(lines)
    except Exception as e:
        print("[OCR] 识别失败:", e)
        return ""
