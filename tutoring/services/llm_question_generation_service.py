import json
import logging
from urllib.error import URLError
from urllib.request import Request, urlopen

from django.conf import settings
from rest_framework import serializers

from tutoring.serializers import GenerateQuestionsResponseSerializer
from tutoring.services.question_generation_prompt_service import (
    QuestionGenerationPromptService,
)

logger = logging.getLogger(__name__)


class LLMQuestionGenerationError(Exception):
    pass


class LLMQuestionGenerationUnavailableError(LLMQuestionGenerationError):
    pass


class LLMQuestionGenerationInvalidResponseError(LLMQuestionGenerationError):
    pass


class LLMQuestionGenerationService:
    REQUEST_TIMEOUT_SECONDS = 60

    def __init__(self, prompt_service=None, transport=None):
        self.prompt_service = prompt_service or QuestionGenerationPromptService()
        self.transport = transport or self._call_local_llm

    def generate(self, content: str, count: int = 5) -> list[dict]:
        prompt = self.prompt_service.build_prompt(content=content, count=count)
        return self.generate_from_prompt(prompt=prompt, expected_count=count)

    def generate_from_prompt(
        self,
        prompt: str,
        expected_count: int | None = None,
    ) -> list[dict]:
        raw_response = self.transport(prompt)
        response_text = self._extract_response_text(raw_response)
        payload = self._parse_json_payload(response_text)

        serializer = GenerateQuestionsResponseSerializer(data=payload)
        try:
            serializer.is_valid(raise_exception=True)
        except serializers.ValidationError as exc:
            raise LLMQuestionGenerationInvalidResponseError(
                "LLM response does not match the expected question schema."
            ) from exc

        questions = serializer.validated_data["questions"]
        if expected_count is not None and len(questions) != expected_count:
            raise LLMQuestionGenerationInvalidResponseError(
                f"LLM returned {len(questions)} questions, expected {expected_count}."
            )

        return questions

    def _call_local_llm(self, prompt: str) -> str:
        url = getattr(settings, "LLM_URL", "http://localhost:11434/api/generate")
        model = getattr(settings, "LLM_MODEL", "qwen2.5:3b-instruct")
        request_payload = {
            "model": model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.2,
                "top_p": 0.95,
            },
        }

        request = Request(
            url,
            data=json.dumps(request_payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        try:
            with urlopen(request, timeout=self.REQUEST_TIMEOUT_SECONDS) as response:
                response_body = response.read().decode("utf-8")
        except (URLError, TimeoutError, ValueError) as exc:
            logger.exception("Local LLM API request failed")
            raise LLMQuestionGenerationUnavailableError(
                "Local LLM API request failed."
            ) from exc

        try:
            response_json = json.loads(response_body)
        except json.JSONDecodeError as exc:
            raise LLMQuestionGenerationInvalidResponseError(
                "Local LLM returned invalid JSON."
            ) from exc

        return self._extract_local_response_text(response_json)

    def _extract_local_response_text(self, response_json: dict) -> str:
        response_text = response_json.get("response")
        if isinstance(response_text, str) and response_text.strip():
            return response_text.strip()

        message = response_json.get("message")
        if isinstance(message, str) and message.strip():
            return message.strip()

        text = response_json.get("text")
        if isinstance(text, str) and text.strip():
            return text.strip()

        raise LLMQuestionGenerationInvalidResponseError(
            "Local LLM response does not contain generated text."
        )

    def _extract_response_text(self, raw_response) -> str:
        if isinstance(raw_response, str):
            return raw_response.strip()

        if isinstance(raw_response, dict):
            text = raw_response.get("text")
            if isinstance(text, str):
                return text.strip()

        raise LLMQuestionGenerationInvalidResponseError(
            "LLM response has an unsupported shape."
        )

    def _parse_json_payload(self, response_text: str) -> dict:
        stripped_text = response_text.strip()
        stripped_text = self._strip_markdown_fences(stripped_text)

        payload = self._try_parse_json(stripped_text)
        if payload is None:
            start = stripped_text.find("{")
            end = stripped_text.rfind("}")
            if start != -1 and end != -1 and end > start:
                payload = self._try_parse_json(stripped_text[start : end + 1])

        if payload is None:
            raise LLMQuestionGenerationInvalidResponseError(
                "LLM response is not valid JSON."
            )

        if not isinstance(payload, dict):
            raise LLMQuestionGenerationInvalidResponseError(
                "LLM response must be a JSON object."
            )

        return payload

    def _strip_markdown_fences(self, text: str) -> str:
        if not text.startswith("```"):
            return text

        lines = text.splitlines()
        if not lines:  # pragma: no cover
            return text

        if lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].startswith("```"):
            lines = lines[:-1]
        if lines and lines[0].strip().lower() == "json":
            lines = lines[1:]

        return "\n".join(lines).strip()

    def _try_parse_json(self, text: str):
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            return None
