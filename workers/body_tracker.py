import cv2
import numpy as np
from ultralytics import YOLO

from workers.base_tracker import BaseTracker


class BodyTracker(BaseTracker):
    def __init__(self, cap, model_path="body-tracking/yolo11n.pt"):
        super().__init__(cap=cap)
        self.model = YOLO(model_path)

    def get_color_for_id(self, track_id):
        if track_id not in self.id_colors:
            np.random.seed(int(track_id))
            color = tuple(
                int(c)
                for c in np.random.randint(50, 255, size=3)
            )
            self.id_colors[track_id] = color

        return self.id_colors[track_id]

    def _process_video(self):
        while self.cap.isOpened() and self.started:
            success, frame = self.cap.read()

            if not success:
                break

            results = self.model.track(
                frame,
                persist=True,
                classes=0,
                tracker="bytetrack.yaml"
            )

            annotated_frame = frame.copy()
            current_people = {}

            if (
                len(results) > 0
                and results[0].boxes is not None
                and results[0].boxes.id is not None
            ):
                boxes = results[0].boxes.xyxy.cpu().numpy()
                track_ids = (
                    results[0]
                    .boxes
                    .id
                    .cpu()
                    .numpy()
                    .astype(int)
                )
                confidences = results[0].boxes.conf.cpu().numpy()

                for box, track_id, conf in zip(
                    boxes,
                    track_ids,
                    confidences
                ):
                    track_id = int(track_id)

                    x1, y1, x2, y2 = map(int, box)

                    center_x = int((x1 + x2) / 2)
                    center_y = int((y1 + y2) / 2)

                    current_people[track_id] = {
                        "center_x": center_x,
                        "center_y": center_y,
                        "frame_width": frame.shape[1],
                        "frame_height": frame.shape[0]
                    }

                    color = self.get_color_for_id(track_id)

                    label = f"ID: {track_id} ({conf * 100:.0f}%)"

                    (w, h), _ = cv2.getTextSize(
                        label,
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.6,
                        2
                    )

                    cv2.rectangle(
                        annotated_frame,
                        (x1, y1),
                        (x2, y2),
                        color,
                        3
                    )

                    cv2.rectangle(
                        annotated_frame,
                        (x1, y1 - h - 10),
                        (x1 + w, y1),
                        color,
                        -1
                    )

                    cv2.putText(
                        annotated_frame,
                        label,
                        (x1, y1 - 5),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.6,
                        (255, 255, 255),
                        2,
                        cv2.LINE_AA
                    )

            else:
                if len(results) > 0:
                    annotated_frame = results[0].plot(
                        line_width=2,
                        boxes=True
                    )

            self.tracked_entities = current_people

            # Сохраняем обработанный кадр для видео потока
            with self.frame_lock:
                self.latest_frame = annotated_frame
