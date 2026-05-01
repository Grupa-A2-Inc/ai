from django.test import TestCase

from tutoring.models import (
    Question,
    QuestionCorrectOption,
    QuestionOption,
    QuestionType,
    StudentInteraction,
)


class ModelTests(TestCase):
    def test_question_save_sets_ml_exercise_id_from_database_id(self):
        question = Question.objects.create(
            subject_id=1,
            topic_id=101,
            question_type=QuestionType.SINGLE_CHOICE,
            content="Question content",
        )

        self.assertEqual(question.ml_exercise_id, str(question.id))

    def test_model_string_representations(self):
        question = Question.objects.create(
            subject_id=1,
            topic_id=101,
            ml_exercise_id="exercise-1",
            question_type=QuestionType.SINGLE_CHOICE,
            content="Question content",
        )
        option = QuestionOption.objects.create(
            question=question,
            text="Answer A",
            display_order=1,
        )
        correct_option = QuestionCorrectOption.objects.create(
            question=question,
            option=option,
        )
        interaction = StudentInteraction.objects.create(
            user_id="student-1",
            question=question,
            ml_exercise_id="exercise-1",
            is_correct=True,
            score=1.0,
            time_spent=12.5,
        )

        self.assertEqual(str(question), f"Question {question.id} - topic 101")
        self.assertEqual(
            str(option),
            f"Option {option.id} for question {question.id}",
        )
        self.assertEqual(
            str(correct_option),
            f"Correct option {option.id} for question {question.id}",
        )
        self.assertEqual(
            str(interaction),
            f"Interaction user=student-1, question={question.id}",
        )
