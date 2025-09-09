import os

INFLUX_TOKEN = ""
INFLUX_URL = ""
INFLUX_PASSWORD = ""
INFLUX_USERNAME = ""
INFLUX_BUCKET = ""
INFLUX_ORG = ""

CONFIG_CALIBRATION_PATH = ""
BASE_MODEL_PATH = os.path.expanduser()

DETECTION_MODEL_PATH = os.path.join(BASE_MODEL_PATH, "models", "gauge_detection_model.pt")
KEY_POINT_MODEL_PATH = os.path.join(BASE_MODEL_PATH, "models", "key_point_model.pt") 
SEGMENTATION_MODEL_PATH = os.path.join(BASE_MODEL_PATH, "models", "best.pt")

# Processing configuration
CAPTURE_INTERVAL = 10  # seconds

# Result path
RESULT_PATH = os.path.expanduser("")

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
