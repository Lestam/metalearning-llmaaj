"""Entry point: `python -m solution adapt|eval|judge-one [options]`."""
import sys

from . import adapt, judge_one, predict

if __name__ == "__main__":
    commands = {"adapt": adapt, "eval": predict, "judge-one": judge_one}
    if len(sys.argv) < 2 or sys.argv[1] not in commands:
        sys.exit("usage: python -m solution adapt|eval|judge-one [options]")
    commands[sys.argv.pop(1)].main()
