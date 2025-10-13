from ultralytics import YOLO
import numpy as np
import cv2
from scipy import odr


def segment_gauge_needle(image, model_path='best.pt'):
    """
    uses fine-tuned yolo v8 to get mask of segmentation
    :param img: numpy image
    :param model_path: path to yolov8 detection model
    :return: segmentation of needle
    """
    model = YOLO(model_path)  # load model

    results = model.predict(
        image)  # run inference, detects gauge face and needle

    # get list of detected boxes, already sorted by confidence
    try:
        needle_mask = results[0].masks.data[0].numpy()
    except:
        needle_mask = results[0].masks.data[0].cpu().numpy()
    needle_mask_resized = cv2.resize(needle_mask,
                                     dsize=(image.shape[1], image.shape[0]),
                                     interpolation=cv2.INTER_NEAREST)

    # scale 255 to fit into the connected component function
    binary_mask = needle_mask_resized.astype(np.uint8) * 255
    num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(
            binary_mask,
            connectivity=8)
    
    # # select only the largest blob to ignore noises
    # if num_labels > 1:
    #     # background has label 0, skip row 0 (from 1 onwards) and get areas
    #     areas = stats[1:, cv2.CC_STAT_AREA]
    #     # get the index of largest area (offset 1 as skipped 0)
    #     largest = np.argmax(areas) + 1
    #     # no /255 as boolean -> uint8 is either 1 or 0
    #     cleaned_mask = (labels == largest).astype(np.uint8)
    # else:
    #     # only have background, no needle detected
    #     cleaned_mask = binary_mask / 255

    # select only the most centered to ignore noises
    if num_labels > 1:
        img_center = np.array([image.shape[1] / 2, image.shape[0] / 2])
        dists = []
        for i in range(1, num_labels):
            centroid = centroids[i]
            dists.append(np.linalg.norm(centroid - img_center))
        closest = np.argmin(dists) + 1
        cleaned_mask = (labels == closest).astype(np.uint8)
    else:
        cleaned_mask = binary_mask / 255

    y_coords, x_coords = np.where(cleaned_mask)

    return x_coords, y_coords

def segment_gauge_needle_use_model(image, model):
    results = model.predict(
        image)  # run inference, detects gauge face and needle

    # get list of detected boxes, already sorted by confidence
    try:
        needle_mask = results[0].masks.data[0].numpy()
    except:
        needle_mask = results[0].masks.data[0].cpu().numpy()
    needle_mask_resized = cv2.resize(needle_mask,
                                     dsize=(image.shape[1], image.shape[0]),
                                     interpolation=cv2.INTER_NEAREST)

    # scale 255 to fit into the connected component function
    binary_mask = needle_mask_resized.astype(np.uint8) * 255
    num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(
            binary_mask,
            connectivity=8)

    # select only the most centered to ignore noises
    if num_labels > 1:
        img_center = np.array([image.shape[1] / 2, image.shape[0] / 2])
        dists = []
        for i in range(1, num_labels):
            centroid = centroids[i]
            dists.append(np.linalg.norm(centroid - img_center))
        closest = np.argmin(dists) + 1
        cleaned_mask = (labels == closest).astype(np.uint8)
    else:
        cleaned_mask = binary_mask / 255

    y_coords, x_coords = np.where(cleaned_mask)

    return x_coords, y_coords


def get_fitted_line(x_coords, y_coords):
    """
    Do orthogonal distance regression (odr) for this.
    """
    odr_model = odr.Model(linear)
    data = odr.Data(x_coords, y_coords)
    ordinal_distance_reg = odr.ODR(data, odr_model, beta0=[0.2, 1.], maxit=600)
    out = ordinal_distance_reg.run()
    line_coeffs = out.beta
    residual_variance = out.res_var
    return line_coeffs, residual_variance


def linear(B, x):
    return B[0] * x + B[1]


def get_start_end_line(needle_mask):
    return np.min(needle_mask), np.max(needle_mask)


def cut_off_line(x, y_min, y_max, line_coeffs):
    line = np.poly1d(line_coeffs)
    y = line(x)
    _cut_off(x, y, y_min, y_max, line_coeffs, 0)
    _cut_off(x, y, y_min, y_max, line_coeffs, 1)
    return x[0], x[1]


def _cut_off(x, y, y_min, y_max, line_coeffs, i):
    if y[i] > y_max:
        y[i] = y_max
        x[i] = 1 / line_coeffs[0] * (y_max - line_coeffs[1])
    if y[i] < y_min:
        y[i] = y_min
        x[i] = 1 / line_coeffs[0] * (y_min - line_coeffs[1])
