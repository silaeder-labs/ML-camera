class BaseTracker:
    def __init__(self, cap):
        self.cap = cap
        self.id_colors = {}
        self.tracked_entities = {}
        self.started = False

    def start(self):
        self.started = True

    def stop(self):
        self.started = False

    def generate_frames(self):
        raise NotImplementedError
