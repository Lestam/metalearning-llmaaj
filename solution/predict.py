"""eval: label unseen conversations with the rulebook saved by adapt."""
import argparse
import csv
import json
from pathlib import Path

from . import llm
from .data import load
from .explain import rulebook_digest
from .judge import judge_vote


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--test", default="/input/test.jsonl")
    ap.add_argument("--artifacts", default="/artifacts")
    ap.add_argument("--output", default="/output/predictions.csv")
    ap.add_argument("--votes", type=int, default=None, help="override the number of judge samples")
    ap.add_argument("--thinking", choices=["on", "off"], default=None, help="override judge thinking")
    ap.add_argument("--refs-k", type=int, default=None, help="0 = all topic examples, k = k most similar")
    args = ap.parse_args()
    book = json.loads((Path(args.artifacts) / "rulebook.json").read_text())
    topics, config = book["topics"], book["config"]
    print(f"rulebook {rulebook_digest(topics)}, model {llm.model_name()}", flush=True)
    rows = load(args.test)
    votes = args.votes if args.votes is not None else config.get("votes", 1)
    thinking = (args.thinking == "on") if args.thinking else config.get("judge_thinking", False)
    refs_k = args.refs_k if args.refs_k is not None else config.get("refs_k", 0)
    print(f"votes={votes} thinking={thinking} refs_k={refs_k}", flush=True)

    def run(row):
        try:
            return judge_vote(row, topics[row["topic"]], votes=votes, exclude_self=False,
                              thinking=thinking, refs_k=refs_k)
        except RuntimeError as error:  # model unreachable: keep the file complete, fall back to the majority class
            print(f"WARNING {row['item_id']}: {error}", flush=True)
            return {"label": "good", "violated_rules": [], "error": str(error)}

    results = llm.pmap(run, rows)
    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.writer(stream)
        writer.writerow(["item_id", "label"])
        for row, res in zip(rows, results):
            writer.writerow([row["item_id"], res["label"]])
    with (out.parent / "predictions_explained.jsonl").open("w", encoding="utf-8") as stream:
        for row, res in zip(rows, results):
            stream.write(json.dumps({"item_id": row["item_id"], "topic": row["topic"], **res},
                                    ensure_ascii=False) + "\n")
    print(json.dumps(llm.STATS), flush=True)


if __name__ == "__main__":
    main()
