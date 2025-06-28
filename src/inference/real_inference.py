# from typing import List
# from io import BytesIO
# import numpy as np
# import cv2
# from ultralytics import YOLO
#
# # loading a model
# model = YOLO("yolov8n.pt")
#
# def predict_frame_from_bytes(frame_bytes: bytes) -> List[dict]:
#     """
#     **input**: jpeg bytes,
#     \
#     **output**: YOLO prediction
#     """
#
#     # decoding from bytes
#     np_arr = np.frombuffer(frame_bytes, np.uint8)
#     frame = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
#
#     if frame is None:
#         raise ValueError("unable to decode frame")
#
#
#     frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
#     results = model.predict(frame_rgb)[0] # prediction
#
#     output = [] # parsing results
#     for box in results.boxes:
#         cls_id = int(box.cls[0])
#         conf = float(box.conf[0])
#         xyxy = box.xyxy[0].tolist()
#
#         output.append({
#             "class_id": cls_id,
#             "confidence": round(conf, 4),
#             "bbox": [round(c, 2) for c in xyxy],
#             "label": model.names[cls_id],
#         })
#
#     return output
