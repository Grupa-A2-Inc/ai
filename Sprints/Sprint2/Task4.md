# Task4.md — Dificultate țintă

# Target Difficulty Estimation

Asta implică 4 lucruri:

mastery-ul trebuie transformat într-o dificultate utilă;  
sistemul trebuie să provoace elevul puțin;  
dificultatea țintă trebuie limitată corect;  
output-ul trebuie folosit în selecția întrebării.

1. definești regula de transformare  
2. stabilești offset-ul peste mastery  
3. creezi DTO-ul de rezultat  
4. implementezi estimatorul  
5. tratezi limitele  
6. testezi pe valori diferite  
7. pregătești output-ul pentru Task 5

## 1. Ideea generală

Nu vrei să dai elevului o întrebare exact la nivelul lui, ci puțin peste, astfel încât să învețe.

De aceea:
```text
target_difficulty = mastery + offset
```

## 2. Formula recomandată

```text
target_difficulty = min(mastery + 0.1, 1.0)
```

Offset-ul de `0.1` este suficient de mic încât să nu fie frustrant, dar suficient de mare încât să fie provocator.

## 3. DTO pentru rezultat

În `dto/difficulty_result.py`:

```python
class DifficultyResult:
    def __init__(self, target_difficulty: float):
        self.target_difficulty = target_difficulty
```

## 4. Implementare

În `services/difficulty_estimator.py`:

```python
from tutoring.dto.difficulty_result import DifficultyResult


class DifficultyEstimator:
    def estimate(self, mastery_score: float) -> DifficultyResult:
        target = min(mastery_score + 0.1, 1.0)
        return DifficultyResult(target_difficulty=target)
```

## 5. Explicație implementare

### De ce `+ 0.1`
Pentru că:
- provoacă elevul puțin
- nu sare prea mult peste nivelul actual
- e ușor de explicat la prezentare

### De ce `min(..., 1.0)`
Pentru că difficulty-ul trebuie să rămână în intervalul `[0,1]`.

## 6. Ce NU trebuie să facă acest task

NU trebuie:
- să aleagă întrebări
- să calculeze mastery
- să filtreze întrebări văzute
- să facă query-uri

## 7. Edge cases

### `mastery = 0.95`
Target devine `1.0`, nu `1.05`

### `mastery = 0.0`
Target devine `0.1`

### Elev nou
Mastery de `0.5` → target de `0.6`

## 8. Testare Task 4

### Test 1
```text
mastery = 0.3
target = 0.4
```

### Test 2
```text
mastery = 0.8
target = 0.9
```

### Test 3
```text
mastery = 0.95
target = 1.0
```

## 9. Definition of Done

Task-ul este gata când:
- target difficulty este mereu între 0 și 1
- este calculată consistent
- folosește mastery-ul ca intrare
- output-ul merge direct în selecție
