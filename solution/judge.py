"""The judge used at prediction time: topic rulebook + labeled reference examples -> good/bad.

The rulebook text built here is exactly what the model sees; EXPLANATION.md quotes it verbatim.
"""
import json
import re
from collections import Counter

from . import llm
from .data import render

JUDGE_SYSTEM = """You are a strict quality reviewer who reproduces the judgement of a domain expert at a Mexican digital bank (Plata).
You review one complete conversation between a client and the bank's AI assistant, together with the source data (CONTEXT) the assistant had.

The expert's rules were learned from the expert's labeled examples. They are listed in priority order:

{rules}

Decision procedure:
1. Read the CONTEXT and the WHOLE conversation; every assistant turn counts.
2. For each rule, decide whether it applies to this conversation and, if it applies, whether any assistant turn violates it. Recompute every number the assistant states from the CONTEXT before deciding.
3. Any violation of an applicable rule makes the conversation "bad". If no applicable rule is violated, the conversation is "good". Do not invent requirements that are not in the rules or not supported by the reference examples.
4. Judge substance, not wording: wrong or invented facts, wrong computations, misused or ignored data, false claims.
   A reply that is correct but phrased differently from the reference examples, or that omits an explanatory remark
   no rule requires, is not a violation. Offering to help or asking whether the client wants something done is not
   a claim that it was done. A computation on a different but internally consistent basis (available vs gross with the
   hold disclosed; a locked deposit inside a labelled total or kept separate) is not a math error: check the inputs and
   the arithmetic, not the choice of basis. Length is not a defect.
5. When unsure, compare with the most similar reference examples below; the expert labeled them.

{references}

Return only JSON:
{{"checks": [{{"rule": "<rule id>", "violated": true|false, "evidence": "<short quote or computation>"}}], "violated_rules": ["<ids of violated rules>"], "label": "good" | "bad"}}"""


def format_rules(rules):
    lines = []
    for r in rules:
        tag = f" [applies {r['principle']}]" if r.get("principle") else ""
        lines.append(f"{r['id']}. {r['rule']}{tag}")
        if r.get("applies_when"):
            lines.append(f"   Applies when: {r['applies_when']}")
        if r.get("how_to_check"):
            lines.append(f"   How to check: {r['how_to_check']}")
    return "\n".join(lines)


def format_references(refs, rule_of_example):
    if not refs:
        return "No reference examples."
    blocks = ["Reference examples labeled by the expert:"]
    for r in refs:
        note = ""
        if r["label"] == "bad" and rule_of_example.get(r["item_id"]):
            note = f" (violates {', '.join(rule_of_example[r['item_id']])})"
        blocks.append(f"--- {render(r)}\nEXPERT LABEL: {r['label']}{note}")
    return "\n\n".join(blocks)


def format_rulebook(topic, artifact):
    """The rules block the judge sees: shared principles, then this topic's knowledge."""
    topic_block = format_rules(artifact["rules"])
    if not artifact.get("principles"):
        return f"RULES FOR TOPIC {topic}:\n{topic_block}"
    return (f"GENERAL PRINCIPLES (all topics):\n{format_rules(artifact['principles'])}\n\n"
            f"TOPIC KNOWLEDGE FOR {topic} (how the principles apply here, plus topic-only requirements):\n{topic_block}")


def system_prompt(topic, artifact, refs):
    return JUDGE_SYSTEM.format(topic=topic, rules=format_rulebook(topic, artifact),
                               references=format_references(refs, artifact.get("rule_of_example", {})))


def _tokens(row):
    return set(re.findall(r"\w+", render(row).lower()))


def nearest(row, refs, k):
    """The k reference examples sharing the most words with the conversation (context + dialogue)."""
    mine = _tokens(row)
    return sorted(refs, key=lambda r: -len(mine & _tokens(r)) / (len(mine | _tokens(r)) or 1))[:k]


def judge_one(row, topic_artifact, exclude_self=True, seed=0, thinking=False, refs_k=0):
    refs = [r for r in topic_artifact["references"] if not (exclude_self and r["item_id"] == row["item_id"])]
    if refs_k:
        refs = nearest(row, refs, refs_k)
    system = system_prompt(row["topic"], topic_artifact, refs)
    reply = llm.chat([{"role": "system", "content": system},
                      {"role": "user", "content": "Review this conversation:\n\n" + render(row)}],
                     json_mode=True, max_tokens=6000 if thinking else 2500, seed=seed, thinking=thinking,
                     temperature=0.0 if seed == 0 else 0.7)
    try:
        data = llm.parse_json(reply)
    except ValueError:
        data = {"label": "bad" if '"bad"' in reply else "good", "violated_rules": [], "parse_error": True}
    label = data.get("label")
    violated = [str(v) for v in data.get("violated_rules") or []]
    if label not in ("good", "bad"):
        label = "bad" if violated else "good"
    return {"label": label, "violated_rules": violated, "checks": data.get("checks", [])}


def judge_vote(row, topic_artifact, votes=1, exclude_self=True, thinking=False, refs_k=0):
    results = [judge_one(row, topic_artifact, exclude_self, seed=s, thinking=thinking, refs_k=refs_k)
               for s in range(votes)]
    tally = Counter(r["label"] for r in results)
    label = "bad" if tally["bad"] > tally["good"] else "good"
    violated = Counter(v for r in results for v in r["violated_rules"])
    return {"label": label, "votes": dict(tally), "violated_rules": [v for v, _ in violated.most_common()],
            "checks": results[0]["checks"]}
