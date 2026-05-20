from django.test import TestCase

from tutoring.models import Question, QuestionType
from tutoring.services.curriculum_catalog_service import CurriculumCatalogService


class CurriculumCatalogServiceTests(TestCase):
    def _create_questions(
        self,
        subject_id: int,
        topic_id: int,
        count: int,
    ):
        Question.objects.bulk_create(
            [
                Question(
                    subject_id=subject_id,
                    topic_id=topic_id,
                    question_type=QuestionType.SINGLE_CHOICE,
                    content=f"Question {index}",
                    difficulty=0.5,
                    is_active=True,
                )
                for index in range(count)
            ]
        )

    def test_catalog_uses_database_subject_topic_pairs(self):
        self._create_questions(subject_id=11, topic_id=2001, count=50)

        catalog = CurriculumCatalogService().list_catalog(topic_id=2001)

        self.assertEqual(
            catalog,
            {
                "subjects": [
                    {
                        "subjectId": 12,
                        "subjectName": "Limba engleză",
                    }
                ],
                "topics": [
                    {
                        "topicId": 2001,
                        "subjectId": 12,
                        "subjectName": "Limba engleză",
                        "grade": 9,
                        "topicName": "Structuri gramaticale de bază",
                    }
                ],
            },
        )

    def test_catalog_ignores_sparse_generated_fallback_topics(self):
        self._create_questions(subject_id=1, topic_id=2001, count=3)
        self._create_questions(subject_id=11, topic_id=2001, count=50)

        catalog = CurriculumCatalogService().list_catalog(topic_id=2001)

        self.assertEqual(
            [topic["subjectId"] for topic in catalog["topics"]],
            [12],
        )

    def test_catalog_canonicalizes_imported_subject_aliases(self):
        self._create_questions(subject_id=4, topic_id=1409, count=50)
        self._create_questions(subject_id=4, topic_id=2009, count=50)

        catalog = CurriculumCatalogService().list_catalog()

        self.assertEqual(
            catalog["subjects"],
            [
                {"subjectId": 5, "subjectName": "Fizică"},
                {"subjectId": 12, "subjectName": "Limba engleză"},
            ],
        )
        self.assertEqual(
            [
                (topic["subjectId"], topic["subjectName"], topic["topicName"])
                for topic in catalog["topics"]
            ],
            [
                (5, "Fizică", "Electricitate"),
                (12, "Limba engleză", "Gramatică avansată și conectori"),
            ],
        )

    def test_english_subject_topics_are_returned_in_romanian(self):
        catalog = CurriculumCatalogService().list_catalog(subject_id=12, grade=9)

        self.assertEqual(
            [topic["topicName"] for topic in catalog["topics"]],
            [
                "Structuri gramaticale de bază",
                "Vocabular cotidian",
                "Verbe frazale",
                "Cuvinte frecvent confundate",
            ],
        )

    def test_metadata_audit_accepts_verified_database_aliases(self):
        self._create_questions(subject_id=11, topic_id=2001, count=50)

        gaps = CurriculumCatalogService().find_database_metadata_gaps()

        self.assertEqual(gaps, [])

    def test_metadata_audit_reports_unmapped_database_pairs(self):
        self._create_questions(subject_id=99, topic_id=9901, count=50)

        gaps = CurriculumCatalogService().find_database_metadata_gaps()

        self.assertEqual(
            gaps,
            [
                {
                    "subjectId": 99,
                    "topicId": 9901,
                    "questionCount": 50,
                }
            ],
        )
