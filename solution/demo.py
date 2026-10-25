"""Local demo UI: `python -m solution demo --artifacts out/artifacts [--port 8000]`, then open http://localhost:8000.

Shows plain Gemma and the Rulebook Judge side by side on any conversation, plus the learned rulebook.
Standard library only; the model is called through solution/llm.py like everywhere else.
"""
import argparse
import json
from concurrent.futures import ThreadPoolExecutor
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from . import baseline, llm
from .judge import judge_vote

PAGE = Path(__file__).with_name("demo.html")
DASHBOARD = Path(__file__).with_name("dashboard.html")


def dashboard_data(book, gold_path, plain_path, ours_path, scores):
    """Precomputed comparison on a labeled test set: no model calls, opens instantly."""
    import csv
    topics = book["topics"]
    gold = {r["item_id"]: r for r in csv.DictReader(open(gold_path, encoding="utf-8-sig"))}
    plain = {r["item_id"]: r["label"] for r in csv.DictReader(open(plain_path, encoding="utf-8"))}
    ours = {}
    for line in Path(ours_path).read_text().splitlines():
        if line.strip():
            r = json.loads(line)
            ours[r["item_id"]] = r
    principle_of = {}
    for t, a in topics.items():
        for r in a.get("principles", []):
            principle_of[r["id"]] = r["id"]
        for r in a["rules"]:
            principle_of[(t, r["id"])] = r.get("principle") or ""
    items, caught = [], {}
    for iid, g in gold.items():
        conv = json.loads(g["conversation"])
        o = ours.get(iid, {})
        if o.get("label") == "bad":
            for rid in set(o.get("violated_rules", [])):
                pid = principle_of.get(rid) or principle_of.get((g["topic"], rid))
                if pid:
                    caught[pid] = caught.get(pid, 0) + 1
        items.append({"id": iid, "topic": g["topic"], "gold": g["label"], "plain": plain.get(iid), "ours": o.get("label"),
                      "rules": o.get("violated_rules", []),
                      "question": next((m["content"] for m in conv if m["role"] == "user"), "")[:160]})
    def confusion(key):
        m = {"good": {"good": 0, "bad": 0}, "bad": {"good": 0, "bad": 0}}
        for it in items:
            if it[key] in ("good", "bad"):
                m[it["gold"]][it[key]] += 1
        return m
    principles = topics[next(iter(topics))].get("principles", [])
    return {"items": items, "confusion": {"plain": confusion("plain"), "ours": confusion("ours")},
            "principles": [{"id": p["id"], "rule": p["rule"], "caught": caught.get(p["id"], 0)} for p in principles],
            "scores": scores}


def make_handler(book, examples, scores, dashboard=None):
    topics, config = book["topics"], book["config"]

    def judge(row):
        art = topics[row["topic"]]
        with ThreadPoolExecutor(2) as pool:
            plain = pool.submit(baseline.judge, row)
            ours = pool.submit(judge_vote, row, art, config.get("votes", 1), False,
                               config.get("judge_thinking", False), config.get("refs_k", 0))
            plain_label, result = plain.result(), ours.result()
        rules = {r["id"]: r for r in art.get("principles", []) + art["rules"]}
        violated = [{"id": rid, "rule": rules.get(rid, {}).get("rule", ""),
                     "evidence": next((c.get("evidence") for c in result["checks"]
                                       if str(c.get("rule")) == rid and c.get("violated")), "")}
                    for rid in result["violated_rules"]]
        return {"plain": plain_label, "judge": result["label"], "violated": violated}

    class Handler(BaseHTTPRequestHandler):
        def _send(self, code, body, ctype="application/json"):
            data = body if isinstance(body, bytes) else json.dumps(body, ensure_ascii=False).encode()
            self.send_response(code)
            self.send_header("Content-Type", f"{ctype}; charset=utf-8")
            self.send_header("Content-Length", str(len(data)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(data)

        def do_GET(self):
            self.path = self.path.split("?", 1)[0].split("#", 1)[0]
            if self.path in ("/", "/index.html"):
                return self._send(200, PAGE.read_bytes(), "text/html")
            if self.path.startswith("/narration/"):
                f = Path(__file__).with_name("narration") / Path(self.path).name
                if f.suffix in (".mp3", ".json") and f.exists():
                    return self._send(200, f.read_bytes(), "audio/mpeg" if f.suffix == ".mp3" else "application/json")
                return self._send(404, {"error": "not found"})
            if self.path == "/dashboard":
                return self._send(200, DASHBOARD.read_bytes(), "text/html")
            if self.path == "/api/dashboard":
                return self._send(200, dashboard or {"error": "no dashboard data loaded"})
            if self.path == "/api/state":
                rulebook = {t: {"principles": a.get("principles", []), "rules": a["rules"],
                                "loo": a.get("loo_train_accuracy")} for t, a in topics.items()}
                return self._send(200, {"model": llm.model_name(), "provider": llm.PROVIDER, "rulebook": rulebook,
                                        "examples": examples, "scores": scores})
            self._send(404, {"error": "not found"})

        def do_POST(self):
            if self.path != "/api/judge":
                return self._send(404, {"error": "not found"})
            try:
                row = json.loads(self.rfile.read(int(self.headers.get("Content-Length", 0))))
                if row.get("topic") not in topics:
                    return self._send(400, {"error": f"topic must be one of {sorted(topics)}"})
                row.setdefault("item_id", "live")
                return self._send(200, judge(row))
            except Exception as error:  # show the reason in the UI instead of a blank screen
                return self._send(500, {"error": f"The model call failed: {str(error)[:300]}"})

        def log_message(self, *args):
            pass

    return Handler


def main():
    ap = argparse.ArgumentParser()
    root = Path(__file__).resolve().parent.parent  # defaults: the demo bundle shipped in the repo (final public run)
    ap.add_argument("--artifacts", default=str(root / "demo"), help="directory with rulebook.json")
    ap.add_argument("--examples", default=str(root / "examples" / "demo_test_conversations.jsonl"),
                    help="unlabeled or labeled JSONL to offer as presets")
    ap.add_argument("--scores", default=str(root / "examples" / "demo_scores.json"),
                    help="JSON with before/after results to display")
    ap.add_argument("--host", default="127.0.0.1", help="0.0.0.0 inside Docker")
    ap.add_argument("--port", type=int, default=8765)
    ap.add_argument("--gold", default=str(root / "data" / "public_test.csv"), help="labeled test CSV for the dashboard")
    ap.add_argument("--plain-preds", default=str(root / "demo" / "plain_gemma_predictions.csv"),
                    help="plain-Gemma predictions CSV (item_id,label)")
    ap.add_argument("--ours-preds", default=str(root / "demo" / "rulebook_judge_predictions.jsonl"),
                    help="predictions_explained.jsonl written by eval")
    args = ap.parse_args()
    book = json.loads((Path(args.artifacts) / "rulebook.json").read_text())
    examples = []
    if args.examples:
        for line in Path(args.examples).read_text().splitlines():
            if line.strip():
                r = json.loads(line)
                examples.append({k: r.get(k) for k in ("item_id", "topic", "context", "conversation", "label")})
    scores = json.loads(Path(args.scores).read_text()) if args.scores else {}
    dashboard = (dashboard_data(book, args.gold, args.plain_preds, args.ours_preds, scores)
                 if args.gold and args.plain_preds and args.ours_preds else None)
    server = ThreadingHTTPServer((args.host, args.port), make_handler(book, examples, scores, dashboard))
    print(f"Demo on http://localhost:{args.port}/dashboard  (live judge: {llm.model_name()} via {llm.PROVIDER})",
          flush=True)
    server.serve_forever()


if __name__ == "__main__":
    main()
