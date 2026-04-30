# S5-02 — Train ML Models for Student Mastery Prediction

## Description

Acest task are scopul de a antrena primul model de Machine Learning pentru estimarea nivelului unui elev pe un anumit topic.

Modelul va fi antrenat pe datasetul exportat în Task 1:

`data/training/student_mastery_dataset.csv`

Taskul acesta se ocupă de partea de training:
```
dataset CSV
    ↓
preprocesare features
    ↓
antrenare modele ML
    ↓
comparare performanță
    ↓
alegere model final
    ↓
salvare model
```

## Goal

La finalul taskului trebuie să avem:
```
un model ML antrenat
un script de training
un fișier .pkl salvat
metrici de evaluare
o metodă clară de trial and error
```
Output final:

`models/mastery_model.pkl`

# What the Model Predicts

Modelul trebuie să prezică:

`target_mastery`

Adică nivelul estimat al elevului pe un topic.

Valoarea trebuie să fie între:

`0.0 și 1.0`

Exemplu:
```
0.2 = elev slab pe topic
0.5 = nivel mediu
0.8 = elev bun pe topic
```

# Input Dataset

Datasetul vine din Task 1 și are coloane de forma:

`student_id,subject_id,topic_id,question_id,question_difficulty,score,is_correct,time_spent,normalized_time,attempt_count_on_topic,average_score_on_topic,average_time_on_topic,normalized_average_time,recent_average_score,recent_average_time,normalized_recent_time,current_mastery,target_mastery`


# Model Selection

În acest task nu antrenăm direct un singur model și gata.

Trebuie să testăm mai multe modele simple și să alegem cel mai bun pe baza metricilor.

Aceasta este partea de trial and error.

## Models to Try

Pentru început, recomandăm 3 modele:
```
1. LinearRegression
2. RandomForestRegressor
3. GradientBoostingRegressor
```

## 1. Linear Regression
Ce este

Un model simplu, liniar.

Încearcă să găsească o formulă de forma:

`target_mastery = a1 * feature1 + a2 * feature2 + ... + b`

Avantaje
- simplu
- rapid
- ușor de explicat profesorului
- bun ca baseline
Dezavantaje
- poate fi prea simplu
- nu prinde relații complexe
De ce îl folosim

Îl folosim ca model de bază.

Dacă modelele mai complexe nu sunt mai bune decât LinearRegression, înseamnă că datasetul este încă simplu sau prea mic.

## 2. RandomForestRegressor
Ce este

Un model bazat pe mai mulți arbori de decizie.

Fiecare arbore încearcă să facă o predicție, iar modelul combină rezultatele.

Avantaje
- bun pentru date tabulare
- prinde relații non-liniare
- nu are nevoie de scalare agresivă
- merge bine pentru MVP-uri
Dezavantaje
- mai greu de explicat decât LinearRegression
- poate overfit-ui dacă datasetul este mic
De ce îl folosim

Este probabil cel mai bun candidat pentru prima versiune serioasă a modelului vostru.

## 3. GradientBoostingRegressor
Ce este

Un model bazat pe arbori, dar antrenați secvențial.

Fiecare arbore încearcă să repare greșelile celui anterior.

Avantaje
- foarte bun pe date tabulare
- poate avea performanță mai bună decât RandomForest
Dezavantaje
- mai sensibil la hiperparametri
- poate overfit-ui
- mai complicat pentru început
De ce îl folosim

Îl testăm ca variantă mai avansată.

Dacă performează mai bine, îl putem păstra. Dacă nu, rămânem pe RandomForest.

# Evaluation Metrics

Pentru că prezicem o valoare numerică între 0 și 1, problema este de tip:

`regression`

Deci folosim metrici de regresie.

# MAE — Mean Absolute Error

Formula conceptuală:

`media erorilor absolute`

Exemplu:
```
predicted = 0.70
actual = 0.60
error = 0.10
```

MAE este ușor de explicat:

în medie, modelul greșește cu 0.08 puncte de mastery
Interpretare
```
MAE = 0.05 → foarte bine
MAE = 0.10 → acceptabil
MAE = 0.20 → slab
MSE — Mean Squared Error
```

# MSE — Mean Squared Error

Penalizează mai tare erorile mari.

Este util pentru comparație, dar MAE este mai ușor de explicat.

# R2 Score

Arată cât de bine explică modelul variația din date.
```
R2 aproape de 1 → bine
R2 aproape de 0 → slab
R2 negativ → foarte slab
```
Pentru început, nu ne bazăm doar pe R2, pentru că datasetul poate fi artificial sau mic.

# Trial and Error Strategy

Trainingul ML nu este o singură încercare.

Trebuie să facem mai multe experimente și să comparăm rezultatele.

## Experiment 1 — Baseline

Primul experiment:
```
LinearRegression
features de bază
```
Scop:

să avem un baseline

Dacă MAE este 0.15, știm că orice model mai complex trebuie să fie mai bun decât 0.15.

## Experiment 2 — RandomForest

Al doilea experiment:

```RandomForestRegressor```

Comparam MAE cu baseline-ul.

Dacă RandomForest are MAE mai mic, îl preferăm.

## Experiment 3 — GradientBoosting

Al treilea experiment:

```GradientBoostingRegressor```

Comparam cu RandomForest.

## Experiment 4 — Feature Selection

Încercăm să eliminăm sau să adăugăm features.

De exemplu:
``` 
Set A — Basic features
subject_id
topic_id
question_difficulty
score
time_spent
current_mastery
``` 

```
Set B — Add historical features
attempt_count_on_topic
average_score_on_topic
average_time_on_topic
``` 

```
Set C — Add recent trend features
recent_average_score
recent_average_time
normalized_recent_time
```
Apoi comparăm rezultatele.

## Experiment 5 — Hyperparameter Tuning

Pentru RandomForest putem încerca:
``` 
n_estimators = 50, 100, 200
max_depth = None, 5, 10
min_samples_split = 2, 5, 10
``` 
Nu trebuie exagerat în Sprint 5.

Scopul este să avem un model funcțional, nu cel mai perfect model posibil.

# File Structure

Se recomandă următoarea structură:
``` 
tutoring/
├── ml/
│   ├── train_mastery_model.py
│   ├── mastery_model_config.py
│   └── mastery_model_loader.py
│
├── models_store/
│   └── mastery_model.pkl
│
└── management/
    └── commands/
        └── train_mastery_model.py
```

# Installs 

```
pandas
scikit-learn
joblib 
```

# Step 2 — Training Script

Creează fișierul:

`tutoring/ml/train_mastery_model.py`

Cod:
```py 
from pathlib import Path

import joblib
import pandas as pd

from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import train_test_split


class MasteryModelTrainer:
    TARGET_COLUMN = "target_mastery"

    FEATURE_COLUMNS = [
        "subject_id",
        "topic_id",
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
    ]

    def train(
        self,
        dataset_path: str,
        model_output_path: str,
    ) -> dict:
        dataset = self._load_dataset(dataset_path)

        self._validate_dataset(dataset)

        features = dataset[self.FEATURE_COLUMNS]
        target = dataset[self.TARGET_COLUMN]

        x_train, x_test, y_train, y_test = train_test_split(
            features,
            target,
            test_size=0.2,
            random_state=42,
        )

        candidate_models = self._build_candidate_models()

        results = []

        for model_name, model in candidate_models.items():
            model.fit(x_train, y_train)

            predictions = model.predict(x_test)
            predictions = self._clamp_predictions(predictions)

            metrics = self._calculate_metrics(
                y_true=y_test,
                y_pred=predictions,
            )

            results.append(
                {
                    "name": model_name,
                    "model": model,
                    "metrics": metrics,
                }
            )

        best_result = self._select_best_model(results)

        self._save_model(
            model=best_result["model"],
            output_path=model_output_path,
        )

        return {
            "best_model": best_result["name"],
            "metrics": best_result["metrics"],
            "all_results": [
                {
                    "name": result["name"],
                    "metrics": result["metrics"],
                }
                for result in results
            ],
        }

    def _load_dataset(self, dataset_path: str) -> pd.DataFrame:
        return pd.read_csv(dataset_path)

    def _validate_dataset(self, dataset: pd.DataFrame) -> None:
        missing_columns = []

        for column in self.FEATURE_COLUMNS + [self.TARGET_COLUMN]:
            if column not in dataset.columns:
                missing_columns.append(column)

        if missing_columns:
            raise ValueError(
                f"Dataset is missing required columns: {missing_columns}"
            )

        if dataset.empty:
            raise ValueError("Dataset is empty. Cannot train ML model.")

    def _build_candidate_models(self) -> dict:
        return {
            "linear_regression": LinearRegression(),
            "random_forest": RandomForestRegressor(
                n_estimators=100,
                max_depth=10,
                random_state=42,
            ),
            "gradient_boosting": GradientBoostingRegressor(
                random_state=42,
            ),
        }

    def _calculate_metrics(self, y_true, y_pred) -> dict:
        return {
            "mae": mean_absolute_error(y_true, y_pred),
            "mse": mean_squared_error(y_true, y_pred),
            "r2": r2_score(y_true, y_pred),
        }

    def _select_best_model(self, results: list[dict]) -> dict:
        return min(
            results,
            key=lambda result: result["metrics"]["mae"],
        )

    def _save_model(self, model, output_path: str) -> None:
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        joblib.dump(model, output_file)

    def _clamp_predictions(self, predictions):
        return [
            max(0.0, min(float(prediction), 1.0))
            for prediction in predictions
        ]
```

# Step 3 — Management Command

Creează fișierul:

`tutoring/management/commands/train_mastery_model.py`

Cod:

```py  
from django.core.management.base import BaseCommand

from tutoring.ml.train_mastery_model import MasteryModelTrainer


class Command(BaseCommand):
    help = "Train ML mastery model from exported dataset."

    def add_arguments(self, parser):
        parser.add_argument(
            "--dataset",
            type=str,
            default="data/training/student_mastery_dataset.csv",
        )

        parser.add_argument(
            "--output",
            type=str,
            default="tutoring/models_store/mastery_model.pkl",
        )

    def handle(self, *args, **options):
        dataset_path = options["dataset"]
        output_path = options["output"]

        trainer = MasteryModelTrainer()

        result = trainer.train(
            dataset_path=dataset_path,
            model_output_path=output_path,
        )

        self.stdout.write(
            self.style.SUCCESS(
                f"Best model: {result['best_model']}"
            )
        )

        self.stdout.write(
            self.style.SUCCESS(
                f"Metrics: {result['metrics']}"
            )
        )

        self.stdout.write(
            self.style.SUCCESS(
                f"Model saved to {output_path}"
            )
        )

        self.stdout.write("All model results:")

        for model_result in result["all_results"]:
            self.stdout.write(
                f"{model_result['name']}: {model_result['metrics']}"
            )
```

# Step 4 — How to Run Training

Mai întâi exporți datasetul:

`python manage.py export_training_dataset`

Apoi antrenezi modelul:

`python manage.py train_mastery_model`

Sau cu path explicit:

```
python manage.py train_mastery_model \
  --dataset data/training/student_mastery_dataset.csv \
  --output tutoring/models_store/mastery_model.pkl
Step 5 — Expected Output
```

În terminal ar trebui să vezi ceva de forma:
```
Best model: random_forest
Metrics: {'mae': 0.07, 'mse': 0.01, 'r2': 0.82}
Model saved to tutoring/models_store/mastery_model.pkl

All model results:
linear_regression: {'mae': 0.12, 'mse': 0.03, 'r2': 0.55}
random_forest: {'mae': 0.07, 'mse': 0.01, 'r2': 0.82}
gradient_boosting: {'mae': 0.08, 'mse': 0.02, 'r2': 0.78}
Step 6 — How We Choose the Best Model
```

Pentru Sprint 5, alegem modelul cu cel mai mic:

`MAE`

Motiv:

`MAE este ușor de interpretat`

Exemplu:

`MAE = 0.08`

înseamnă:

`modelul greșește în medie cu 0.08 puncte de mastery`

Pentru mastery între 0 și 1, asta este acceptabil pentru început.


### (Asta zice GPT dar mai faceti voi putin research si vedeti si celelalte MSE si R2 ce am scris mai sus pe acolo)
### Nu luat direct MAE. faceti teste si interpretati rezultatele, puteti incerca pe urmatoarele saptamani si alte modele.

# Step 7 — Trial and Error Process

Trial and error înseamnă că nu presupunem din start că un model este cel mai bun.

Testăm, comparăm, schimbăm și repetăm.

`Trial 1 — Basic Model`

Rulezi cu `LinearRegression`.

Scop:

baseline

Dacă MAE este mare, știm că avem nevoie de model mai complex.

`Trial 2 — RandomForest`

Rulezi cu RandomForest.

Dacă MAE scade, modelul este mai bun.

`Trial 3 — GradientBoosting`

Rulezi cu GradientBoosting.

Comparam cu RandomForest.

`Trial 4 — Change Features`

Poți încerca să scoți sau să adaugi features.

Exemplu:
```
fără recent_average_score
cu recent_average_score
fără time_spent
cu time_spent
```

Dacă un feature înrăutățește performanța, îl eliminăm.

`Trial 5 — Change Hyperparameters`

Pentru RandomForest poți testa:

```
RandomForestRegressor(n_estimators=50, max_depth=5)
RandomForestRegressor(n_estimators=100, max_depth=10)
RandomForestRegressor(n_estimators=200, max_depth=None)
```
Comparam MAE.

# Step 8 — Model Loader

Pentru Task 3, unde modelul va fi integrat în engine, este util să avem un loader.

Creează fișierul:

`tutoring/ml/mastery_model_loader.py`

Cod:
```py 
from pathlib import Path

import joblib


class MasteryModelLoader:
    def __init__(
        self,
        model_path: str = "tutoring/models_store/mastery_model.pkl",
    ):
        self.model_path = Path(model_path)
        self._model = None

    def load(self):
        if self._model is not None:
            return self._model

        if not self.model_path.exists():
            return None

        self._model = joblib.load(self.model_path)

        return self._model
 ```

Acest loader nu este încă responsabil să facă predicții. El doar încarcă modelul.

Predicția va fi făcută în Task 3, prin MLMasteryEstimator.

# Step 10 — Tests

Creează fișierul:

`tutoring/tests/test_mastery_model_trainer.py`

Cod:

```py 
from pathlib import Path
import tempfile

import pandas as pd
from django.test import TestCase

from tutoring.ml.train_mastery_model import MasteryModelTrainer


class MasteryModelTrainerTests(TestCase):
    def test_train_saves_model_file(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            dataset_path = Path(temporary_directory) / "dataset.csv"
            model_path = Path(temporary_directory) / "mastery_model.pkl"

            dataset = pd.DataFrame(
                [
                    {
                        "subject_id": 2,
                        "topic_id": 1102,
                        "question_difficulty": 0.5,
                        "score": 1.0,
                        "is_correct": 1,
                        "time_spent": 40.0,
                        "normalized_time": 0.33,
                        "attempt_count_on_topic": 1,
                        "average_score_on_topic": 0.8,
                        "average_time_on_topic": 45.0,
                        "normalized_average_time": 0.37,
                        "recent_average_score": 0.8,
                        "recent_average_time": 45.0,
                        "normalized_recent_time": 0.37,
                        "current_mastery": 0.5,
                        "target_mastery": 0.6,
                    },
                    {
                        "subject_id": 2,
                        "topic_id": 1102,
                        "question_difficulty": 0.7,
                        "score": 0.0,
                        "is_correct": 0,
                        "time_spent": 90.0,
                        "normalized_time": 0.75,
                        "attempt_count_on_topic": 2,
                        "average_score_on_topic": 0.5,
                        "average_time_on_topic": 65.0,
                        "normalized_average_time": 0.54,
                        "recent_average_score": 0.5,
                        "recent_average_time": 65.0,
                        "normalized_recent_time": 0.54,
                        "current_mastery": 0.6,
                        "target_mastery": 0.52,
                    },
                    {
                        "subject_id": 3,
                        "topic_id": 1201,
                        "question_difficulty": 0.3,
                        "score": 1.0,
                        "is_correct": 1,
                        "time_spent": 30.0,
                        "normalized_time": 0.25,
                        "attempt_count_on_topic": 3,
                        "average_score_on_topic": 0.9,
                        "average_time_on_topic": 35.0,
                        "normalized_average_time": 0.29,
                        "recent_average_score": 0.9,
                        "recent_average_time": 35.0,
                        "normalized_recent_time": 0.29,
                        "current_mastery": 0.7,
                        "target_mastery": 0.75,
                    },
                    {
                        "subject_id": 3,
                        "topic_id": 1201,
                        "question_difficulty": 0.8,
                        "score": 0.5,
                        "is_correct": 0,
                        "time_spent": 100.0,
                        "normalized_time": 0.83,
                        "attempt_count_on_topic": 4,
                        "average_score_on_topic": 0.6,
                        "average_time_on_topic": 70.0,
                        "normalized_average_time": 0.58,
                        "recent_average_score": 0.6,
                        "recent_average_time": 70.0,
                        "normalized_recent_time": 0.58,
                        "current_mastery": 0.55,
                        "target_mastery": 0.53,
                    },
                    {
                        "subject_id": 4,
                        "topic_id": 1301,
                        "question_difficulty": 0.4,
                        "score": 1.0,
                        "is_correct": 1,
                        "time_spent": 25.0,
                        "normalized_time": 0.2,
                        "attempt_count_on_topic": 5,
                        "average_score_on_topic": 0.85,
                        "average_time_on_topic": 32.0,
                        "normalized_average_time": 0.26,
                        "recent_average_score": 0.85,
                        "recent_average_time": 32.0,
                        "normalized_recent_time": 0.26,
                        "current_mastery": 0.65,
                        "target_mastery": 0.72,
                    },
                ]
            )

            dataset.to_csv(dataset_path, index=False)

            trainer = MasteryModelTrainer()

            result = trainer.train(
                dataset_path=str(dataset_path),
                model_output_path=str(model_path),
            )

            self.assertTrue(model_path.exists())
            self.assertIn("best_model", result)
            self.assertIn("metrics", result)
            self.assertIn("all_results", result)
```

Definition of Done

Task-ul este gata când:
```
- există training script
- training script citește datasetul exportat
- sunt testate minim 3 modele
- se calculează MAE, MSE și R2
- se alege modelul cu cel mai mic MAE
- modelul este salvat în models_store/mastery_model.pkl
- există management command pentru training
- există model loader
- există teste pentru training
- echipa înțelege procesul de trial and error
```
Summary

Task 2 antrenează primul model ML global pentru estimarea mastery-ului elevului.

Nu alegem modelul din burtă.

Testăm mai multe modele:
```
LinearRegression
RandomForestRegressor
GradientBoostingRegressor
```
Le comparăm folosind:

```
MAE
MSE
R2
```

Alegem modelul cu cel mai bun MAE și îl salvăm pentru folosire în Task 3.