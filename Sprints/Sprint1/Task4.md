# Task 4 : Question Selection

„Transform mastery-ul elevului într-o dificultate țintă și selectez, dintre întrebările disponibile, itemul care se potrivește cel mai bine acelui nivel.”

Aici sunt patru idei importante.

+ Prima este că sistemul nu alege o întrebare random.
+ A doua este că sistemul nu alege neapărat cea mai ușoară sau cea mai grea întrebare. 
+ A treia este că selecția trebuie să fie deterministă și explicabilă.
+ A patra este că Task 4 trebuie să lucreze bine împreună cu Task 5, care elimină întrebările deja văzute.

Pasi de abordare : 

+ Mai întâi definești ce este dificultatea țintă;

+ Apoi stabilești ce proprietate a întrebării folosești în comparație;
+ După aceea implementezi engine-ul de selecție;
+ Apoi definești regula de fallback;
+ La final testezi că aceeași intrare produce o alegere coerentă.

## 1. Ce intra in Task 4

Task 4 consumă rezultatele anterioare din sprint:

din Task 2 primește lista de candidate questions;
din Task 3 primește mastery score-ul elevului;
din Task 5 va primi, direct sau indirect, lista de seen question IDs.

În forma minimă, selecția are nevoie de:

+ ```candidate_questions```;
+ ```mastery_score```;
+ eventual ```seen_question_ids```.

Dar, din punct de vedere arhitectural, e bine să separi:

```QuestionRecommendationEngine``` calculează target difficulty;
```QuestionSelectionEngine``` face selecția efectivă.

Asta se potrivește foarte bine cu structura ta de proiect, unde ai ambele componente separate.

## 2. Ce inseamna dificultatea tinta 

Dificultatea țintă este nivelul de dificultate pe care sistemul îl consideră optim pentru următoarea întrebare.

Nu trebuie să fie egală cu mastery-ul.
De multe ori e chiar mai bine să fie puțin peste mastery, pentru ca elevul să fie provocat și să progreseze

```python
target_difficulty = min(mastery_score + 0.1, 1.0) 
```

For now mergem cu asta

## 3. Ce propietate a intrebarii compari

In teorie avem 3 dificultati :

+ dificultatea initiala
+ dificultatea observata
+ dificultatea efectiva

În mod ideal, ```QuestionSelectionEngine``` ar trebui să compare target difficulty cu effective difficulty. Dar în Sprint 1 încă nu ai recalibrare completă și nici servicii mature pentru difficulty calibration.
De aceea, pentru prima iterație, cea mai sănătoasă decizie este:
folosești ```difficulty_initial``` ca proxy pentru dificultatea întrebării.

## 4. Cum trebuie sa arate responsabilitatea ```Question Selection Engine```

El trebuie doar să răspundă la întrebarea:

„Având o listă de întrebări eligibile și o dificultate țintă, care este întrebarea cea mai apropiată?”

## 5. Implementare de baza ```Question Selection Engine```

In ```services/question_selection_engine.py``` o prima versiune poate fi
```python
class QuestionSelectionEngine:
    def select(self, candidate_questions, target_difficulty: float, seen_question_ids=None):
        seen_question_ids = seen_question_ids or []

        eligible_questions = [
            question for question in candidate_questions
            if question.id not in seen_question_ids
        ]

        if not eligible_questions:
            return None

        selected_question = min(
            eligible_questions,
            key=lambda question: abs(question.difficulty_initial - target_difficulty)
        )

        return selected_question
```

## 6. De ce e scris asa

Aici sunt câteva decizii foarte importante.

a) ```seen_question_ids = seen_question_ids or []```

Asta face codul robust. Dacă nu primești listă de seen questions, nu crapi, ci mergi cu listă goală.

b) construiești ```eligible_questions```

Aici se aplică filtrarea minimă pentru Task 5.
Dacă o întrebare este deja văzută, nu o mai lași în competiție.

c) ```if not eligible_questions: return None```

Asta e foarte important.
Trebuie să ai fallback clar dacă nu există nimic eligibil.

Nu întorci excepție haotică.
Nu alegi la întâmplare.
Spui clar: „nu am putut selecta nimic”.

d) ```folosești min(..., key=...)```

Asta este inima selecției.

Comparația este:

```python
abs(question.difficulty_initial - target_difficulty)
```

## 7. Ce face ```QuestionRecommendationEngine``` in raport cu Task4

Aici trebuie separare clara

```QuestionRecommendationEngine```:
citește contextul elevului;
construiește features;
calculează mastery;
calculează target difficulty;
apelează ```QuestionSelectionEngine```.

```QuestionSelectionEngine```:
primește target difficulty și întrebările eligibile;
returnează întrebarea potrivită.

Asta ar putea arăta așa:

```python
from tutoring.repositories.student_data_repository import StudentDataRepository
from tutoring.services.feature_engineering_service import FeatureEngineeringService
from tutoring.services.mastery_estimator import MasteryEstimator
from tutoring.services.question_selection_engine import QuestionSelectionEngine
from tutoring.dto.question_recommendation_result import QuestionRecommendationResult


class QuestionRecommendationEngine:
    def __init__(self):
        self.repository = StudentDataRepository()
        self.feature_service = FeatureEngineeringService()
        self.mastery_estimator = MasteryEstimator()
        self.selection_engine = QuestionSelectionEngine()

    def recommend(self, user_id: int, subject_id: int, topic_id: int):
        student_context = self.repository.build_student_context(
            user_id=user_id,
            subject_id=subject_id,
            topic_id=topic_id,
        )

        features = self.feature_service.build_features(student_context)
        mastery_result = self.mastery_estimator.estimate(features)

        target_difficulty = min(mastery_result.mastery_score + 0.1, 1.0)

        selected_question = self.selection_engine.select(
            candidate_questions=student_context.candidate_questions,
            target_difficulty=target_difficulty,
            seen_question_ids=student_context.seen_question_ids,
        )

        if selected_question is None:
            return None

        return QuestionRecommendationResult(
            question_id=selected_question.id,
            difficulty=selected_question.difficulty_initial,
            source="selection",
        )
```

Task 3 produce ```mastery_result```.
Task 4 îl transformă în ```target_difficulty``` și apoi în ```selected_question```

## 8. DTO-ul pentru rezultat

In ```dto/question_recommendation_result.py``` o varianta initiala ar fi:

```python
 class QuestionRecommendationResult:
    def __init__(self, question_id: int, difficulty: float, source: str):
        self.question_id = question_id
        self.difficulty = difficulty
        self.source = source
```

Mai târziu poți adăuga și:
```target_difficulty```;
```mastery_score```;
```reason```;
dar pentru Sprint 1 nu e obligatoriu.

## 9. Ce faci daca 2 intrebari sunt la fel de apropiate?

Exemplu:
target difficulty = 0.5
ai întrebări de 0.4 și 0.6

For now alegem cea cu dificultatea mai mare

```python
selected_question = min(
    eligible_questions,
    key=lambda question: (
        abs(question.difficulty_initial - target_difficulty),
        -question.difficulty_initial
    )
) 
```

In caz de egalitate doar ia una.

## 10. Ce facem daca nu avem intrebari eligibile

În Sprint 1, dacă nu există întrebări eligibile după filtrare, QuestionSelectionEngine trebuie să întoarcă ```None```.

Apoi ```QuestionRecommendationEngine``` poate:
fie să întoarcă și el ```None```;
fie să pregătească viitorul fallback către ```QuestionGenerationEngine```.

Dar pentru Sprint 1, fiindcă generarea nu e implementată încă, cea mai curată variantă este:
selection_engine.select(...) -> ```None```
apoi engine-ul principal întoarce ```None```
iar endpoint-ul răspunde cu eroare controlată.

## 11. Ce faci cu ```difficulty_estimator.py```

În Sprint 1, nu e nevoie să-l transformi într-un serviciu complex separat. Poți aborda problema în două moduri.

Varianta simplă

Calculezi direct ```target_difficulty``` în ```QuestionRecommendationEngine```.

Este cea mai practică variantă pentru Sprint 1.

Varianta mai „clean architecture”

Faci un mic DifficultyEstimator:

```python 
from tutoring.dto.difficulty_result import DifficultyResult


class DifficultyEstimator:
    def estimate(self, mastery_score: float) -> DifficultyResult:
        target_difficulty = min(mastery_score + 0.1, 1.0)
        return DifficultyResult(target_difficulty=target_difficulty)
```

si DTO-ul 

```python
 class DifficultyResult:
    def __init__(self, target_difficulty: float):
        self.target_difficulty = target_difficulty
```

Nota : Pentru cel care ia taskul de preferat sa luati a 2-a varianta pentru a nu ne bate capul mai tarziu cu refactoring

## 12. Cum testezi Task 4

Caz 1 — selecție simplă

Candidate questions:
0.2, 0.5, 0.8
Target difficulty:
0.55

Trebuie să alegi 0.5.

Caz 2 — elev mai slab

Mastery:
0.3
Target:
0.4
Candidate:
0.2, 0.5, 0.8

Trebuie să alegi 0.5, pentru că este la 0.1 distanță, iar 0.2 e la 0.2.

Caz 3 — egalitate

Target:
0.5
Candidate:
0.4, 0.6

Dacă ai ales regula „preferă mai greu la egalitate”, trebuie să alegi 0.6.

Caz 4 — totul văzut

Toate întrebările eligibile sunt deja în ```seen_question_ids```.

Trebuie să întorci ```None```.

Exemple : 

```python
def test_selection_engine_returns_closest_question():
    question_easy = DummyQuestion(id=1, difficulty_initial=0.2)
    question_medium = DummyQuestion(id=2, difficulty_initial=0.5)
    question_hard = DummyQuestion(id=3, difficulty_initial=0.8)

    engine = QuestionSelectionEngine()

    selected = engine.select(
        candidate_questions=[question_easy, question_medium, question_hard],
        target_difficulty=0.55,
        seen_question_ids=[],
    )

    assert selected.id == 2
```

Pentru tie-break:

```python
def test_selection_engine_prefers_harder_question_on_tie():
    question_left = DummyQuestion(id=1, difficulty_initial=0.4)
    question_right = DummyQuestion(id=2, difficulty_initial=0.6)

    engine = QuestionSelectionEngine()

    selected = engine.select(
        candidate_questions=[question_left, question_right],
        target_difficulty=0.5,
        seen_question_ids=[],
    )

    assert selected.id == 2
```

Pentru no candidates: 

```python 
def test_selection_engine_returns_none_when_all_questions_seen():
    question_one = DummyQuestion(id=1, difficulty_initial=0.5)

    engine = QuestionSelectionEngine()

    selected = engine.select(
        candidate_questions=[question_one],
        target_difficulty=0.5,
        seen_question_ids=[1],
    )

    assert selected is None
```
