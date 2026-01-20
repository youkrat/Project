import json
import time
from config import SD_MOUNT_POINT

def get_log_filename():
    date = time.strftime("%Y-%m-%d", time.localtime())
    return f"{SD_MOUNT_POINT}/weather_{date}.jsonl"

def log(payload):
    with open(get_log_filename(), "a") as f:
        f.write(json.dumps(payload) + "\n")
