"""Plain Gemma judge with no learned rules: the reference point for 'better than the same model'."""
import argparse
import json
from collections import Counter

from . import llm
from .data import load, macro_topic_accuracy, render

PROMPT = """You are evaluating a bank assistant's replies for a Mexican digital bank.
Read the source data and the whole conversation. Decide whether the assistant's replies are good or bad.
Return JSON: {"reason": "<one sentence>", "label": "good" | "bad"}"""


def judge(row, seed=0):
    reply = llm.chat([{"role": "system", "content": PROMPT}, {"role": "user", "content": render(row)}],
                     json_mode=True, max_tokens=400, seed=seed)
    try:
        label = llm.parse_json(reply).get("label")
    except ValueError:
        label = None
    return label if label in ("good", "bad") else ("bad" if "bad" in reply.lower() else "good")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--test", required=True)
    ap.add_argument("--out", default="out/baseline.json")
    ap.add_argument("--predictions", default="", help="also write item_id,label CSV")
    args = ap.parse_args()
    rows = load(args.test, require_labels=True)
    labels = llm.pmap(judge, rows)
    preds = {r["item_id"]: lab for r, lab in zip(rows, labels)}
    acc, per_topic = macro_topic_accuracy(rows, preds)
    result = {"macro_topic_accuracy": acc, "by_topic": per_topic, "predicted": dict(Counter(labels)),
              "model": llm.model_name(), "provider": llm.PROVIDER, "stats": llm.STATS}
    print(json.dumps(result, indent=1))
    from pathlib import Path
    if args.predictions:
        Path(args.predictions).parent.mkdir(parents=True, exist_ok=True)
        Path(args.predictions).write_text("item_id,label\n" + "".join(f"{k},{v}\n" for k, v in preds.items()))
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out).write_text(json.dumps(result, indent=1))


if __name__ == "__main__":
    main()
