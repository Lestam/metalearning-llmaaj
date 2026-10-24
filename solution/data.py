"""Load challenge JSONL/CSV inputs and render one example as judge-readable text."""
import json
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
from common import TOPICS, load_dataset  # noqa: E402

LABELS = ("good", "bad")


def load(path, require_labels=False):
    rows = load_dataset(path, require_labels=require_labels)
    return [{"item_id": r["item_id"], "topic": r["topic"], "context": r["context"],
             "conversation": r["conversation"], "label": r.get("label")} for r in rows]


def render(row, with_label=False):
    turns = "\n".join(f"[{m['role'].upper()}]\n{m['content']}" for m in row["conversation"])
    text = (f"EXAMPLE {row['item_id']}\nTOPIC: {row['topic']}\n"
            f"CONTEXT (source data available to the assistant):\n"
            f"{json.dumps(row['context'], ensure_ascii=False, indent=1)}\n"
            f"CONVERSATION:\n{turns}")
    if with_label:
        text += f"\nEXPERT LABEL: {row['label']}"
    return text


def by_topic(rows):
    return {t: [r for r in rows if r["topic"] == t] for t in TOPICS}


def macro_topic_accuracy(rows, predictions):
    """Same metric as src/evaluate.py: mean of per-topic accuracies."""
    per_topic = {}
    for topic, items in by_topic(rows).items():
        if items:
            per_topic[topic] = sum(predictions[r["item_id"]] == r["label"] for r in items) / len(items)
    return sum(per_topic.values()) / len(per_topic), per_topic


def label_counts(rows):
    return Counter((r["topic"], r["label"]) for r in rows)
