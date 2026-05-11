#!/usr/bin/env bash
set -Eeuo pipefail

# Retrains the global mastery model from accumulated StudentInteraction rows.
# Schedule this script with cron/systemd timer on the server; it is safe to run
# while the app is online because the final model replacement is atomic.

APP_DIR="${APP_DIR:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
PYTHON_BIN="${PYTHON_BIN:-$APP_DIR/.venv/bin/python}"

DATASET_PATH="${DATASET_PATH:-$APP_DIR/data/training/student_mastery_dataset.csv}"
MODEL_PATH="${MASTERY_MODEL_PATH:-${MODEL_PATH:-$APP_DIR/tutoring/models_store/mastery_model.pkl}}"
export MASTERY_MODEL_PATH="$MODEL_PATH"
MIN_ROWS="${MIN_ROWS:-100}"

RUN_DIR="${RUN_DIR:-$APP_DIR/tmp/model_training}"
LOG_DIR="${LOG_DIR:-$APP_DIR/logs}"
LOCK_FILE="${LOCK_FILE:-$RUN_DIR/retrain_mastery_model.lock}"

mkdir -p "$RUN_DIR" "$LOG_DIR" "$(dirname "$DATASET_PATH")" "$(dirname "$MODEL_PATH")"

TIMESTAMP="$(date -u +"%Y%m%dT%H%M%SZ")"
LOG_FILE="$LOG_DIR/retrain_mastery_model_$TIMESTAMP.log"
DATASET_DIR="$(dirname "$DATASET_PATH")"
MODEL_DIR="$(dirname "$MODEL_PATH")"
TMP_DATASET="$DATASET_DIR/.student_mastery_dataset_$TIMESTAMP.tmp.csv"
TMP_MODEL="$MODEL_DIR/.mastery_model_$TIMESTAMP.tmp.pkl"
PUBLISHED=0

log() {
    printf '[%s] %s\n' "$(date -u +"%Y-%m-%dT%H:%M:%SZ")" "$*"
}

fail() {
    log "ERROR: $*"
    exit 1
}

cleanup() {
    if [[ "$PUBLISHED" != "1" ]]; then
        rm -f "$TMP_DATASET" "$TMP_MODEL"
    fi
}

trap cleanup EXIT

exec > >(tee -a "$LOG_FILE") 2>&1
exec 9>"$LOCK_FILE"

if ! flock -n 9; then
    log "Another retraining job is already running. Exiting."
    exit 0
fi

cd "$APP_DIR"

log "Starting mastery model retraining"
log "APP_DIR=$APP_DIR"
log "PYTHON_BIN=$PYTHON_BIN"
log "DATASET_PATH=$DATASET_PATH"
log "MASTERY_MODEL_PATH=$MASTERY_MODEL_PATH"

[[ -x "$PYTHON_BIN" ]] || fail "Python executable not found or not executable: $PYTHON_BIN"

log "Exporting training dataset from StudentInteraction"
"$PYTHON_BIN" manage.py export_training_dataset --output "$TMP_DATASET"

ROW_COUNT="$("$PYTHON_BIN" -c "import pandas as pd; import sys; print(len(pd.read_csv(sys.argv[1])))" "$TMP_DATASET")"
log "Exported dataset rows: $ROW_COUNT"

if (( ROW_COUNT < MIN_ROWS )); then
    fail "Dataset has $ROW_COUNT rows, below MIN_ROWS=$MIN_ROWS. Keeping existing model."
fi

log "Training candidate models and selecting best model"
"$PYTHON_BIN" manage.py train_mastery_model \
    --dataset "$TMP_DATASET" \
    --output "$TMP_MODEL"

[[ -s "$TMP_MODEL" ]] || fail "Training did not create a non-empty model file: $TMP_MODEL"

log "Validating trained model can be loaded and used for prediction"
"$PYTHON_BIN" -c '
import joblib
import pandas as pd
import sys

model_path = sys.argv[1]
model = joblib.load(model_path)
sample = pd.DataFrame([{
    "subject_id": 2,
    "topic_id": 1102,
    "question_difficulty": 0.5,
    "score": 0.5,
    "is_correct": 0,
    "time_spent": 60.0,
    "normalized_time": 0.5,
    "attempt_count_on_topic": 12,
    "average_score_on_topic": 0.5,
    "average_time_on_topic": 60.0,
    "normalized_average_time": 0.5,
    "recent_average_score": 0.5,
    "recent_average_time": 60.0,
    "normalized_recent_time": 0.5,
    "current_mastery": 0.5,
}])
prediction = float(model.predict(sample)[0])
if not 0.0 <= prediction <= 1.0:
    raise SystemExit(f"Prediction out of range: {prediction}")
print(f"Validation prediction: {prediction:.4f}")
' "$TMP_MODEL"

log "Publishing new dataset and model atomically"
mv "$TMP_DATASET" "$DATASET_PATH"
mv "$TMP_MODEL" "$MODEL_PATH"
PUBLISHED=1

log "Mastery model retraining completed successfully"
