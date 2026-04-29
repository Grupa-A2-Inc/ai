from tutoring.models import Question, StudentProfile, StudentTopicLevel

class StudentSyncService:
    DEFAULT_MASTERY = 0.5

    def sync_student(self, student_id: str):
        student, created = StudentProfile.objects.get_or_create(student_id=student_id, defaults={"is_active": True})

        topics = Question.objects.filter(is_active=True).values(
            "subject_id",
            "topic_id"
        ).distinct()

        for topic in topics:
            StudentTopicLevel.objects.get_or_create(
                student=student,
                subject_id=topic["subject_id"],
                topic_id=topic["topic_id"],
                defaults={"mastery_score": self.DEFAULT_MASTERY}
            )

        return student, created
