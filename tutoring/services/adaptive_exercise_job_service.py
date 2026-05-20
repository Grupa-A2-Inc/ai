import logging
from concurrent.futures import ThreadPoolExecutor

from django.conf import settings
from django.db import close_old_connections

from tutoring.models import (
    AdaptiveExerciseGenerationJob,
    AdaptiveExerciseGenerationJobStatus,
)
from tutoring.services.adaptive_exercise_service import (
    AdaptiveExerciseService,
    StudentNotFoundError,
)

logger = logging.getLogger(__name__)

_executor = ThreadPoolExecutor(
    max_workers=getattr(settings, "ADAPTIVE_EXERCISE_JOB_WORKERS", 1)
)


class AdaptiveExerciseGenerationJobService:
    def create_job(
        self,
        student_id: str,
        subject_id: int,
        topic_id: int,
        count: int,
    ) -> AdaptiveExerciseGenerationJob:
        job = AdaptiveExerciseGenerationJob.objects.create(
            student_id=student_id,
            subject_id=subject_id,
            topic_id=topic_id,
            count=count,
        )
        _executor.submit(self._run_job, str(job.id))
        return job

    def get_job(self, job_id) -> AdaptiveExerciseGenerationJob | None:
        return AdaptiveExerciseGenerationJob.objects.filter(id=job_id).first()

    def _run_job(self, job_id: str) -> None:
        close_old_connections()
        try:
            job = AdaptiveExerciseGenerationJob.objects.get(id=job_id)
            job.status = AdaptiveExerciseGenerationJobStatus.RUNNING
            job.save(update_fields=["status", "updated_at"])

            exercises = AdaptiveExerciseService().generate_exercises(
                student_id=job.student_id,
                subject_id=job.subject_id,
                topic_id=job.topic_id,
                count=job.count,
            )

            job.status = AdaptiveExerciseGenerationJobStatus.DONE
            job.result = {"exercises": exercises}
            job.error = ""
            job.save(update_fields=["status", "result", "error", "updated_at"])
        except StudentNotFoundError as exc:
            logger.exception("Adaptive exercise generation job failed")
            self._mark_failed(job_id=job_id, error="Studentul nu există.")
        except Exception:
            logger.exception("Unexpected adaptive exercise generation job failure")
            self._mark_failed(
                job_id=job_id,
                error="Serviciul de exerciții adaptive nu este disponibil.",
            )
        finally:
            close_old_connections()

    def _mark_failed(self, job_id: str, error: str) -> None:
        AdaptiveExerciseGenerationJob.objects.filter(id=job_id).update(
            status=AdaptiveExerciseGenerationJobStatus.FAILED,
            error=error,
        )
