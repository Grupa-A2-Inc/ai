from pathlib import Path
from types import SimpleNamespace

from tutoring.services.mastery_strategy_selector import MasteryStrategySelector
from tutoring.services.question_generation_prompt_service import (
    QuestionGenerationPromptService,
)


def test_strategy_selector_reads_attempt_count_from_dict():
    selector = MasteryStrategySelector()

    assert selector.select({"attempt_count_on_topic": 1}) == "rule_based"


def test_strategy_selector_returns_ml_when_model_exists(tmp_path):
    model_path = tmp_path / "model.pkl"
    model_path.write_bytes(b"model")
    selector = MasteryStrategySelector()
    selector.model_path = Path(model_path)

    result = selector.select(SimpleNamespace(attempt_count=10))

    assert result == "ml"


def test_question_generation_prompt_contains_trimmed_content_and_count():
    prompt = QuestionGenerationPromptService().build_prompt(
        content="  lesson content  ",
        count=3,
    )

    assert "Generate exactly 3 questions" in prompt
    assert "Lesson content:\nlesson content" in prompt
