import json
from types import SimpleNamespace
from unittest.mock import patch
from urllib.error import URLError

import pytest
from django.test import override_settings

from tutoring.services.llm_question_generation_service import (
    LLMQuestionGenerationInvalidResponseError,
    LLMQuestionGenerationService,
    LLMQuestionGenerationUnavailableError,
)


VALID_PAYLOAD = {
    "questions": [
        {
            "text": "Question?",
            "type": "SINGLE_CHOICE",
            "answers": ["A", "B", "C", "D"],
            "correctAnswers": ["A"],
            "difficulty": 0.5,
        }
    ]
}


class DummyPromptService:
    def build_prompt(self, content, count):
        return f"{content}:{count}"


class ResponseContext:
    def __init__(self, body):
        self.body = body

    def __enter__(self):
        return SimpleNamespace(read=lambda: self.body.encode("utf-8"))

    def __exit__(self, exc_type, exc, traceback):
        return False


def test_generate_uses_prompt_service_and_transport():
    service = LLMQuestionGenerationService(
        prompt_service=DummyPromptService(),
        transport=lambda prompt: json.dumps(VALID_PAYLOAD),
    )

    questions = service.generate(content="lesson", count=1)

    assert questions == VALID_PAYLOAD["questions"]


def test_generate_repairs_invalid_first_response():
    prompts = []
    responses = iter(
        [
            json.dumps(
                {
                    "questions": [
                        {
                            **VALID_PAYLOAD["questions"][0],
                            "correctAnswers": ["Z"],
                        }
                    ]
                }
            ),
            json.dumps(VALID_PAYLOAD),
        ]
    )

    def transport(prompt):
        prompts.append(prompt)
        return next(responses)

    service = LLMQuestionGenerationService(transport=transport)

    questions = service.generate_from_prompt("prompt", expected_count=1)

    assert questions == VALID_PAYLOAD["questions"]
    assert len(prompts) == 2
    assert "Repair it into valid JSON" in prompts[1]
    assert "\"questions\" must contain exactly 1 items" in prompts[1]


def test_generate_rejects_invalid_schema():
    service = LLMQuestionGenerationService(
        transport=lambda prompt: json.dumps(
            {"questions": [{**VALID_PAYLOAD["questions"][0], "correctAnswers": ["Z"]}]}
        )
    )

    with pytest.raises(LLMQuestionGenerationInvalidResponseError):
        service.generate_from_prompt("prompt")


def test_generate_rejects_unexpected_count():
    service = LLMQuestionGenerationService(
        transport=lambda prompt: json.dumps(VALID_PAYLOAD)
    )

    with pytest.raises(LLMQuestionGenerationInvalidResponseError):
        service.generate_from_prompt("prompt", expected_count=2)


def test_extract_response_text_accepts_dict_text_and_rejects_unsupported_shape():
    service = LLMQuestionGenerationService(transport=lambda prompt: "")

    assert service._extract_response_text({"text": "  body  "}) == "body"

    with pytest.raises(LLMQuestionGenerationInvalidResponseError):
        service._extract_response_text(["bad"])


def test_parse_json_payload_accepts_markdown_and_embedded_json():
    service = LLMQuestionGenerationService(transport=lambda prompt: "")

    assert service._parse_json_payload("```json\n{\"questions\": []}\n```") == {
        "questions": []
    }
    assert service._parse_json_payload("```\njson\n{\"questions\": []}\n```") == {
        "questions": []
    }
    assert service._parse_json_payload("prefix {\"questions\": []} suffix") == {
        "questions": []
    }


@pytest.mark.parametrize("response", ["not json", "[1, 2, 3]"])
def test_parse_json_payload_rejects_invalid_or_non_object_json(response):
    service = LLMQuestionGenerationService(transport=lambda prompt: "")

    with pytest.raises(LLMQuestionGenerationInvalidResponseError):
        service._parse_json_payload(response)


@pytest.mark.parametrize(
    ("response_json", "expected"),
    [
        ({"response": " generated "}, "generated"),
        ({"message": " message "}, "message"),
        ({"text": " text "}, "text"),
    ],
)
def test_extract_local_response_text_supported_fields(response_json, expected):
    service = LLMQuestionGenerationService(transport=lambda prompt: "")

    assert service._extract_local_response_text(response_json) == expected


def test_extract_local_response_text_rejects_missing_text():
    service = LLMQuestionGenerationService(transport=lambda prompt: "")

    with pytest.raises(LLMQuestionGenerationInvalidResponseError):
        service._extract_local_response_text({})


@patch("tutoring.services.llm_question_generation_service.urlopen")
@override_settings(LLM_URL="http://ollama:11434/api/generate")
def test_call_local_llm_posts_prompt_and_extracts_response(urlopen):
    urlopen.return_value = ResponseContext(json.dumps({"response": " generated "}))
    service = LLMQuestionGenerationService(transport=lambda prompt: "")

    assert service._call_local_llm("prompt") == "generated"
    request = urlopen.call_args.args[0]
    assert request.method == "POST"
    assert request.full_url == "http://ollama:11434/api/generate"
    request_payload = json.loads(request.data.decode("utf-8"))
    assert request_payload["prompt"] == "prompt"
    assert request_payload["options"]["temperature"] == 0.1


@patch("tutoring.services.llm_question_generation_service.urlopen")
def test_call_local_llm_rejects_unavailable_service(urlopen):
    urlopen.side_effect = URLError("down")
    service = LLMQuestionGenerationService(transport=lambda prompt: "")

    with pytest.raises(LLMQuestionGenerationUnavailableError):
        service._call_local_llm("prompt")


@patch("tutoring.services.llm_question_generation_service.urlopen")
def test_call_local_llm_rejects_invalid_json(urlopen):
    urlopen.return_value = ResponseContext("not json")
    service = LLMQuestionGenerationService(transport=lambda prompt: "")

    with pytest.raises(LLMQuestionGenerationInvalidResponseError):
        service._call_local_llm("prompt")
