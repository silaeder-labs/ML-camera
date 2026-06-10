import cv2
import threading
import time


class BaseTracker:
    def __init__(self, cap):
        self.cap = cap
        self.id_colors = {}
        self.tracked_entities = {}
        self.started = False
        self.processing_thread = None
        self.latest_frame = None
        self.frame_lock = threading.Lock()

    def start(self):
        if self.started:
            return
        
        self.started = True
        self.processing_thread = threading.Thread(target=self._process_video, daemon=True)
        self.processing_thread.start()

    def stop(self):
        self.started = False
        if self.processing_thread is not None:
            self.processing_thread.join(timeout=2.0)

    def _process_video(self):
        """Обрабатывает видео в фоновом режиме"""
        raise NotImplementedError

    def get_latest_frame(self):
        """Возвращает последний обработанный кадр"""
        with self.frame_lock:
            if self.latest_frame is None:
                return None
            return self.latest_frame.copy()

    def generate_frames(self):
        """Генерирует кадры для видео потока в браузер"""
        while self.started:
            frame = self.get_latest_frame()
            
            if frame is None:
                time.sleep(0.01)
                continue

            ret, buffer = cv2.imencode('.jpg', frame)
            
            if not ret:
                continue

            frame_bytes = buffer.tobytes()

            yield (
                b'--frame\r\n'
                b'Content-Type: image/jpeg\r\n\r\n'
                + frame_bytes +
                b'\r\n'
            )
