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
    DEFAULT_REQUEST_TIMEOUT_SECONDS = 35
    MAX_REPAIR_RESPONSE_LENGTH = 8000
    MAX_REPAIR_ORIGINAL_PROMPT_LENGTH = 12000

    def __init__(self, prompt_service=None, transport=None, provider=None):
        self.prompt_service = prompt_service or QuestionGenerationPromptService()
        self.transport = transport or self._call_configured_llm
        self.request_timeout_seconds = getattr(
            settings,
            "LLM_REQUEST_TIMEOUT_SECONDS",
            self.DEFAULT_REQUEST_TIMEOUT_SECONDS,
        )
        self.provider = (
            provider
            if provider is not None
            else getattr(settings, "LLM_PROVIDER", "ollama")
        ).strip().lower()

    def generate(self, content: str, count: int = 5) -> list[dict]:
        prompt = self.prompt_service.build_prompt(content=content, count=count)
        return self.generate_from_prompt(prompt=prompt, expected_count=count)

    def generate_from_prompt(
        self,
        prompt: str,
        expected_count: int | None = None,
        default_difficulty: float | None = None,
    ) -> list[dict]:
        return self._generate_valid_questions_with_repair(
            prompt=prompt,
            expected_count=expected_count,
            default_difficulty=default_difficulty,
        )

    def _generate_valid_questions_with_repair(
        self,
        prompt: str,
        expected_count: int | None = None,
        default_difficulty: float | None = None,
    ) -> list[dict]:
        try:
            return self._generate_from_prompt_once(
                prompt=prompt,
                expected_count=expected_count,
                default_difficulty=default_difficulty,
            )
        except LLMQuestionGenerationInvalidResponseError as first_error:
            raw_response = getattr(first_error, "raw_response", "")
            repair_prompt = self._build_repair_prompt(
                original_prompt=prompt,
                invalid_response=raw_response,
                validation_error=str(first_error),
                expected_count=expected_count,
            )
            try:
                return self._generate_from_prompt_once(
                    prompt=repair_prompt,
                    expected_count=expected_count,
                    default_difficulty=default_difficulty,
                )
            except LLMQuestionGenerationInvalidResponseError as second_error:
                raise second_error from first_error

    def _generate_from_prompt_once(
        self,
        prompt: str,
        expected_count: int | None = None,
        default_difficulty: float | None = None,
    ) -> list[dict]:
        raw_response = self.transport(prompt)
        response_text = self._extract_response_text(raw_response)
        try:
            payload = self._parse_json_payload(response_text)
            self._apply_default_difficulty(
                payload=payload,
                default_difficulty=default_difficulty,
            )
            self._normalize_question_types(payload)
            return self._validate_payload(payload, expected_count=expected_count)
        except LLMQuestionGenerationInvalidResponseError as exc:
            exc.raw_response = response_text
            logger.warning("Invalid LLM response text: %s", response_text[:2000])
            raise

    def _apply_default_difficulty(
        self,
        payload: dict,
        default_difficulty: float | None,
    ) -> None:
        if default_difficulty is None:
            return

        questions = payload.get("questions")
        if not isinstance(questions, list):
            return

        for question in questions:
            if isinstance(question, dict) and "difficulty" not in question:
                question["difficulty"] = default_difficulty

    def _normalize_question_types(self, payload: dict) -> None:
        questions = payload.get("questions")
        if not isinstance(questions, list):
            return

        for question in questions:
            if not isinstance(question, dict):
                continue

            correct_answers = question.get("correctAnswers")
            if not isinstance(correct_answers, list):
                continue

            if len(correct_answers) == 1:
                question["type"] = "SINGLE_CHOICE"
            elif len(correct_answers) > 1:
                question["type"] = "MULTIPLE_CHOICE"

    def _validate_payload(
        self,
        payload: dict,
        expected_count: int | None = None,
    ) -> list[dict]:

        serializer = GenerateQuestionsResponseSerializer(data=payload)
        try:
            serializer.is_valid(raise_exception=True)
        except serializers.ValidationError as exc:
            logger.warning("LLM response schema errors: %s", exc.detail)
            raise LLMQuestionGenerationInvalidResponseError(
                "LLM response does not match the expected question schema."
            ) from exc

        questions = serializer.validated_data["questions"]
        if expected_count is not None and len(questions) != expected_count:
            logger.warning(
                "LLM returned %s questions, expected %s.",
                len(questions),
                expected_count,
            )
            raise LLMQuestionGenerationInvalidResponseError(
                f"LLM returned {len(questions)} questions, expected {expected_count}."
            )

        return questions

    def _build_repair_prompt(
        self,
        original_prompt: str,
        invalid_response: str,
        validation_error: str,
        expected_count: int | None = None,
    ) -> str:
        expected_count_rule = ""
        if expected_count is not None:
            expected_count_rule = (
                f"- \"questions\" must contain exactly {expected_count} items.\n"
            )

        truncated_response = invalid_response[: self.MAX_REPAIR_RESPONSE_LENGTH]
        truncated_original_prompt = original_prompt[
            : self.MAX_REPAIR_ORIGINAL_PROMPT_LENGTH
        ]

        return (
            "You returned an invalid response for a question generation API.\n"
            "Repair it into valid JSON that matches this exact contract.\n\n"
            "Original generation prompt:\n"
            f"{truncated_original_prompt}\n\n"
            "Validation error:\n"
            f"{validation_error}\n\n"
            "Invalid response:\n"
            f"{truncated_response}\n\n"
            "Required JSON contract:\n"
            "- Return a single JSON object and nothing else.\n"
            "- The top-level object must contain exactly one key: \"questions\".\n"
            f"{expected_count_rule}"
            "- Every question object must contain exactly these keys: "
            "\"text\", \"type\", \"answers\", \"correctAnswers\", \"difficulty\".\n"
            "- \"type\" must be exactly \"SINGLE_CHOICE\" or \"MULTIPLE_CHOICE\".\n"
            "- \"answers\" must contain exactly 4 non-empty strings.\n"
            "- \"correctAnswers\" must contain exact string copies from \"answers\".\n"
            "- For SINGLE_CHOICE, \"correctAnswers\" must contain exactly 1 item.\n"
            "- For MULTIPLE_CHOICE, \"correctAnswers\" must contain at least 2 items.\n"
            "- \"difficulty\" must be a JSON number between 0.0 and 1.0.\n"
            "- The \"text\" field must not reveal or include the correct answer.\n"
            "- Do not include markdown, comments, explanations, trailing commas, "
            "or text outside JSON.\n"
        )

    def _call_configured_llm(self, prompt: str) -> str:
        if self.provider == "gemini":
            return self._call_gemini_llm(prompt)

        if self.provider == "ollama":
            return self._call_local_llm(prompt)

        raise LLMQuestionGenerationUnavailableError(
            f"Unsupported LLM provider: {self.provider}"
        )

    def _call_local_llm(self, prompt: str) -> str:
        url = getattr(settings, "LLM_URL", "http://localhost:11434/api/generate")
        model = getattr(settings, "LLM_MODEL", "qwen2.5:3b-instruct")
        request_payload = {
            "model": model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.1,
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
            with urlopen(request, timeout=self.request_timeout_seconds) as response:
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

    def _call_gemini_llm(self, prompt: str) -> str:
        api_key = getattr(settings, "GEMINI_API_KEY", "")
        if not api_key:
            raise LLMQuestionGenerationUnavailableError(
                "Gemini API key is not configured."
            )

        base_url = getattr(
            settings,
            "GEMINI_BASE_URL",
            "https://generativelanguage.googleapis.com/v1beta",
        )
        model = getattr(settings, "GEMINI_MODEL", "gemini-2.5-flash")
        url = f"{base_url.rstrip('/')}/models/{model}:generateContent"
        request_payload = {
            "contents": [
                {
                    "role": "user",
                    "parts": [{"text": prompt}],
                }
            ],
            "generationConfig": {
                "temperature": 0.1,
                "topP": 0.95,
                "responseMimeType": "application/json",
            },
        }

        request = Request(
            url,
            data=json.dumps(request_payload).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "x-goog-api-key": api_key,
            },
            method="POST",
        )

        try:
            with urlopen(request, timeout=self.request_timeout_seconds) as response:
                response_body = response.read().decode("utf-8")
        except (URLError, TimeoutError, ValueError) as exc:
            logger.exception("Gemini LLM API request failed")
            raise LLMQuestionGenerationUnavailableError(
                "Gemini LLM API request failed."
            ) from exc

        try:
            response_json = json.loads(response_body)
        except json.JSONDecodeError as exc:
            raise LLMQuestionGenerationInvalidResponseError(
                "Gemini returned invalid JSON."
            ) from exc

        return self._extract_gemini_response_text(response_json)

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

    def _extract_gemini_response_text(self, response_json: dict) -> str:
        candidates = response_json.get("candidates")
        if not isinstance(candidates, list) or not candidates:
            raise LLMQuestionGenerationInvalidResponseError(
                "Gemini response does not contain candidates."
            )

        content = candidates[0].get("content")
        if not isinstance(content, dict):
            raise LLMQuestionGenerationInvalidResponseError(
                "Gemini response does not contain content."
            )

        parts = content.get("parts")
        if not isinstance(parts, list):
            raise LLMQuestionGenerationInvalidResponseError(
                "Gemini response does not contain content parts."
            )

        for part in parts:
            if isinstance(part, dict):
                text = part.get("text")
                if isinstance(text, str) and text.strip():
                    return text.strip()

        raise LLMQuestionGenerationInvalidResponseError(
            "Gemini response does not contain generated text."
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
