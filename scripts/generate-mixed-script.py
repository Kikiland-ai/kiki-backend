#!/usr/bin/env python3
"""Run from any directory; credentials are read only from the process environment."""
import argparse
import json
import os
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from prototypes.mixed_script.pipeline import (
    DEFAULT_FIXTURE, DEFAULT_INPUT, DEFAULT_MODEL, FixtureGenerator,
    GeminiGenerator, PipelineError, read_json, run_pipeline, save_result, validate_input,
)


def main():
    parser = argparse.ArgumentParser(description="English -> Odia-led translation -> mixed text and speech script.")
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--mode", choices=["fixture", "gemini"], default="fixture",
                        help="fixture makes no API calls; gemini makes two requests")
    parser.add_argument("--fixture", type=Path, default=DEFAULT_FIXTURE)
    parser.add_argument("--model", default=os.environ.get("GEMINI_TEXT_MODEL", DEFAULT_MODEL))
    parser.add_argument("--output", type=Path, help="save JSON to a new file; existing files are preserved")
    args = parser.parse_args()
    try:
        if args.output and args.output.exists():
            raise PipelineError("Output already exists; choose a new output path.")
        if args.output and not args.output.parent.is_dir():
            raise PipelineError("Output parent directory does not exist.")
        source = read_json(args.input)
        validate_input(source)
        generator = (FixtureGenerator(read_json(args.fixture)) if args.mode == "fixture" else
                     GeminiGenerator(os.environ.get("GEMINI_API_KEY", ""), model=args.model))
        result = run_pipeline(source, generator)
        if args.output:
            save_result(result, args.output)
            print(f"Saved {args.mode} result to {args.output}")
            print(result["paragraph"])
            print("Meaning/Odia review pending. Audio has not been generated.")
        else:
            print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except PipelineError as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
