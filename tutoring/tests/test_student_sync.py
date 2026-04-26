import pytest
from tutoring.models import StudentProfile, StudentTopicLevel, Question, QuestionType
from tutoring.services.student_sync_service import StudentSyncService

# Mark all tests in this module to use the database
pytestmark = pytest.mark.django_db


class TestStudentSyncService:
    def test_sync_new_student_creates_profile_and_levels(self):
        """Verifică dacă un student nou este creat cu nivelurile de topic implicite."""
        # Setup: Creăm întrebări folosind câmpurile corecte: 'content' și 'question_type'
        Question.objects.create(
            subject_id=1,
            topic_id=101,
            is_active=True,
            content="Q1",
            question_type=QuestionType.SINGLE_CHOICE
        )
        Question.objects.create(
            subject_id=1,
            topic_id=102,
            is_active=True,
            content="Q2",
            question_type=QuestionType.SINGLE_CHOICE
        )

        service = StudentSyncService()
        student, created = service.sync_student(student_id=12)

        assert created is True
        assert StudentProfile.objects.filter(student_id=12).exists()
        # Verificăm dacă s-au creat cele 2 niveluri de topic
        assert StudentTopicLevel.objects.filter(student=student).count() == 2

    def test_sync_existing_student_is_idempotent(self):
        """Verifică dacă apelarea multiplă nu duplică studentul."""
        Question.objects.create(
            subject_id=1,
            topic_id=101,
            is_active=True,
            content="Q1",
            question_type=QuestionType.SINGLE_CHOICE
        )

        service = StudentSyncService()
        service.sync_student(student_id=12)

        # A doua apelare
        student, created = service.sync_student(student_id=12)

        assert created is False
        assert StudentProfile.objects.count() == 1

    def test_sync_adds_missing_topics_only(self):
        """Verifică dacă se adaugă doar topicele noi pentru un student existent."""
        service = StudentSyncService()

        # 1. Creăm primul topic și sincronizăm
        Question.objects.create(
            subject_id=1, topic_id=101, is_active=True,
            content="Q1", question_type=QuestionType.SINGLE_CHOICE
        )
        service.sync_student(student_id=12)

        # 2. Apare un topic nou (id 202)
        Question.objects.create(
            subject_id=1, topic_id=202, is_active=True,
            content="Q2", question_type=QuestionType.SINGLE_CHOICE
        )

        # 3. Sincronizăm din nou
        service.sync_student(student_id=12)

        assert StudentTopicLevel.objects.filter(student__student_id=12).count() == 2