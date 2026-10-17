#!/usr/bin/env python3
"""Export app-native records, or explicitly publish using the merged kiki-web implementation."""
import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from prototypes.concept_library.library import ConceptLibrary
from prototypes.concept_library.web_adapter import connect, package


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--web-root', required=True, type=Path)
    parser.add_argument('--output', type=Path, default=Path('work/concept-media-export'))
    parser.add_argument('--concepts', nargs='+')
    parser.add_argument('--apply', action='store_true')
    parser.add_argument('--project')
    parser.add_argument('--bucket')
    parser.add_argument('--expected-current', help='Explicit expected media head; requires one concept')
    args = parser.parse_args()
    library = ConceptLibrary()
    try:
        concepts = args.concepts or [c['concept_id'] for c in library.concepts()]
        prepared = [(cid, *package(cid, args.web_root, library)) for cid in concepts]
        if args.apply and (not args.project or not args.bucket):
            raise ValueError('--apply requires the approved --project and existing private --bucket')
        if args.expected_current and len(concepts) != 1:
            raise ValueError('--expected-current requires exactly one concept')
        if args.apply and any(not p.manifest.narration and not p.manifest.artifacts for _, p, _ in prepared):
            raise ValueError('Some concepts have no app-compatible media. Select supported concepts explicitly; all originals remain in the library.')
        args.output.mkdir(parents=True, exist_ok=True)
        report = []
        for cid, p, exclusions in prepared:
            (args.output / (cid + '.json')).write_text(json.dumps(p.record, ensure_ascii=False, indent=2) + '\n', encoding='utf-8', newline='\n')
            report.append({'conceptId': cid, 'mediaRevision': p.manifest.mediaRevision, 'narration': len(p.manifest.narration),
                'artifacts': len(p.manifest.artifacts), 'exclusions': exclusions,
                'hasAppCompatibleMedia': bool(p.manifest.narration or p.manifest.artifacts),
                'fullPacketProjected': not exclusions, 'cloudStatus': 'not_written'})
        if args.apply:
            from firebase_admin import firestore, initialize_app, storage
            _, media, _ = connect(args.web_root)
            app = initialize_app(options={'projectId': args.project}, name='kiki-library-import')
            client = firestore.client(app=app)
            for cid, p, _ in prepared:
                head = client.document('learningCatalog/LP-ANALOG-MODULATION').get(timeout=10)
                if (head.to_dict() or {}).get('currentVersion') != p.manifest.catalogVersion:
                    raise ValueError('Active catalog differs; publication stopped')
            # Use the existing native publisher's immutable records, object storage and head preconditions.
            store = media.BucketMediaAssets(storage.bucket(args.bucket, app=app))
            for row, (_, p, _) in zip(report, prepared):
                row['cloudStatus'] = media.publish(client, store, p, args.expected_current)
        (args.output / 'compatibility.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8', newline='\n')
        print(json.dumps(report, indent=2))
        return 0
    finally:
        library.close()


if __name__ == '__main__':
    try:
        sys.exit(main())
    except (ValueError, KeyError) as error:
        sys.exit(str(error))
