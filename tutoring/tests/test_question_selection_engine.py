from dataclasses import dataclass

from tutoring.services.question_selection_engine import QuestionSelectionEngine


@dataclass
class DummyQuestion:
    id: int
    difficulty: float


class TestQuestionSelectionEngine:
    def setup_method(self):
        self.engine = QuestionSelectionEngine()

    def test_returns_closest_question_to_target(self):
        candidate_questions = [
            DummyQuestion(id=1, difficulty=0.2),
            DummyQuestion(id=2, difficulty=0.5),
            DummyQuestion(id=3, difficulty=0.8),
        ]

        selected_question = self.engine.select(
            candidate_questions=candidate_questions,
            target_difficulty=0.55,
            seen_question_ids=[],
        )

        assert selected_question is not None
        assert selected_question.id == 2
        assert selected_question.difficulty == 0.5

    def test_prefers_harder_question_on_tie(self):
        candidate_questions = [
            DummyQuestion(id=1, difficulty=0.4),
            DummyQuestion(id=2, difficulty=0.6),
        ]

        selected_question = self.engine.select(
            candidate_questions=candidate_questions,
            target_difficulty=0.5,
            seen_question_ids=[],
        )

        assert selected_question is not None
        assert selected_question.id == 2
        assert selected_question.difficulty == 0.6

    def test_skips_seen_question_and_selects_next_best(self):
        candidate_questions = [
            DummyQuestion(id=1, difficulty=0.5),
            DummyQuestion(id=2, difficulty=0.6),
            DummyQuestion(id=3, difficulty=0.8),
        ]

        selected_question = self.engine.select(
            candidate_questions=candidate_questions,
            target_difficulty=0.5,
            seen_question_ids=[1],
        )

        assert selected_question is not None
        assert selected_question.id == 2
        assert selected_question.difficulty == 0.6

    def test_returns_none_when_all_questions_are_seen(self):
        candidate_questions = [
            DummyQuestion(id=1, difficulty=0.5),
            DummyQuestion(id=2, difficulty=0.6),
        ]

        selected_question = self.engine.select(
            candidate_questions=candidate_questions,
            target_difficulty=0.5,
            seen_question_ids=[1, 2],
        )

        assert selected_question is None

    def test_returns_none_when_candidate_list_is_empty(self):
        selected_question = self.engine.select(
            candidate_questions=[],
            target_difficulty=0.5,
            seen_question_ids=[],
        )

        assert selected_question is None

    def test_works_when_seen_question_ids_is_none(self):
        candidate_questions = [
            DummyQuestion(id=1, difficulty=0.4),
            DummyQuestion(id=2, difficulty=0.7),
        ]

        selected_question = self.engine.select(
            candidate_questions=candidate_questions,
            target_difficulty=0.45,
            seen_question_ids=None,
        )

        assert selected_question is not None
        assert selected_question.id == 1