from django.test import override_settings
from django.urls import reverse
from rest_framework.test import APITestCase

from tutoring.models import (
    Question,
    QuestionCorrectOption,
    QuestionOption,
    QuestionType,
    StudentInteraction,
    StudentProfile,
    StudentTopicLevel,
)


@override_settings(EXTERNAL_API_KEY="test-secret")
class AdaptiveFlowE2ETests(APITestCase):
    def setUp(self):
        self.student_id = "student-uuid-e2e"
        self.subject_id = 2
        self.topic_id = 1102

        self.selected_question = self._create_question(
            question_id=101,
            difficulty=0.6,
            content="Calculati derivata lui f(x)=3x^2+2x",
            answers=["6x+2", "3x+2", "6x^2+2", "3x^2"],
            correct_answer_indexes=[0],
        )

        self.other_question = self._create_question(
            question_id=102,
            difficulty=0.9,
            content="Care este integrala lui x?",
            answers=["x", "x^2/2 + C", "2x + C", "ln(x) + C"],
            correct_answer_indexes=[1],
        )

    def _sync_student(self):
        return self.client.post(
            reverse("student-sync"),
            {
                "requestId": "req-e2e-1",
                "studentId": self.student_id,
            },
            format="json",
            HTTP_X_API_KEY="test-secret",
        )

    def _request_exercises(self, count: int = 1):
        return self.client.post(
            reverse("adaptive-exercises"),
            {
                "studentId": self.student_id,
                "subjectId": self.subject_id,
                "topicId": self.topic_id,
                "count": count,
            },
            format="json",
            HTTP_X_API_KEY="test-secret",
        )

    def _send_feedback(self, ml_exercise_id: str, score: float, time_spent: float):
        return self.client.post(
            reverse("adaptive-feedback"),
            {
                "studentId": self.student_id,
                "subjectId": self.subject_id,
                "topicId": self.topic_id,
                "results": [
                    {
                        "mlExerciseId": ml_exercise_id,
                        "score": score,
                        "timeSpent": time_spent,
                    }
                ],
            },
            format="json",
            HTTP_X_API_KEY="test-secret",
        )

    def _create_question(
        self,
        question_id: int,
        difficulty: float,
        content: str,
        answers: list[str],
        correct_answer_indexes: list[int],
    ) -> Question:
        question = Question.objects.create(
            id=question_id,
            subject_id=self.subject_id,
            topic_id=self.topic_id,
            question_type=QuestionType.SINGLE_CHOICE,
            content=content,
            difficulty=difficulty,
            is_active=True,
        )

        created_options = []
        for index, answer in enumerate(answers, start=1):
            created_options.append(
                QuestionOption.objects.create(
                    question=question,
                    text=answer,
                    display_order=index,
                )
            )

        for answer_index in correct_answer_indexes:
            QuestionCorrectOption.objects.create(
                question=question,
                option=created_options[answer_index],
            )

        return question

    def test_full_adaptive_flow_sync_exercises_feedback_updates_student_and_question(self):
        sync_response = self._sync_student()

        self.assertEqual(sync_response.status_code, 200)
        self.assertEqual(sync_response.data["status"], "ok")
        self.assertTrue(
            StudentProfile.objects.filter(
                student_id=self.student_id,
                is_active=True,
            ).exists()
        )
        self.assertTrue(
            StudentTopicLevel.objects.filter(
                student__student_id=self.student_id,
                subject_id=self.subject_id,
                topic_id=self.topic_id,
            ).exists()
        )

        exercises_response = self._request_exercises(count=1)

        self.assertEqual(exercises_response.status_code, 200)
        self.assertEqual(len(exercises_response.data["exercises"]), 1)

        exercise = exercises_response.data["exercises"][0]

        self.selected_question.refresh_from_db()
        self.other_question.refresh_from_db()

        self.assertEqual(exercise["exerciseId"], self.selected_question.ml_exercise_id)
        self.assertEqual(exercise["text"], self.selected_question.content)
        self.assertEqual(exercise["type"], "SINGLE_CHOICE")
        self.assertEqual(
            exercise["answers"],
            ["6x+2", "3x+2", "6x^2+2", "3x^2"],
        )
        self.assertEqual(exercise["correctAnswers"], ["6x+2"])
        self.assertEqual(exercise["difficulty"], 0.6)
        self.assertEqual(self.other_question.times_answered, 0)

        feedback_response = self._send_feedback(
            ml_exercise_id=exercise["exerciseId"],
            score=1,
            time_spent=30,
        )

        self.assertEqual(feedback_response.status_code, 200)
        self.assertEqual(feedback_response.data, {"ack": True})

        topic_level = StudentTopicLevel.objects.get(
            student__student_id=self.student_id,
            subject_id=self.subject_id,
            topic_id=self.topic_id,
        )
        self.selected_question.refresh_from_db()

        self.assertAlmostEqual(topic_level.mastery_score, 0.6)
        self.assertEqual(self.selected_question.times_answered, 1)
        self.assertEqual(self.selected_question.times_correct, 1)
        self.assertEqual(self.selected_question.avg_time_spent, 30.0)

        interaction = StudentInteraction.objects.get(
            user_id=self.student_id,
            question=self.selected_question,
            ml_exercise_id=exercise["exerciseId"],
        )

        self.assertTrue(interaction.is_correct)
        self.assertEqual(interaction.score, 1.0)
        self.assertEqual(interaction.time_spent, 30.0)

    def test_full_adaptive_flow_bad_feedback_decreases_mastery_and_keeps_times_correct(self):
        sync_response = self._sync_student()

        self.assertEqual(sync_response.status_code, 200)

        exercises_response = self._request_exercises(count=1)

        self.assertEqual(exercises_response.status_code, 200)
        exercise = exercises_response.data["exercises"][0]

        feedback_response = self._send_feedback(
            ml_exercise_id=exercise["exerciseId"],
            score=0,
            time_spent=90,
        )

        self.assertEqual(feedback_response.status_code, 200)
        self.assertEqual(feedback_response.data, {"ack": True})

        topic_level = StudentTopicLevel.objects.get(
            student__student_id=self.student_id,
            subject_id=self.subject_id,
            topic_id=self.topic_id,
        )
        self.selected_question.refresh_from_db()

        self.assertAlmostEqual(topic_level.mastery_score, 0.4)
        self.assertEqual(self.selected_question.times_answered, 1)
        self.assertEqual(self.selected_question.times_correct, 0)
        self.assertEqual(self.selected_question.avg_time_spent, 90.0)

        interaction = StudentInteraction.objects.get(
            user_id=self.student_id,
            question=self.selected_question,
            ml_exercise_id=exercise["exerciseId"],
        )

        self.assertFalse(interaction.is_correct)
        self.assertEqual(interaction.score, 0.0)
        self.assertEqual(interaction.time_spent, 90.0)

    def test_second_exercise_request_avoids_question_already_answered(self):
        sync_response = self._sync_student()

        self.assertEqual(sync_response.status_code, 200)

        first_exercises_response = self._request_exercises(count=1)

        self.assertEqual(first_exercises_response.status_code, 200)
        first_exercise = first_exercises_response.data["exercises"][0]
        self.selected_question.refresh_from_db()
        self.assertEqual(first_exercise["exerciseId"], self.selected_question.ml_exercise_id)

        feedback_response = self._send_feedback(
            ml_exercise_id=first_exercise["exerciseId"],
            score=1,
            time_spent=25,
        )

        self.assertEqual(feedback_response.status_code, 200)

        second_exercises_response = self._request_exercises(count=1)

        self.assertEqual(second_exercises_response.status_code, 200)
        self.assertEqual(len(second_exercises_response.data["exercises"]), 1)

        second_exercise = second_exercises_response.data["exercises"][0]

        self.other_question.refresh_from_db()

        self.assertEqual(second_exercise["exerciseId"], self.other_question.ml_exercise_id)
        self.assertNotEqual(second_exercise["exerciseId"], first_exercise["exerciseId"])
