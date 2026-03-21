# Task 5 : Seen Questions Filtering

„Asigur că sistemul nu repetă inutil întrebări pe care elevul le-a mai văzut, păstrând în același timp relevanța recomandării.”

Aici sunt câteva idei foarte importante.

+ Prima este că filtrarea întrebărilor văzute nu este doar o optimizare tehnică, ci o regulă de calitate a experienței de învățare.
+ A doua este că această filtrare trebuie făcută într-un loc clar din arhitectură.
+ A treia este că trebuie să existe o regulă explicită pentru cazul în care toate întrebările au fost deja văzute.
+ A patra este că Task 5 trebuie să rămână simplu în Sprint 1: nu faceți încă politici sofisticate de spaced repetition, ci doar evitați repetiția inutilă.

Cum abordam taskul 

+ Mai întâi definești ce înseamnă „seen question”;
+ Apoi stabilești de unde vine această informație;
+ După aceea alegi unde se aplică filtrarea;
+ Apoi definești fallback-ul;
+ La final testezi că sistemul nu repetă întrebări când are alternative valide.

## 1. Ce inseamna "seen question" in Sprint 1

O întrebare este considerată „seen” dacă există cel puțin o interacțiune între elev și acea întrebare pe topicul și materia curente.

Adică:
dacă elevul a răspuns măcar o dată la întrebarea 15, atunci întrebarea 15 intră în seen_question_ids.

## 2. De unde vine informatia despre intrebarile vazute

Task 5 depinde de Task 2 

Informația vine din StudentDataRepository, care trebuie să poată întoarce lista de întrebări deja văzute de elev. În explicația pentru Task 2, asta era metoda get_seen_question_ids(...)

O implementare buna era :

```python
def get_seen_question_ids(self, user_id: int, subject_id: int, topic_id: int):
    return list(
        StudentInteraction.objects.filter(
            user_id=user_id,
            question__subject_id=subject_id,
            question__topic_id=topic_id,
        ).values_list("question_id", flat=True).distinct()
    ) 
```
Nota : vorbesti cu cel de la Task 2 inainte daca lasati asa implementarea ca sa nu stai dupa el.

## 3. Unde trebuie facuta filtrarea 

Filtrarea trebuie facuta in ```Question Selection Engine```, nu in repository si nici in endpoint

```QuestionSelectionEngine``` trebuie să decidă:
„dintre întrebările candidate, pe care le mai las în joc?”

Asta este locul corect.

Asta e chestie din Task 4, again trebuie coordonare.

## 4. Cum trebuie definit flow-ul

repository-ul construiește ```student_context```;
```student_context``` conține ```candidate_questions``` și ```seen_question_ids```;
```QuestionSelectionEngine``` primește ambele;
engine-ul filtrează candidate questions;
apoi, din cele rămase, alege cea mai apropiată de target difficulty.

Deci filtrarea întrebărilor văzute nu vine după selecție, ci înainte de selecția finală.

Asta este foarte important.
Nu alegi mai întâi „cea mai bună” întrebare și apoi vezi dacă e văzută.
Mai întâi excluzi ce nu e eligibil, apoi alegi din ce a rămas.

## 5. Implementarea corecta in Question Selection Engine

In ```services/question_selection_engine.py``` implementarea pentru Sprint 1 buna ar fi

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
            key=lambda question: (
                abs(question.difficulty_initial - target_difficulty),
                -question.difficulty_initial
            )
        )

        return selected_question
```

Coordonare buna cu cel de la Task 4 !!!

## 6. De ce e scris asa ?

E si 6 de la taskul 4, nu am sa stau sa scriu din nou :))

## 7. Ce fallback trebuie sa existe 

Trebuie să decizi explicit ce faci dacă toate întrebările candidate sunt deja în seen_question_ids.

În Sprint 1, ai două variante rezonabile.

Varianta A — returnezi ```None```

Este cea mai curată și mai simplă.

Avantaje:
ușor de implementat;
ușor de explicat;
pregătește integrarea ulterioară cu ```QuestionGenerationEngine```.

Aceasta este varianta pe care eu o recomand pentru Sprint 1.

Varianta B — relaxezi regula și alegi totuși o întrebare văzută

Asta poate avea sens mai târziu, dar în Sprint 1 complică inutil logica.

Pentru prima iterație, mai bine păstrezi regula clară:
dacă totul este văzut, selecția eșuează controlat.

Apoi, în Sprint 3, poți spune:
dacă nu există întrebare eligibilă, generează una nouă.

Asta se potrivește foarte bine cu arhitectura ta, unde QuestionGenerationEngine apare ca fallback dacă nu există o întrebare potrivită.

Nota : O sa folosim varianta A for now

## 8. O varianta mai curata de implementare 
```python
class QuestionSelectionEngine:
    def filter_seen_questions(self, candidate_questions, seen_question_ids):
        seen_question_ids = set(seen_question_ids or [])
        return [
            question for question in candidate_questions
            if question.id not in seen_question_ids
        ]

    def select(self, candidate_questions, target_difficulty: float, seen_question_ids=None):
        eligible_questions = self.filter_seen_questions(
            candidate_questions,
            seen_question_ids
        )

        if not eligible_questions:
            return None

        return min(
            eligible_questions,
            key=lambda question: (
                abs(question.difficulty_initial - target_difficulty),
                -question.difficulty_initial
            )
        ) 
```

Primul: poți testa filtrarea separat.
Al doilea: codul devine mai clar semantic.

Observă și că am transformat seen_question_ids în set, ceea ce este mai eficient la căutare decât listă.

O sa incercam sa folosit set ca e mult mai rapid pe termen lung

## 9. Ce faci cu intrebarile repetate

Aici e o subtilitate pedagogică.

Există situații în care repetarea unei întrebări poate fi bună. De exemplu, pentru consolidare sau spaced repetition.

Dar asta nu este scopul Sprintului 1.

În Sprint 1, regula voastră este:
evitați repetiția inutilă.

Deci nu încercați să implementați încă:
repetition strategies;
revision mode;
relearning loops.

Acestea sunt funcționalități de sprinturi viitoare.

## 10. Cum testezi Task 5

Caz 1 — există alternative nevăzute

Ai candidate questions:
1, 2, 3

Seen questions:
[1]

Trebuie ca întrebarea 1 să fie exclusă, iar selecția să se facă dintre 2 și 3.

Caz 2 — întrebarea „cea mai bună” este văzută

Ai target difficulty = 0.5
Question 1 are 0.5, dar este văzută
Question 2 are 0.6 și nu este văzută

Trebuie să alegi întrebarea 2.

Asta este testul cel mai important, pentru că arată că Task 5 chiar schimbă rezultatul selecției.

Caz 3 — toate sunt văzute

Ai candidate questions:
1, 2, 3

Seen questions:
[1, 2, 3]

Trebuie să întorci None.

Caz 4 — seen list goală

Ai candidate questions:
1, 2, 3

Seen questions:
[]

Se comportă exact ca Task 4 simplu. Nimic nu este exclus.

Exemple :

Un test simplu de filtrare

```python 
def test_filter_seen_questions_excludes_seen_items():
    question_one = DummyQuestion(id=1, difficulty_initial=0.5)
    question_two = DummyQuestion(id=2, difficulty_initial=0.6)

    engine = QuestionSelectionEngine()

    eligible = engine.filter_seen_questions(
        candidate_questions=[question_one, question_two],
        seen_question_ids=[1],
    )

    assert len(eligible) == 1
    assert eligible[0].id == 2
```

Un test foarte important pentru efectul asupra selecției:

```python 
def test_selection_skips_best_question_if_already_seen():
    best_question = DummyQuestion(id=1, difficulty_initial=0.5)
    second_best_question = DummyQuestion(id=2, difficulty_initial=0.6)

    engine = QuestionSelectionEngine()

    selected = engine.select(
        candidate_questions=[best_question, second_best_question],
        target_difficulty=0.5,
        seen_question_ids=[1],
    )

    assert selected.id == 2
```

Si unul de fallback 
```python 
def test_selection_returns_none_when_all_questions_are_seen():
    question_one = DummyQuestion(id=1, difficulty_initial=0.5)
    question_two = DummyQuestion(id=2, difficulty_initial=0.6)

    engine = QuestionSelectionEngine()

    selected = engine.select(
        candidate_questions=[question_one, question_two],
        target_difficulty=0.5,
        seen_question_ids=[1, 2],
    )

    assert selected is None
```

## 11. Cum arata integrarea in ```QuestionRecommendationEngine```

```python
class QuestionRecommendationEngine:
    def recommend(self, user_id: int, subject_id: int, topic_id: int):
        student_context = self.repository.build_student_context(
            user_id=user_id,
            subject_id=subject_id,
            topic_id=topic_id,
        )

        features = self.feature_service.build_features(student_context)
        mastery_result = self.mastery_estimator.estimate(features)
        difficulty_result = self.difficulty_estimator.estimate(mastery_result.mastery_score)

        selected_question = self.selection_engine.select(
            candidate_questions=student_context.candidate_questions,
            target_difficulty=difficulty_result.target_difficulty,
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