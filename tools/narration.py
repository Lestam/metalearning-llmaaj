"""Record the dashboard's audio walkthrough with ElevenLabs (voice david_arena, eleven_multilingual_v2).

One mp3 per dashboard block in solution/narration/; the dashboard plays them in order and highlights each block.
The API key is read from the macOS Keychain (service "elevenlabs-api-key") for the requests only, never printed.
Usage: python tools/narration.py [--force]
"""
import argparse
import json
import os
import subprocess
import sys
import urllib.error
import urllib.request

API = "https://api.elevenlabs.io/v1/text-to-speech/{voice}?output_format=mp3_44100_128"
VOICE = "DduhIyyKkOosbP8VefhP"  # david_arena — the voice of the Dead Fools Club and TRRRack trailers
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "solution", "narration")

LINES = [
    ("intro", "Banks check their AI assistants with an AI judge. But a generic judge doesn't know the bank's rules. "
              "So it misses mistakes a real expert would catch. We built a judge that learns the expert's rules. "
              "Gemma 4 reads conversations the expert marked good or bad, and writes down the rules behind those labels. "
              "Then it tests every rule on the data, and keeps only the ones that hold up. "
              "The judge applies exactly that rulebook to new conversations."),
    ("hero", "Same model. Same test. Same metric. Plain Gemma agrees with the expert seventy-nine percent of the time. "
             "With the learned rulebook, ninety-one. Bad replies slipping through drop from sixteen out of thirty, to three."),
    ("topics", "Every topic improves. Spending gains the most, because its rules are definitions nobody can guess. "
               "Refunds come off. Transfers between your own accounts are not spending."),
    ("steps", "Each step was measured. The rulebook gave the first jump. Making the judge recompute the numbers gave the second. "
              "Judging substance, not wording, stopped it from punishing good answers."),
    ("errors", "Plain Gemma is too lenient. It accepts wrong figures and wrong product promises. "
               "Our judge is strict where the expert is strict. The price is a few good replies rejected."),
    ("rulebook", "The rulebook is plain text. Every rule links to the conversations that prove it. "
                 "So compliance can read it, check it, and change it."),
    ("fails", "It still struggles with heavy arithmetic. And it can't catch a mistake the expert never showed it."),
    ("business", "Judging one conversation costs about a fifth of a cent. Learning a new rulebook costs about fifty cents, "
                 "and twenty minutes. When a tariff changes, the expert labels a small sample, and the judge re-learns. No retraining."),
    ("next", "One more thing. Next, we split the work. Code checks the numbers, with no model at all. "
             "The rulebook judge handles meaning. And the expert looks only where the two disagree."),
]


def key():
    try:
        return subprocess.run(["security", "find-generic-password", "-a", os.environ.get("USER", ""),
                               "-s", "elevenlabs-api-key", "-w"], capture_output=True, text=True, check=True).stdout.strip()
    except subprocess.CalledProcessError:
        sys.exit("no ElevenLabs key in the Keychain (service elevenlabs-api-key)")


def say(k, text, path):
    body = json.dumps({"text": text, "model_id": "eleven_multilingual_v2", "seed": 7,
                       "voice_settings": {"stability": .55, "similarity_boost": .8, "style": .35,
                                          "use_speaker_boost": True}}).encode()
    req = urllib.request.Request(API.format(voice=VOICE), data=body, headers={
        "xi-api-key": k, "Content-Type": "application/json", "Accept": "audio/mpeg"})
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            open(path, "wb").write(r.read())
    except urllib.error.HTTPError as e:
        sys.exit(f"ElevenLabs {e.code}: {e.read()[:300]!r}")


def main():
    a = argparse.ArgumentParser(); a.add_argument("--force", action="store_true"); o = a.parse_args()
    os.makedirs(OUT, exist_ok=True)
    k = key()
    for name, text in LINES:
        path = os.path.join(OUT, f"{name}.mp3")
        if os.path.exists(path) and not o.force:
            continue
        say(k, text, path)
        print("recorded", name, flush=True)
    json.dump([{"block": n, "text": t} for n, t in LINES], open(os.path.join(OUT, "script.json"), "w"), indent=1)


if __name__ == "__main__":
    main()
