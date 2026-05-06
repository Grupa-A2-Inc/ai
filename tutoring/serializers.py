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


class GeneratedQuestionSerializer(serializers.Serializer):
    text = serializers.CharField(allow_blank=False, trim_whitespace=True)
    type = serializers.ChoiceField(
        choices=["SINGLE_CHOICE", "MULTIPLE_CHOICE"]
    )
    answers = serializers.ListField(
        child=serializers.CharField(allow_blank=False, trim_whitespace=True),
        min_length=4,
        max_length=4,
    )
    correctAnswers = serializers.ListField(
        child=serializers.CharField(allow_blank=False, trim_whitespace=True),
        min_length=1,
    )
    difficulty = serializers.FloatField(min_value=0.0, max_value=1.0)

    def validate(self, attrs):
        answers = attrs["answers"]
        correct_answers = attrs["correctAnswers"]

        if any(correct_answer not in answers for correct_answer in correct_answers):
            raise serializers.ValidationError(
                {"correctAnswers": "All correct answers must be present in answers."}
            )

        if attrs["type"] == "SINGLE_CHOICE" and len(correct_answers) != 1:
            raise serializers.ValidationError(
                {"correctAnswers": "Single choice questions must have exactly one correct answer."}
            )

        return attrs


class GenerateQuestionsRequestSerializer(serializers.Serializer):
    content = serializers.CharField(allow_blank=False, trim_whitespace=True)
    count = serializers.IntegerField(
        min_value=1,
        required=False,
        default=5,
    )


class GenerateQuestionsResponseSerializer(serializers.Serializer):
    questions = GeneratedQuestionSerializer(many=True)
