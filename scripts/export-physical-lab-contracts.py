"""Export frontend-readable contracts without creating services or calling providers."""
import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from fastapi import FastAPI
from contracts.physical_lab import ExperimentPack, CreatePreparation, PreparationEvent
from prototypes.physical_labs.api import physical_lab_router


def main():
    parser = argparse.ArgumentParser(); parser.add_argument('--check', action='store_true'); args = parser.parse_args()
    root = Path(__file__).resolve().parents[1] / 'contracts'
    app = FastAPI(title='Kiki physical lab preparation', version='1.0.0')
    app.include_router(physical_lab_router(None, None, None))
    documents = {'physical-lab-pack.schema.json': ExperimentPack.model_json_schema(),
                 'physical-lab-create.schema.json': CreatePreparation.model_json_schema(),
                 'physical-lab-event.schema.json': PreparationEvent.model_json_schema(),
                 'physical-lab.openapi.json': app.openapi()}
    for name, value in documents.items():
        data = json.dumps(value, indent=2, sort_keys=True) + '\n'
        path = root / name
        if args.check:
            if not path.is_file() or path.read_text() != data:
                raise SystemExit('Stale physical lab contract: ' + name)
        else:
            path.write_text(data)
        print(name)


if __name__ == '__main__':
    main()
