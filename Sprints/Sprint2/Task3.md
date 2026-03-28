# Task3.md — Mastery îmbunătățit

# Improved Mastery Calculation

Asta implică 4 lucruri:

mastery-ul nu mai trebuie să depindă doar de accuracy;  
viteza de răspuns trebuie inclusă în estimare;  
rezultatul trebuie să fie stabil și explicabil;  
output-ul trebuie să poată fi folosit pentru target difficulty.

1. definești formula nouă  
2. stabilești ponderile  
3. creezi DTO-ul de rezultat  
4. implementezi estimatorul  
5. tratezi cazurile limită  
6. testezi pe profiluri de elevi  
7. pregătești output-ul pentru Task 4

## 1. Ideea generală

Mastery-ul trebuie să reflecte:
- cât de corect răspunde elevul
- cât de eficient răspunde

Deci nu mai este doar:
```text
mastery = accuracy
```

Ci:
```text
mastery = combinație între accuracy și normalized_time
```

## 2. Formula recomandată

```text
mastery = 0.7 * accuracy + 0.3 * normalized_time
```

De ce e bună:
- accuracy are pondere mai mare
- viteza influențează, dar nu domină
- rezultatul rămâne în `[0,1]`

## 3. DTO pentru rezultat

În `dto/mastery_result.py`:

```python
class MasteryResult:
    def __init__(self, mastery_score: float):
        self.mastery_score = mastery_score
```

## 4. Implementare

În `services/mastery_estimator.py`:

```python
from tutoring.dto.mastery_result import MasteryResult


class MasteryEstimator:
    def estimate(self, normalized_features) -> MasteryResult:
        mastery = (
            0.7 * normalized_features.accuracy
            + 0.3 * normalized_features.normalized_time
        )

        mastery = max(0.0, min(mastery, 1.0))

        return MasteryResult(mastery_score=mastery)
```

## 5. Explicație implementare

### De ce 0.7 / 0.3
Pentru că învățarea trebuie să fie influențată mai mult de corectitudine decât de viteză.

### De ce clamp între 0 și 1
Chiar dacă formula e sigură, e sănătos să garantezi:
```python
max(0.0, min(mastery, 1.0))
```

### De ce output DTO
Ca să poți extinde mai târziu:
- confidence
- explanation
- feature breakdown

## 6. Ce NU trebuie să facă acest task

NU trebuie:
- să calculeze target difficulty
- să selecteze întrebări
- să facă query-uri în DB
- să modifice contextul elevului

## 7. Edge cases

### Elev nou
Cu:
- `accuracy = 0.5`
- `normalized_time = 0.5`

Rezultă:
```text
mastery = 0.5
```

### Elev foarte bun
Accuracy mare + timp bun → mastery mare

### Elev rapid dar greșește
Mastery nu trebuie să fie mare doar pentru că e rapid

## 8. Testare Task 3

### Test 1 — elev bun
- accuracy = 0.9
- normalized_time = 0.8

```text
mastery = 0.7 * 0.9 + 0.3 * 0.8 = 0.87
```

### Test 2 — elev mediu
- accuracy = 0.6
- normalized_time = 0.5

```text
mastery = 0.57
```

### Test 3 — elev slab
- accuracy = 0.2
- normalized_time = 0.3

```text
mastery = 0.23
```

## 9. Definition of Done

Task-ul este gata când:
- mastery-ul este între 0 și 1
- depinde de accuracy și normalized_time
- formula este stabilă și explicabilă
- output-ul poate fi consumat de Task 4
