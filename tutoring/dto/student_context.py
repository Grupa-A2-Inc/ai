from dataclasses import dataclass

@dataclass
class StudentContext:
    user_id: int
    subject_id: int | None = None
    topic_id: int | None = None
    profile: object | None = None
    progress: object | None = None
    recent_attempts: list | None = None
    recent_answers: list | None = None
    material_views: list | None = None