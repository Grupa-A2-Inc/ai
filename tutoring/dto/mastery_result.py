from dataclasses import dataclass

@dataclass
class MasteryResult:
    def __init__(self, mastery_score: float):
        self.mastery_score = mastery_score
    