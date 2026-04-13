from __future__ import annotations

import csv
import random
import re
from pathlib import Path

from app.api.v1.schemas import QuestionExample, QuestionOut

_CSV_PATH = Path(__file__).resolve().parent.parent / "db" / "leetcode_dataset - lc.csv"

_questions_by_id: dict[int, QuestionOut] = {}
_questions_list: list[QuestionOut] = []
_loaded = False


def _parse_examples(description: str) -> tuple[str, list[QuestionExample], list[str]]:
    """Extract the prose description, examples, and constraints from a LeetCode description block."""
    lines = description.split("\n")

    prose_lines: list[str] = []
    examples: list[QuestionExample] = []
    constraints: list[str] = []

    section = "prose"
    current_example: dict[str, str | None] = {"input": "", "output": "", "explanation": None}

    for line in lines:
        stripped = line.strip()

        if re.match(r"^Example\s*\d", stripped):
            section = "example"
            if current_example["input"]:
                examples.append(QuestionExample(**current_example))  # type: ignore[arg-type]
                current_example = {"input": "", "output": "", "explanation": None}
            continue

        if stripped.lower().startswith("constraints") or stripped.lower().startswith("constraint"):
            section = "constraints"
            continue

        if section == "prose":
            prose_lines.append(line)
        elif section == "example":
            if stripped.lower().startswith("input:"):
                current_example["input"] = stripped[len("input:"):].strip()
            elif stripped.lower().startswith("output:"):
                val = stripped[len("output:"):].strip()
                if current_example["output"]:
                    current_example["explanation"] = val
                else:
                    current_example["output"] = val
            elif stripped.lower().startswith("explanation:"):
                current_example["explanation"] = stripped[len("explanation:"):].strip()
        elif section == "constraints":
            cleaned = stripped.lstrip("- •·")
            if cleaned:
                constraints.append(cleaned)

    if current_example["input"]:
        examples.append(QuestionExample(**current_example))  # type: ignore[arg-type]

    prose = "\n".join(prose_lines).strip()
    return prose, examples, constraints


def _load() -> None:
    global _loaded
    if _loaded:
        return

    with open(_CSV_PATH, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                qid = int(row["id"])
            except (ValueError, KeyError):
                continue

            raw_desc = row.get("description", "")
            prose, examples, constraints = _parse_examples(raw_desc)

            topics_raw = row.get("related_topics", "")
            topics = [t.strip() for t in topics_raw.split(",") if t.strip()]

            try:
                acc = float(row.get("acceptance_rate", "0"))
            except ValueError:
                acc = None

            q = QuestionOut(
                id=qid,
                title=row.get("title", ""),
                description=prose or raw_desc,
                difficulty=row.get("difficulty", "Medium"),
                acceptance_rate=acc,
                related_topics=topics,
                url=row.get("url"),
                examples=examples,
                constraints=constraints,
            )
            _questions_by_id[qid] = q
            _questions_list.append(q)

    _loaded = True


def get_all() -> list[QuestionOut]:
    _load()
    return _questions_list


def get_by_id(question_id: int) -> QuestionOut | None:
    _load()
    return _questions_by_id.get(question_id)


def get_filtered(
    difficulty: str | None = None,
    skip: int = 0,
    limit: int = 20,
) -> tuple[list[QuestionOut], int]:
    _load()
    filtered = _questions_list
    if difficulty:
        filtered = [q for q in filtered if q.difficulty.lower() == difficulty.lower()]
    total = len(filtered)
    return filtered[skip : skip + limit], total


def get_random(difficulty: str | None = None) -> QuestionOut | None:
    _load()
    pool = _questions_list
    if difficulty:
        pool = [q for q in pool if q.difficulty.lower() == difficulty.lower()]
    if not pool:
        return None
    return random.choice(pool)
