from ultralytics import YOLO
import numpy as np
import cv2
from scipy import odr

# hard coded model path to detect gauge center
GAUGE_CENTER_MODEL_PATH = "analog_gauge_reader/models/center.pt"
CLASS_ID = {"center": 0, "start": 1, "end": 2}
N_CLASS = 3


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
    except Exception as e:
        print(f"Center detection model path is wrong: {e}")
        return None

    # run inference
    results = model.predict(image)
    boxes = results[0].boxes
    # res is a list of 3 [x1, y1, x2, y2]
    # res[0], res[1], res[2] are center, start and end
    res = []
    xyxys = boxes.xyxy.cpu().numpy()
    # confidence
    confs = boxes.conf.cpu().numpy()
    # return the most confident box
    clss = boxes.cls.cpu().numpy()

    # keypoints
    for cls_name, cls_id in CLASS_ID.items():
        cls_xyxys = xyxys[cls_id == clss]
        cls_confs = confs[cls_id == clss]
        if len(cls_confs) == 0:
            print(f"No {cls_name} point is found")
            res.append([])
        else:
            # vertices in xyxy form
            # x1, y1, x2, y2
            best_box = cls_xyxys[np.argmax(cls_confs)]
            # * to change from numpy array to list
            res.append(best_box.tolist())

    return res