from django.db import migrations, models


def replace_null_ml_exercise_ids(apps, schema_editor):
    StudentInteraction = apps.get_model("tutoring", "StudentInteraction")
    StudentInteraction.objects.filter(ml_exercise_id__isnull=True).update(
        ml_exercise_id=""
    )


class Migration(migrations.Migration):

    dependencies = [
        ("tutoring", "0004_alter_student_identifiers_to_char"),
    ]

    operations = [
        migrations.RunPython(
            replace_null_ml_exercise_ids,
            reverse_code=migrations.RunPython.noop,
        ),
        migrations.AlterField(
            model_name="studentinteraction",
            name="ml_exercise_id",
            field=models.CharField(blank=True, max_length=100),
        ),
    ]
