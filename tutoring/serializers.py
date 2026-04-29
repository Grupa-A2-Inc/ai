from rest_framework import serializers

class RecommendationRequestSerializer(serializers.Serializer):
    user_id = serializers.IntegerField(min_value=1)
    subject_id = serializers.IntegerField(min_value=1)
    topic_id = serializers.IntegerField(min_value=1)

class RecommendationResponseSerializer(serializers.Serializer):
    question_id = serializers.IntegerField()
    difficulty = serializers.FloatField()
    source = serializers.CharField()

class StudentSyncRequestSerializer(serializers.Serializer):
    requestId = serializers.CharField()
    studentId = serializers.IntegerField(min_value=1)

class AdaptiveFeedbackResultSerializer(serializers.Serializer):
    mlExerciseId = serializers.CharField()
    score = serializers.FloatField(min_value=0.0, max_value=1.0)
    timeSpent = serializers.FloatField(min_value=0.0)


class AdaptiveFeedbackRequestSerializer(serializers.Serializer):
    studentId = serializers.IntegerField(min_value=1)
    subjectId = serializers.IntegerField(min_value=1)
    topicId = serializers.IntegerField(min_value=1)
    results = AdaptiveFeedbackResultSerializer(many=True)

    def validate_results(self, value):
        if not value:
            raise serializers.ValidationError(
                "At least one feedback result is required."
            )
        return value