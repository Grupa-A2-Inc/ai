# Task2.md — Normalizare date

# Feature Engineering: Data Normalization

Asta implică 4 lucruri:

indicatorii calculați trebuie aduși la aceeași scară;  
valorile trebuie să fie comparabile între ele;  
timpul trebuie transformat într-un scor util;  
rezultatul trebuie pregătit pentru mastery.

1. definești ce normalizezi  
2. alegi formula de normalizare  
3. creezi DTO-ul de rezultate normalizate  
4. implementezi serviciul  
5. tratezi cazurile limită  
6. testezi formula  
7. pregătești output-ul pentru mastery

## 1. Ce normalizezi

În Sprint 2, normalizăm în special:
- `avg_time`

`accuracy` este deja în intervalul `[0, 1]`, deci nu mai are nevoie de transformare.

## 2. De ce trebuie normalizat timpul

`avg_time` poate avea valori ca:
- 10
- 25
- 40
- 120

Nu îl poți combina direct cu accuracy, pentru că nu e deja în intervalul `[0, 1]`.

De aceea construim un `normalized_time` unde:
- timp mic = scor mai bun
- timp mare = scor mai slab

## 3. Formula de normalizare

O formulă simplă și bună pentru Sprint 2 este:

```text
normalized_time = 1 / (1 + avg_time / 30)
```

Exemple:
- `avg_time = 15` → `normalized_time ≈ 0.66`
- `avg_time = 30` → `normalized_time = 0.5`
- `avg_time = 60` → `normalized_time ≈ 0.33`

Asta e foarte util pentru că:
- nu explodează pe valori mari
- rămâne mereu în `(0, 1]`
- e ușor de explicat

## 4. DTO nou

În `dto/normalized_features.py`:

```python
class NormalizedFeatures:
    def __init__(self, accuracy: float, normalized_time: float, attempt_count: int):
        self.accuracy = accuracy
        self.normalized_time = normalized_time
        self.attempt_count = attempt_count
```

## 5. Implementarea serviciului

În `services/feature_engineering_service.py` poți adăuga:

```python
from tutoring.dto.normalized_features import NormalizedFeatures


class FeatureEngineeringService:
    def normalize(self, features) -> NormalizedFeatures:
        normalized_time = 1 / (1 + features.avg_time / 30)

        return NormalizedFeatures(
            accuracy=features.accuracy,
            normalized_time=normalized_time,
            attempt_count=features.attempt_count,
        )
```

## 6. Explicație implementare

### De ce `1 / (1 + avg_time / 30)`
Pentru că:
- când timpul crește, scorul scade
- nu ajungi niciodată sub 0
- pentru timp mediu, ai scor mediu
- este stabil numeric

### De ce nu folosim încă formule complicate
Pentru Sprint 2 vrem ceva:
- clar
- stabil
- explicabil
- ușor de testat

## 7. Ce NU trebuie să facă acest task

NU trebuie:
- să calculeze mastery
- să selecteze întrebări
- să modifice istoricul
- să facă query-uri
- să aplice business logic de recomandare

## 8. Edge cases

### `avg_time = 0`
Scorul devine:
```text
1 / (1 + 0) = 1
```
Perfect valid.

### `avg_time` foarte mare
Scorul se apropie de 0, dar nu devine negativ.

### Elev nou
Dacă `avg_time = 30.0`, rezultatul este `0.5`, ceea ce e neutru.

## 9. Testare Task 2

### Test 1
```python
avg_time = 15
```
Așteptat:
```text
normalized_time ≈ 0.66
```

### Test 2
```python
avg_time = 30
```
Așteptat:
```text
normalized_time = 0.5
```

### Test 3
```python
avg_time = 60
```
Așteptat:
```text
normalized_time ≈ 0.33
```

## 10. Definition of Done

Task-ul este gata când:
- `normalized_time` este mereu între 0 și 1
- formula funcționează pe valori mici și mari
- rezultatul este utilizabil în mastery
- DTO-ul de output este clar
- serviciul poate fi integrat în engine
