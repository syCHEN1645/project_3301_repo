import numpy as np
from sklearn.cluster import MeanShift, KMeans
from scipy.spatial.distance import cdist

MEAN_DIST_KEY = "mean distance of predicted and true"
PCK_KEY = "Percentage of true where at least one predicted is close"
NON_ASSIGNED_KEY = "Percentage non assigned predicted points"


def full_key_point_extraction(heatmaps, threshold=0.5, bandwidth=20):
    key_point_list = []
    for i in range(heatmaps.shape[0]):
        # middle
        if i == 1:
            cluster_centers = extract_key_points(heatmaps[i], threshold,
                                                 bandwidth)
            key_point_list.append(cluster_centers)
        # start and end
        else:
            cluster_center = extract_start_end_points(heatmaps[i], threshold)
            key_point_list.append(cluster_center)
    return key_point_list


def extract_start_end_points(heatmap, threshold):
    # normalize heatmap to range 0, 1
    heatmap = heatmap / np.max(heatmap)

    coords = np.argwhere(heatmap > threshold)
    # swap coordinates
    coords[:, [1, 0]] = coords[:, [0, 1]]

    kmeans = KMeans(n_clusters=1, n_init=3)
    kmeans.fit(coords)

    cluster_center = kmeans.cluster_centers_

    return cluster_center


def extract_key_points(heatmap, threshold, bandwidth):

    # normalize heatmap to range 0, 1
    heatmap = heatmap / np.max(heatmap)

    # Get pixel coordinates of pixels with value greater than 0.5
    coords = np.argwhere(heatmap > threshold)
    # swap coordinates
    coords[:, [1, 0]] = coords[:, [0, 1]]

    # Perform mean shift clustering
    ms = MeanShift(bandwidth=bandwidth, n_jobs=-1)
    ms.fit(coords)

    # Plot results
    cluster_centers = ms.cluster_centers_

    return cluster_centers


def key_point_metrics(predicted, ground_truth, threshold=10):
    """
    Gives back three different metrics to evaluate the predicted keypoints.
    For mean_distance each prediction is assigned to the true keypoint
    with smallest distance to it and then these distances are averaged
    For p_non_assigned we have the percentage of predicted key points
    that are not close to any true keypoint and therefore are non_assigned.
    For pck we have the percentage of true key points,
    where at least one predicted key point is close to it.

    For both p_non_assigned and pck,
    two key_points being close means that their distance is smaller than the threshold.
    :param predicted:
    :param ground_truth:
    :param threshold:
    :return:
    """
    distances = cdist(predicted, ground_truth)

    cor_pred_indices = np.argmin(
        distances, axis=1)  # indices of truth that are closest to predictions
    cor_true_indices = np.argmin(
        distances, axis=0)  # indices of predictions that are closest to truth

    # extract the corresponding ground truth points
    corresponding_truth = ground_truth[cor_pred_indices]

    # calculate the Euclidean distances between predicted points and corresponding groundtruths
    pred_distances = np.linalg.norm(predicted[:len(corresponding_truth)] -
                                    corresponding_truth,
                                    axis=1)
    mean_distance = np.mean(pred_distances)

    non_assigned = np.sum(pred_distances > threshold)
    p_non_assigned = non_assigned / len(predicted)

    # extract the corresponding predicted points
    corresponding_pred = predicted[cor_true_indices]

    gt_distances = np.linalg.norm(ground_truth[:len(corresponding_pred)] -
                                  corresponding_pred,
                                  axis=1)
    correct = np.sum(gt_distances <= threshold)
    pck = correct / len(
        ground_truth
    )  # compute PCK as percentage of correctly predicted keypoints

    results_dict = {
        MEAN_DIST_KEY: mean_distance,
        PCK_KEY: pck,
        NON_ASSIGNED_KEY: p_non_assigned
    }
    return results_dict
