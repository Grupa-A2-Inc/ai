class StudentDataRepository:
    def get_student_profile(self, user_id):
        pass

    def get_student_progress(self, user_id, subject_id=None, topic_id=None):
        pass

    def get_recent_test_attempts(self, user_id, subject_id=None, topic_id=None, limit=10):
        pass

    def get_recent_attempt_answers(self, user_id, subject_id=None, topic_id=None, limit=20):
        pass