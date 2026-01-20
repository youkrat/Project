from flask import Flask, request, jsonify

app = Flask(__name__)

# In-memory storage (later → CSV or database)
latest_data = {
    "temperature": None,
    "humidity": None,
    "light": None
}

# ---------------------------
# ESP32 → Flask (POST data)
# ---------------------------
@app.route("/api/data", methods=["POST"])
def receive_data():
    global latest_data
    data = request.json

    latest_data["temperature"] = data.get("temperature")
    latest_data["humidity"] = data.get("humidity")
    latest_data["light"] = data.get("light")

    return jsonify({"status": "ok"}), 200

# ---------------------------
# Browser → Flask (GET data)
# ---------------------------
@app.route("/api/data", methods=["GET"])
def send_data():
    return jsonify(latest_data)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
