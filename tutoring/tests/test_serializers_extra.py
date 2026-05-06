from tutoring.serializers import GeneratedQuestionSerializer


def valid_question(**overrides):
    question = {
        "text": "Question?",
        "type": "SINGLE_CHOICE",
        "answers": ["A", "B", "C", "D"],
        "correctAnswers": ["A"],
        "difficulty": 0.5,
    }
    question.update(overrides)
    return question


def test_generated_question_accepts_valid_payload():
    serializer = GeneratedQuestionSerializer(data=valid_question())

    assert serializer.is_valid()


def test_generated_question_rejects_correct_answer_outside_answers():
    serializer = GeneratedQuestionSerializer(
        data=valid_question(correctAnswers=["Z"])
    )

    assert not serializer.is_valid()
    assert "correctAnswers" in serializer.errors


def test_generated_question_rejects_multiple_correct_answers_for_single_choice():
    serializer = GeneratedQuestionSerializer(
        data=valid_question(correctAnswers=["A", "B"])
    )

    assert not serializer.is_valid()
    assert "correctAnswers" in serializer.errors
