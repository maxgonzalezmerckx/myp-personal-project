from flask import Flask, jsonify, render_template, request

from physics.serve import NET_HEIGHT_MEN, NET_HEIGHT_WOMEN, simulate_trajectory

app = Flask(__name__)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/theory")
def theory():
    return render_template("theory.html")


@app.route("/simulator")
def simulator():
    return render_template("simulator.html")


@app.route("/api/simulate", methods=["POST"])
def api_simulate():
    data = request.get_json(silent=True) or {}

    try:
        speed = float(data.get("speed", 25.0))
        angle_deg = float(data.get("angle_deg", 15.0))
        spin_rpm = float(data.get("spin_rpm", 0.0))
        height = float(data.get("height", 2.5))
        net_type = data.get("net_type", "men")
        include_drag = bool(data.get("include_drag", True))
        include_magnus = bool(data.get("include_magnus", True))
    except (TypeError, ValueError):
        return jsonify({"error": "Invalid parameter values."}), 400

    if not (5.0 <= speed <= 50.0):
        return jsonify({"error": "Speed must be between 5 and 50 m/s."}), 400
    if not (0.0 <= angle_deg <= 60.0):
        return jsonify({"error": "Angle must be between 0 and 60 degrees."}), 400
    if not (-300.0 <= spin_rpm <= 300.0):
        return jsonify({"error": "Spin must be between -300 and 300 rpm."}), 400
    if not (1.0 <= height <= 4.0):
        return jsonify({"error": "Height must be between 1 and 4 m."}), 400

    net_height = NET_HEIGHT_MEN if net_type == "men" else NET_HEIGHT_WOMEN

    result = simulate_trajectory(
        speed=speed,
        angle_deg=angle_deg,
        spin_rpm=spin_rpm,
        height=height,
        net_height=net_height,
        include_drag=include_drag,
        include_magnus=include_magnus,
    )

    return jsonify(result)


if __name__ == "__main__":
    app.run(debug=True)
