class FallbackQuestionPromptService:
    def build_prompt(
        self,
        subject_id: int,
        topic_id: int,
        target_difficulty: float,
    ) -> str:
        return f"""
You are an educational question generation assistant.

Generate exactly ONE question for an adaptive learning platform.

Context:
- subject_id: {subject_id}
- topic_id: {topic_id}
- target_difficulty: {target_difficulty}

Return ONLY valid JSON in this exact format:

{{
  "questions": [
    {{
      "text": "...",
      "type": "SINGLE_CHOICE" or "MULTIPLE_CHOICE",
      "answers": ["...", "...", "...", "..."],
      "correctAnswers": ["..."],
      "difficulty": 0.5
    }}
  ]
}}

Rules:
- Generate exactly one question.
- The question must match the subject and topic.
- The difficulty must be close to target_difficulty.
- Difficulty must be a float between 0.0 and 1.0.
- answers must contain exactly 4 options.
- correctAnswers must contain only values that also exist in answers.
- SINGLE_CHOICE must have exactly one correct answer.
- MULTIPLE_CHOICE may have one or more correct answers.
- Do not return markdown.
- Do not return explanations.
- Return JSON only.
"""