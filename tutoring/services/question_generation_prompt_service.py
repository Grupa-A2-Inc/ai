class QuestionGenerationPromptService:
    def build_prompt(self, content: str, count: int) -> str:
        lesson_content = content.strip()

        return (
            "You are an educational question generation assistant.\n\n"
            f"Generate exactly {count} questions based only on the lesson content below.\n\n"
            "Return only valid JSON in this exact format:\n"
            "{\n"
            "  \"questions\": [\n"
            "    {\n"
            "      \"text\": \"...\",\n"
            "      \"type\": \"SINGLE_CHOICE\" or \"MULTIPLE_CHOICE\",\n"
            "      \"answers\": [\"...\", \"...\", \"...\", \"...\"],\n"
            "      \"correctAnswers\": [\"...\"],\n"
            "      \"difficulty\": 0.5\n"
            "    }\n"
            "  ]\n"
            "}\n\n"
            f"Rules:\n"
            f"- Generate exactly {count} questions.\n"
            "- Each question must have 4 answer options.\n"
            "- correctAnswers must contain only values from answers.\n"
            "- difficulty must be between 0.0 and 1.0.\n"
            "- Do not return markdown.\n"
            "- Do not return explanations.\n"
            "- Use only the lesson content.\n\n"
            "- Write the questions in the Romanian language.\n\n"
            "- VERY IMPORTANT : DO NOT HALLUCINATE !\n\n"
            f"Lesson content:\n{lesson_content}\n"
        )
