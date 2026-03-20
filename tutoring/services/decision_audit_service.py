class DecisionAuditService:
    def log_difficulty_adjustment(self, user_id, subject_id, old_value, new_value, reason):
        pass

    def log_recommendation(self, user_id, recommendation):
        pass

    def log_model_prediction(self, user_id, subject_id, topic_id, prediction_type, score, source):
        pass