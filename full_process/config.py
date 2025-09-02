import os

INFLUX_TOKEN = "TQi4S2rfGX7tx90BXpW-6vR_GzUt7RjZFHuue2s1OKU9NmfwcTcAY2CO5jFGHlxNh2JfbCvhywQRPPbw17tMsQ=="
INFLUX_URL = "https://us-east-1-1.aws.cloud2.influxdata.com/"
INFLUX_PASSWORD = ""
INFLUX_USERNAME = "digiwell"
INFLUX_BUCKET = "bucket-0"
INFLUX_ORG = "is307"

CONFIG_CALIBRATION_PATH = "config_calibration.json"
BASE_MODEL_PATH = os.path.expanduser("~/Desktop/project_3301_repo/analog_gauge_reader")

DETECTION_MODEL_PATH = os.path.join(BASE_MODEL_PATH, "models", "gauge_detection_model.pt")
KEY_POINT_MODEL_PATH = os.path.join(BASE_MODEL_PATH, "models", "key_point_model.pt") 
SEGMENTATION_MODEL_PATH = os.path.join(BASE_MODEL_PATH, "models", "best.pt")

# Processing configuration
CAPTURE_INTERVAL = 10  # seconds

# Result path
RESULT_PATH = os.path.expanduser("~/Desktop/project_3301_repo/camera_link/processed_results")

# Verify model files exist
def verify_model_files():
    """Check if all required model files exist"""
    models = {
        "Detection Model": DETECTION_MODEL_PATH,
        "Key Point Model": KEY_POINT_MODEL_PATH, 
        "Segmentation Model": SEGMENTATION_MODEL_PATH
    }
    
    missing_models = []
    for name, path in models.items():
        if not os.path.exists(path):
            missing_models.append(f"{name}: {path}")
        else:
            print(f"✓ Found {name}: {path}")
    
    if missing_models:
        print("❌ Missing model files:")
        for model in missing_models:
            print(f"  - {model}")
        return False
    
    print("✅ All model files found!")
    return True

if __name__ == "__main__":
    verify_model_files()