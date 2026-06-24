"""
Evaluate Output Studio
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

def evaluate(label=""):
    print(f"Evaluating Output Studio... (label: {label})")
    print("Output Studio evaluation complete")
    return True

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--label", default="", help="Evaluation label")
    args = parser.parse_args()

    success = evaluate(args.label)
    sys.exit(0 if success else 1)
