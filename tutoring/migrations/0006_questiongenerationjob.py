import uuid

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("tutoring", "0005_remove_studentinteraction_ml_exercise_id_null"),
    ]

    operations = [
        migrations.CreateModel(
            name="QuestionGenerationJob",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("PENDING", "Pending"),
                            ("RUNNING", "Running"),
                            ("DONE", "Done"),
                            ("FAILED", "Failed"),
                        ],
                        default="PENDING",
                        max_length=20,
                    ),
                ),
                ("content", models.TextField()),
                ("count", models.IntegerField(default=5)),
                ("result", models.JSONField(blank=True, null=True)),
                ("error", models.TextField(blank=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "ordering": ["-created_at"],
            },
        ),
    ]
