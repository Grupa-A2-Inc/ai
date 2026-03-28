# Task1.md — Calcul accuracy + timp

# Feature Engineering: Accuracy and Average Time

Asta implică 4 lucruri:

AI-ul trebuie să știe din ce date calculează indicatorii;  
istoricul elevului trebuie transformat în valori numerice utile;  
accuracy și avg_time trebuie calculate coerent;  
rezultatul trebuie trimis mai departe într-un format standardizat.

1. definești indicatorii calculați  
2. extragi istoricul elevului  
3. calculezi accuracy  
4. calculezi avg_time  
5. tratezi cazul fără istoric  
6. creezi DTO-ul de rezultat  
7. implementezi serviciul  
8. testezi rezultatul

## 1. Definești indicatorii calculați

Pentru Sprint 2, primii indicatori utili sunt:

- `accuracy`
- `avg_time`
- `attempt_count`

### Accuracy
```text
accuracy = correct_answers / total_answers
```

### Average Time
```text
avg_time = total_time_spent / total_answers
```

### Attempt Count
```text
attempt_count = total_answers
```

Acești indicatori vor fi folosiți în taskurile următoare pentru normalizare și mastery.

## 2. Datele de intrare

Datele vin din `student_context.history`.

Acest istoric conține interacțiunile elevului, de exemplu:
- `is_correct`
- `score`
- `time_spent`
- `answered_at`

Exemplu conceptual:
```python
[
    {"is_correct": True, "time_spent": 20},
    {"is_correct": False, "time_spent": 35},
    {"is_correct": True, "time_spent": 25},
]
```

## 3. DTO pentru rezultate

În `dto/topic_features.py`:

```python
class TopicFeatures:
    def __init__(self, accuracy: float, avg_time: float, attempt_count: int):
        self.accuracy = accuracy
        self.avg_time = avg_time
        self.attempt_count = attempt_count
```

DTO-ul doar transportă indicatorii. Nu face calcule și nu ia decizii.

## 4. Implementarea serviciului

În `services/feature_engineering_service.py`:

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

        correct_count = sum(
            1 for interaction in history if interaction.is_correct
        )

        accuracy = correct_count / attempt_count

        avg_time = sum(
            interaction.time_spent for interaction in history
        ) / attempt_count

        return TopicFeatures(
            accuracy=accuracy,
            avg_time=avg_time,
            attempt_count=attempt_count,
        )
```

## 5. Explicație implementare

### `history = list(student_context.history)`
Transformăm queryset-ul în listă pentru a-l parcurge mai sigur și mai clar.

### Cazul fără istoric
```python
if not history:
```
Întoarcem:
- `accuracy = 0.5`
- `avg_time = 30.0`
- `attempt_count = 0`

Asta oferă un punct neutru pentru elevii noi.

### Calcul accuracy
```python
correct_count = sum(...)
accuracy = correct_count / attempt_count
```

### Calcul avg_time
```python
avg_time = sum(...) / attempt_count
```

## 6. Ce NU trebuie să facă acest serviciu

NU trebuie:
- să normalizeze datele
- să calculeze mastery
- să facă query-uri în DB
- să selecteze întrebări
- să calculeze dificultatea țintă

Rolul lui este doar să transforme istoricul în indicatori de bază.

## 7. Edge cases

### Elev nou
`history = []`  
Trebuie să întorci valori default, fără crash.

### Toate răspunsurile greșite
Accuracy trebuie să fie `0.0`, nu eroare.

### Timpuri foarte mari
Nu le tratezi special încă. Vor fi normalizate în Task 2.

## 8. Testare Task 1

### Test 1 — elev bun
```python
history = [
    (True, 20),
    (True, 25),
    (True, 30),
]
```
Rezultat așteptat:
- `accuracy = 1.0`
- `avg_time = 25.0`
- `attempt_count = 3`

### Test 2 — elev mediu
```python
history = [
    (True, 20),
    (False, 40),
]
```
Rezultat:
- `accuracy = 0.5`
- `avg_time = 30.0`

### Test 3 — elev nou
```python
history = []
```
Rezultat:
- `accuracy = 0.5`
- `avg_time = 30.0`
- `attempt_count = 0`

## 9. Definition of Done

Task-ul este gata când:
- accuracy este calculat corect
- avg_time este calculat corect
- attempt_count este corect
- cazul fără istoric este tratat
- DTO-ul este folosit
- serviciul poate fi apelat din engine
