# S5-01 — Build ML Dataset and Define Rule-Based to ML Transition

## Description

Acest task pregătește baza pentru antrenarea modelului de Machine Learning din Sprintul 5.

Scopul este să construim un dataset ML pornind de la istoricul real al elevilor, adică din `StudentInteraction`, și să stabilim clar cum se face trecerea de la sistemul rule-based la sistemul bazat pe ML.

Decizia finală pentru arhitectură este:

Folosim un singur model ML global
Nu antrenăm câte un model separat pentru fiecare topic.

Modelul global va primi ca input și informații despre:

```
student
subject
topic
istoricul elevului pe acel topic
nivelul curent al elevului pe acel topic
dificultatea întrebărilor
scorurile elevului
timpul de răspuns 
```

Astfel, chiar dacă modelul este global, el poate diferenția faptul că același elev poate fi bun la un topic și slab la altul.

# Main Decision

Vom folosi următoarea regulă:
```
primele 10 răspunsuri ale unui elev pe un topic → rule-based
după 10 răspunsuri pe acel topic → ML-based 
```

Această regulă rezolvă problema de cold start.

Un elev nou nu are istoric. Dacă nu are istoric, modelul ML nu are suficiente date despre el pentru acel topic.

De aceea, la început folosim sistemul rule-based, iar după ce s-au strâns suficiente StudentInteraction, putem folosi ML.

# Why We Do Not Train One Model Per Topic

Nu vom antrena modele separate de forma:

model_topic_1102.pkl
model_topic_1103.pkl
model_topic_1201.pkl

Această variantă pare intuitivă, dar are probleme:

- ai nevoie de multe date pentru fiecare topic
- unele topicuri vor avea prea puține interacțiuni
- apar multe fișiere de model greu de gestionat
- deployment-ul devine mai complicat
- trainingul devine fragmentat

Varianta aleasă este:

### un singur model global

care primește subject_id și topic_id ca features.

# Why One Global Model Still Works Per Topic

Modelul global poate diferenția nivelul elevului pe topic dacă datasetul este construit corect.

Cheia este să nu folosim doar features globale despre elev.

Trebuie să folosim features calculate pe combinația:

student_id + subject_id + topic_id

Exemplu:

student-1 pe topic 1102:
average_score_on_topic = 0.9
current_mastery = 0.82
attempt_count_on_topic = 20

student-1 pe topic 1205:
average_score_on_topic = 0.35
current_mastery = 0.38
attempt_count_on_topic = 18

Deși este același elev, modelul vede contexte diferite și poate prezice niveluri diferite.

# Runtime Flow for a New Student

Când apare un elev nou, prin endpoint-ul de sync se creează:
```
StudentProfile
StudentTopicLevel pentru fiecare topic
```

Nivelul default este:

```mastery_score = 0.5```

Asta înseamnă că elevul pornește de la un nivel mediu.

# Cold Start Strategy

Pentru un elev nou pe un topic nou:

```history_count = 0```

Nu avem destule date.

Atunci sistemul folosește rule-based.

Flow:
```
StudentTopicLevel = 0.5
↓
target difficulty ≈ 0.5 / 0.6
↓
se recomandă întrebări medii
```
După fiecare răspuns, backend-ul trimite feedback către AI, iar AI-ul salvează:

```StudentInteraction```

și actualizează:

```StudentTopicLevel```

# Rule-Based Phase

Regula este:
```py 
if interaction_count_on_topic < 10:
    use_rule_based = True
else:
    use_ml = True
```
Pentru primele 10 răspunsuri ale elevului pe topic, sistemul folosește formula rule-based existentă.

Această formulă folosește:
```
accuracy
normalized_time
current_mastery
question difficulty
```

Scopul acestei faze este să colectăm suficient istoric minim pentru elev pe acel topic.

# ML Phase

După ce elevul are cel puțin 10 interacțiuni pe acel topic:

```interaction_count_on_topic >= 10```

sistemul poate folosi modelul ML global.

Modelul primește features calculate tot pe acel topic, nu pe tot istoricul global al elevului.

Exemplu de input pentru ML:

```
subject_id
topic_id
question_difficulty
attempt_count_on_topic
average_score_on_topic
average_time_on_topic
recent_average_score
recent_average_time
current_mastery
```
Modelul returnează:

```predicted_mastery```

Apoi DifficultyEstimator poate transforma acest mastery într-o dificultate țintă.

# Important Runtime Rule

Datasetul ML NU se construiește la fiecare răspuns.

La fiecare răspuns se face doar:
```
1. salvare StudentInteraction
2. update StudentTopicLevel
```
Datasetul se construiește periodic, de exemplu:

```
manual
zilnic
săptămânal
înainte de re-training
la final de sprint/demo
```

Flow:

```
StudentInteraction se acumulează continuu
↓
exportăm dataset periodic
↓
antrenăm model ML global
↓
salvăm modelul
↓
runtime folosește modelul pentru predicții
Data Sources
```
Datasetul se construiește din următoarele modele:
```
Question
StudentInteraction
StudentTopicLevel
StudentProfile
```

## Question

Question conține banca de întrebări.

În prezent avem aproximativ:

100 întrebări pe topic

Din Question folosim:
``` 
question_id
subject_id
topic_id
difficulty
times_answered
times_correct
avg_time_spent
```
Aceste date descriu întrebarea.

## StudentInteraction

StudentInteraction este sursa principală pentru ML.

Acest tabel trebuie populat cu date reale din feedback-ul backend-ului.

Din StudentInteraction folosim:
```
user_id
question_id
score
is_correct
time_spent
created_at
```
Fără StudentInteraction, nu avem dataset real.

## StudentTopicLevel

StudentTopicLevel reprezintă nivelul curent al elevului pe un topic.

Din StudentTopicLevel folosim:

`current_mastery`

Acest câmp poate fi folosit ca feature în dataset.

# Difference Between StudentInteraction and StudentTopicLevel

Ele nu se înlocuiesc una pe alta.
```
StudentInteraction = istoricul brut
StudentTopicLevel = rezumatul/nivelul curent
```
Analog:
```
StudentInteraction = toate notele elevului
StudentTopicLevel = media actuală pe topic
```
Pentru ML avem nevoie de ambele.

Features Used in the Dataset

Datasetul trebuie să conțină features calculate per:

`student_id + subject_id + topic_id`

Features recomandate:

```
student_id
subject_id
topic_id
question_id
question_difficulty
score
is_correct
time_spent
normalized_time
attempt_count_on_topic
average_score_on_topic
average_time_on_topic
recent_average_score
recent_average_time
normalized_recent_time
current_mastery
target_mastery
```

#Feature Explanation

`student_id`

Identifică elevul.

Pentru modelul ML, acest câmp poate fi păstrat în dataset pentru analiză, dar în modelul inițial poate fi exclus din training numeric, ca să nu învățăm pe ID-uri arbitrare.

`subject_id`

Identifică materia.

Ajută modelul să diferențieze între materii.

`topic_id`

Identifică topicul.

Este foarte important pentru că modelul global trebuie să știe pentru ce topic face predicția.

`question_difficulty`

Vine din:

interaction.question.difficulty

Arată cât de grea era întrebarea.

`score`

Vine din:

interaction.score

Poate fi:
```
0
0.5
1
```
`is_correct`

Vine din:

interaction.is_correct

Pentru ML îl transformăm în:
```
1 dacă True
0 dacă False
```
`time_spent`
Vine din:

interaction.time_spent

Arată cât timp a stat elevul pe întrebare.

`normalized_time`

Transformă timpul într-o valoare între 0 și 1.

Exemplu:

`normalized_time = min(time_spent / 120, 1.0)`

Dacă elevul stă 60 secunde:

```
normalized_time = 0.5
attempt_count_on_topic
```
Numărul de interacțiuni anterioare ale elevului pe acel topic.

Exemplu:

`dacă elevul a răspuns deja la 7 întrebări pe topic, attempt_count_on_topic = 7`

Acest feature ajută la diferențierea între:

estimare slabă, cu puține date
estimare mai stabilă, cu multe date

`average_score_on_topic`

Media scorurilor elevului pe acel topic până la momentul curent.

`average_time_on_topic`

Timpul mediu al elevului pe acel topic.

`recent_average_score`

Media scorurilor recente, de exemplu ultimele 5 interacțiuni pe topic.

Acest feature ajută modelul să observe trendul.

`recent_average_time`

Timpul mediu recent pe topic.

`current_mastery`

Vine din:

StudentTopicLevel.mastery_score

Este nivelul persistent curent al elevului pe acel topic.

`target_mastery`

Este label-ul pe care modelul îl va învăța.

Pentru început, deoarece nu avem un label uman real, folosim o formulă rule-based pentru a genera un label provizoriu.

Aceasta este o abordare de tip:

weak supervision
## Target Mastery Formula

Pentru început, folosim:
```
performance_mastery = (
    0.7 * average_score_on_topic
    + 0.3 * (1 - normalized_average_time)
)

target_mastery = (
    0.8 * current_mastery
    + 0.2 * performance_mastery
)

target_mastery = max(0.0, min(target_mastery, 1.0))
```
## Dataset Format

Datasetul final va fi un singur CSV global, nu câte un CSV pentru fiecare elev/topic.

Exemplu:
```csv
student_id,subject_id,topic_id,question_id,question_difficulty,score,time_spent,current_mastery,target_mastery
student-1,2,1102,101,0.5,1.0,35,0.5,0.6
student-1,2,1102,102,0.7,0.0,80,0.6,0.48
student-2,2,1102,101,0.5,0.5,60,0.5,0.52
student-3,3,1201,501,0.4,1.0,25,0.7,0.74
```
Why One CSV Is Enough

Nu facem:

student_1_topic_1102.csv
student_1_topic_1103.csv
student_2_topic_1102.csv

Asta ar crea haos și multe fișiere mici.

Facem:

`student_mastery_dataset.csv`

cu toate interacțiunile.

Fiecare rând conține student_id, subject_id și topic_id, deci modelul știe contextul fiecărei interacțiuni.

## Dataset Builder File

Creează fișierul:

`tutoring/ml/dataset_builder.py`

## Dataset Builder Code 
```py 
import csv
from pathlib import Path

from tutoring.models import StudentInteraction, StudentProfile, StudentTopicLevel


class StudentMasteryDatasetBuilder:
    MAX_TIME = 120.0

    def build_dataset(self, output_path: str) -> None:
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        rows = self._build_rows()

        with output_file.open("w", newline="", encoding="utf-8") as csv_file:
            writer = csv.DictWriter(
                csv_file,
                fieldnames=self._fieldnames(),
            )

            writer.writeheader()
            writer.writerows(rows)

    def _build_rows(self) -> list[dict]:
        interactions = StudentInteraction.objects.select_related(
            "question"
        ).order_by(
            "user_id",
            "question__subject_id",
            "question__topic_id",
            "created_at",
        )

        grouped_history = {}
        rows = []

        for interaction in interactions:
            subject_id = interaction.question.subject_id
            topic_id = interaction.question.topic_id

            key = (
                interaction.user_id,
                subject_id,
                topic_id,
            )

            previous_history = grouped_history.get(key, [])

            features = self._build_features(
                interaction=interaction,
                previous_history=previous_history,
                subject_id=subject_id,
                topic_id=topic_id,
            )

            rows.append(features)

            previous_history.append(interaction)
            grouped_history[key] = previous_history

        return rows

    def _build_features(
        self,
        interaction,
        previous_history,
        subject_id: int,
        topic_id: int,
    ) -> dict:
        attempt_count = len(previous_history)

        previous_scores = [
            item.score for item in previous_history
        ]

        previous_times = [
            item.time_spent for item in previous_history
        ]

        average_score = (
            sum(previous_scores) / len(previous_scores)
            if previous_scores else 0.5
        )

        average_time = (
            sum(previous_times) / len(previous_times)
            if previous_times else 60.0
        )

        recent_history = previous_history[-5:]

        recent_scores = [
            item.score for item in recent_history
        ]

        recent_times = [
            item.time_spent for item in recent_history
        ]

        recent_average_score = (
            sum(recent_scores) / len(recent_scores)
            if recent_scores else average_score
        )

        recent_average_time = (
            sum(recent_times) / len(recent_times)
            if recent_times else average_time
        )

        normalized_time = min(interaction.time_spent / self.MAX_TIME, 1.0)
        normalized_average_time = min(average_time / self.MAX_TIME, 1.0)
        normalized_recent_time = min(recent_average_time / self.MAX_TIME, 1.0)

        current_mastery = self._get_current_mastery(
            student_id=interaction.user_id,
            subject_id=subject_id,
            topic_id=topic_id,
        )

        target_mastery = self._calculate_target_mastery(
            current_mastery=current_mastery,
            average_score=average_score,
            normalized_average_time=normalized_average_time,
        )

        return {
            "student_id": interaction.user_id,
            "subject_id": subject_id,
            "topic_id": topic_id,
            "question_id": interaction.question_id,
            "question_difficulty": interaction.question.difficulty,
            "score": interaction.score,
            "is_correct": 1 if interaction.is_correct else 0,
            "time_spent": interaction.time_spent,
            "normalized_time": normalized_time,
            "attempt_count_on_topic": attempt_count,
            "average_score_on_topic": average_score,
            "average_time_on_topic": average_time,
            "normalized_average_time": normalized_average_time,
            "recent_average_score": recent_average_score,
            "recent_average_time": recent_average_time,
            "normalized_recent_time": normalized_recent_time,
            "current_mastery": current_mastery,
            "target_mastery": target_mastery,
        }

    def _get_current_mastery(
        self,
        student_id: str,
        subject_id: int,
        topic_id: int,
    ) -> float:
        try:
            student = StudentProfile.objects.get(
                student_id=student_id,
                is_active=True,
            )

            topic_level = StudentTopicLevel.objects.get(
                student=student,
                subject_id=subject_id,
                topic_id=topic_id,
            )

            return topic_level.mastery_score

        except (StudentProfile.DoesNotExist, StudentTopicLevel.DoesNotExist):
            return 0.5

    def _calculate_target_mastery(
        self,
        current_mastery: float,
        average_score: float,
        normalized_average_time: float,
    ) -> float:
        performance_mastery = (
            0.7 * average_score
            + 0.3 * (1 - normalized_average_time)
        )

        target_mastery = (
            0.8 * current_mastery
            + 0.2 * performance_mastery
        )

        return max(0.0, min(target_mastery, 1.0))

    def _fieldnames(self) -> list[str]:
        return [
            "student_id",
            "subject_id",
            "topic_id",
            "question_id",
            "question_difficulty",
            "score",
            "is_correct",
            "time_spent",
            "normalized_time",
            "attempt_count_on_topic",
            "average_score_on_topic",
            "average_time_on_topic",
            "normalized_average_time",
            "recent_average_score",
            "recent_average_time",
            "normalized_recent_time",
            "current_mastery",
            "target_mastery",
        ] 
```

## Management Command

Creează fișierul:

`tutoring/management/commands/export_training_dataset.py`

# Management Command Code

``` 
from django.core.management.base import BaseCommand

from tutoring.ml.dataset_builder import StudentMasteryDatasetBuilder


class Command(BaseCommand):
    help = "Export ML training dataset from StudentInteraction."

    def add_arguments(self, parser):
        parser.add_argument(
            "--output",
            type=str,
            default="data/training/student_mastery_dataset.csv",
        )

    def handle(self, *args, **options):
        output_path = options["output"]

        builder = StudentMasteryDatasetBuilder()
        builder.build_dataset(output_path)

        self.stdout.write(
            self.style.SUCCESS(
                f"Training dataset exported successfully to {output_path}"
            )
        )
```  
      
How to Run
`python manage.py export_training_dataset`

sau:

`python manage.py export_training_dataset --output data/training/student_mastery_dataset.csv`

## If StudentInteraction Is Empty

Dacă StudentInteraction este gol, datasetul va avea doar header.

Asta înseamnă:

nu avem date pentru ML

În acest caz avem două opțiuni:
```
1. rulăm aplicația și colectăm feedback real
2. generăm date simulate pentru demo
```
Datele simulate sunt acceptabile pentru testarea pipeline-ului, dar nu pentru un model serios.

Definition of Done

Task-ul este gata când:
```
- decizia de model ML global este documentată
- regula de primele 10 interacțiuni rule-based este documentată
- există StudentMasteryDatasetBuilder
- există export_training_dataset command
- datasetul este construit din StudentInteraction
- features sunt calculate per student + subject + topic
- Question este folosit pentru difficulty
- StudentTopicLevel este folosit pentru current_mastery
- target_mastery este calculat
- datasetul final este un singur CSV global
- echipa înțelege că ML-ul se folosește după minimum 10 interacțiuni pe topic
Summary
``` 
Task 1 definește baza pentru ML.

Vom folosi:

un singur model ML global

dar features locale pentru fiecare:

student + subject + topic

Primele 10 răspunsuri ale unui elev pe un topic rămân rule-based.

După 10 interacțiuni, sistemul poate folosi modelul ML pentru predicții mai bune.

Datasetul ML nu se construiește la fiecare răspuns, ci periodic, din istoricul acumulat în StudentInteraction.