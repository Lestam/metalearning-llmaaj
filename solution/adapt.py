"""adapt: learn the expert's rules from labeled conversations and save everything eval needs.

The rulebook has two levels:
  - principles: how the expert wants ANY client question handled (shared by all topics), learned from all examples;
  - topic knowledge: definitions, product facts and computations for one topic, each tied to a principle.

Pipeline:
  0. principles - Gemma 4 (thinking) reads every labeled example and writes cross-topic principles.
  1. mine     - per topic, Gemma 4 (thinking) reads ALL labeled examples of the topic and writes the topic knowledge
                the principles need, each item linked to the training examples that support it.
  2. validate - the judge (rules + labeled references, leave-one-out) labels every training example.
  3. refine   - Gemma 4 (thinking) sees the misjudged examples and revises the rules; the revision is kept
                only if leave-one-out training accuracy does not drop.
  4. explain  - EXPLANATION.md is generated from the final artifacts (rules, priorities, examples, boundaries).
"""
import argparse
import json
import time
from pathlib import Path

from . import llm
from .data import TOPICS, by_topic, load, render
from .explain import write_explanation
from .judge import format_rules, judge_vote

MINER_SYSTEM = """You are reverse-engineering the evaluation rules of a domain expert at a Mexican digital bank (Plata).
The expert reviewed complete conversations between clients and the bank's AI assistant and labeled each one "good" or "bad".
A conversation is "bad" if ANY assistant turn violates ANY applicable expert rule. The CONTEXT is the source data the assistant had.

Your job: infer the expert's rules for the topic "{topic}" so that another reviewer, applying only your rules, reproduces every label.
{principles_note}
Method:
- For every "bad" example find the concrete defect: recompute numbers from the CONTEXT, check what data was used or ignored, what was promised, what was omitted, the language, links, dates, tone, safety, scope. Compare it with "good" examples that look similar but were accepted.
- Generalize each defect into a rule that is specific and checkable (state exactly what to compute or look for), not a vague quality statement.
- Also learn from "good" examples what the expert tolerates, so rules do not over-reject.
- Order rules by priority (most decisive first). Every "bad" example should be explained by at least one rule.

Return only JSON:
{{"rules": [{{"id": "{prefix}1", "rule": "<the requirement, imperative, specific>", "applies_when": "<when this rule is relevant>",
  "how_to_check": "<exact computation or check against CONTEXT>", "bad_examples": ["<item_id violating it>"], "good_examples": ["<item_id complying with it>"],
  "why": "<one sentence: what the expert cares about>", "principle": "<id of the general principle this applies, if any>"}}],
 "tolerated": ["<things the expert accepts that a generic reviewer might reject, with item_ids>"],
 "ambiguous": [{{"note": "<labels that look inconsistent or hard to explain>", "examples": ["<item_id>"]}}]}}"""

REFINE_SYSTEM = MINER_SYSTEM + """

You already proposed the rules below, but a reviewer applying them misjudged some training examples.
Revise the rules so they reproduce the expert: fix rules that over-reject (good examples marked bad), add or sharpen rules
for missed defects (bad examples marked good), delete rules that are not supported. Keep rule ids stable where possible
and keep links to training examples. Return the complete revised JSON in the same format.

CURRENT RULES:
{rules}

MISJUDGED TRAINING EXAMPLES (expert label vs reviewer label and the reviewer's reasoning):
{errors}"""


PRINCIPLES_SYSTEM = """You are reverse-engineering the evaluation principles of a domain expert at a Mexican digital bank (Plata).
The expert reviewed complete conversations between clients and the bank's AI assistant across four topics
(financial_position, savings, spending, credit) and labeled each "good" or "bad". A conversation is "bad" if ANY
assistant turn violates ANY applicable expert requirement. The CONTEXT is the source data the assistant had.

Your job: find the GENERAL principles the expert applies to every topic - how the assistant must use the data it has,
treat the client's claims, compute and present answers, stay consistent, and what it may or may not claim to do.
Topic-specific facts and definitions come later; here state each principle so it applies to any topic, and show it
with "bad" examples from DIFFERENT topics. A principle must be checkable, not a vague quality wish.
Order principles by priority (most decisive first). Prefer 5-9 principles that together explain most "bad" labels.

Return only JSON:
{{"principles": [{{"id": "G1", "rule": "<the principle, imperative, general>", "applies_when": "<when it is relevant>",
  "how_to_check": "<what to verify against CONTEXT and the conversation>", "bad_examples": ["<item_id>"],
  "good_examples": ["<item_id>"], "why": "<one sentence: what the expert cares about>"}}]}}"""

PRINCIPLES_NOTE = """
The expert's GENERAL principles (shared by all topics) are already established:
{principles}

Here, find the TOPIC KNOWLEDGE for "{topic}" that a reviewer needs to apply these principles correctly: definitions
(what counts, which period, which rate), product facts the expert treats as true, required computations, and any
topic-only requirement. Do not restate the general principles; give each item the id of the principle it serves
in "principle" (or "" for a topic-only requirement).
"""

PRIORS_NOTE = """

PRIOR HYPOTHESES. The same expert's rules for this topic, learned earlier from a different labeled sample.
Treat them only as hypotheses: keep a prior rule if the labels below support it (cite the supporting item_ids from
THIS data), rewrite it if the labels show a different boundary, and drop it if the labels contradict it.
The new data may also contain requirements the priors do not mention; find those too.

{priors}"""

PRIORS_PATH = Path(__file__).with_name("priors.json")


PREFIX = {"financial_position": "F", "savings": "S", "spending": "P", "credit": "C"}


def load_priors(topic):
    if not PRIORS_PATH.exists():
        return []
    return json.loads(PRIORS_PATH.read_text()).get(topic, [])


def mine_principles(rows, use_priors=True):
    examples = "\n\n".join(render(r, with_label=True) for r in rows)
    system = PRINCIPLES_SYSTEM
    priors = load_priors("_principles") if use_priors else []
    if priors:
        system += PRIORS_NOTE.format(priors="\n".join(f"- {p}" for p in priors))
    reply = llm.chat([{"role": "system", "content": system},
                      {"role": "user", "content": f"All labeled examples:\n\n{examples}"}],
                     thinking=True, max_tokens=24000)
    data = llm.parse_json(reply)
    return normalize({"rules": data.get("principles") or []}, "G")["rules"]


def principles_note(principles, topic):
    if not principles:
        return ""
    return PRINCIPLES_NOTE.format(topic=topic, principles=format_rules(principles))


def mine(topic, rows, use_priors=True, principles=()):
    prefix = PREFIX[topic]
    examples = "\n\n".join(render(r, with_label=True) for r in rows)
    system = MINER_SYSTEM.format(topic=topic, prefix=prefix, principles_note=principles_note(principles, topic))
    priors = load_priors(topic) if use_priors else []
    if priors:
        system += PRIORS_NOTE.format(priors="\n".join(f"- {p}" for p in priors))
    reply = llm.chat([{"role": "system", "content": system},
                      {"role": "user", "content": f"Labeled examples for topic {topic}:\n\n{examples}"}],
                     thinking=True, json_mode=False, max_tokens=24000)
    return normalize(llm.parse_json(reply), prefix)


def refine(topic, rows, mined, errors, round_no, principles=()):
    prefix = PREFIX[topic]
    examples = "\n\n".join(render(r, with_label=True) for r in rows)
    err_text = "\n\n".join(
        f"{render(e['row'])}\nEXPERT LABEL: {e['row']['label']}\nREVIEWER LABEL: {e['pred']['label']}"
        f" (flagged: {', '.join(e['pred']['violated_rules']) or 'none'})\nREVIEWER CHECKS: "
        f"{json.dumps(e['pred']['checks'], ensure_ascii=False)[:1500]}" for e in errors)
    system = REFINE_SYSTEM.format(topic=topic, prefix=prefix, errors=err_text,
                                  principles_note=principles_note(principles, topic),
                                  rules=json.dumps(mined, ensure_ascii=False, indent=1))
    reply = llm.chat([{"role": "system", "content": system},
                      {"role": "user", "content": f"All labeled examples for topic {topic}:\n\n{examples}"}],
                     thinking=True, max_tokens=24000, seed=round_no)
    return normalize(llm.parse_json(reply), prefix)


def normalize(mined, prefix):
    rules = []
    for i, r in enumerate(mined.get("rules") or [], 1):
        if not isinstance(r, dict) or not r.get("rule"):
            continue
        r["id"] = f"{prefix}{len(rules) + 1}"  # ids are assigned here so topics never share ids
        for key in ("bad_examples", "good_examples"):
            r[key] = [str(x) for x in r.get(key) or []]
        rules.append(r)
    if not rules:
        raise ValueError("Miner returned no rules")
    return {"rules": rules, "tolerated": mined.get("tolerated") or [], "ambiguous": mined.get("ambiguous") or []}


def topic_artifact(rows, mined, principles=()):
    rule_of_example = {}
    for r in list(principles) + mined["rules"]:
        for iid in r["bad_examples"]:
            rule_of_example.setdefault(iid, []).append(r["id"])
    ids = {r["item_id"] for r in rows}
    rule_of_example = {k: v for k, v in rule_of_example.items() if k in ids}
    return {"principles": list(principles), "rules": mined["rules"], "tolerated": mined["tolerated"],
            "ambiguous": mined["ambiguous"], "references": rows, "rule_of_example": rule_of_example}


REFS_K = 0  # set from --refs-k: 0 = all topic examples in the judge prompt, k = the k most similar
JUDGE_THINKING = True  # the judge reasons before labeling (recomputes figures); same setting is saved for eval


def validate(rows, artifact, votes):
    def one(r):
        try:
            return judge_vote(r, artifact, votes=votes, exclude_self=True, refs_k=REFS_K, thinking=JUDGE_THINKING)
        except RuntimeError as error:  # model unavailable for this example: count it as unjudged, keep going
            return {"label": None, "violated_rules": [], "checks": [], "error": str(error)[:200]}
    preds = llm.pmap(one, rows)
    judged = [(r, p) for r, p in zip(rows, preds) if p["label"] is not None]
    if len(judged) < len(rows):
        print(f"WARNING: {len(rows) - len(judged)} of {len(rows)} examples could not be judged", flush=True)
    acc = sum(p["label"] == r["label"] for r, p in judged) / max(len(judged), 1)
    for p in preds:
        p["label"] = p["label"] or "unjudged"
    return acc, preds


def adapt_topic(topic, rows, rounds, votes, log, use_priors=True, principles=()):
    t0 = time.time()
    try:
        mined = mine(topic, rows, use_priors, principles)
    except (ValueError, RuntimeError) as error:  # keep going: fall back to the prior hypotheses as rules
        log(f"[{topic}] mining failed ({error}); using priors as the starting rulebook")
        prefix = PREFIX[topic]
        mined = {"rules": [{"id": f"{prefix}{i}", "rule": p, "bad_examples": [], "good_examples": [],
                            "source": "prior (mining failed)"} for i, p in enumerate(load_priors(topic), 1)]
                 or [{"id": f"{prefix}1", "rule": "Every figure and fact stated must match the CONTEXT.",
                      "bad_examples": [], "good_examples": []}], "tolerated": [], "ambiguous": []}
    artifact = topic_artifact(rows, mined, principles)
    acc, preds = validate(rows, artifact, votes)
    history = [{"round": 0, "loo_train_accuracy": acc, "n_rules": len(mined["rules"])}]
    log(f"[{topic}] mined {len(mined['rules'])} rules, LOO train acc {acc:.3f}")
    best = (acc, artifact, preds)
    for round_no in range(1, rounds + 1):
        errors = [{"row": r, "pred": p} for r, p in zip(rows, best[2]) if p["label"] != r["label"]]
        if not errors:
            break
        try:
            candidate = topic_artifact(rows, refine(topic, rows, {k: best[1][k] for k in ("rules", "tolerated", "ambiguous")},
                                                    errors, round_no, principles), principles)
        except (ValueError, RuntimeError) as error:
            log(f"[{topic}] refine round {round_no} failed: {error}")
            continue
        cand_acc, cand_preds = validate(rows, candidate, votes)
        kept = cand_acc >= best[0]
        history.append({"round": round_no, "loo_train_accuracy": cand_acc, "n_rules": len(candidate["rules"]),
                        "kept": kept, "errors_before": len(errors)})
        log(f"[{topic}] refine {round_no}: {len(candidate['rules'])} rules, LOO acc {cand_acc:.3f} "
            f"({'kept' if kept else 'rejected'}, best {max(best[0], cand_acc):.3f})")
        if kept:
            best = (cand_acc, candidate, cand_preds)
    acc, artifact, preds = best
    artifact["train_predictions"] = {r["item_id"]: p for r, p in zip(rows, preds)}
    artifact["loo_train_accuracy"] = acc
    artifact["history"] = history
    artifact["seconds"] = round(time.time() - t0, 1)
    return artifact


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--train", default="/input/train.jsonl")
    ap.add_argument("--artifacts", default="/artifacts")
    ap.add_argument("--rounds", type=int, default=1)
    ap.add_argument("--votes", type=int, default=1)
    ap.add_argument("--no-priors", action="store_true", help="ignore solution/priors.json")
    ap.add_argument("--no-principles", action="store_true", help="per-topic rules only (no shared principles)")
    ap.add_argument("--refs-k", type=int, default=10, help="reference examples per judge call (0 = all of the topic)")
    ap.add_argument("--judge-thinking", choices=["on", "off"], default="on")
    args = ap.parse_args()
    global REFS_K, JUDGE_THINKING
    REFS_K = args.refs_k
    JUDGE_THINKING = args.judge_thinking == "on"
    out = Path(args.artifacts)
    out.mkdir(parents=True, exist_ok=True)
    rows = load(args.train, require_labels=True)
    logs = []

    def log(msg):
        print(msg, flush=True)
        logs.append(msg)

    topics = by_topic(rows)
    principles = []
    if not args.no_principles:
        try:
            principles = mine_principles(rows, not args.no_priors)
            log(f"[all] mined {len(principles)} general principles: " + " | ".join(p["rule"][:60] for p in principles))
        except (ValueError, RuntimeError) as error:
            log(f"[all] principle mining failed ({error}); falling back to per-topic rules only")
    artifacts = dict(zip(TOPICS, llm.pmap(
        lambda t: adapt_topic(t, topics[t], args.rounds, args.votes, log, not args.no_priors, principles),
        TOPICS, workers=4)))
    config = {"provider": llm.PROVIDER, "model": llm.model_name(), "votes": args.votes, "rounds": args.rounds,
              "priors": (not args.no_priors) and PRIORS_PATH.exists(), "principles": principles, "refs_k": args.refs_k,
              "judge_thinking": JUDGE_THINKING,
              "train_size": len(rows), "stats": llm.STATS}
    (out / "rulebook.json").write_text(json.dumps({"config": config, "topics": artifacts}, ensure_ascii=False, indent=1))
    (out / "adapt_log.txt").write_text("\n".join(logs))
    write_explanation(out, artifacts, config)
    for t in TOPICS:
        log(f"{t}: LOO train acc {artifacts[t]['loo_train_accuracy']:.3f}, topic rules: "
            + "; ".join(r["id"] for r in artifacts[t]["rules"]))
    log(json.dumps(llm.STATS))


if __name__ == "__main__":
    main()


__all__ = ["format_rules"]
