import cv2
import threading
import time


class BaseTracker:
    def __init__(self, cap, camera_angles=None, camera_view_angles=None):
        self.cap = cap
        self.id_colors = {}
        self.tracked_entities = {}
        self.started = False
        self.processing_thread = None
        self.latest_frame = None
        self.frame_lock = threading.Lock()
        
        # Параметры камеры для автоматического расчета поворота
        self.camera_angles = camera_angles if camera_angles else [0, 0]
        self.camera_view_angles = camera_view_angles if camera_view_angles else [84, 54]
        self.camera_rotation = [0, 0]  # Текущий расчитанный поворот камеры
        self.rotation_lock = threading.Lock()

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

    def update_camera_rotation(self, frame_width, frame_height):
        """Автоматически обновляет углы поворота камеры на основе отслеживаемых объектов"""
        if not self.tracked_entities:
            return
        
        # Берем первый отслеживаемый объект (можно изменить логику выбора)
        track_id = next(iter(self.tracked_entities))
        entity = self.tracked_entities[track_id]
        
        screen_center_x = frame_width // 2
        screen_center_y = frame_height // 2
        
        # Рассчитываем новые углы
        angles_x = round(
            (self.camera_angles[0] + 
             (entity["center_x"] - screen_center_x) / (screen_center_x * 2) * self.camera_view_angles[0]) % 360, 
            3
        )
        angles_y = round(
            (self.camera_angles[1] + 
             (entity["center_y"] - screen_center_y) / (screen_center_y * 2) * self.camera_view_angles[1]) % 360, 
            3
        )
        
        with self.rotation_lock:
            self.camera_rotation = [angles_x, angles_y]

    def get_camera_rotation(self):
        """Возвращает текущие углы поворота камеры"""
        with self.rotation_lock:
            return self.camera_rotation.copy()
