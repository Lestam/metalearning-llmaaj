# Rulebook Judge — a Gemma 4 judge that learns an expert's rules

Solution for **A Judge That Learns from an Expert** (Plata partner track, Hacktoberfest Hack Day Barcelona 2026).
The original task description is kept in [CHALLENGE.md](CHALLENGE.md).

## What it is and who it is for

Teams that evaluate an AI assistant with an LLM judge, when the judge must agree with a domain expert rather than
with "common sense". Give it a set of conversations the expert labeled `good`/`bad`; `adapt` writes down the
expert's rules as a readable rulebook, and `eval` applies exactly that rulebook to new conversations.
The rulebook is an artifact a support lead or a compliance officer can read, check and argue with.

## How it works

```
adapt (train.jsonl, labeled)                               eval (test.jsonl, unlabeled)
 ├─ 0. principles: Gemma 4 reads ALL examples → cross-topic principles      ┐
 ├─ 1. topic knowledge: per topic, definitions/product facts/computations   │  rulebook.json
 │      each tied to a principle and to the training examples behind it     ├─► judge: principles + topic knowledge
 ├─ 2. validate: the judge labels every training example leave-one-out      │   + expert-labeled references
 ├─ 3. refine: Gemma 4 revises rules on its own mistakes; a revision is     │   → {checks, violated_rules, label}
 │      kept only if leave-one-out accuracy does not drop                   │
 └─ 4. EXPLANATION.md generated from rulebook.json (same text the judge sees)┘
```

* **Two-level rulebook.** General principles (e.g. *verify the client's claims before agreeing*, *count only money that is
  really the client's and available*) apply to every topic; topic knowledge holds the facts and definitions the
  principles need (e.g. *spending = purchases − refunds + transfers to other people*). New expert requirements in an
  unseen training set are usually new instances of the same principles.
* **Priors, then evidence.** [solution/priors.json](solution/priors.json) holds our manual analysis of the public data.
  `adapt` passes it to the miner only as hypotheses to confirm, rewrite or drop against the new labels.
* **Any violation ⇒ `bad`.** The judge checks each rule against the CONTEXT and every assistant turn and recomputes the
  numbers; the label is `bad` if any applicable rule is violated.

## How to run

Docker (the interface the organizers use):

```sh
docker build -t rulebook-judge .
# adapt: /input/train.jsonl -> /artifacts (rulebook.json, EXPLANATION.md, adapt_log.txt)
docker run --rm --env-file .env -v "$PWD/in:/input" -v "$PWD/artifacts:/artifacts" rulebook-judge adapt
# eval: /input/test.jsonl + /artifacts -> /output/predictions.csv
docker run --rm --env-file .env -v "$PWD/in:/input" -v "$PWD/artifacts:/artifacts" -v "$PWD/out:/output" rulebook-judge eval
```

Model access is configured with environment variables (see [.env.example](.env.example)):

| Variable | Meaning |
|---|---|
| `GEMMA_PROVIDER` | `gemini` (Gemini API key), `vertex` (Vertex AI, Application Default Credentials) or `openai` (any OpenAI-compatible host serving Gemma 4) |
| `GEMINI_API_KEY` | key from https://aistudio.google.com/apikey — serves `gemma-4-26b-a4b-it` |
| `VERTEX_PROJECT`, `VERTEX_LOCATION` | for `vertex`; model `google/gemma-4-26b-a4b-it-maas` |
| `GEMMA_FALLBACK` | optional second provider used automatically when the first one is rate-limited |

Local run without Docker (Python ≥ 3.10):

```sh
pip install -r requirements.txt
python3 src/prepare_inputs.py --train data/public_train.csv --test data/public_test.csv --out-dir out/in
python -m solution adapt --train out/in/train.jsonl --artifacts out/artifacts
python -m solution eval  --test out/in/test.jsonl  --artifacts out/artifacts --output out/predictions.csv
python3 src/evaluate.py --test data/public_test.csv --predictions out/predictions.csv --out out/score.json
```

Judge one conversation live (shows the label and the violated rules):

```sh
python -m solution judge-one example.json --artifacts out/artifacts
```

## Expertise: what knowledge is built in and where it comes from

* **Learned at `adapt` time from the expert's labels** — the rulebook in `artifacts/rulebook.json`, explained in
  `artifacts/EXPLANATION.md` (principles, topic knowledge, linked training examples, known boundaries).
* **Our manual prior** — [solution/priors.json](solution/priors.json): 7 cross-topic principles and topic definitions
  derived by reading all 60 `bad` training conversations next to similar `good` ones. Only hypotheses; the new labels decide.
* Where the model is called: [solution/llm.py](solution/llm.py) (`chat`), prompts in
  [solution/adapt.py](solution/adapt.py) (miner) and [solution/judge.py](solution/judge.py) (judge).

## The model and its license

**Gemma 4 26B A4B (instruction-tuned)** by Google DeepMind, used through the Gemini API or Vertex AI.
License: Apache 2.0 — https://ai.google.dev/gemma/apache_2 (Gemma 4 terms: https://ai.google.dev/gemma/terms).
Every model call in this project — rule mining and judging — uses Gemma 4.

## Proof that it does better than the same model without it

Public test set (80 conversations), metric `macro_topic_accuracy` from `src/evaluate.py`:

| Judge | macro topic accuracy | financial_position | savings | spending | credit |
|---|---|---|---|---|---|
| Plain Gemma 4 26B, generic "is this reply good?" prompt ([solution/baseline.py](solution/baseline.py)) | 0.787 | 0.773 | 0.900 | 0.609 | 0.867 |
| **Rulebook Judge** (this project: `adapt` on public train → `eval`, Gemma 4 26B on Vertex AI) | **0.911** | 0.818 | 1.000 | 0.826 | 1.000 |

Same model, same test set, same metric script; the only difference is the learned rulebook layer. Cohen's kappa (mean
over topics) 0.809. The full explanation generated by that `adapt` run is in
[docs/EXPLANATION_public_run.md](docs/EXPLANATION_public_run.md).

What moved the score (public test, macro topic accuracy): learned rulebook 0.824 → judge reasons before labeling
(recomputes the figures) 0.860 → "judge substance, not wording" 0.880 → only the 10 most similar labeled
examples in the prompt instead of the whole topic 0.933 on the same rulebook (0.911 after a fresh full `adapt`).
80 test conversations: differences of 1–2 points are within noise.

## Where it does not work

* **Arithmetic-heavy spending questions** (merchant/category totals with refunds, averages over several months): the
  judge sometimes recomputes a correct answer wrongly and rejects it (spending is our weakest topic, 0.826).
* **Over-strict rules**: when the expert accepted a reply that skips an explanation the rules ask for, the judge can
  still call it `bad`; most remaining errors are good replies rejected, not bad replies accepted.
* **Defects of a kind absent from training data** can be missed: rules only cover what the labels show. Every
  `EXPLANATION.md` lists the training conversations the judge still disagrees with (section "Boundaries").
* **Rate limits**: with heavy parallel load Gemma 4 endpoints return 429; the client retries with backoff and can
  fall back to a second provider (`GEMMA_FALLBACK`), so runs are slower but complete.

## Credits

* Task, data and evaluation scripts (`src/`, `data/`, `CHALLENGE.md`): Plata.
* Built with the help of an AI coding assistant (Claude Code); the approach, the manual rule analysis and all results
  were checked by the team. Libraries: `openai`, `google-genai`, `google-auth`.
* Code in `solution/` is MIT-licensed (see [LICENSE](LICENSE)).
