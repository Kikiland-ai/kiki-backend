#!/usr/bin/env python3
"""Build, list or read the saved concept library. No provider or cloud calls."""
import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from prototypes.concept_library.library import DATABASE, ROOT, ConceptLibrary, build

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('command', choices=['build', 'list', 'get'])
parser.add_argument('concept', nargs='?')
parser.add_argument('--database', type=Path, default=DATABASE)
parser.add_argument('--root', type=Path, default=ROOT)
args = parser.parse_args()
if args.command == 'build':
    print(build(args.database, args.root))
else:
    library = ConceptLibrary(args.database, args.root)
    try:
        print(json.dumps(library.packet(args.concept) if args.command == 'get' else library.concepts(), ensure_ascii=False, indent=2))
    finally:
        library.close()
