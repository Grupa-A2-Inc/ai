# S5-05 — LLM Fallback Question Generation for Adaptive Recommendation

Description

Acest task implementează mecanismul de fallback pentru cazul în care sistemul adaptiv nu găsește o întrebare potrivită pentru elev.

În flow-ul actual, backend-ul cere exerciții prin:

`POST /ai/api/v1/adaptive/exercises`

AI-ul încearcă să aleagă întrebări existente din baza de date folosind:

`QuestionRecommendationEngine`

Dar pot apărea situații în care engine-ul nu găsește o întrebare potrivită:

nu există întrebări pe acel topic
toate întrebările au fost deja văzute
nu există întrebare apropiată de dificultatea țintă
banca de întrebări este prea mică pentru acel topic

În această situație, AI-ul trebuie să apeleze un LLM ca fallback, să genereze o întrebare nouă în formatul nostru standard, să o salveze în baza de date și apoi să o returneze către backend.

# Goal

Scopul taskului este:

dacă rule-based / ML nu găsește întrebare potrivită,
atunci generăm una nouă cu LLM,
o salvăm în Question + QuestionOption + QuestionCorrectOption,
îi setăm ml_exercise_id,
și o trimitem backend-ului ca exercițiu adaptiv.

## Final Flow
```
Backend cere exerciții
        ↓
/ai/api/v1/adaptive/exercises
        ↓
AdaptiveExerciseService
        ↓
QuestionRecommendationEngine.recommend(...)
        ↓
dacă găsește întrebare
        ↓
returnează întrebare din DB
        ↓
dacă NU găsește întrebare
        ↓
apelează LLM fallback
        ↓
generează întrebare nouă
        ↓
salvează întrebarea în DB
        ↓
returnează întrebarea către backend
``` 

## Important Context

Se consideră că în Task 4 există deja un service care poate apela LLM-ul.

De exemplu:
```
LLMQuestionGenerationService
QuestionGenerationPromptService
```
Pentru acest task nu trebuie refăcut mecanismul de apelare LLM.

Trebuie doar adăugat un prompt nou, specific pentru fallback adaptiv.       

# API Impact

Nu se creează endpoint nou.

Fallback-ul se integrează în endpoint-ul deja existent:

`POST /ai/api/v1/adaptive/exercises`

Request-ul rămâne același:
```
{
  "studentId": "student-uuid-1",
  "subjectId": 2,
  "topicId": 1102,
  "count": 5
}
```
Response-ul rămâne același:
```
{
  "exercises": [
    {
      "exerciseId": "ai-101",
      "text": "Care este forma generală a ecuației de gradul al doilea?",
      "type": "SINGLE_CHOICE",
      "answers": ["ax² + bx + c = 0", "ax + b = 0", "a/x + b = 0", "x + y = 0"],
      "correctAnswers": ["ax² + bx + c = 0"],
      "difficulty": 0.5
    }
  ]
}
```
Diferența este internă: dacă nu există întrebare potrivită în DB, AI-ul creează una nouă cu LLM.

# Required Behavior

## Case 1 — Engine găsește întrebare

Flow normal:
```
QuestionRecommendationEngine găsește întrebare
↓
întrebarea se serializează
↓
se setează ml_exercise_id
↓
se returnează backend-ului
``` 

## Case 2 — Engine nu găsește întrebare

Fallback:
```
QuestionRecommendationEngine returnează None
↓
se construiește prompt LLM
↓
LLM generează întrebare
↓
întrebarea este validată
↓
întrebarea este salvată în DB
↓
se returnează backend-ului
```

## Case 3 — LLM eșuează

Dacă LLM-ul nu răspunde sau generează JSON invalid:
```
nu salvăm nimic în DB
returnăm mai puține exerciții decât count
sau returnăm eroare dacă nu avem niciun exercițiu
``` 

# Data Model

Se folosesc modelele existente:

```
Question
QuestionOption
QuestionCorrectOption
``` 

Nu este nevoie de un model nou.

Dar `Question` trebuie să aibă deja: (deci vedeti sa aveti BD-ul updated)

```
ml_exercise_id = models.CharField(
    max_length=100,
    unique=True,
    null=True,
    blank=True,
)
```

Această legătură este necesară pentru Sprint 3 - Task 4, când backend-ul trimite feedback folosind:
```
{
  "mlExerciseId": "ai-123"
}
``` 

Generated Question Format from LLM

LLM-ul trebuie să genereze o singură întrebare în formatul:
```
{
  "text": "Care este forma generală a ecuației de gradul al doilea?",
  "type": "SINGLE_CHOICE",
  "answers": ["ax² + bx + c = 0", "ax + b = 0", "a/x + b = 0", "x + y = 0"],
  "correctAnswers": ["ax² + bx + c = 0"],
  "difficulty": 0.5
}

```

Pentru fallback, generăm câte o întrebare pe rând, pentru că trebuie să o salvăm imediat în DB și să îi dăm `ml_exercise_id`.

# Prompt Requirement

Se refolosește LLM-ul din Task 4, dar cu prompt diferit.

Prompt-ul trebuie să includă:
```
subjectId
topicId
targetDifficulty
questionType permis
format JSON exact
reguli stricte
```
Nu avem neapărat conținut de lecție în fallback, deci prompt-ul trebuie să ceară o întrebare educațională pentru acel topic, pe baza contextului disponibil.

Dacă avem numele topicului sau lecției, îl includem. Dacă nu, folosim doar subjectId și topicId.

Prompt Example
```
You are an educational question generation assistant.

Generate exactly ONE question for an adaptive learning platform.

Context:
- subject_id: {subject_id}
- topic_id: {topic_id}
- target_difficulty: {target_difficulty}

Return ONLY valid JSON, with this exact structure:

{
  "text": "...",
  "type": "SINGLE_CHOICE" or "MULTIPLE_CHOICE",
  "answers": ["...", "...", "...", "..."],
  "correctAnswers": ["..."],
  "difficulty": 0.5
}

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
```

# New Files

Recomandat:
```
tutoring/services/llm_fallback_question_service.py
tutoring/services/fallback_question_persistence_service.py
```

## Step 1 — LLM Fallback Prompt Service

Fișier:

`tutoring/services/fallback_question_prompt_service.py`

Cod:
```
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

Return ONLY valid JSON, with this exact structure:

{{
  "text": "...",
  "type": "SINGLE_CHOICE" or "MULTIPLE_CHOICE",
  "answers": ["...", "...", "...", "..."],
  "correctAnswers": ["..."],
  "difficulty": 0.5
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
```

# Step 2 — LLM Fallback Question Service

Acest service folosește LLM-ul deja existent din Task 4.

Presupunem că aveți ceva de genul:

`LLMQuestionGenerationService.generate_from_prompt(prompt)`

Fișier:

`tutoring/services/llm_fallback_question_service.py`

Cod:
```
class LLMFallbackQuestionGenerationError(Exception):
    pass


class LLMFallbackQuestionService:
    def __init__(
        self,
        prompt_service,
        llm_service,
    ):
        self.prompt_service = prompt_service
        self.llm_service = llm_service

    def generate_question(
        self,
        subject_id: int,
        topic_id: int,
        target_difficulty: float,
    ) -> dict:
        prompt = self.prompt_service.build_prompt(
            subject_id=subject_id,
            topic_id=topic_id,
            target_difficulty=target_difficulty,
        )

        question_data = self.llm_service.generate_from_prompt(prompt)

        self._validate_question_data(question_data)

        return question_data

    def _validate_question_data(self, question_data: dict) -> None:
        required_fields = [
            "text",
            "type",
            "answers",
            "correctAnswers",
            "difficulty",
        ]

        for field in required_fields:
            if field not in question_data:
                raise LLMFallbackQuestionGenerationError(
                    f"Missing field from LLM response: {field}"
                )

        if question_data["type"] not in ["SINGLE_CHOICE", "MULTIPLE_CHOICE"]:
            raise LLMFallbackQuestionGenerationError(
                "Invalid question type from LLM."
            )

        answers = question_data["answers"]
        correct_answers = question_data["correctAnswers"]

        if not isinstance(answers, list) or len(answers) != 4:
            raise LLMFallbackQuestionGenerationError(
                "LLM question must contain exactly 4 answers."
            )

        if not isinstance(correct_answers, list) or len(correct_answers) < 1:
            raise LLMFallbackQuestionGenerationError(
                "LLM question must contain at least one correct answer."
            )

        for correct_answer in correct_answers:
            if correct_answer not in answers:
                raise LLMFallbackQuestionGenerationError(
                    "correctAnswers must contain only values from answers."
                )

        if question_data["type"] == "SINGLE_CHOICE" and len(correct_answers) != 1:
            raise LLMFallbackQuestionGenerationError(
                "SINGLE_CHOICE must have exactly one correct answer."
            )

        difficulty = float(question_data["difficulty"])

        if difficulty < 0.0 or difficulty > 1.0:
            raise LLMFallbackQuestionGenerationError(
                "Difficulty must be between 0.0 and 1.0."
            )
```

# Step 3 — Persist Generated Question in DB

Fișier:

`tutoring/services/fallback_question_persistence_service.py`

Cod:
```
from tutoring.models import (
    Question,
    QuestionOption,
    QuestionCorrectOption,
    QuestionType,
)


class FallbackQuestionPersistenceService:
    def save_generated_question(
        self,
        subject_id: int,
        topic_id: int,
        question_data: dict,
    ) -> Question:
        question_type = self._map_question_type(question_data["type"])

        question = Question.objects.create(
            subject_id=subject_id,
            topic_id=topic_id,
            question_type=question_type,
            content=question_data["text"],
            difficulty=float(question_data["difficulty"]),
            is_active=True,
        )

        options_by_text = {}

        for index, answer_text in enumerate(question_data["answers"], start=1):
            option = QuestionOption.objects.create(
                question=question,
                text=answer_text,
                display_order=index,
            )

            options_by_text[answer_text] = option

        for correct_answer_text in question_data["correctAnswers"]:
            QuestionCorrectOption.objects.create(
                question=question,
                option=options_by_text[correct_answer_text],
            )

        return question

    def _map_question_type(self, llm_type: str) -> str:
        if llm_type == "SINGLE_CHOICE":
            return QuestionType.SINGLE_CHOICE

        if llm_type == "MULTIPLE_CHOICE":
            return QuestionType.MULTIPLE_CHOICE

        raise ValueError(f"Unsupported question type: {llm_type}")
``` 

## Step 4 — Integrate Fallback in AdaptiveExerciseService

În `AdaptiveExerciseService`, când engine-ul returnează None, apelăm fallback-ul.

Exemplu:
```
class AdaptiveExerciseService:
    def generate_exercises(
        self,
        student_id: str,
        subject_id: int,
        topic_id: int,
        count: int = 5,
    ) -> list[dict]:
        self._validate_student_exists(student_id)

        generated_question_ids = set()
        exercises = []

        max_attempts = count * 3
        attempts = 0

        while len(exercises) < count and attempts < max_attempts:
            attempts += 1

            recommendation = self.engine.recommend(
                user_id=student_id,
                subject_id=subject_id,
                topic_id=topic_id,
            )

            if recommendation is None:
                fallback_question = self._generate_fallback_question(
                    subject_id=subject_id,
                    topic_id=topic_id,
                    target_difficulty=0.5,
                )

                exercise = self._prepare_question_for_response(
                    question=fallback_question,
                )

                exercises.append(exercise)
                continue

            if recommendation.question_id in generated_question_ids:
                fallback_question = self._generate_fallback_question(
                    subject_id=subject_id,
                    topic_id=topic_id,
                    target_difficulty=recommendation.difficulty,
                )

                exercise = self._prepare_question_for_response(
                    question=fallback_question,
                )

                exercises.append(exercise)
                continue

            generated_question_ids.add(recommendation.question_id)

            question = Question.objects.get(id=recommendation.question_id)

            exercise = self._prepare_question_for_response(question)

            exercises.append(exercise)

        return exercises
```

## Step 5 — Helper for Preparing Question Response
```
import uuid

def _prepare_question_for_response(self, question: Question) -> dict:
    exercise_id = f"ai-{question.id}-{uuid.uuid4().hex[:8]}"

    question.ml_exercise_id = exercise_id
    question.save(update_fields=["ml_exercise_id"])

    return self.serializer.serialize(
        question=question,
        exercise_id=exercise_id,
    )
```
Important: folosim UUID în exercise_id, nu doar ai-{question.id}, ca să evităm probleme dacă aceeași întrebare este trimisă de mai multe ori în timp.

## Step 6 — Full AdaptiveExerciseService with Fallback
```
import uuid

from tutoring.models import Question, StudentProfile
from tutoring.services.recommendation_engine import QuestionRecommendationEngine
from tutoring.services.question_serialization_service import QuestionSerializationService
from tutoring.services.fallback_question_prompt_service import FallbackQuestionPromptService
from tutoring.services.llm_fallback_question_service import (
    LLMFallbackQuestionService,
    LLMFallbackQuestionGenerationError,
)
from tutoring.services.fallback_question_persistence_service import (
    FallbackQuestionPersistenceService,
)
from tutoring.services.llm_question_generation_service import LLMQuestionGenerationService


class StudentNotFoundError(Exception):
    pass


class AdaptiveExerciseServiceUnavailableError(Exception):
    pass


class AdaptiveExerciseService:
    DEFAULT_FALLBACK_DIFFICULTY = 0.5

    def __init__(self):
        self.engine = QuestionRecommendationEngine()
        self.serializer = QuestionSerializationService()

        self.fallback_prompt_service = FallbackQuestionPromptService()
        self.llm_service = LLMQuestionGenerationService()
        self.fallback_generator = LLMFallbackQuestionService(
            prompt_service=self.fallback_prompt_service,
            llm_service=self.llm_service,
        )
        self.fallback_persistence = FallbackQuestionPersistenceService()

    def generate_exercises(
        self,
        student_id: str,
        subject_id: int,
        topic_id: int,
        count: int = 5,
    ) -> list[dict]:
        self._validate_student_exists(student_id)

        generated_question_ids = set()
        exercises = []

        max_attempts = count * 3
        attempts = 0

        while len(exercises) < count and attempts < max_attempts:
            attempts += 1

            recommendation = self.engine.recommend(
                user_id=student_id,
                subject_id=subject_id,
                topic_id=topic_id,
            )

            if recommendation is None:
                fallback_question = self._create_fallback_question(
                    subject_id=subject_id,
                    topic_id=topic_id,
                    target_difficulty=self.DEFAULT_FALLBACK_DIFFICULTY,
                )

                exercises.append(
                    self._prepare_question_for_response(fallback_question)
                )
                continue

            if recommendation.question_id in generated_question_ids:
                fallback_question = self._create_fallback_question(
                    subject_id=subject_id,
                    topic_id=topic_id,
                    target_difficulty=recommendation.difficulty,
                )

                exercises.append(
                    self._prepare_question_for_response(fallback_question)
                )
                continue

            generated_question_ids.add(recommendation.question_id)

            question = Question.objects.get(
                id=recommendation.question_id,
                is_active=True,
            )

            exercises.append(
                self._prepare_question_for_response(question)
            )

        if not exercises:
            raise AdaptiveExerciseServiceUnavailableError()

        return exercises

    def _validate_student_exists(self, student_id: str) -> None:
        exists = StudentProfile.objects.filter(
            student_id=student_id,
            is_active=True,
        ).exists()

        if not exists:
            raise StudentNotFoundError()

    def _create_fallback_question(
        self,
        subject_id: int,
        topic_id: int,
        target_difficulty: float,
    ) -> Question:
        try:
            question_data = self.fallback_generator.generate_question(
                subject_id=subject_id,
                topic_id=topic_id,
                target_difficulty=target_difficulty,
            )

            return self.fallback_persistence.save_generated_question(
                subject_id=subject_id,
                topic_id=topic_id,
                question_data=question_data,
            )

        except Exception as exc:
            raise AdaptiveExerciseServiceUnavailableError() from exc

    def _prepare_question_for_response(self, question: Question) -> dict:
        exercise_id = f"ai-{question.id}-{uuid.uuid4().hex[:8]}"

        question.ml_exercise_id = exercise_id
        question.save(update_fields=["ml_exercise_id"])

        return self.serializer.serialize(
            question=question,
            exercise_id=exercise_id,
        )
```

# Important Design Decision
Why save fallback questions in DB?

Pentru că întrebarea generată trebuie să poată intra în același flow ca întrebările normale.

După ce este salvată în DB:
```
Question
QuestionOption
QuestionCorrectOption
```
ea poate fi folosită de:

```
QuestionRecommendationEngine
StudentInteraction
StudentDataRepository
ML dataset
future recommendations
```
Asta înseamnă că întrebările generate de LLM nu sunt temporare.

Ele devin parte din banca de întrebări.

# Feedback Compatibility

Când backend-ul primește fallback question:
```
{
  "exerciseId": "ai-250-a83f91bd",
  "text": "...",
  "type": "SINGLE_CHOICE",
  "answers": ["A", "B", "C", "D"],
  "correctAnswers": ["A"],
  "difficulty": 0.5
}
```
Mai târziu, backend-ul trimite feedback:
```
{
  "studentId": "student-uuid-1",
  "subjectId": 2,
  "topicId": 1102,
  "results": [
    {
      "mlExerciseId": "ai-250-a83f91bd",
      "score": 1,
      "timeSpent": 44
    }
  ]
}
```
Task 4 găsește întrebarea prin:

`Question.objects.get(ml_exercise_id="ai-250-a83f91bd")`

și creează:

`StudentInteraction`

Deci întrebarea generată de fallback devine vizibilă pentru ML.

# What This Task Must NOT Do

Taskul NU trebuie să:
```
creeze endpoint nou
rescrie LLM service-ul din Task 4
modifice feedback endpoint
antreneze model ML
modifice StudentInteraction
înlocuiască QuestionRecommendationEngine
```
Acest task doar adaugă fallback-ul în flow-ul adaptiv existent.

# Tests Required

Trebuie adăugate teste pentru:
``` 
engine găsește întrebare → nu se apelează LLM
engine returnează None → se apelează LLM fallback
LLM generează întrebare validă → se salvează în DB
fallback question are QuestionOption și QuestionCorrectOption
fallback question primește ml_exercise_id
response-ul conține întrebarea generată
LLM eșuează → eroare controlată
``` 
Test Example — Conceptual
```py 
def test_fallback_creates_question_when_engine_returns_none(self):
    service = AdaptiveExerciseService()

    service.engine.recommend = lambda *args, **kwargs: None

    service.fallback_generator.generate_question = lambda *args, **kwargs: {
        "text": "Generated fallback question",
        "type": "SINGLE_CHOICE",
        "answers": ["A", "B", "C", "D"],
        "correctAnswers": ["A"],
        "difficulty": 0.5,
    }

    exercises = service.generate_exercises(
        student_id="student-uuid-1",
        subject_id=2,
        topic_id=1102,
        count=1,
    )

    self.assertEqual(len(exercises), 1)
    self.assertEqual(Question.objects.count(), 1)
    self.assertEqual(QuestionOption.objects.count(), 4)
    self.assertEqual(QuestionCorrectOption.objects.count(), 1)
```

# Definition of Done

Taskul este gata când:
```
AdaptiveExerciseService poate folosi fallback LLM
fallback-ul se declanșează când engine-ul returnează None
fallback-ul generează întrebare în formatul standard
întrebarea este validată
întrebarea este salvată în Question
opțiunile sunt salvate în QuestionOption
răspunsurile corecte sunt salvate în QuestionCorrectOption
întrebarea primește ml_exercise_id
întrebarea este returnată backend-ului
feedback-ul ulterior poate crea StudentInteraction pentru ea
întrebarea devine vizibilă pentru ML dataset
există teste pentru succes și eșec
```

# Summary

Acest task completează sistemul adaptiv.

Până acum:

rule-based / ML alegea doar din întrebările existente

După acest task:

dacă nu există întrebare potrivită,
LLM creează una nouă,
AI o salvează în DB,
iar sistemul o poate folosi în viitor.

Asta face sistemul mai robust, pentru că nu se blochează atunci când banca de întrebări este insuficientă.
