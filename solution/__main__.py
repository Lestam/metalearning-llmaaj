"""Entry point: `python -m solution adapt|eval|judge-one|demo [options]`."""
import sys

from . import adapt, demo, judge_one, predict

if __name__ == "__main__":
    commands = {"adapt": adapt, "eval": predict, "judge-one": judge_one, "demo": demo}
    if len(sys.argv) < 2 or sys.argv[1] not in commands:
        sys.exit("usage: python -m solution adapt|eval|judge-one|demo [options]")
    commands[sys.argv.pop(1)].main()
