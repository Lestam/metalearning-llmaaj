"""judge-one: label a single conversation and show which learned rules it violates (for live demos).

Input: a JSON file (or stdin) with {"topic", "context", "conversation"} — the same fields as test.jsonl.
"""
import argparse
import json
import sys
from pathlib import Path

from .judge import judge_vote


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("example", nargs="?", help="JSON file with topic, context, conversation (default: stdin)")
    ap.add_argument("--artifacts", default="/artifacts")
    args = ap.parse_args()
    row = json.loads(Path(args.example).read_text() if args.example else sys.stdin.read())
    row.setdefault("item_id", "live")
    book = json.loads((Path(args.artifacts) / "rulebook.json").read_text())
    topics, config = book["topics"], book["config"]
    if row.get("topic") not in topics:
        sys.exit(f"topic must be one of {sorted(topics)}")
    rules = {r["id"]: r for r in topics[row["topic"]].get("principles", []) + topics[row["topic"]]["rules"]}
    result = judge_vote(row, topics[row["topic"]], exclude_self=False, votes=config.get("votes", 1),
                        thinking=config.get("judge_thinking", False), refs_k=config.get("refs_k", 0))
    print(f"LABEL: {result['label'].upper()}")
    for rid in result["violated_rules"]:
        print(f"  violated {rid}: {rules.get(rid, {}).get('rule', '(unknown rule id)')}")
    for check in result["checks"]:
        if check.get("violated"):
            print(f"  evidence for {check.get('rule')}: {check.get('evidence')}")


if __name__ == "__main__":
    main()
