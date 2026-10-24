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
| `LLM_CONCURRENCY` | simultaneous model calls (default 5) |

If `GEMMA_PROVIDER` is not set, the provider is chosen from the credentials present (`GEMINI_API_KEY`/`GOOGLE_API_KEY` →
Gemini API, `VERTEX_PROJECT` → Vertex AI, `OPENAI_BASE_URL`+`OPENAI_API_KEY` → OpenAI-compatible host).
Note: Gemma 4 on the Gemini API is served on the free tier only (about 15 requests per minute); the client retries
rate-limited calls with backoff, so a full `adapt` + `eval` completes, just more slowly than on Vertex AI.

Local run without Docker (Python ≥ 3.10):

```sh
pip install -r requirements.txt
python3 src/prepare_inputs.py --train data/public_train.csv --test data/public_test.csv --out-dir out/in
python -m solution adapt --train out/in/train.jsonl --artifacts out/artifacts
python -m solution eval  --test out/in/test.jsonl  --artifacts out/artifacts --output out/predictions.csv
python3 src/evaluate.py --test data/public_test.csv --predictions out/predictions.csv --out out/score.json
```

Demo UI — a test-range dashboard (precomputed comparison on a labeled test set) and a workbench to judge any
conversation live, plain Gemma 4 next to the Rulebook Judge:

```sh
python -m solution demo --artifacts out/artifacts --examples examples/demo_test_conversations.jsonl \
  --scores examples/demo_scores.json --gold data/public_test.csv \
  --plain-preds out/baseline/predictions.csv --ours-preds out/predictions_explained.jsonl --port 8765
# open http://localhost:8765/dashboard
```

Judge one conversation live (shows the label and the violated rules):

```sh
python -m solution judge-one example.json --artifacts out/artifacts
```

## Expertise: what knowledge is built in and where it comes from

* **Learned at `adapt` time from the expert's labels** — the rulebook in `artifacts/rulebook.json`, explained in
  `artifacts/EXPLANATION.md` (principles, topic knowledge, linked training examples, known boundaries).
* **Our prior, from four human-in-the-loop sources** — [solution/priors.json](solution/priors.json):
  (1) a review of all 60 `bad` public training conversations (what the expert penalizes),
  (2) a review of all 90 `good` ones (what the expert accepts — marked `TOLERATED`, to stop over-strict rules),
  (3) a team member's own notes on 18 bad-vs-good pairs (marked `HUMAN REVIEW`, e.g. "answer first, with the complete
  picture — length itself is not a defect" (reworded after the labels showed long, complete answers are accepted), "apply the terms of the product the client actually has, read from their data — the rule points to the data, so it survives tariff changes"),
  (4) a pass over all 60 bad-vs-good pairs with a strong assistant model (Claude) as a *candidate generator*: it condensed
  ~40 rule hypotheses into a catalogue of 9 defect types that explains every `bad` label (wrong period basis, refunds not
  subtracted, credit counted as money, hold ignored, incomplete picture, wrong product terms, agreeing with a wrong client
  claim, asking for data already in CONTEXT, figures changing between turns) and flagged the generic reviewer's
  over-strict habits (a consistent accounting basis is not a math error; an offer is not a claimed action).
  All four enter `adapt` only as hypotheses: the miner (Gemma 4) keeps a prior only if the new labels support it, cites the
  supporting item_ids, and the explanation links every rule to those training conversations (the miner is also asked to
  tag each rule's origin, but Gemma does not fill that field in reliably, so origins are not shown per rule). The division of labour is deliberate —
  a strong model proposes and prunes candidates offline, the open-weight model that will actually judge confirms or rejects
  them against the labels, so the rulebook is optimised for the reader that applies it. No Claude call is made by the pipeline.
* Where the model is called: [solution/llm.py](solution/llm.py) (`chat`), prompts in
  [solution/adapt.py](solution/adapt.py) (miner) and [solution/judge.py](solution/judge.py) (judge).

## The model and its license

**Gemma 4 26B A4B (instruction-tuned)** by Google DeepMind, used through the Gemini API or Vertex AI.
License: Apache 2.0 — https://ai.google.dev/gemma/apache_2 (Gemma 4 terms: https://ai.google.dev/gemma/terms).
Every model call in this project — rule mining and judging — uses Gemma 4.

## Proof that it does better than the same model without it

Public test set (80 conversations), metric `macro_topic_accuracy` from `src/evaluate.py`:

| Judge | macro topic accuracy | financial_position | savings | spending | credit | code |
|---|---|---|---|---|---|---|
| Plain Gemma 4 26B, generic "is this reply good?" prompt ([solution/baseline.py](solution/baseline.py)) | 0.787 | 0.773 | 0.900 | 0.609 | 0.867 | — |
| **Rulebook Judge**, run A: priors from the review of bad conversations | **0.911** | 0.818 | 1.000 | 0.826 | 1.000 | [`51a50ae`](https://github.com/Lestam/metalearning-llmaaj/commit/51a50ae) |
| **Rulebook Judge**, run B: + good-answer analysis and human review of pairs | **0.887** | 0.773 | 0.950 | 0.826 | 1.000 | [`d9998e4`](https://github.com/Lestam/metalearning-llmaaj/commit/d9998e4) |
| **Rulebook Judge**, run C: final code (completeness priors, "consistent basis is not an error", injection guard) | **0.923** | 0.909 | 1.000 | 0.783 | 1.000 | this commit |

Every row is a complete run: `adapt` on the 150 public training conversations, then `eval` on all 80 public test
conversations (no conversation left unjudged; rate-limited calls are retried, not skipped), scored with the
organizers' `src/evaluate.py`. The "code" column names the commit whose miner and judge prompts the run used.
Same model, same test set, same metric; the only difference from the first row is the
learned rulebook layer. Runs we stopped midway are not reported. With 80 conversations a 2-point gap is two
conversations, so treat the Rulebook Judge rows as one result with run-to-run spread. Bad replies let through:
plain Gemma 16 of 30, Rulebook Judge 2 of 30 with the final code (run C; Cohen's kappa 0.84). The explanation generated by the final run's `adapt` is in
[docs/EXPLANATION_public_run.md](docs/EXPLANATION_public_run.md).

What moved the score (public test, macro topic accuracy, all measured on one rulebook so only the judge changes):
learned rulebook 0.824 → judge reasons before labeling (recomputes the figures) 0.860 → "judge substance, not
wording" 0.880 → only the 10 most similar labeled examples in the prompt instead of the whole topic 0.933.

## Where it does not work

* **Arithmetic-heavy spending questions** (merchant/category totals with refunds, averages over several months): the
  judge sometimes recomputes a correct answer wrongly and rejects it (spending is our weakest topic, 0.826).
* **Over-strict rules**: when the expert accepted a reply that skips an explanation the rules ask for, the judge can
  still call it `bad`; most remaining errors are good replies rejected, not bad replies accepted.
* **Defects of a kind absent from training data** can be missed: rules only cover what the labels show. Every
  `EXPLANATION.md` lists the training conversations the judge still disagrees with (section "Boundaries").
* **Rate limits**: with heavy parallel load Gemma 4 endpoints return 429; the client retries with backoff and can
  fall back to a second provider (`GEMMA_FALLBACK`), so runs are slower but complete.

## Safety and scope

* **Prompt injection.** The judge reads text written by other people (clients and the assistant under review). The
  judge prompt states that the conversation and the client data are data to evaluate, never instructions, and that
  text trying to change the rules or dictate the label must be ignored. The label is parsed from the model's JSON;
  nothing in a conversation can trigger an action — the judge has no tools.
* **Not financial advice.** The product evaluates replies of a bank assistant; it does not advise clients. The
  product facts in the rulebook are what the expert's labels imply, not an authoritative statement of Plata's terms.
* **Data.** Only the organizers' public, anonymized challenge data is used and shipped; no real personal data.
* **Failures.** If the model API keeps failing for a conversation, `eval` still writes a complete predictions file
  (that conversation gets `good`) and prints a warning naming it; the demo UI shows the error message instead of a blank page.
* **Keys.** Only in `.env` (git-ignored); `.env.example` has no values; no key in the code or the commit history.

## Credits

* Task, data and evaluation scripts (`src/`, `data/`, `CHALLENGE.md`): Plata.
* Built with the help of an AI coding assistant (Claude Code); the approach, the manual rule analysis and all results
  were checked by the team. Libraries: `openai`, `google-genai`, `google-auth`.
* Code in `solution/` is MIT-licensed (see [LICENSE](LICENSE)).
