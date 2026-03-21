# Task 2 : Student History Retrieval

StudentDataRepository are exact acest rol: să citească istoricul elevului, răspunsurile recente, întrebările deja văzute și întrebările disponibile, centralizând query-urile importante.

+ Primul este să știi exact ce date consumă AI-ul.

+ Al doilea este să separi clar logica de acces la bază de logica de business.

+ Al treilea este să returnezi date într-o formă ușor de consumat de FeatureEngineeringService și QuestionRecommendationEngine.

Cu alte cuvinte, repository-ul nu trebuie să decidă nimic. El doar trebuie să adune și să livreze datele corecte.

## 1. Ce trebuie sa poata citi StudentDataRepository

În Sprint 1, minimul realist este să implementezi trei fluxuri de date:

istoricul elevului pe topic;
lista întrebărilor deja văzute;
lista întrebărilor candidate pentru topic.

„Răspunsurile recente” pot fi integrate fie ca parte din istoricul elevului, fie ca metodă separată, dar pentru prima iterație nu trebuie complicat inutil dacă nu le folosești încă separat în logică.

## 2. Ce trebuie sa existe in models.py

Ca repository-ul să funcționeze, trebuie să ai modele minime care descriu întrebările și interacțiunile elevului.

Un model ```Question```, care descrie întrebarea;
un model ```StudentInteraction```, care descrie faptul că un elev a răspuns la o întrebare.

Model de Question 
```python
from django.db import models

class Question(models.Model):
    subject_id = models.IntegerField()
    topic_id = models.IntegerField()

    content = models.TextField()

    difficulty_initial = models.FloatField(default=0.5)
    difficulty_observed = models.FloatField(default=0.5)

    times_answered = models.IntegerField(default=0)
    times_correct = models.IntegerField(default=0)
    avg_time_spent = models.FloatField(default=0.0)

    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"Question {self.id} - topic {self.topic_id}"
```

Model de StudentInteraction 
```python
 class StudentInteraction(models.Model):
    user_id = models.IntegerField()
    question = models.ForeignKey(Question, on_delete=models.CASCADE)

    is_correct = models.BooleanField()
    score = models.FloatField(default=0.0)
    time_spent = models.FloatField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Interaction user={self.user_id}, question={self.question_id}"
```

Nota : Probabil chestii precum score nu sunt asa relevante pentru Sprintul 1,dar le-am lasat ca vom avea nevoie sigur in viitor si nu avem motiv sa nu il punem acum.

## 3. Metodele StudentDataRepository 

+ Prima este pentru istoricul elevului pe un topic.
+ A doua este pentru întrebările deja văzute de acel elev.
+ A treia este pentru întrebările candidate disponibile pe topic.
+ A patra, opțional, este pentru contextul complet, care le combină.

```python
class StudentDataRepository:
    def get_student_history(self, user_id: int, subject_id: int, topic_id: int):
        ...

    def get_recent_student_history(self, user_id: int, subject_id: int, topic_id: int, limit: int = 10):
        ...

    def get_seen_question_ids(self, user_id: int, subject_id: int, topic_id: int):
        ...

    def get_candidate_questions(self, subject_id: int, topic_id: int):
        ...
```

## 4. Cum implementezi query-urile

```python 
from tutoring.models import Question, StudentInteraction


class StudentDataRepository:
    def get_student_history(self, user_id: int, subject_id: int, topic_id: int):
        return StudentInteraction.objects.filter(
            user_id=user_id,
            question__subject_id=subject_id,
            question__topic_id=topic_id,
        ).select_related("question").order_by("created_at")

    def get_recent_student_history(self, user_id: int, subject_id: int, topic_id: int, limit: int = 10):
        return StudentInteraction.objects.filter(
            user_id=user_id,
            question__subject_id=subject_id,
            question__topic_id=topic_id,
        ).select_related("question").order_by("-created_at")[:limit]

    def get_seen_question_ids(self, user_id: int, subject_id: int, topic_id: int):
        return list(
            StudentInteraction.objects.filter(
                user_id=user_id,
                question__subject_id=subject_id,
                question__topic_id=topic_id,
            ).values_list("question_id", flat=True).distinct()
        )

    def get_candidate_questions(self, subject_id: int, topic_id: int):
        return Question.objects.filter(
            subject_id=subject_id,
            topic_id=topic_id,
            is_active=True,
        )
```

Aici sunt câteva detalii importante.

select_related("question") este util pentru că fiecare interacțiune are un ForeignKey spre întrebare, iar astfel eviți query-uri suplimentare când accesezi detalii din question.

order_by("created_at") pentru history general îți dă ordine cronologică, ceea ce e bun dacă ulterior calculezi progresul.

order_by("-created_at")[:limit] pentru recent history îți dă cele mai noi interacțiuni.

distinct() pe values_list("question_id", flat=True) este important, pentru că elevul poate să fi răspuns de mai multe ori la aceeași întrebare, dar pentru filtrarea „seen questions” vrei doar ID-urile unice.

## 5. Ce trebuie sa retureze repository-ul 

Repository-ul poate întoarce ori queryset-uri Django, ori DTO-uri, ori structuri simple Python. Pentru Sprint 1, cel mai sănătos este:

interacțiunile și întrebările candidate pot fi întoarse ca queryset-uri;
lista de seen questions e bine să fie o listă simplă de ID-uri.

Pentru ```StudentContext``` vom face un dto in ```dto/student_context.py```.

```python
 class StudentContext:
    def __init__(self, history, recent_history, seen_question_ids, candidate_questions):
        self.history = history
        self.recent_history = recent_history
        self.seen_question_ids = seen_question_ids
        self.candidate_questions = candidate_questions
```

Iar studentdatapreository va avea o metoda de compunere :

```python 
from tutoring.dto.student_context import StudentContext

class StudentDataRepository:
    ...

    def build_student_context(self, user_id: int, subject_id: int, topic_id: int) -> StudentContext:
        history = self.get_student_history(user_id, subject_id, topic_id)
        recent_history = self.get_recent_student_history(user_id, subject_id, topic_id)
        seen_question_ids = self.get_seen_question_ids(user_id, subject_id, topic_id)
        candidate_questions = self.get_candidate_questions(subject_id, topic_id)

        return StudentContext(
            history=history,
            recent_history=recent_history,
            seen_question_ids=seen_question_ids,
            candidate_questions=candidate_questions,
        )
```

## 6. Cum se leaga Task2 de restul sistemului 

Aici trebuie să vezi repo-ul ca pe un furnizor pentru două componente principale.

Prima este FeatureEngineeringService, care transformă istoricul brut în indicatori utili, cum ar fi accuracy, scoruri recente, timpul mediu pe întrebare și numărul de încercări. Documentul spune exact asta.

A doua este QuestionSelectionEngine, care folosește topicul, dificultatea dorită și întrebările deja văzute pentru a alege întrebarea potrivită.

Cu alte cuvinte, Task 2 alimentează direct Task 3 și Task 4. Dacă istoricul sau candidate questions sunt greșite, tot pipeline-ul se strică.

## 7. Ce validari sunt utile in task2 

Dacă elevul nu are istoric, get_student_history() trebuie să întoarcă queryset gol, nu eroare;

Dacă nu există întrebări candidate, get_candidate_questions() trebuie să întoarcă queryset gol;

Dacă nu există seen questions, metoda trebuie să întoarcă listă goală;

repository-ul nu trebuie să crape dacă baza e goală.

## 8. Cum pregatesti date de test pentru Task 2

Task 2 nu poate fi considerat gata fără seed data sau date de test.
Pentru demo, ai nevoie de ceva simplu:

două topicuri;
câteva întrebări pe fiecare topic;
un elev cu 4–5 interacțiuni pe un topic;
un elev nou, fără interacțiuni.

Exemplu conceptual:

pentru topic 8 ai întrebări cu dificultăți 0.2, 0.5 și 0.8;
elevul 12 a răspuns deja la întrebările 1 și 2;
întrebarea 3 este încă nevăzută.

În felul ăsta poți demonstra ușor:
că history se citește bine;
că seen questions se extrag corect;
că candidate questions se filtrează corect.

## 9. Cum testezi Task 2

Aici ai nevoie de teste simple, dar clare.

Primul test: elev cu istoric existent.
Te aștepți ca get_student_history() să întoarcă interacțiunile potrivite pentru user, subject și topic.

Al doilea test: seen questions.
Te aștepți ca get_seen_question_ids() să întoarcă doar ID-uri unice.

Al treilea test: candidate questions.
Te aștepți ca get_candidate_questions() să întoarcă doar întrebările active de pe topicul și materia cerute.

Al patrulea test: elev nou.
Te aștepți la history gol, seen questions goală, dar candidate questions disponibile.

Exemplu de test pentru seen questions:

```python 
def test_get_seen_question_ids_returns_unique_ids():
    repo = StudentDataRepository()

    seen_ids = repo.get_seen_question_ids(
        user_id=12,
        subject_id=3,
        topic_id=8,
    )

    assert len(seen_ids) == len(set(seen_ids))
```

Nu e un test complet, dar îți arată ideea corectă.

## 10. Cum ar trebuie sa foloseasca engine-ul acest task ```question_recommendation_engine.py```

```python
from tutoring.repositories.student_data_repository import StudentDataRepository


class QuestionRecommendationEngine:
    def __init__(self):
        self.repository = StudentDataRepository()

    def recommend(self, user_id: int, subject_id: int, topic_id: int):
        student_context = self.repository.build_student_context(
            user_id=user_id,
            subject_id=subject_id,
            topic_id=topic_id,
        )

        # aici merg mai departe feature engineering, mastery, selection
        ...
```


