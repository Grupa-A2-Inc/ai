from django.db import models


class Question(models.Model):
    subject_id = models.IntegerField()
    topic_id = models.IntegerField()
    content = models.TextField()
    difficulty_initial = models.FloatField(default=0.5)
    difficulty_observed = models.FloatField(default=0.5)
    times_answered = models.IntegerField(default=0)
    times_correct = models.IntegerField(default=0)
    avg_time_spent = models.FloatField(default=0.0)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"Question {self.id} - topic {self.topic_id}"


class StudentInteraction(models.Model):
    user_id = models.IntegerField()
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    is_correct = models.BooleanField()
    score = models.FloatField(default=0.0)
    time_spent = models.FloatField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Interaction user={self.user_id}, question={self.question_id}"
