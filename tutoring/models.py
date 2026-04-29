from django.db import models


class QuestionType(models.TextChoices):
    SINGLE_CHOICE = "single_choice", "Single Choice"
    MULTIPLE_CHOICE = "multiple_choice", "Multiple Choice"


class Question(models.Model):
    subject_id = models.IntegerField()
    topic_id = models.IntegerField()
    ml_exercise_id = models.CharField(
        max_length=100,
        unique=True,
        null=True,
        blank=True,
    )

    question_type = models.CharField(
        max_length=20,
        choices=QuestionType.choices
    )

    content = models.TextField()
    difficulty = models.FloatField(default=0.5)

    is_active = models.BooleanField(default=True)

    times_answered = models.IntegerField(default=0)
    times_correct = models.IntegerField(default=0)
    avg_time_spent = models.FloatField(default=0.0)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

        if not self.ml_exercise_id:
            self.ml_exercise_id = str(self.id)
            super().save(update_fields=["ml_exercise_id"])

    def __str__(self):
        return f"Question {self.id} - topic {self.topic_id}"


class QuestionOption(models.Model):
    question = models.ForeignKey(
        Question,
        on_delete=models.CASCADE,
        related_name="options"
    )

    text = models.TextField()
    display_order = models.IntegerField(default=0)

    def __str__(self):
        return f"Option {self.id} for question {self.question_id}"


class QuestionCorrectOption(models.Model):
    question = models.ForeignKey(
        Question,
        on_delete=models.CASCADE,
        related_name="correct_options"
    )

    option = models.ForeignKey(
        QuestionOption,
        on_delete=models.CASCADE,
        related_name="correct_for_questions"
    )

    def __str__(self):
        return f"Correct option {self.option_id} for question {self.question_id}"


class StudentInteraction(models.Model):
    user_id = models.IntegerField()

    ml_exercise_id = models.CharField(
        max_length=100,
        null=True,
        blank=True,
    )

    question = models.ForeignKey(
        Question,
        on_delete=models.CASCADE,
        related_name="interactions"
    )

    is_correct = models.BooleanField()
    score = models.FloatField(default=0.0)
    time_spent = models.FloatField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Interaction user={self.user_id}, question={self.question_id}"


class StudentProfile(models.Model):
    student_id = models.IntegerField(unique=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

class StudentTopicLevel(models.Model):
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE)
    subject_id = models.IntegerField()
    topic_id = models.IntegerField()
    mastery_score = models.FloatField(default=0.5)

    class Meta:
        unique_together = ("student","subject_id", "topic_id")