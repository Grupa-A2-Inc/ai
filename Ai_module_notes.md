# AI Module – Architecture and Explanation (Updated Version)

Acest document explică modulul de AI al aplicației Adaptive Tutor într-un mod clar atât pentru colegii din echipă cât și pentru profesorul îndrumător. Scopul lui este să descrie arhitectura sistemului, rolul fiecărei componente și modul în care sistemul generează o întrebare adaptivă pentru un elev.

Documentul reflectă **varianta actualizată a arhitecturii**, în care:

* elevul alege topicul
* AI-ul generează sau selectează următoarea întrebare pe acel topic
* dificultatea întrebărilor se ajustează în timp pe baza performanței elevilor

---

# 1. Ideea generală a modulului AI

Modulul AI are rolul de a decide **care este următoarea întrebare optimă pentru un elev pe un anumit topic**.

Sistemul nu decide ce topic trebuie studiat. Acest lucru este ales de elev în interfață.

După ce elevul alege topicul, AI-ul analizează istoricul elevului și determină:

* cât de bine stă elevul pe acel topic
* ce dificultate ar trebui să aibă următoarea întrebare
* ce întrebare existentă se potrivește cel mai bine
* dacă este nevoie de generarea unei întrebări noi

În plus, sistemul îmbunătățește în timp estimarea dificultății fiecărei întrebări pe baza datelor reale colectate de la elevi.

---

# 2. Poziția modulului AI în arhitectura aplicației

Arhitectura sistemului este următoarea:

Frontend → Backend principal → AI Service (Django)

Frontend-ul comunică cu backend-ul principal al aplicației.

Backend-ul principal cere AI-ului o recomandare atunci când elevul solicită o întrebare nouă.

AI-ul procesează cererea și returnează întrebarea optimă.

---

# 3. Fluxul complet al unei cereri

Fluxul unei cereri de întrebare nouă este:

1. Elevul alege un topic în interfață
2. Frontend-ul trimite cererea către backend
3. Backend-ul trimite către AI: `user_id`, `subject_id`, `topic_id`
4. AI-ul citește istoricul elevului pe acel topic
5. Se calculează indicatorii de performanță ai elevului
6. Se estimează nivelul elevului pe topic
7. Se estimează dificultatea optimă a următoarei întrebări
8. Se caută o întrebare existentă potrivită
9. Dacă nu există, se generează una nouă
10. Se loghează decizia AI
11. Întrebarea este trimisă înapoi către backend

---

# 4. Structura proiectului Django

```text
adaptive_ai/
└── tutoring/
    ├── models.py
    ├── serializers.py
    ├── views.py
    ├── urls.py

    ├── repositories/
    │   └── student_data_repository.py

    ├── dto/
    │   ├── student_context.py
    │   ├── topic_features.py
    │   ├── mastery_result.py
    │   ├── difficulty_result.py
    │   └── question_recommendation_result.py

    ├── services/
    │   ├── feature_engineering_service.py
    │   ├── mastery_estimator.py
    │   ├── difficulty_estimator.py
    │   ├── question_selection_engine.py
    │   ├── question_generation_engine.py
    │   ├── question_recommendation_engine.py
    │   ├── decision_audit_service.py
    │   ├── explanation_service.py
    │   └── question_difficulty_calibration_service.py

    ├── ml/
    │   ├── dataset_builder.py
    │   ├── model_training_service.py
    │   ├── model_inference_service.py
    │   └── model_registry.py

    └── management/
        └── commands/
            └── train_adaptive_model.py
```

Această structură separă clar responsabilitățile fiecărei componente.

---

# 5. Cum funcționează dificultatea întrebărilor

Fiecare întrebare are două tipuri de dificultate.

## 1️⃣ Dificultatea inițială

Este stabilită manual când întrebarea este creată.

Valorile inițiale sunt:

```
0.2 → easy
0.5 → medium
0.8 → hard
```

Aceasta reprezintă estimarea profesorului sau a creatorului de conținut.

## 2️⃣ Dificultatea observată

Pe măsură ce elevii răspund la întrebări, sistemul colectează date precum:

* câți elevi au răspuns
* câți au răspuns corect
* cât timp au petrecut

Din aceste date se calculează **dificultatea observată**.

Formula simplă este:

```
accuracy_rate = correct_answers / total_answers
observed_difficulty = 1 - accuracy_rate
```

Exemple:

| Corect | Total | Accuracy | Difficulty |
| ------ | ----- | -------- | ---------- |
| 80     | 100   | 0.8      | 0.2        |
| 50     | 100   | 0.5      | 0.5        |
| 20     | 100   | 0.2      | 0.8        |

Astfel sistemul învață cât de grea este de fapt întrebarea.

---

# 6. Dificultatea finală a întrebării

Sistemul folosește o **dificultate efectivă**.

Aceasta combină dificultatea inițială cu cea observată.

```
effective_difficulty = initial_weight * initial_difficulty
                     + observed_weight * observed_difficulty
```

Pe măsură ce întrebarea primește mai multe răspunsuri, greutatea dificultății observate crește.

Acest lucru permite sistemului să corecteze estimările inițiale.

---

# 7. `models.py`

Acest fișier definește structura datelor.

Pentru întrebări sunt salvate informații precum:

* dificultatea inițială
* dificultatea observată
* numărul de răspunsuri
* numărul de răspunsuri corecte
* timpul mediu de rezolvare

Aceste date sunt folosite pentru recalibrarea dificultății.

---

# 8. `StudentDataRepository`

Această clasă se ocupă cu accesul la baza de date.

Ea citește informațiile necesare pentru AI:

* istoricul elevului
* răspunsurile recente
* întrebările deja văzute
* întrebările disponibile

Rolul ei este să centralizeze toate query-urile importante.

---

# 9. `FeatureEngineeringService`

Această componentă transformă datele brute în indicatori utili.

Exemple de indicatori calculați:

* acuratețea răspunsurilor
* scorurile recente la teste
* timpul mediu pe întrebare
* numărul de încercări

Acești indicatori sunt folosiți pentru estimarea nivelului elevului.

---

# 10. `MasteryEstimator`

Această componentă estimează nivelul elevului pe topic.

Scorul de mastery reprezintă cât de bine stă elevul pe acel topic.

Există două variante:

* rule-based (reguli simple)
* model-based (folosind ML)

---

# 11. `QuestionSelectionEngine`

Această componentă caută o întrebare existentă în banca de întrebări.

Selecția se face pe baza:

* topicului
* dificultății dorite
* întrebărilor deja văzute

Sistemul alege întrebarea cu **dificultatea efectivă cea mai apropiată de dificultatea țintă**.

Update : Putem alege nivelul dificultatii tinta la o distanta fixa in modul fata de nivelul de mastery al elevului. De exemplu, daca elevul are mastery 0.4, putem seta dificultatea tinta la 0.5 sau 0.6 pentru a-l provoca sa invete.
Daca nu exista putem apela la QuestionGenerationEngine.
---

# 12. `QuestionGenerationEngine`

Dacă nu există o întrebare potrivită în bancă, sistemul poate genera una nouă.

În prima versiune generarea poate folosi template-uri.

În versiuni viitoare se poate folosi un model AI generativ.

---

# 13. `QuestionRecommendationEngine`

Aceasta este componenta centrală a sistemului.

Ea coordonează întregul proces.

Fluxul intern este:

1. construiește feature-urile
2. estimează mastery
3. estimează dificultatea
4. selectează întrebare
5. generează întrebare dacă este nevoie
6. loghează decizia

---

# 14. `QuestionDifficultyCalibrationService`

Această componentă actualizează dificultatea întrebărilor pe baza datelor reale.

Ea calculează:

* rata de răspuns corect
* dificultatea observată
* dificultatea efectivă

Acest proces poate fi rulat periodic sau după acumularea unui număr suficient de răspunsuri.

---

# 15. `DecisionAuditService`

Această componentă salvează deciziile luate de AI.

Sunt salvate informații precum:

* întrebarea recomandată
* motivul alegerii
* dificultatea estimată
* sursa deciziei

Acest lucru ajută la debugging și analiză.

---

# 16. Stratul de Machine Learning

Stratul ML permite îmbunătățirea sistemului în timp.

Componentele principale sunt:

### `DatasetBuilder`

Construiește dataset-ul pentru antrenarea modelului.

### `ModelTrainingService`

Antrenează modelul folosind datele istorice.

### `ModelInferenceService`

Folosește modelul pentru predicții în producție.

### `ModelRegistry`

Gestionează versiunea modelelor.

---

# 17. Avantajele arhitecturii

Această arhitectură oferă mai multe beneficii:

* separarea clară a responsabilităților
* ușurință în extinderea sistemului
* posibilitatea integrării ML
* transparență în deciziile AI

---

# 18. Rezumat final

Modulul AI primește un topic ales de elev și decide care este **următoarea întrebare optimă** pentru acel elev.

Decizia se bazează pe:

* istoricul elevului
* estimarea nivelului de înțelegere
* dificultatea optimă pentru învățare
* dificultatea reală a întrebărilor observată în timp

Prin acest mecanism sistemul oferă **adaptive learning**, adică fiecare elev primește întrebări potrivite nivelului său.

Pe măsură ce sistemul colectează mai multe date, estimările devin mai precise și experiența de învățare devine mai personalizată.
