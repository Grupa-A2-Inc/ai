# QuestionRecommendationEngine.md — Flow complet Sprint 2

# End-to-End Recommendation Flow

Acesta este flow-ul final al Sprintului 2:

```text
student_history
   ↓
build_features
   ↓
normalize
   ↓
estimate_mastery
   ↓
estimate_target_difficulty
   ↓
select_question
   ↓
return recommendation
```

## Rolul engine-ului

`QuestionRecommendationEngine` este orchestratorul.  
El:
- cere datele
- apelează serviciile în ordinea corectă
- construiește recomandarea finală

El nu trebuie să conțină logică grea de calcul, ci doar să coordoneze.

## DTO final de răspuns

În `dto/question_recommendation_result.py`:

```python
class QuestionRecommendationResult:
    def __init__(self, question_id: int, subject_id: int, topic_id: int, difficulty: float, source: str):
        self.question_id = question_id
        self.subject_id = subject_id
        self.topic_id = topic_id
        self.difficulty = difficulty
        self.source = source
```

## Implementarea completă

În `services/question_recommendation_engine.py`:

```python
from tutoring.repositories.student_data_repository import StudentDataRepository
from tutoring.services.feature_engineering_service import FeatureEngineeringService
from tutoring.services.mastery_estimator import MasteryEstimator
from tutoring.services.difficulty_estimator import DifficultyEstimator
from tutoring.services.question_selection_engine import QuestionSelectionEngine
from tutoring.dto.question_recommendation_result import QuestionRecommendationResult


class QuestionRecommendationEngine:
    def __init__(self):
        self.repository = StudentDataRepository()
        self.feature_service = FeatureEngineeringService()
        self.mastery_estimator = MasteryEstimator()
        self.difficulty_estimator = DifficultyEstimator()
        self.selection_engine = QuestionSelectionEngine()

    def recommend(self, user_id: int, subject_id: int, topic_id: int):
        student_context = self.repository.build_student_context(
            user_id=user_id,
            subject_id=subject_id,
            topic_id=topic_id,
        )

        raw_features = self.feature_service.build_features(student_context)

        normalized_features = self.feature_service.normalize(raw_features)

        mastery_result = self.mastery_estimator.estimate(normalized_features)

        difficulty_result = self.difficulty_estimator.estimate(
            mastery_result.mastery_score
        )

        selected_question = self.selection_engine.select(
            candidate_questions=student_context.candidate_questions,
            target_difficulty=difficulty_result.target_difficulty,
            seen_question_ids=student_context.seen_question_ids,
        )

        if selected_question is None:
            return None

        return QuestionRecommendationResult(
            question_id=selected_question.id,
            subject_id=selected_question.subject_id,
            topic_id=selected_question.topic_id,
            difficulty=selected_question.difficulty,
            source="selection",
        )
```

## Explicație pe pași

### 1. `build_student_context(...)`
Ia din repository:
- history
- seen questions
- candidate questions

### 2. `build_features(...)`
Calculează:
- accuracy
- avg_time
- attempt_count

### 3. `normalize(...)`
Transformă timpul într-un scor comparabil

### 4. `estimate(...)` din mastery
Construiește mastery score-ul

### 5. `estimate(...)` din difficulty
Transformă mastery în target difficulty

### 6. `select(...)`
Alege întrebarea optimă

### 7. `QuestionRecommendationResult`
Construiește obiectul final care va ajunge în API response

## Ce obții la finalul Sprintului 2

Un pipeline complet și coerent:

```text
history → features → normalized_features → mastery → target_difficulty → selected_question
```

Asta înseamnă că Sprintul 2 nu doar îmbunătățește AI-ul, ci îi dă un flow clar și matur.
