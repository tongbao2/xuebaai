# -*- coding: utf-8 -*-
# PyInstaller custom hook for rapidocr_onnxruntime.
# hiddenimports and datas must be top-level assignments.
import os

hiddenimports = [
    "rapidocr_onnxruntime",
    "rapidocr_onnxruntime.cal_rec_boxes",
    "rapidocr_onnxruntime.cal_rec_boxes.main",
    "rapidocr_onnxruntime.ch_ppocr_det",
    "rapidocr_onnxruntime.ch_ppocr_det.text_detect",
    "rapidocr_onnxruntime.ch_ppocr_det.utils",
    "rapidocr_onnxruntime.ch_ppocr_rec",
    "rapidocr_onnxruntime.ch_ppocr_rec.text_recognize",
    "rapidocr_onnxruntime.ch_ppocr_rec.utils",
    "rapidocr_onnxruntime.ch_ppocr_cls",
    "rapidocr_onnxruntime.ch_ppocr_cls.text_cls",
    "rapidocr_onnxruntime.ch_ppocr_cls.utils",
    "rapidocr_onnxruntime.utils",
    "rapidocr_onnxruntime.utils.infer_engine",
    "rapidocr_onnxruntime.utils.load_image",
    "rapidocr_onnxruntime.utils.logger",
    "rapidocr_onnxruntime.utils.parse_parameters",
    "rapidocr_onnxruntime.utils.process_img",
    "rapidocr_onnxruntime.utils.vis_res",
    "rapidocr_onnxruntime.main",
]

_rr = r"C:\Users\iMac\.qclaw\workspace-agent-7ec9d5d2\study-ai\rapidocr_onnxruntime"
datas = [
    (os.path.join(_rr, "config.yaml"), "rapidocr_onnxruntime"),
    (os.path.join(_rr, "models"), "rapidocr_onnxruntime/models"),
]
