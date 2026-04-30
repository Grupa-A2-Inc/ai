# S5-03 — Integrate ML Model into Recommendation Engine

Adică: după ce Task1 face dataset-ul și Task2 antrenează modelul, Task3 trebuie să bage modelul ML în flow-ul real de recomandare.

Până acum engine-ul tău funcționează așa:
```
StudentDataRepository
        ↓
FeatureEngineeringService
        ↓
MasteryEstimator rule-based
        ↓
DifficultyEstimator
        ↓
QuestionSelectionEngine

În Task3, flow-ul devine:

StudentDataRepository
        ↓
FeatureEngineeringService
        ↓
decizie: rule-based sau ML
        ↓
MLMasteryEstimator / RuleBasedMasteryEstimator
        ↓
DifficultyEstimator
        ↓
QuestionSelectionEngine
Ideea principală
```

Nu arunci engine-ul vechi. Îl modifici controlat astfel încât:
```
dacă elevul are sub 10 interacțiuni pe topic → rule-based
dacă elevul are 10+ interacțiuni pe topic și modelul există → ML
dacă modelul ML nu există / crapă → fallback rule-based
```
Asta înseamnă că aplicația rămâne stabilă chiar dacă modelul ML nu e antrenat încă.

Ce trebuie implementat
## 1. MLMasteryEstimator

Fișier recomandat:

`tutoring/services/ml_mastery_estimator.py`

Rolul lui:
```
primește features
încarcă modelul salvat în Task2
face predict
returnează mastery_score între 0 și 1
```
Exemplu conceptual:
```py  
class MLMasteryEstimator:
    def estimate(self, features):
        model = self.model_loader.load()

        if model is None:
            raise ModelNotAvailableError()

        input_row = self._build_model_input(features)

        prediction = model.predict(input_row)[0]
        prediction = max(0.0, min(float(prediction), 1.0))

        return MasteryResult(mastery_score=prediction)
``` 

## 2. MasteryStrategySelector

Fișier recomandat:

`tutoring/services/mastery_strategy_selector.py`

Rolul lui:

decide dacă folosim ML sau rule-based

Regula:
```py 
if attempt_count_on_topic < 10:
    return "rule_based"

if ml_model_is_missing:
    return "rule_based"
``` 
return "ml"

Asta e important pentru cold start.

## 3. Modificare în QuestionRecommendationEngine

Engine-ul nu mai apelează direct doar:

`self.mastery_estimator.estimate(features)`

ci face:
```
strategy = self.strategy_selector.select(normalized_features)

if strategy == "ml":
    mastery_result = self.ml_mastery_estimator.estimate(normalized_features)
else:
    mastery_result = self.rule_based_mastery_estimator.estimate(normalized_features)
```
Deci engine-ul devine hybrid:

rule-based + ML
## 4. Fallback dacă ML crapă

Foarte important.

Dacă fișierul:

`tutoring/models_store/mastery_model.pkl`

nu există sau modelul dă eroare, sistemul nu trebuie să crape.

Trebuie să facă:
```
try:
    mastery_result = self.ml_mastery_estimator.estimate(features)
except Exception:
    mastery_result = self.rule_based_mastery_estimator.estimate(features)
```
Asta este obligatoriu pentru demo.

Cum se folosește modelul ML

La runtime, când backend-ul cere:

`POST /api/adaptive/exercises`

Task3 din Sprint 4 apelează:

`QuestionRecommendationEngine.recommend(...)`

În interiorul engine-ului, după Task3 Sprint 5, se întâmplă:
```
1. se construiește contextul elevului
2. se calculează features
3. se verifică attempt_count_on_topic
4. dacă are sub 10 răspunsuri → rule-based
5. dacă are 10+ răspunsuri → ML predict
6. se calculează target difficulty
7. se alege întrebarea
Ce NU face Task3
``` 
Task3 NU trebuie să:
```
antreneze modelul
exporte dataset
genereze întrebări cu LLM
modifice endpointul de feedback
rescrie QuestionSelectionEngine
```

Trainingul este Task2. LLM-ul este Task4. Task3 doar integrează modelul antrenat în engine.

# Definition of Done

Task3 e gata când:
```
- există MLMasteryEstimator
- există strategie rule-based vs ML
- engine-ul folosește ML doar după 10 interacțiuni pe topic
- engine-ul face fallback la rule-based dacă modelul lipsește
- endpointul /api/adaptive/exercises funcționează fără schimbări mari
- testele vechi încă trec
- există teste pentru:
  - sub 10 interacțiuni → rule-based
  - 10+ interacțiuni + model disponibil → ML
  - model lipsă → rule-based fallback
``` 
Pe scurt:

Task1 = construiește dataset
Task2 = antrenează model
Task3 = pune modelul în engine