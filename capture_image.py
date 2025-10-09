import cv2
import os
from datetime import datetime

SAVE_PATH = "captured_images"


# returns:
# same return values as saveImage
def captureImage(capture, index):
    os.makedirs(SAVE_PATH, exist_ok=True)

    print(f"Capture from camera {index}")

    ret, frame = capture.read()
    if ret:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        name = f"{index}_{timestamp}"
        rgb_img = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        #pil_img = Image.fromarray(rgb_img)
        # name of the image (without .jpg) and absolute path
        # filename, path = saveImage(frame, SAVE_PATH, index)
        return name, rgb_img
    print("Failed to capture")
    return None, None



# returns:
# name of the image without .jpg (which is camera index + timestamp)
# absolute path of the image
def saveImage(frame, folderpath, index):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    name = f"{index}_{timestamp}"
    filepath = f"{folderpath}/{name}.jpg"

    cv2.imwrite(filepath, frame)

    print(f"Saved {filepath}")
    absPath = os.path.abspath(filepath)
    return name, absPath

