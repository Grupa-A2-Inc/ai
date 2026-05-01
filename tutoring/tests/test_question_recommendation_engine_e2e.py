from dataclasses import dataclass
from unittest import TestCase

from tutoring.services.recommendation_engine import QuestionRecommendationEngine


@dataclass
class DummyQuestion:
    id: int
    subject_id: int
    topic_id: int
    difficulty: float


@dataclass
class DummyInteraction:
    is_correct: bool
    time_spent: float


@dataclass
class DummyStudentContext:
    history: list
    seen_question_ids: list
    candidate_questions: list


class FakeRepository:
    """
    Repository fake folosit doar în teste.

    De ce există:
    - vrem să testăm flow-ul complet din QuestionRecommendationEngine
    - NU vrem să depindem de DB real sau de query-uri reale
    - oferim direct student_context-ul de care engine-ul are nevoie

    Semnătura build_student_context(...) este păstrată identic cu repository-ul real
    ca engine-ul să poată folosi fake-ul fără modificări.
    """

    def __init__(self, student_context):
        self.student_context = student_context

    def build_student_context(self, user_id: int, subject_id: int, topic_id: int):
        return self.student_context


class QuestionRecommendationEngineE2ETests(TestCase):
    def test_end_to_end_returns_expected_recommendation(self):
        """
        Flow testat:
        1. repository construiește student_context
        2. feature_service calculează raw features
        3. feature_service normalizează
        4. mastery_estimator calculează mastery
        5. difficulty_estimator calculează target difficulty
        6. selection_engine alege întrebarea
        7. engine întoarce QuestionRecommendationResult

        Date:
        history:
        - corect, 20 sec
        - greșit, 40 sec
        - corect, 30 sec

        Calcul:
        correct_count = 2
        attempt_count = 3
        accuracy = 2 / 3 = 0.6667

        avg_time = (20 + 40 + 30) / 3 = 30

        Presupunem formula de normalizare folosită în proiect:
        normalized_time = avg_time / 60 = 30 / 60 = 0.5

        Formula de mastery:
        mastery = 0.7 * accuracy + 0.3 * (1 - normalized_time)
        mastery = 0.7 * 0.6667 + 0.3 * (1 - 0.5)
        mastery = 0.4667 + 0.15
        mastery = 0.6167

        Target difficulty:
        target_difficulty = mastery + 0.1 = 0.7167

        Întrebări eligibile:
        - id=2, difficulty=0.6
        - id=3, difficulty=0.8
        (id=1 este exclusă pentru că este văzută deja)

        Distanțe:
        |0.6 - 0.7167| = 0.1167
        |0.8 - 0.7167| = 0.0833

        0.8 este mai aproape de target, deci întrebarea corectă este id=3.
        """

        engine = QuestionRecommendationEngine()

        student_context = DummyStudentContext(
            history=[
                DummyInteraction(is_correct=True, time_spent=20.0),
                DummyInteraction(is_correct=False, time_spent=40.0),
                DummyInteraction(is_correct=True, time_spent=30.0),
            ],
            seen_question_ids=[1],
            candidate_questions=[
                DummyQuestion(id=1, subject_id=3, topic_id=8, difficulty=0.5),
                DummyQuestion(id=2, subject_id=3, topic_id=8, difficulty=0.6),
                DummyQuestion(id=3, subject_id=3, topic_id=8, difficulty=0.8),
            ],
        )

        engine.repository = FakeRepository(student_context)

        result = engine.recommend(
            user_id=12,
            subject_id=3,
            topic_id=8,
        )

        self.assertIsNotNone(result)
        self.assertEqual(result.question_id, 3)
        self.assertEqual(result.subject_id, 3)
        self.assertEqual(result.topic_id, 8)
        self.assertEqual(result.difficulty, 0.8)
        self.assertEqual(result.source, "selection")

    def test_end_to_end_returns_none_when_all_questions_are_seen(self):
        """
        Scenariu:
        - există candidate questions
        - dar toate sunt deja în seen_question_ids

        În acest caz:
        - selection_engine filtrează tot
        - nu mai rămâne nicio întrebare eligibilă
        - engine-ul trebuie să întoarcă None

        Asta verifică fallback-ul corect.
        """

        engine = QuestionRecommendationEngine()

        student_context = DummyStudentContext(
            history=[
                DummyInteraction(is_correct=True, time_spent=20.0),
                DummyInteraction(is_correct=True, time_spent=25.0),
            ],
            seen_question_ids=[10, 11],
            candidate_questions=[
                DummyQuestion(id=10, subject_id=4, topic_id=12, difficulty=0.6),
                DummyQuestion(id=11, subject_id=4, topic_id=12, difficulty=0.7),
            ],
        )

        engine.repository = FakeRepository(student_context)

        result = engine.recommend(
            user_id=15,
            subject_id=4,
            topic_id=12,
        )

        self.assertIsNone(result)

    def test_end_to_end_returns_none_when_candidate_list_is_empty(self):
        """
        Scenariu:
        - studentul are istoric
        - dar repository-ul nu găsește nicio întrebare candidat

        În acest caz:
        - selection_engine primește listă goală
        - întoarce None
        - engine-ul trebuie să întoarcă None

        Verificăm că sistemul nu crapă și gestionează cazul controlat.
        """

        engine = QuestionRecommendationEngine()

        student_context = DummyStudentContext(
            history=[
                DummyInteraction(is_correct=True, time_spent=22.0),
                DummyInteraction(is_correct=False, time_spent=35.0),
            ],
            seen_question_ids=[],
            candidate_questions=[],
        )

        engine.repository = FakeRepository(student_context)

        result = engine.recommend(
            user_id=9,
            subject_id=2,
            topic_id=5,
        )

        self.assertIsNone(result)

    def test_end_to_end_handles_new_student_with_no_history(self):
        """
        Scenariu:
        - elev nou
        - history goală
        - candidate questions există

        Presupunerea din proiect:
        pentru history goală, feature_service întoarce valori default:
        - accuracy = 0.5
        - avg_time = 30.0
        - attempt_count = 0

        Apoi:
        normalized_time = 30 / 60 = 0.5

        mastery = 0.7 * 0.5 + 0.3 * (1 - 0.5)
        mastery = 0.35 + 0.15
        mastery = 0.5

        target_difficulty = 0.5 + 0.1 = 0.6

        Candidate questions:
        - 0.4
        - 0.6
        - 0.9

        Distanțe față de target 0.6:
        |0.4 - 0.6| = 0.2
        |0.6 - 0.6| = 0.0
        |0.9 - 0.6| = 0.3

        Întrebarea corectă trebuie să fie cea cu difficulty = 0.6, adică id=22.
        """

        engine = QuestionRecommendationEngine()

        student_context = DummyStudentContext(
            history=[],
            seen_question_ids=[],
            candidate_questions=[
                DummyQuestion(id=21, subject_id=1, topic_id=3, difficulty=0.4),
                DummyQuestion(id=22, subject_id=1, topic_id=3, difficulty=0.6),
                DummyQuestion(id=23, subject_id=1, topic_id=3, difficulty=0.9),
            ],
        )

        engine.repository = FakeRepository(student_context)

        result = engine.recommend(
            user_id=100,
            subject_id=1,
            topic_id=3,
        )

        self.assertIsNotNone(result)
        self.assertEqual(result.question_id, 22)
        self.assertEqual(result.subject_id, 1)
        self.assertEqual(result.topic_id, 3)
        self.assertEqual(result.difficulty, 0.6)
        self.assertEqual(result.source, "selection")

    def test_end_to_end_skips_best_seen_question_and_selects_next_best(self):
        """
        Scenariu:
        cea mai bună întrebare după target difficulty este deja văzută.

        History:
        - corect, 20 sec
        - corect, 25 sec
        - greșit, 35 sec

        Calcul:
        correct_count = 2
        attempt_count = 3
        accuracy = 2 / 3 = 0.6667

        avg_time = (20 + 25 + 35) / 3 = 26.6667

        normalized_time = 26.6667 / 60 ≈ 0.4444

        mastery = 0.7 * 0.6667 + 0.3 * (1 - 0.4444)
        mastery = 0.4667 + 0.1667
        mastery ≈ 0.6334

        target_difficulty = 0.6334 + 0.1 = 0.7334

        Candidate questions:
        - id=31, difficulty=0.7   (dar este văzută deja)
        - id=32, difficulty=0.8
        - id=33, difficulty=0.9

        Dacă n-am filtra seen questions:
        0.7 ar fi foarte aproape de target.

        Dar pentru că id=31 este în seen_question_ids,
        trebuie să fie exclusă.

        Distanțe rămase:
        |0.8 - 0.7334| = 0.0666
        |0.9 - 0.7334| = 0.1666

        Așadar, întrebarea corectă este id=32.
        """

        engine = QuestionRecommendationEngine()

        student_context = DummyStudentContext(
            history=[
                DummyInteraction(is_correct=True, time_spent=20.0),
                DummyInteraction(is_correct=True, time_spent=25.0),
                DummyInteraction(is_correct=False, time_spent=35.0),
            ],
            seen_question_ids=[31],
            candidate_questions=[
                DummyQuestion(id=31, subject_id=7, topic_id=2, difficulty=0.7),
                DummyQuestion(id=32, subject_id=7, topic_id=2, difficulty=0.8),
                DummyQuestion(id=33, subject_id=7, topic_id=2, difficulty=0.9),
            ],
        )

        engine.repository = FakeRepository(student_context)

        result = engine.recommend(
            user_id=50,
            subject_id=7,
            topic_id=2,
        )

        self.assertIsNotNone(result)
        self.assertEqual(result.question_id, 32)
        self.assertEqual(result.subject_id, 7)
        self.assertEqual(result.topic_id, 2)
        self.assertEqual(result.difficulty, 0.8)
        self.assertEqual(result.source, "selection")
