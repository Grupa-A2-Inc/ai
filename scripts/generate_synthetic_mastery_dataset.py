import argparse
import csv
import random
from pathlib import Path


MAX_TIME = 120.0

FIELDNAMES = [
    "student_id",
    "subject_id",
    "topic_id",
    "question_id",
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
    "target_mastery",
]


TOPICS_BY_SUBJECT = {
    1: [101, 102, 103, 104, 105],
    2: [1101, 1102, 1103, 1104, 1105],
    3: [1201, 1202, 1203, 1204, 1205],
    4: [1301, 1302, 1303, 1304, 1305],
}


def clamp(value: float) -> float:
    return max(0.0, min(float(value), 1.0))


def normalized_time(time_spent: float) -> float:
    return clamp(time_spent / MAX_TIME)


def sigmoid(value: float) -> float:
    return 1 / (1 + 2.718281828 ** (-value))


def target_mastery(
    current_mastery: float,
    average_score: float,
    normalized_average_time: float,
) -> float:
    performance_mastery = (
        0.7 * average_score
        + 0.3 * (1 - normalized_average_time)
    )
    return clamp(0.8 * current_mastery + 0.2 * performance_mastery)


def choose_score(
    rng: random.Random,
    ability: float,
    difficulty: float,
) -> float:
    success_probability = sigmoid((ability - difficulty) * 7.0)
    roll = rng.random()

    if roll < success_probability:
        return 1.0
    if roll < success_probability + 0.18:
        return 0.5
    return 0.0


def choose_time(
    rng: random.Random,
    ability: float,
    difficulty: float,
    score: float,
) -> float:
    challenge = clamp(difficulty - ability + 0.5)
    base_time = 25 + 70 * challenge

    if score == 1.0:
        base_time -= 12
    elif score == 0.0:
        base_time += 18

    return round(max(8.0, min(base_time + rng.gauss(0, 9), 120.0)), 2)


def build_rows(
    student_count: int,
    interactions_per_topic: int,
    seed: int,
) -> list[dict]:
    rng = random.Random(seed)
    rows = []

    for student_index in range(1, student_count + 1):
        student_id = f"synthetic-student-{student_index:04d}"
        base_ability = clamp(rng.betavariate(4, 4))

        for subject_id, topic_ids in TOPICS_BY_SUBJECT.items():
            subject_bias = rng.uniform(-0.12, 0.12)

            for topic_id in topic_ids:
                topic_ability = clamp(
                    base_ability + subject_bias + rng.uniform(-0.2, 0.2)
                )
                current_mastery = clamp(0.5 + rng.uniform(-0.08, 0.08))
                previous_scores = []
                previous_times = []

                for attempt_index in range(interactions_per_topic):
                    difficulty = clamp(
                        rng.triangular(0.15, 0.95, current_mastery)
                        + rng.uniform(-0.08, 0.08)
                    )
                    score = choose_score(
                        rng=rng,
                        ability=topic_ability,
                        difficulty=difficulty,
                    )
                    time_spent = choose_time(
                        rng=rng,
                        ability=topic_ability,
                        difficulty=difficulty,
                        score=score,
                    )

                    average_score = (
                        sum(previous_scores) / len(previous_scores)
                        if previous_scores else 0.5
                    )
                    average_time = (
                        sum(previous_times) / len(previous_times)
                        if previous_times else 60.0
                    )

                    recent_scores = previous_scores[-5:]
                    recent_times = previous_times[-5:]
                    recent_average_score = (
                        sum(recent_scores) / len(recent_scores)
                        if recent_scores else average_score
                    )
                    recent_average_time = (
                        sum(recent_times) / len(recent_times)
                        if recent_times else average_time
                    )

                    target = target_mastery(
                        current_mastery=current_mastery,
                        average_score=average_score,
                        normalized_average_time=normalized_time(average_time),
                    )

                    question_id = (
                        subject_id * 1_000_000
                        + topic_id * 100
                        + (attempt_index % 100)
                    )

                    rows.append(
                        {
                            "student_id": student_id,
                            "subject_id": subject_id,
                            "topic_id": topic_id,
                            "question_id": question_id,
                            "question_difficulty": round(difficulty, 4),
                            "score": score,
                            "is_correct": 1 if score == 1.0 else 0,
                            "time_spent": time_spent,
                            "normalized_time": round(normalized_time(time_spent), 4),
                            "attempt_count_on_topic": len(previous_scores),
                            "average_score_on_topic": round(average_score, 4),
                            "average_time_on_topic": round(average_time, 4),
                            "normalized_average_time": round(
                                normalized_time(average_time),
                                4,
                            ),
                            "recent_average_score": round(recent_average_score, 4),
                            "recent_average_time": round(recent_average_time, 4),
                            "normalized_recent_time": round(
                                normalized_time(recent_average_time),
                                4,
                            ),
                            "current_mastery": round(current_mastery, 4),
                            "target_mastery": round(target, 4),
                        }
                    )

                    previous_scores.append(score)
                    previous_times.append(time_spent)
                    current_mastery = clamp(
                        0.82 * current_mastery
                        + 0.18 * (0.75 * score + 0.25 * (1 - normalized_time(time_spent)))
                    )

    rng.shuffle(rows)
    return rows


def write_dataset(output_path: Path, rows: list[dict]) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open("w", newline="", encoding="utf-8") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate a deterministic synthetic mastery training dataset."
    )
    parser.add_argument(
        "--output",
        default="data/training/student_mastery_dataset.csv",
    )
    parser.add_argument("--students", type=int, default=120)
    parser.add_argument("--interactions-per-topic", type=int, default=18)
    parser.add_argument("--seed", type=int, default=42)

    args = parser.parse_args()

    rows = build_rows(
        student_count=args.students,
        interactions_per_topic=args.interactions_per_topic,
        seed=args.seed,
    )
    output_path = Path(args.output)
    write_dataset(output_path=output_path, rows=rows)

    print(f"Wrote {len(rows)} rows to {output_path}")


if __name__ == "__main__":
    main()
