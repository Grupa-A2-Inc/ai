# Task 3 : Simple Mastery Calculation 

„Transform istoricul brut al elevului într-un scor numeric coerent, între 0 și 1, care descrie cât de bine stă elevul pe un topic.”

Aici sunt trei idei foarte importante.

+ Prima este că mastery-ul nu este același lucru cu accuracy-ul. Accuracy-ul este doar o parte din imagine.
+ A doua este că mastery-ul trebuie să fie stabil și explicabil, nu o cutie neagră.
+ A treia este că output-ul Task-ului 3 trebuie să poată fi folosit direct de Task 4, unde se calculează dificultatea țintă și se selectează întrebarea.

Cu alte cuvinte, Task 3 este puntea dintre „date” și „decizie”.

+ Mai întâi stabilești ce indicatori vrei să extragi din istoric;

+ După aceea implementezi un serviciu de feature engineering;

+ Apoi definești un rezultat standard pentru mastery;

+ După aceea implementezi estimatorul rule-based;

+ La final validezi că scorul produs are sens în câteva scenarii concrete.

## 1. Ce inseamna mastery 

„Un scor care aproximează cât de bine stă elevul pe topicul ales, pe baza performanței sale anterioare.”

Este o estimare operationala, foloita pentru a alege urmatoarea intrebare

De aceea, în Sprint 1, formula trebuie să fie:
ușor de calculat;
ușor de explicat;
ușor de ajustat mai târziu.

## 2. Ce date intra in Task 3

Task 3 consumă datele venite din Task 2, adică din ```StudentDataRepository```.

În forma minimă, ai nevoie de:
istoricul elevului pe topic;
eventual istoricul recent;
lista interacțiunilor, fiecare cu is_correct și time_spent.

Din aceste date vei extrage câțiva indicatori simpli. Pentru Sprint 1, cei mai sănătoși sunt:

accuracy;
average time;
number of attempts.

Asta este suficient. Nu trebuie să complici cu 10 feature-uri din prima.

## 3. Imparti Task 3 in doua componente

```FeatureEngineeringService``` și ```MasteryEstimator```.

```FeatureEngineeringService``` raspunde la intrebarea "Ce indicatori extrag din istoricul brut?"

```MasteryEstimator``` raspunde la intrebarea "Cum combin acesti indicatori intr-un scor final?"

## 4. Ce trebuie sa faca ```FeatureEngineeringService```

In Sprint1 e suficient sa implementezi :

+ accuracy = proporția de răspunsuri corecte;
+ avg_time = timpul mediu petrecut pe întrebare;
+ attempt_count = câte interacțiuni există pe topic.

Asta înseamnă că dacă elevul are 10 răspunsuri, dintre care 7 corecte, accuracy-ul este 0.7.

Dacă timpii au fost 20, 30 și 40 secunde, average time este 30.

### DTO pentru features 

in ```dto/topic_features.py``` definim obiectul care transporta aceste valori 

```python 
class TopicFeatures:
    def __init__(self, accuracy: float, avg_time: float, attempt_count: int):
        self.accuracy = accuracy
        self.avg_time = avg_time
        self.attempt_count = attempt_count
```

## 5. Implementarea "FeaturesEngineering Service"

In ```services/feature_engineering_service.py``` o implementare pentru Sprint1 ar putea fi :

```python
 from tutoring.dto.topic_features import TopicFeatures

class FeatureEngineeringService:
    def build_features(self, student_context) -> TopicFeatures:
        history = list(student_context.history)

        if not history:
            return TopicFeatures(
                accuracy=0.5,
                avg_time=30.0,
                attempt_count=0,
            )

        attempt_count = len(history)
        correct_count = sum(1 for interaction in history if interaction.is_correct)
        accuracy = correct_count / attempt_count

        avg_time = sum(interaction.time_spent for interaction in history) / attempt_count

        return TopicFeatures(
            accuracy=accuracy,
            avg_time=avg_time,
            attempt_count=attempt_count,
        )
```

## 6. De ce e scris asa?

Aici sunt câteva decizii foarte importante.

a) history = list(student_context.history)

Dacă repository-ul întoarce queryset, îl convertim într-o listă, ca să putem itera clar și eventual să evităm comportamente surprinzătoare dacă îl folosim de mai multe ori.

b) cazul if not history

Asta este foarte important.
Trebuie să existe comportament pentru elev nou.

Dacă elevul nu are încă istoric, nu poți împărți la zero și nici nu poți produce erori. Trebuie să alegi niște valori default rezonabile.

De exemplu:
accuracy = 0.5
avg_time = 30.0
attempt_count = 0

De ce 0.5 la accuracy?
Pentru că este un punct neutru. Nu vrei nici să consideri elevul foarte bun, nici foarte slab.

c) attempt_count

Poate părea banal, dar e util. Chiar dacă în Sprint 1 nu îl folosești foarte mult în formulă, îți oferă context și îl poți folosi mai târziu pentru a pondera încrederea în mastery.

## 7. Ce trebuie sa faca ```MasteryEstimator```

```MasteryEstimator``` primeste features si intoarce un scor final

In Sprint 1 vrem sa facem o varianta rule-based.

### DTO pentru rezultat 

In ```dto/mastery_result.py``` definesti iesirea

```python 
class MasteryResult:
    def __init__(self, mastery_score: float):
        self.mastery_score = mastery_score
```

## 8. Cum alegi formula

Aici trebuie să fii foarte pragmatic.

Cea mai sănătoasă formulă pentru început este una care:

+ premiază accuracy mare;

+ penalizează timp mare;

+ produce rezultat între 0 și 1.

```mastery = 0.7 * accuracy + 0.3 * (1 - normalized_time)```

Dacă elevul răspunde corect și relativ repede, scorul crește.
Dacă răspunde prost și foarte lent, scorul scade.

## 10. Normalizarea timpului

Vrem sa normalizam secundele intre 0 si 1

Pentru Sprint 1 facem ceva simplu : 

```python
 normalized_time = min(avg_time / 60.0, 1.0)
```

Asta înseamnă:
dacă avg_time este 30 secunde, normalized_time = 0.5
dacă avg_time este 60 secunde, normalized_time = 1.0
dacă avg_time este 90 secunde, tot 1.0

Nu este o normalizare perfectă, dar pentru Sprint 1 este suficientă și foarte ușor de explicat.


## 11. Implementarea MasteryEstimator

```services/mastery_estimator.py``` o varianta buna este :

```python 
from tutoring.dto.mastery_result import MasteryResult


class MasteryEstimator:
    def estimate(self, features) -> MasteryResult:
        normalized_time = min(features.avg_time / 60.0, 1.0)

        mastery = 0.7 * features.accuracy + 0.3 * (1 - normalized_time)

        mastery = max(0.0, min(mastery, 1.0))

        return MasteryResult(mastery_score=mastery)
```

## 12. Cum se leaga Task 3 de Task 4

Task 3 produce mastery score-ul.
Task 4 îl folosește pentru a calcula dificultatea țintă.

De exemplu:
dacă mastery = 0.4
poți seta target difficulty = 0.5 sau 0.6

Adică Task 3 nu alege întrebarea, dar creează baza pe care Task 4 o folosește.

Asta e foarte important de înțeles: Task 3 produce semnalul care ghidează selecția.

## 13. Ce fac elevii noi

Aici este unul dintre cele mai importante edge cases.

Pentru un elev nou:
nu ai history;
nu ai accuracy real;
nu ai avg_time real.

Ai două variante.

Prima este să folosești valori default, cum am arătat mai sus.
A doua este să definești direct un mastery implicit, de exemplu 0.5.

Eu prefer varianta în care FeatureEngineeringService întoarce feature-uri default, iar MasteryEstimator aplică aceeași formulă ca pentru toată lumea. E mai unitar și mai curat. So o sa o folosim pe asta :)

## 14. Cum testezi Task 3

Aici trebuie să ai câteva scenarii foarte clare.

### Caz 1 — elev bun

Exemplu:
accuracy = 0.9
avg_time = 15 sec

Normalized time = 0.25

Mastery:
0.7 * 0.9 + 0.3 * (1 - 0.25)
= 0.63 + 0.225
= 0.855

Asta are sens. Elevul primește mastery mare.

### Caz 2 — elev mediu

Exemplu:
accuracy = 0.6
avg_time = 30 sec

Normalized time = 0.5

Mastery:
0.7 * 0.6 + 0.3 * 0.5
= 0.42 + 0.15
= 0.57

Din nou, are sens.

### Caz 3 — elev slab

Exemplu:
accuracy = 0.3
avg_time = 60 sec

Normalized time = 1.0

Mastery:
0.7 * 0.3 + 0.3 * 0
= 0.21

Scor mic. Exact ce vrei.

### Caz 4 — elev nou

Feature defaults:
accuracy = 0.5
avg_time = 30 sec

Mastery:
0.7 * 0.5 + 0.3 * 0.5
= 0.5

Scor neutru. Foarte bun pentru bootstrap.

Exemplu test : 

```python
 def test_mastery_estimator_returns_high_score_for_good_student():
    features = TopicFeatures(
        accuracy=0.9,
        avg_time=15.0,
        attempt_count=10,
    )

    estimator = MasteryEstimator()
    result = estimator.estimate(features)

    assert 0.8 <= result.mastery_score <= 1.0
```

## 15. Cum foloseste engine-ul Task 3

In ```question_recommendation_engine.py``` flowu-ul ar trebui sa arate aproximativ asa:

```python 
from tutoring.repositories.student_data_repository import StudentDataRepository
from tutoring.services.feature_engineering_service import FeatureEngineeringService
from tutoring.services.mastery_estimator import MasteryEstimator


class QuestionRecommendationEngine:
    def __init__(self):
        self.repository = StudentDataRepository()
        self.feature_service = FeatureEngineeringService()
        self.mastery_estimator = MasteryEstimator()

    def recommend(self, user_id: int, subject_id: int, topic_id: int):
        student_context = self.repository.build_student_context(
            user_id=user_id,
            subject_id=subject_id,
            topic_id=topic_id,
        )

        features = self.feature_service.build_features(student_context)
        mastery_result = self.mastery_estimator.estimate(features)

        # de aici merge mai departe în Task 4
        ...
```

Engine-ul orchestrează.
Feature service extrage indicatori.
Mastery estimator calculează scorul.

