from rest_framework import serializers

class AdaptiveExerciseSerializer(serializers.Serializer):
    exerciseId = serializers.CharField()
    text = serializers.CharField()
    type = serializers.ChoiceField(
        choices=["SINGLE_CHOICE", "MULTIPLE_CHOICE"]
    )
    answers = serializers.ListField(
        child=serializers.CharField(),
        min_length=2,
    )
    correctAnswers = serializers.ListField(
        child=serializers.CharField(),
        min_length=1,
    )
    difficulty = serializers.FloatField(min_value=0.0, max_value=1.0)


class AdaptiveExercisesResponseSerializer(serializers.Serializer):
    exercises = AdaptiveExerciseSerializer(many=True)

class AdaptiveExercisesRequestSerializer(serializers.Serializer):
    studentId = serializers.CharField()
    subjectId = serializers.IntegerField(min_value=1)
    topicId = serializers.IntegerField(min_value=1)
    count = serializers.IntegerField(
        min_value=1,
        max_value=20,
        required=False,
        default=5,
    )

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