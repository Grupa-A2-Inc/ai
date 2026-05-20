import json

from tutoring.services.curriculum_catalog_service import SUBJECTS, TOPICS


GENERAL_DIFFICULTY_CALIBRATION = (
    "- 0.0-0.3: basic recognition, direct recall, definitions, simple identification\n"
    "- 0.4-0.6: standard application or understanding of one concept in a familiar context\n"
    "- 0.7-0.8: multi-step reasoning, comparison, interpretation, or applying concepts in a less direct context\n"
    "- 0.9-1.0: complex transfer, synthesis, edge cases, evaluation, or combining multiple concepts"
)


SUBJECT_DIFFICULTY_CALIBRATIONS = {
    1: (
        "- 0.0-0.3: recognize vocabulary, grammar, punctuation rules, or basic text features\n"
        "- 0.4-0.6: apply a grammar/text rule or identify meaning in a familiar fragment\n"
        "- 0.7-0.8: interpret meaning, compare formulations, infer tone, or analyze text structure\n"
        "- 0.9-1.0: nuanced literary interpretation, argumentation, synthesis, or advanced composition decisions"
    ),
    2: (
        "- 0.0-0.3: direct formula/concept recognition or one simple operation\n"
        "- 0.4-0.6: standard application with one or two expected steps\n"
        "- 0.7-0.8: multi-step problem, distractors close to common mistakes\n"
        "- 0.9-1.0: non-routine problem, transfer, edge case, or combining multiple concepts"
    ),
    3: (
        "- 0.0-0.3: identify a biological term, structure, function, or definition\n"
        "- 0.4-0.6: classify examples or explain one relation/process in a familiar context\n"
        "- 0.7-0.8: compare processes, infer cause-effect, or interpret a short biological scenario\n"
        "- 0.9-1.0: synthesize multiple systems, evaluate consequences, or reason across contexts"
    ),
    4: (
        "- 0.0-0.3: identify a geographic term, location, factor, or direct definition\n"
        "- 0.4-0.6: classify examples or explain a known geographic relation\n"
        "- 0.7-0.8: compare regions/processes, infer cause-effect, or interpret a scenario/map-like context\n"
        "- 0.9-1.0: synthesize multiple factors, evaluate consequences, or reason across scales"
    ),
    5: (
        "- 0.0-0.3: recognize a physical quantity, unit, law, formula, or direct concept\n"
        "- 0.4-0.6: standard application with one formula or one/two calculation steps\n"
        "- 0.7-0.8: multi-step problem, unit conversions, or distractors based on common misconceptions\n"
        "- 0.9-1.0: integrated reasoning, non-routine transfer, edge cases, or multiple laws combined"
    ),
    6: (
        "- 0.0-0.3: recognize a chemical term, symbol, class, definition, or simple fact\n"
        "- 0.4-0.6: apply a standard rule, classify a substance/reaction, or solve a direct calculation\n"
        "- 0.7-0.8: combine concepts, interpret a reaction/scenario, or use close distractors\n"
        "- 0.9-1.0: synthesize multiple concepts, evaluate transformations, or solve non-routine cases"
    ),
    7: (
        "- 0.0-0.3: identify a term, event, date range, person, institution, or definition\n"
        "- 0.4-0.6: explain a relation, classify examples, or apply a known historical concept\n"
        "- 0.7-0.8: compare events, infer cause-effect, or interpret a short historical scenario\n"
        "- 0.9-1.0: synthesize multiple events, evaluate consequences, or reason across periods"
    ),
    8: (
        "- 0.0-0.3: identify basic concepts, tools, file types, or interface elements\n"
        "- 0.4-0.6: choose or apply a standard operation in a familiar scenario\n"
        "- 0.7-0.8: troubleshoot, compare options, or apply digital safety rules to a scenario\n"
        "- 0.9-1.0: solve an integrated workflow, optimize a process, or reason about tradeoffs/security"
    ),
    9: (
        "- 0.0-0.3: recognize syntax, basic concepts, simple input/output, or one control structure\n"
        "- 0.4-0.6: trace or write a standard algorithm using one core concept\n"
        "- 0.7-0.8: combine structures, reason about edge cases, or compare algorithmic choices\n"
        "- 0.9-1.0: design or analyze non-trivial algorithms, optimize, or reason about complexity"
    ),
    10: (
        "- 0.0-0.3: recognize terms, definitions, simple distinctions, or basic operators\n"
        "- 0.4-0.6: apply a concept to a familiar example or classify an argument\n"
        "- 0.7-0.8: analyze reasoning, compare structures, detect assumptions or fallacies\n"
        "- 0.9-1.0: evaluate arguments, synthesize concepts, or handle ambiguous edge cases"
    ),
    11: (
        "- 0.0-0.3: recognize terms, definitions, simple distinctions, or known positions\n"
        "- 0.4-0.6: apply a concept to a familiar example or classify a philosophical position\n"
        "- 0.7-0.8: analyze reasoning, compare positions, detect assumptions or implications\n"
        "- 0.9-1.0: evaluate arguments, synthesize theories, or handle ambiguous scenarios"
    ),
    12: (
        "- 0.0-0.3: recognize vocabulary, grammar forms, basic meanings, or simple usage\n"
        "- 0.4-0.6: apply grammar/vocabulary in a standard sentence or identify text meaning\n"
        "- 0.7-0.8: infer tone/meaning, choose context-sensitive usage, or interpret a short text\n"
        "- 0.9-1.0: advanced grammar, nuanced interpretation, argument, style, or composition decisions"
    ),
}


class FallbackQuestionPromptService:
    def build_prompt(
        self,
        subject_id: int,
        topic_id: int,
        target_difficulty: float,
        mastery_score: float,
        student_features: dict | None = None,
        example_questions=None,
        avoid_question_texts=None,
        count: int = 1,
    ) -> str:
        subject = self._resolve_subject(subject_id)
        topic = self._resolve_topic(topic_id)
        student_features = student_features or {}
        example_questions = list(example_questions or [])
        avoid_question_texts = list(avoid_question_texts or [])
        min_difficulty, max_difficulty = self._difficulty_range(target_difficulty)

        context = {
            "subjectId": subject_id,
            "subjectName": subject.get("subjectName"),
            "topicId": topic_id,
            "topicName": topic.get("topicName"),
            "grade": topic.get("grade"),
            "masteryScore": round(float(mastery_score), 3),
            "targetDifficulty": round(float(target_difficulty), 3),
            "allowedDifficultyRange": {
                "min": min_difficulty,
                "max": max_difficulty,
            },
            "studentFeatures": student_features,
            "exampleQuestions": example_questions,
            "avoidQuestionTexts": avoid_question_texts,
        }

        subject_calibration = SUBJECT_DIFFICULTY_CALIBRATIONS.get(
            subject_id,
            GENERAL_DIFFICULTY_CALIBRATION,
        )

        return (
            "You are an educational question generation assistant.\n\n"
            f"Generate exactly {count} question(s) for an adaptive learning platform.\n"
            "Write the question and answers in Romanian, except when the subject is English.\n\n"
            "Context:\n"
            f"{json.dumps(context, ensure_ascii=False, indent=2)}\n\n"
            "General difficulty calibration:\n"
            f"{GENERAL_DIFFICULTY_CALIBRATION}\n\n"
            f"Subject-specific difficulty calibration for subjectId {subject_id}:\n"
            f"{subject_calibration}\n\n"
            "Return ONLY valid JSON, with this exact structure:\n"
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
            "Rules:\n"
            f"- Generate exactly {count} question(s).\n"
            "- Each generated question must be distinct and must test a different angle of the topic.\n"
            "- Do not generate duplicate or semantically equivalent questions in the same response.\n"
            "- The question must match the subject, grade, and topic.\n"
            "- The question difficulty must be close to targetDifficulty and inside allowedDifficultyRange.\n"
            "- Use the difficulty calibration to decide the cognitive demand of the question.\n"
            "- answers must contain exactly 4 options.\n"
            "- correctAnswers must contain only values that also exist in answers.\n"
            "- correctAnswers must copy the exact answer option text, character-for-character.\n"
            "- SINGLE_CHOICE must have exactly one correct answer.\n"
            "- If there is only one correct answer, use SINGLE_CHOICE.\n"
            "- MULTIPLE_CHOICE must have at least two correct answers.\n"
            "- If you cannot identify at least two correct answers, do not use MULTIPLE_CHOICE.\n"
            "- Before returning, solve the question yourself and verify that correctAnswers is truly correct.\n"
            "- Avoid duplicating avoidQuestionTexts and exampleQuestions.\n"
            "- Do not return markdown.\n"
            "- Do not return explanations.\n"
            "- Return JSON only.\n"
        )

    def _resolve_subject(self, subject_id: int) -> dict:
        return next(
            (
                subject
                for subject in SUBJECTS
                if subject["subjectId"] == subject_id
            ),
            {"subjectId": subject_id, "subjectName": f"Subject {subject_id}"},
        )

    def _resolve_topic(self, topic_id: int) -> dict:
        return next(
            (
                topic
                for topic in TOPICS
                if topic["topicId"] == topic_id
            ),
            {
                "topicId": topic_id,
                "topicName": f"Topic {topic_id}",
                "grade": None,
            },
        )

    def _difficulty_range(self, target_difficulty: float) -> tuple[float, float]:
        target = max(0.0, min(float(target_difficulty), 1.0))
        return (
            round(max(0.0, target - 0.15), 3),
            round(min(1.0, target + 0.15), 3),
        )
