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
    studentId = serializers.CharField()

class AdaptiveFeedbackResultSerializer(serializers.Serializer):
    mlExerciseId = serializers.CharField()
    score = serializers.FloatField(min_value=0.0, max_value=1.0)
    timeSpent = serializers.FloatField(min_value=0.0)


class AdaptiveFeedbackRequestSerializer(serializers.Serializer):
    studentId = serializers.CharField()
    subjectId = serializers.IntegerField(min_value=1)
    topicId = serializers.IntegerField(min_value=1)
    results = AdaptiveFeedbackResultSerializer(many=True)

    def validate_results(self, value):
        if not value:
            raise serializers.ValidationError(
                "At least one feedback result is required."
            )
        return value


class CurriculumCatalogQuerySerializer(serializers.Serializer):
    grade = serializers.IntegerField(min_value=1, required=False)
    subjectId = serializers.IntegerField(min_value=1, required=False)
    topicId = serializers.IntegerField(min_value=1, required=False)


class CurriculumSubjectSerializer(serializers.Serializer):
    subjectId = serializers.IntegerField()
    subjectName = serializers.CharField()


class CurriculumTopicSerializer(serializers.Serializer):
    topicId = serializers.IntegerField()
    subjectId = serializers.IntegerField()
    subjectName = serializers.CharField()
    grade = serializers.IntegerField()
    topicName = serializers.CharField()


class CurriculumCatalogResponseSerializer(serializers.Serializer):
    subjects = CurriculumSubjectSerializer(many=True)
    topics = CurriculumTopicSerializer(many=True)


class ChatSupportRequestSerializer(serializers.Serializer):
    message = serializers.CharField(
        max_length=1000,
        min_length=1,
        help_text="The user's question or message for chat support"
    )
    studentId = serializers.CharField(
        required=False,
        help_text="Optional: the student ID for personalized context"
    )
    topicId = serializers.IntegerField(
        required=False,
        min_value=1,
        help_text="Optional: the topic ID being studied"
    )
    context = serializers.CharField(
        required=False,
        max_length=500,
        allow_blank=True,
        help_text="Optional: additional context for the chat"
    )
    language = serializers.ChoiceField(
        choices=["en", "ro"],
        default="en",
        required=False,
        help_text="Language for response: 'en' for English, 'ro' for Romanian"
    )


class ChatSupportResponseSerializer(serializers.Serializer):
    response = serializers.CharField(
        help_text="The chat support response"
    )
    timestamp = serializers.DateTimeField(
        help_text="When the response was generated"
    )
    model = serializers.CharField(
        help_text="The LLM model used"
    )
