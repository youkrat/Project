import urequests

NODE_RED_URL = "http://NODE_RED_IP:1880/ui"

def send(payload: dict):
    """
    Send payload to Node-RED via HTTP POST.
    Fail silently to avoid disrupting the main loop.
    """
    try:
        r = urequests.post(
            NODE_RED_URL,
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        r.close()
    except Exception:
        pass
