# Task5.md — Selecție optimă

# Optimal Question Selection

Asta implică 4 lucruri:

sistemul trebuie să pornească de la target difficulty;  
trebuie să excludă întrebările deja văzute;  
trebuie să aleagă întrebarea cea mai apropiată;  
la egalitate trebuie să aibă o regulă stabilă.

1. primești candidate_questions  
2. filtrezi seen_question_ids  
3. compari difficulty cu target  
4. alegi cea mai apropiată întrebare  
5. tratezi egalitățile  
6. tratezi lipsa de candidați  
7. returnezi întrebarea aleasă  
8. testezi scenarii reale

## 1. Ideea generală

Task-ul ăsta răspunde la întrebarea:

**„Având o dificultate țintă și o listă de întrebări disponibile, pe care o aleg?”**

## 2. Regula de selecție

Alegi întrebarea cu cea mai mică distanță față de target difficulty:

```text
distance = abs(question.difficulty - target_difficulty)
```

La egalitate:
- alegi întrebarea mai grea

## 3. Implementare

În `services/question_selection_engine.py`:

```python
class QuestionSelectionEngine:
    def select(self, candidate_questions, target_difficulty: float, seen_question_ids=None):
        seen_question_ids = set(seen_question_ids or [])

        eligible_questions = [
            question for question in candidate_questions
            if question.id not in seen_question_ids
        ]

        if not eligible_questions:
            return None

        return min(
            eligible_questions,
            key=lambda question: (
                abs(question.difficulty - target_difficulty),
                -question.difficulty
            )
        )
```

## 4. Explicație implementare

### De ce filtrăm întâi seen questions
Pentru că nu vrei să alegi o întrebare deja văzută dacă există alternativă.

### De ce folosim `set`
Pentru verificarea mai rapidă:
```python
question.id not in seen_question_ids
```

### De ce `min(..., key=...)`
Pentru că vrei întrebarea cu distanța cea mai mică.

### De ce `-question.difficulty`
La egalitate între două întrebări la fel de apropiate, o preferi pe cea puțin mai grea.

## 5. Ce NU trebuie să facă acest task

NU trebuie:
- să calculeze mastery
- să calculeze target difficulty
- să facă query-uri în DB
- să construiască history
- să întoarcă JSON

## 6. Edge cases

### Toate întrebările sunt văzute
Returnezi `None`

### Nu există candidate questions
Returnezi `None`

### Egalitate de distanță
Alegi varianta mai grea

## 7. Testare Task 5

### Test 1 — selecție simplă
- target = 0.55
- întrebări: 0.2, 0.5, 0.8  
Alegi 0.5

### Test 2 — egalitate
- target = 0.5
- întrebări: 0.4, 0.6  
Alegi 0.6

### Test 3 — cea mai bună întrebare e deja văzută
- target = 0.5
- 0.5 este văzută
- 0.6 nu e văzută  
Alegi 0.6

### Test 4 — toate văzute
Returnezi `None`

## 8. Definition of Done

Task-ul este gata când:
- seen questions sunt excluse
- întrebarea aleasă este cea mai apropiată de target
- există tie-break stabil
- `None` este returnat când nu există variante valide
