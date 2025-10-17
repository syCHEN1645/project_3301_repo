from ultralytics import YOLO
import numpy as np
import cv2
from scipy import odr

# hard coded model path to detect gauge center
GAUGE_CENTER_MODEL_PATH = "analog_gauge_reader/models/center.pt"


def detect_gauge_center(image, model_path=GAUGE_CENTER_MODEL_PATH):
    """
    uses fine-tuned yolo v8 to get bounding box of gauge center, start point and end point
    :param img: numpy image
    :param model_path: path to yolov8 detection model
    :return: detection of center
    """
    # load model
    try:
        model = YOLO(model_path)
    except:
        print("Center detection model path is wrong")

    # run inference
    results = model.predict(image)
    # res is a list of 3 [x1, y1, x2, y2]
    # res[0], res[1], res[2] are center, start and end
    res = []

    # center point
    boxes = results[0].boxes
    if boxes == None or len(boxes) == 0:
        print("Center is not found")
        res.append([])
    else:
        # vertices in xyxy form
        # x1, y1, x2, y2
        xyxys = boxes.xyxy.cpu().numpy()
        # confidence
        confs = boxes.conf.cpu().numpy()
        # return the most confident box
        best_box = xyxys[0]
        best_conf = confs[0]
        for xyxy, conf in zip(xyxys, confs):
            if conf > best_conf:
                best_box = xyxy
        # * to change from numpy array to list
        res.append(*best_box)
    
    # start point
    boxes = results[1].boxes
    if boxes == None or len(boxes) == 0:
        print("Start point is not found")
        res.append([])
    else:
        # vertices in xyxy form
        # x1, y1, x2, y2
        xyxys = boxes.xyxy.cpu().numpy()
        # confidence
        confs = boxes.conf.cpu().numpy()
        # return the most confident box
        best_box = xyxys[0]
        best_conf = confs[0]
        for xyxy, conf in zip(xyxys, confs):
            if conf > best_conf:
                best_box = xyxy
        res.append(*best_box)

    # end point
    boxes = results[2].boxes
    if boxes == None or len(boxes) == 0:
        print("End point is not found")
        res.append([])
    else:
        # vertices in xyxy form
        # x1, y1, x2, y2
        xyxys = boxes.xyxy.cpu().numpy()
        # confidence
        confs = boxes.conf.cpu().numpy()
        # return the most confident box
        best_box = xyxys[0]
        best_conf = confs[0]
        for xyxy, conf in zip(xyxys, confs):
            if conf > best_conf:
                best_box = xyxy
        res.append(*best_box)

    return res