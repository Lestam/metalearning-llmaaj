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
    ("intro", "Banks check their AI assistants with an AI judge, but a generic judge doesn't know the bank's rules, "
              "so it misses the mistakes a real expert would catch. That's why we built a judge that learns those rules itself. "
              "Gemma 4 reads conversations the expert marked good or bad, writes down the rules behind those labels, "
              "and then tests every rule on the data, keeping only the ones that hold up. "
              "The judge then applies exactly that rulebook to new conversations."),
    ("hero", "Here is what that changes. With the same model, the same test and the same metric, plain Gemma agrees with "
             "the expert seventy-nine percent of the time, and with the learned rulebook, ninety-three. In practice, the bad "
             "replies that slip through drop from sixteen out of thirty to just one."),
    ("topics", "Every topic improves, and spending improves the most, because its rules are definitions nobody can guess: "
               "refunds come off, and transfers between your own accounts don't count as spending."),
    ("steps", "We measured every step. The rulebook gave the first jump, asking the judge to recompute the numbers gave the "
              "second, and telling it to judge substance rather than wording stopped it from punishing good answers."),
    ("errors", "So where do the errors go? Plain Gemma is too lenient, and lets wrong figures and wrong promises through. "
               "Our judge is strict where the expert is strict, and the price is a few good replies rejected."),
    ("rulebook", "And because the rulebook is plain text, with every rule linked to the conversations that prove it, "
                 "compliance can read it, check it, and change it."),
    ("fails", "It isn't perfect. It still struggles with heavy arithmetic, and it can't catch a mistake the expert never showed it."),
    ("business", "For the business, judging one conversation costs about a fifth of a cent, and learning a new rulebook costs "
                 "about fifty cents and twenty minutes. So when a tariff changes, the expert labels a small sample, and the "
                 "judge simply re-learns, with no retraining."),
    ("next", "And one more thing. Next, we split the work: code checks the numbers without any model, the rulebook judge "
             "handles meaning, and the expert only looks where the two disagree."),
]


def key():
    try:
        return subprocess.run(["security", "find-generic-password", "-a", os.environ.get("USER", ""),
                               "-s", "elevenlabs-api-key", "-w"], capture_output=True, text=True, check=True).stdout.strip()
    except subprocess.CalledProcessError:
        sys.exit("no ElevenLabs key in the Keychain (service elevenlabs-api-key)")


def say(k, text, path, previous_text="", next_text="", calm=False):
    """previous_text / next_text let ElevenLabs keep the intonation continuous across separately recorded parts."""
    settings = ({"stability": .72, "similarity_boost": .8, "style": .12, "use_speaker_boost": True} if calm
                else {"stability": .55, "similarity_boost": .8, "style": .35, "use_speaker_boost": True})
    body = json.dumps({"text": text, "model_id": "eleven_multilingual_v2", "seed": 7, "voice_settings": settings,
                       "previous_text": previous_text, "next_text": next_text}).encode()
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
    for i, (name, text) in enumerate(LINES):
        path = os.path.join(OUT, f"{name}.mp3")
        if os.path.exists(path) and not o.force:
            continue
        say(k, text, path, previous_text=LINES[i - 1][1] if i else "",
            next_text=LINES[i + 1][1] if i + 1 < len(LINES) else "", calm=name != "intro")
        print("recorded", name, flush=True)
    json.dump([{"block": n, "text": t} for n, t in LINES], open(os.path.join(OUT, "script.json"), "w"), indent=1)


if __name__ == "__main__":
    main()
