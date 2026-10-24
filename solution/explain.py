"""Generate EXPLANATION.md for the jury from the exact artifacts that eval uses.

Nothing here is written by hand: rules, priorities, linked examples and boundaries all come from
rulebook.json, and the judge prompt is rendered with the same function eval calls.
"""
import hashlib
import json
from collections import Counter

from .data import TOPICS
from .judge import JUDGE_SYSTEM, format_rulebook


def _clip(text, limit):
    text = " ".join(text.split())
    return text[:limit] + ("…" if len(text) > limit else "")


def _excerpt(row, limit=260):
    user = next((m["content"] for m in row["conversation"] if m["role"] == "user"), "")
    last = next((m["content"] for m in reversed(row["conversation"]) if m["role"] == "assistant"), "")
    return f"Client: “{_clip(user, limit)}” → Assistant: “{_clip(last, limit)}”"


def rulebook_digest(topics):
    return hashlib.sha256(json.dumps({t: format_rulebook(t, topics[t]) for t in TOPICS}, ensure_ascii=False,
                                     sort_keys=True).encode()).hexdigest()[:12]


def _rule_lines(rule, rank, refs, flagged):
    tag = f" — applies principle {rule['principle']}" if rule.get("principle") else ""
    lines = [f"**{rule['id']} (priority {rank}{tag}).** {rule['rule']}", ""]
    for key, label in (("source", "Origin"), ("applies_when", "Applies when"), ("how_to_check", "How it is checked"),
                       ("why", "Why the expert cares")):
        if rule.get(key):
            lines.append(f"- *{label}:* {rule[key]}")
    lines.append(f"- *Used by the judge on training data:* flagged in {flagged.get(rule['id'], 0)} conversation(s).")
    for iid in [i for i in rule["bad_examples"] if i in refs][:2]:
        lines.append(f"- Example `{iid}` ({refs[iid]['topic']}) — expert label **{refs[iid]['label']}**, "
                     f"illustrates a violation of {rule['id']}: {_excerpt(refs[iid])}")
    for iid in [i for i in rule["good_examples"] if i in refs][:1]:
        lines.append(f"- Example `{iid}` ({refs[iid]['topic']}) — expert label **{refs[iid]['label']}**, "
                     f"complies with {rule['id']}: {_excerpt(refs[iid])}")
    lines.append("")
    return lines


def write_explanation(out_dir, topics, config):
    lines = [
        "# How the judge decides — generated automatically by `adapt`",
        "",
        f"Model: **{config['model']}** (Gemma 4, Apache 2.0) via `{config['provider']}`. "
        f"Training examples: {config['train_size']}. Rulebook fingerprint: `{rulebook_digest(topics)}` "
        "(`eval` loads the same rulebook.json and prints this fingerprint).",
        "",
        "## Decision procedure and priorities",
        "",
        "1. Every conversation is checked against the **general principles** (shared by all topics) and against the "
        "**topic knowledge** of its `topic` (definitions, product facts, computations — each tied to the principle it serves).",
        "2. The judge checks every rule against the source data (CONTEXT) and **every** assistant turn, "
        "recomputing every number the assistant states.",
        "3. **Any violation of an applicable rule makes the conversation `bad`** — one violation outweighs any number "
        "of things done well. A conversation is `good` only if no applicable rule is violated.",
        "4. Principles come first, then topic knowledge; within each list the order is priority (most decisive first). "
        "The order decides which violation is reported first; it never turns a violation into `good`.",
        "5. Behaviour listed under *Tolerated* is explicitly **not** a violation, even if a generic reviewer would object. "
        "The judge rates substance (facts, computations, use of data, claims), not wording: a correct reply phrased "
        "differently, or an offer to help, is not a violation.",
        "6. Unclear cases are decided by comparison with the expert-labeled training examples, which the judge sees "
        "together with the rule each bad example violates.",
        "",
    ]
    all_refs = {r["item_id"]: r for t in TOPICS for r in topics[t]["references"]}
    all_flagged = Counter(v for t in TOPICS for p in topics[t]["train_predictions"].values() if p["label"] == "bad"
                          for v in p["violated_rules"])
    principles = topics[TOPICS[0]].get("principles") or []
    if principles:
        lines += ["## General principles (all topics)", "",
                  "Learned from all training examples at once; each is illustrated with examples from different topics.", ""]
        for rank, rule in enumerate(principles, 1):
            lines += _rule_lines(rule, rank, all_refs, all_flagged)
    for topic in TOPICS:
        art = topics[topic]
        refs = {r["item_id"]: r for r in art["references"]}
        flagged = Counter(v for p in art["train_predictions"].values() if p["label"] == "bad"
                          for v in p["violated_rules"])
        n_bad = sum(r["label"] == "bad" for r in art["references"])
        history = ", ".join(f"round {h['round']}: {h['loo_train_accuracy']:.1%} ({h['n_rules']} rules"
                            + ("" if h.get("kept", True) else ", rejected") + ")" for h in art["history"])
        lines += [f"## Topic `{topic}` — {len(refs)} training examples ({n_bad} bad)", "",
                  "Leave-one-out accuracy on training data (each example judged without seeing itself): "
                  f"**{art['loo_train_accuracy']:.1%}**. Learning history: {history}.", "",
                  "### Topic knowledge (priority order)", ""]
        for rank, rule in enumerate(art["rules"], 1):
            lines += _rule_lines(rule, rank, refs, flagged)
        if art["tolerated"]:
            lines += ["### Tolerated by the expert (not violations)", ""]
            lines += [f"- {t if isinstance(t, str) else json.dumps(t, ensure_ascii=False)}" for t in art["tolerated"]]
            lines.append("")
        lines += ["### Boundaries: where this rulebook is unreliable", ""]
        for amb in art["ambiguous"]:
            if isinstance(amb, dict):
                ids = ", ".join(f"`{i}`" for i in amb.get("examples", []))
                lines.append(f"- {amb.get('note', '')}" + (f" Examples: {ids}." if ids else ""))
            else:
                lines.append(f"- {amb}")
        misses = [(iid, p) for iid, p in art["train_predictions"].items() if p["label"] != refs[iid]["label"]]
        if misses:
            lines.append(f"- The judge still disagrees with the expert on {len(misses)} of {len(refs)} training "
                         "examples (leave-one-out); expect similar conversations to be misjudged:")
            for iid, p in misses[:8]:
                flagged_txt = f" (flagged {', '.join(p['violated_rules'])})" if p["violated_rules"] else ""
                lines.append(f"  - `{iid}`: expert **{refs[iid]['label']}**, judge **{p['label']}**{flagged_txt}. "
                             f"{_excerpt(refs[iid], 160)}")
        else:
            lines.append("- No leave-one-out disagreements on training data; defects of kinds absent from training "
                         "data can still be missed.")
        lines.append("")
    lines += ["## Consistency with the implementation", "",
              "`eval` (`solution/predict.py`) loads `rulebook.json` from this directory and, for each conversation, "
              "sends Gemma the system prompt below with `{rules}` replaced by the principles and that topic's knowledge "
              "exactly as listed above (rendered by `solution/judge.py:format_rulebook`) and `{references}` replaced by the labeled "
              "training examples of the same topic. The predicted label is the `label` field of the model's JSON "
              "reply; `predictions_explained.jsonl` records the violated rule ids for every prediction.", "",
              "```text", JUDGE_SYSTEM, "```", "", "Rendered rules block for each topic, verbatim:", ""]
    for topic in TOPICS:
        lines += [f"<details><summary>{topic}</summary>", "", "```text", format_rulebook(topic, topics[topic]),
                  "```", "", "</details>", ""]
    (out_dir / "EXPLANATION.md").write_text("\n".join(lines), encoding="utf-8")
