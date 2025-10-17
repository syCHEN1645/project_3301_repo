import argparse
import os
import logging
import time
import json

import cv2
import numpy as np
from PIL import Image

from plots_circle import RUN_PATH, Plotter
from gauge_detection.detection_inference import detection_gauge_face
from gauge_center_detection.gauge_center_inference import detect_gauge_center
from key_point_detection.key_point_inference import KeyPointInference, detect_key_points
from geometry.circle import fit_circle, get_line_circle_point, \
    get_point_from_angle, get_polar_angle, get_theta_middle, get_circle_error
from angle_reading_fit.angle_converter import AngleConverter
from angle_reading_fit.line_fit import line_fit, line_fit_ransac
from segmentation.segmenation_inference import get_start_end_line, segment_gauge_needle, \
    get_fitted_line, cut_off_line
from evaluation import constants

from pathlib import Path

OCR_THRESHOLD = 0.7
RESOLUTION = (
    448, 448
)  # make sure both dimensions are multiples of 14 for keypoint detection

# Several flags to set or unset for pipeline
WRAP_AROUND_FIX = True
RANSAC = True

WARP_OCR = True

# if random_rotations true then random rotations.
RANDOM_ROTATIONS = False
ZERO_POINT_ROTATION = True

OCR_ROTATION = RANDOM_ROTATIONS or ZERO_POINT_ROTATION


def crop_image(img, box, flag=False, two_dimensional=False):
    """
    crop image
    :param img: orignal image
    :param box: in the xyxy format
    :return: cropped image
    """
    img = np.copy(img)
    if two_dimensional:
        cropped_img = img[box[1]:box[3],
                          box[0]:box[2]]  # image has format [y, x]
    else:
        cropped_img = img[box[1]:box[3],
                          box[0]:box[2], :]  # image has format [y, x, rgb]

    height = int(box[3] - box[1])
    width = int(box[2] - box[0])

    # want to preserve aspect ratio but make image square, so do padding
    if height > width:
        delta = height - width
        left, right = delta // 2, delta - (delta // 2)
        top = bottom = 0
    else:
        delta = width - height
        top, bottom = delta // 2, delta - (delta // 2)
        left = right = 0

    pad_color = [0, 0, 0]
    new_img = cv2.copyMakeBorder(cropped_img,
                                 top,
                                 bottom,
                                 left,
                                 right,
                                 cv2.BORDER_CONSTANT,
                                 value=pad_color)

    if flag:
        return new_img, (top, bottom, left, right)
    return new_img


def move_point_resize(point, original_resolution, resized_resolution):
    new_point_x = point[0] * resized_resolution[0] / original_resolution[0]
    new_point_y = point[1] * resized_resolution[1] / original_resolution[1]
    return new_point_x, new_point_y


# here assume that both resolutions are squared
def rescale_circle_resize(circle_params, original_resolution,
                           resized_resolution):
    x0, y0, ap, bp, phi = circle_params

    # move circle center
    x0_new, y0_new = move_point_resize((x0, y0), original_resolution,
                                       resized_resolution)

    # rescale axis
    scaling_factor = resized_resolution[0] / original_resolution[0]
    ap_x_new = scaling_factor * ap
    bp_x_new = scaling_factor * bp

    return x0_new, y0_new, ap_x_new, bp_x_new, phi


def process_image(image, detection_model_path, key_point_model_path,
                  segmentation_model_path, run_path, debug, eval_mode,
                  start_marking, end_marking, unit, image_is_raw=False):

    result = []
    errors = {}
    result_full = {}

    if not image_is_raw:
        logging.info("Start processing image at path %s", image)
        image = Image.open(image).convert("RGB")
        image = np.asarray(image)
    else:
        logging.info("Start processing image")

    plotter = Plotter(run_path, image)

    if eval_mode:
        result_full[constants.IMG_SIZE_KEY] = {
            'width': image.shape[1],
            'height': image.shape[0]
        }

    if debug:
        plotter.save_img()

    # ------------------Gauge detection-------------------------
    if debug:
        print("-------------------")
        print("Gauge Detection")

    logging.info("Start Gauge Detection")

    box, all_boxes = detection_gauge_face(image, detection_model_path)

    if debug:
        plotter.plot_bounding_box_img(all_boxes)

    # crop image to only gauge face
    cropped_img = crop_image(image, box)

    # resize
    cropped_resized_img = cv2.resize(cropped_img,
                                     dsize=RESOLUTION,
                                     interpolation=cv2.INTER_CUBIC)

    if eval_mode:
        result_full[constants.GAUGE_DET_KEY] = {
            'x': box[0].item(),
            'y': box[1].item(),
            'width': box[2].item() - box[0].item(),
            'height': box[3].item() - box[1].item(),
        }

    if debug:
        plotter.set_image(cropped_resized_img)
        plotter.plot_image('cropped')

    logging.info("Finish Gauge Detection")

    # ------------------Key Point Detection-------------------------

    # if debug:
    #     print("-------------------")
    #     print("Key Point Detection")

    logging.info("Start gauge center detection")

    # plotting of the center point is done with the start end points
    keypoints = detect_gauge_center(cropped_resized_img)
    # 0: center
    # 1: start
    # 2: end
    center_x = (keypoints[0][0] + keypoints[0][2]) / 2
    center_y = (keypoints[0][1] + keypoints[0][3]) / 2
    center = np.array([center_x, center_y])

    start_x = (keypoints[1][0] + keypoints[1][2]) / 2
    start_y = (keypoints[1][1] + keypoints[1][3]) / 2
    start = np.array([start_x, start_y])

    end_x = (keypoints[2][0] + keypoints[2][2]) / 2
    end_y = (keypoints[2][1] + keypoints[2][3]) / 2
    end = np.array([end_x, end_y])

    # ------------------Key Point Detection-------------------------

    # if debug:
    #     print("-------------------")
    #     print("Key Point Detection")

    # logging.info("Start key point detection")

    # key_point_inferencer = KeyPointInference(key_point_model_path)
    # heatmaps = key_point_inferencer.predict_heatmaps(cropped_resized_img)
    # key_point_list = detect_key_points(heatmaps)

    # key_points = key_point_list[1]
    # start_point = key_point_list[0]
    # end_point = key_point_list[2]

    # if eval_mode:
    #     if start_point.shape == (1, 2):
    #         result_full[constants.KEYPOINT_START_KEY] = {
    #             'x': start_point[0][0],
    #             'y': start_point[0][1]
    #         }
    #     else:
    #         result_full[constants.KEYPOINT_START_KEY] = constants.FAILED
    #     if end_point.shape == (1, 2):
    #         result_full[constants.KEYPOINT_END_KEY] = {
    #             'x': end_point[0][0],
    #             'y': end_point[0][1]
    #         }
    #     else:
    #         result_full[constants.KEYPOINT_END_KEY] = constants.FAILED
    #     result_full[constants.KEYPOINT_NOTCH_KEY] = []
    #     for point in key_points:
    #         result_full[constants.KEYPOINT_NOTCH_KEY].append({
    #             'x': point[0],
    #             'y': point[1]
    #         })

    # if debug:
    #     plotter.plot_heatmaps(heatmaps)
    #     plotter.plot_key_points(key_point_list)

    # logging.info("Finish key point detection")

    # ------------------Circle Fitting-------------------------

    if debug:
        print("-------------------")
        print("Circle Fitting")

    logging.info("Start circle fitting")

    circle_params = fit_circle(center, start, end)
    # circle_error = get_circle_error([start, end], circle_params)
    # errors["circle fit error"] = circle_error

    if debug:
        # plot circle
        plotter.plot_circle([center, start, end], circle_params, 'key_points')

    logging.info("Finish circle fitting")

    # calculate zero point

    # Find bottom point to set there the zero for wrap around
    if WRAP_AROUND_FIX and start.shape == (1, 2) \
        and end.shape == (1, 2):
        theta_start = get_polar_angle(start.flatten(), circle_params)
        theta_end = get_polar_angle(end.flatten(), circle_params)
        theta_zero = get_theta_middle(theta_start, theta_end)
    else:
        bottom_middle = np.array((RESOLUTION[0] / 2, RESOLUTION[1]))
        theta_zero = get_polar_angle(bottom_middle, circle_params)

    zero_point = get_point_from_angle(theta_zero, circle_params)
    if debug:
        plotter.plot_zero_point_circle(np.array(zero_point), start, end, circle_params)

    # # ------------------OCR-------------------------

    # ------------------Segmentation-------------------------

    if debug:
        print("-------------------")
        print("Segmentation")

    logging.info("Start segmentation")

    try:
        needle_mask_x, needle_mask_y = segment_gauge_needle(
            cropped_resized_img, segmentation_model_path)
    except AttributeError:
        logging.error("Segmentation failed, no needle found")
        errors[constants.SEGMENTATION_FAILED_KEY] = True
        result.append({constants.READING_KEY: constants.FAILED})
        result_full[constants.NEEDLE_MASK_KEY] = constants.FAILED
        write_files(result, result_full, errors, run_path, eval_mode)
        raise Exception("Segmentation failed, no needle found")

    if eval_mode:
        result_full[constants.NEEDLE_MASK_KEY] = {
            'x': needle_mask_x.tolist(),
            'y': needle_mask_y.tolist()
        }

    needle_line_coeffs, needle_error = get_fitted_line(needle_mask_x,
                                                       needle_mask_y)
    needle_line_start_x, needle_line_end_x = get_start_end_line(needle_mask_x)
    needle_line_start_y, needle_line_end_y = get_start_end_line(needle_mask_y)

    needle_line_start_x, needle_line_end_x = cut_off_line(
        [needle_line_start_x, needle_line_end_x], needle_line_start_y,
        needle_line_end_y, needle_line_coeffs)

    errors["Needle line residual variance"] = needle_error

    if debug:
        plotter.plot_segmented_line(needle_mask_x, needle_mask_y,
                                    (needle_line_start_x, needle_line_end_x),
                                    needle_line_coeffs)

    logging.info("Finish segmentation")

    # ------------------Project OCR Numbers to circle-------------------------

    # ------------------Project start and end points to circle-------------------------

    start_point_xy = [start[0], start[1]]
    end_point_xy = [end[0], end[1]]
    theta_start = get_polar_angle(start_point_xy, circle_params)
    theta_end = get_polar_angle(end_point_xy, circle_params)

    # ------------------Project Needle to circle-------------------------

    point_needle_circle = get_line_circle_point(
        needle_line_coeffs, (needle_line_start_x, needle_line_end_x),
        circle_params)

    if point_needle_circle.shape[0] == 0:
        logging.error("Needle line and circle do not intersect!")
        errors[constants.OCR_NONE_DETECTED_KEY] = True
        result.append({constants.READING_KEY: constants.FAILED})
        write_files(result, result_full, errors, run_path, eval_mode)
        raise Exception("Needle line and circle do not intersect")

    if debug:
        plotter.plot_circle(point_needle_circle.reshape(1, 2),
                             circle_params, 'needle_point')

    # ------------------Fit line to angles and get reading of needle-------------------------

    # Find angle of needle circle point
    needle_angle = get_polar_angle(point_needle_circle, circle_params)

    angle_converter = AngleConverter(theta_zero)

    angle_number_list = []
    # for number in number_labels:
    #     angle_number_list.append(
    #         (angle_converter.convert_angle(number.theta), number.number))

    angle_number_list.append((angle_converter.convert_angle(theta_start), start_marking))
    angle_number_list.append((angle_converter.convert_angle(theta_end), end_marking))
    angle_number_arr = np.array(angle_number_list)

    if RANSAC:
        reading_line_coeff, inlier_mask, outlier_mask = line_fit_ransac(
            angle_number_arr[:, 0], angle_number_arr[:, 1])
    else:
        reading_line_coeff = line_fit(angle_number_arr[:, 0],
                                      angle_number_arr[:, 1])

    reading_line = np.poly1d(reading_line_coeff)
    reading_line_res = np.sum(
        abs(
            np.polyval(reading_line_coeff, angle_number_arr[:, 0]) -
            angle_number_arr[:, 0]))
    reading_line_mean_err = reading_line_res / len(angle_number_arr)
    errors["Mean residual on fitted angle line"] = reading_line_mean_err

    needle_angle_conv = angle_converter.convert_angle(needle_angle)

    reading = reading_line(needle_angle_conv)

    result.append({
        constants.READING_KEY: reading,
        constants.MEASURE_UNIT_KEY: unit
    })

    if debug:
        if RANSAC:
            plotter.plot_linear_fit_ransac(angle_number_arr,
                                           (needle_angle_conv, reading),
                                           reading_line, inlier_mask,
                                           outlier_mask)
        else:
            plotter.plot_linear_fit(angle_number_arr,
                                    (needle_angle_conv, reading), reading_line)

        print(f"Final reading is: {reading} {unit}")
        plotter.plot_final_reading_circle([], point_needle_circle,
                                           round(reading, 1), circle_params)

    # ------------------Write result to file-------------------------
    write_files(result, result_full, errors, run_path, eval_mode)

    return {"value": reading, "unit": unit}


def write_files(result, result_full, errors, run_path, eval_mode):
    result_path = os.path.join(run_path, constants.RESULT_FILE_NAME)
    write_json_file(result_path, result)

    error_path = os.path.join(run_path, constants.ERROR_FILE_NAME)
    write_json_file(error_path, errors)

    if eval_mode:
        result_full_path = os.path.join(run_path,
                                        constants.RESULT_FULL_FILE_NAME)
        write_json_file(result_full_path, result_full)


def write_json_file(filename, dictionary):
    file_json = json.dumps(dictionary, indent=4)
    with open(filename, "w") as outfile:
        outfile.write(file_json)


# Streamline pipeline to pass image straight into model without saving it
def main():
    args = read_args()

    input_path = args.input
    detection_model = args.detection_model
    key_point_model = args.key_point_model
    segmentation_model = args.segmentation_model
    base_path = args.base_path

    start_marking = args.start_marking
    end_marking = args.end_marking

    # time_str = time.strftime("%Y%m%d%H%M%S")
    # base_path = os.path.join(base_path, RUN_PATH + '_' + time_str)
    # os.makedirs(base_path)
    os.makedirs(base_path, exist_ok=True)

    name = os.path.basename(input_path)

    args_dict = vars(args)
    # move arguments.json to a arguments folder
    # file_path = os.path.join(base_path, "arguments.json")
    log_name = os.path.basename(input_path)
    os.makedirs(os.path.join(base_path, "arguments"), exist_ok=True)
    file_path = os.path.join(base_path, "arguments", f"{name}.json")
    write_json_file(file_path, args_dict)

    # move run.log to a log folder
    # log_path = os.path.join(base_path, "run.log")
    os.makedirs(os.path.join(base_path, "logs"), exist_ok=True)
    log_path = os.path.join(base_path, "logs", f"{name}.log")

    logging.basicConfig(filename=log_path,
                        filemode='w',
                        format='%(name)s - %(levelname)s - %(message)s',
                        level=logging.INFO)

    
    if os.path.isfile(input_path):
        image_name = os.path.basename(input_path)
        run_path = os.path.join(base_path, image_name)
        process_image(input_path,
                      detection_model,
                      key_point_model,
                      segmentation_model,
                      run_path,
                      debug=args.debug,
                      eval_mode=args.eval,
                      start_marking=args.start_marking,
                      end_marking=args.end_marking,
                      unit=args.unit)
    elif os.path.isdir(input_path):
        for image_name in os.listdir(input_path):
            img_path = os.path.join(input_path, image_name)
            run_path = os.path.join(base_path, image_name)
            try:
                process_image(img_path,
                              detection_model,
                              key_point_model,
                              segmentation_model,
                              run_path,
                              debug=args.debug,
                              eval_mode=args.eval,
                              start_marking=args.start_marking,
                              end_marking=args.end_marking,
                              unit=args.unit)

            # pylint: disable=broad-except
            # For now want to catch general exceptions and still continue with the other images.
            except Exception as err:
                err_msg = f"Unexpected {err=}, {type(err)=}"
                print(err_msg)
                logging.error(err_msg)

    else:
        print("Error: input file or directory does not exist.")
        logging.error("input file or directory does not exist.")


def read_args():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--input',
        type=str,
        required=True,
        help=
        "Path to input image. If a directory then it will pass all images of directory"
    )
    parser.add_argument('--detection_model',
                        type=str,
                        required=False,
                        default="models/gauge_detection_model.pt",
                        help="Path to detection model")
    parser.add_argument('--key_point_model',
                        type=str,
                        required=False,
                        default="models/key_point_model.pt",
                        help="Path to key point model")
    parser.add_argument('--segmentation_model',
                        type=str,
                        required=False,
                        default="models/segmentation_model.pt",
                        help="Path to segmentation model")
    parser.add_argument('--base_path',
                        type=str,
                        required=True,
                        help="Path where run folder is stored")

    parser.add_argument('--debug', action='store_true')
    parser.add_argument('--eval', action='store_true')
    
    # calibration inputs
    parser.add_argument('--start_marking',
                        type=float,
                        required=True)
    parser.add_argument('--end_marking',
                        type=float,
                        required=True)
    parser.add_argument('--unit',
                        type=str,
                        required=True)
    return parser.parse_args()


if __name__ == "__main__":
    main()
