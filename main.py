import cv2
from flask import Flask, Response, render_template, jsonify, request

from workers.body_tracker import BodyTracker
from workers.face_tracker import FaceTracker

app = Flask(
    __name__,
    template_folder="web/templates",
    static_folder="web/static",
    static_url_path="/static"
)

CAMERA_CURRENT_ANGLE = 0
CAMERA_NEW_ROTATION = 0
CAMERA_VIEW_ANGLE = 84 # 84 for macbook pro camera, 55 for studio camera

TRACKING_MODES = {
    "face": FaceTracker,
    "body": BodyTracker
}

current_mode = "face"
current_tracker = None
cap = None


def start_tracker(mode_name):
    global current_tracker, current_mode

    if current_tracker is not None:
        current_tracker.stop()

    tracker_class = TRACKING_MODES[mode_name]
    current_tracker = tracker_class(cap)
    current_tracker.start()
    current_mode = mode_name


def color_to_hex(color):
    if color is None:
        return "#787878"

    b, g, r = [max(0, min(255, int(c))) for c in color]
    return f"#{r:02x}{g:02x}{b:02x}"

# =========================
# API для поворота камеры
# =========================

@app.route('/rotation')
def get_rotation():
    return jsonify({"rotation": CAMERA_NEW_ROTATION})


# =========================
# Видео поток
# =========================

@app.route('/video_feed')
def video_feed():
    return Response(
        current_tracker.generate_frames(),
        mimetype='multipart/x-mixed-replace; boundary=frame'
    )


# =========================
# Список ID
# =========================

@app.route('/ids')
def get_ids():
    if current_tracker is None:
        return jsonify([])

    return jsonify(
        sorted([int(track_id) for track_id in current_tracker.tracked_entities.keys()])
    )


@app.route('/tracking_state')
def tracking_state():
    if current_tracker is None:
        return jsonify({
            "ids": [],
            "colors": {}
        })

    ids = sorted([int(track_id) for track_id in current_tracker.tracked_entities.keys()])
    colors = {}

    for track_id in ids:
        color = current_tracker.id_colors.get(track_id)
        colors[str(track_id)] = color_to_hex(color)

    return jsonify({
        "ids": ids,
        "colors": colors
    })


# =========================
# Смещение относительно центра
# =========================

@app.route('/offset/<int:track_id>')
def get_offset(track_id):
    if current_tracker is None:
        return jsonify({
            "error": "Tracking not started"
        })

    if track_id not in current_tracker.tracked_entities:
        return jsonify({
            "error": "ID not found"
        })

    global CAMERA_NEW_ROTATION

    face = current_tracker.tracked_entities[track_id]

    screen_center_x = face["frame_width"] // 2
    screen_center_y = face["frame_height"] // 2

    dx = face["center_x"] - screen_center_x
    dy = face["center_y"] - screen_center_y

    angles_x = round((CAMERA_CURRENT_ANGLE + (face["center_x"] - screen_center_x) / (screen_center_x*2) * CAMERA_VIEW_ANGLE) % 360, 3)

    CAMERA_NEW_ROTATION = angles_x

    return jsonify({
        "id": track_id,

        "face_x": face["center_x"],
        "face_y": face["center_y"],

        "screen_x": screen_center_x,
        "screen_y": screen_center_y,

        "dx": dx,
        "dy": dy, 

        "angles_x": angles_x
    })


# =========================
# Главная страница
# =========================

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/tracking_mode', methods=['GET', 'POST'])
def tracking_mode():
    if request.method == 'GET':
        return jsonify({
            "mode": current_mode
        })

    data = request.get_json(silent=True) or {}
    mode_name = data.get('mode')

    if mode_name not in TRACKING_MODES:
        return jsonify({
            "error": "Unknown mode"
        }), 400

    if mode_name != current_mode:
        start_tracker(mode_name)

    return jsonify({
        "mode": current_mode
    })


# =========================
# Запуск
# =========================

if __name__ == '__main__':
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        raise RuntimeError("Не удалось открыть видеопоток")

    start_tracker(current_mode)
    app.run(
        host='0.0.0.0',
        port=5001,
        debug=False,
        threaded=True
    )
