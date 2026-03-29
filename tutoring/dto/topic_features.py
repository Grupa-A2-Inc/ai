from dataclasses import dataclass

@dataclass
class TopicFeatures:
    def __init__(self, accuracy: float, avg_time: float, attempt_count: int):
        self.accuracy = accuracy
        self.avg_time = avg_time
        self.attempt_count = attempt_count