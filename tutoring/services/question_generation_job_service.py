import logging
from concurrent.futures import ThreadPoolExecutor

from django.conf import settings
from django.db import close_old_connections

from tutoring.models import QuestionGenerationJob, QuestionGenerationJobStatus
from tutoring.services.llm_question_generation_service import (
    LLMQuestionGenerationError,
    LLMQuestionGenerationService,
)

logger = logging.getLogger(__name__)

_executor = ThreadPoolExecutor(
    max_workers=getattr(settings, "LLM_GENERATION_JOB_WORKERS", 1)
)


class QuestionGenerationJobService:
    def create_job(self, content: str, count: int) -> QuestionGenerationJob:
        job = QuestionGenerationJob.objects.create(
            content=content,
            count=count,
        )
        _executor.submit(self._run_job, str(job.id))
        return job

    def get_job(self, job_id) -> QuestionGenerationJob | None:
        return QuestionGenerationJob.objects.filter(id=job_id).first()

    def _run_job(self, job_id: str) -> None:
        close_old_connections()
        try:
            job = QuestionGenerationJob.objects.get(id=job_id)
            job.status = QuestionGenerationJobStatus.RUNNING
            job.save(update_fields=["status", "updated_at"])

            questions = LLMQuestionGenerationService().generate(
                content=job.content,
                count=job.count,
            )

            job.status = QuestionGenerationJobStatus.DONE
            job.result = {"questions": questions}
            job.error = ""
            job.save(update_fields=["status", "result", "error", "updated_at"])
        except LLMQuestionGenerationError as exc:
            logger.exception("Question generation job failed")
            self._mark_failed(job_id=job_id, error=str(exc))
        except Exception as exc:
            logger.exception("Unexpected question generation job failure")
            self._mark_failed(job_id=job_id, error="Unexpected generation error.")
        finally:
            close_old_connections()

    def _mark_failed(self, job_id: str, error: str) -> None:
        QuestionGenerationJob.objects.filter(id=job_id).update(
            status=QuestionGenerationJobStatus.FAILED,
            error=error,
        )
