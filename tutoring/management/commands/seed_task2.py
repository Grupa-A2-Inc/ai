from django.core.management.base import BaseCommand
from tutoring.models import Question, StudentInteraction


class Command(BaseCommand):
    help = "Seed demo data for Task 2"

    def handle(self, *args, **kwargs):
        Question.objects.all().delete()
        StudentInteraction.objects.all().delete()

        q1 = Question.objects.create(subject_id=3, topic_id=8, content="Q1 topic8", difficulty_initial=0.2)
        q2 = Question.objects.create(subject_id=3, topic_id=8, content="Q2 topic8", difficulty_initial=0.5)
        q3 = Question.objects.create(subject_id=3, topic_id=8, content="Q3 topic8", difficulty_initial=0.8)

        Question.objects.create(subject_id=3, topic_id=9, content="Q1 topic9", difficulty_initial=0.4)
        Question.objects.create(subject_id=3, topic_id=9, content="Q2 topic9", difficulty_initial=0.6)

        StudentInteraction.objects.create(user_id=12, question=q1, is_correct=True, time_spent=30.0)
        StudentInteraction.objects.create(user_id=12, question=q1, is_correct=False, time_spent=45.0)
        StudentInteraction.objects.create(user_id=12, question=q2, is_correct=True, time_spent=20.0)
        StudentInteraction.objects.create(user_id=12, question=q2, is_correct=True, time_spent=18.0)
        StudentInteraction.objects.create(user_id=12, question=q2, is_correct=False, time_spent=60.0)


        self.stdout.write(self.style.SUCCESS("Seed data created."))
