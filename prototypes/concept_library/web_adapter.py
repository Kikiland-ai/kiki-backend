"""Project the saved library through the actual kiki-web media publisher, without schema forks."""
import importlib
import json
from pathlib import Path
import sys

from .library import ConceptLibrary


def connect(web_root):
    root = Path(web_root).resolve()
    sys.path.insert(0, str(root / 'apps/api/src'))
    return root, importlib.import_module('kiki_api.concept_media'), importlib.import_module('kiki_api.learning_catalog')


def package(concept_id, web_root, library=None):
    """Return an app-native package and explicit exclusions; never relabel concept audio."""
    root, media, catalog_module = connect(web_root)
    from kiki_api.learning_models import Lesson
    from kiki_api.media_models import MediaManifest

    owns_library = library is None
    library = library or ConceptLibrary()
    try:
        saved = library.packet(concept_id)
        catalog = catalog_module.build_catalog(root / 'data-model/ledgers/electronics/analog-modulation.json', root / 'data-model/cases/analog-modulation-odia.json')
        if catalog.version != saved['contentVersion']:
            raise ValueError('Saved content differs from the merged catalog version')
        base = f"learningCatalog/{saved['planId']}/versions/{catalog.version}"
        lesson = Lesson.model_validate(catalog.documents[f'{base}/lessons/{concept_id}'])
        source = catalog.documents[f'{base}/sourceConcepts/{concept_id}']
        if {c.id: {'en': c.body.en, 'or': c.body.or_} for c in lesson.placards} != {c['id']: c['body'] for c in saved['placards']}:
            raise ValueError('Saved placards differ from merged app source text')
        narration, assets, excluded = [], {}, []
        for clip in saved['narration']:
            if clip['scope'] != 'placard':
                excluded.append({'kind': 'narration', 'assetId': clip['audioSha256'], 'reason': 'App contract requires per-placard recordings; original concept recording retained in SQLite'})
                continue
            identifier = clip['audioSha256']
            data, mime = library.asset(identifier)
            assets[identifier] = data
            narration.append({'renditionId': clip['placardId'] + '.' + clip['language'], 'placardId': clip['placardId'],
                'lang': clip['language'], 'assetId': identifier, 'mimeType': mime, 'bytes': len(data), 'durationSeconds': clip['durationSeconds'],
                'sourceTextSha256': clip['displayTextSha256'], 'speechScriptSha256': clip['speechTextSha256'], 'audioSha256': identifier,
                'narrationKind': 'generated', 'speech': {'provider': 'Gemini Developer API', 'model': clip['providerModel'],
                    'voice': 'Kore', 'style': 'clear, patient Odia-English teaching narration',
                    'generator': 'kiki-backend prototypes/mixed_script/speech.py; recovered packet import',
                    'generatedAt': 'not_recorded_in_recovered_packet'},
                'timing': {'kind': 'clip_duration_only', 'alignment': 'not_performed'},
                'review': {'status': 'unreviewed', 'pronunciation': 'pending', 'nativeOdia': 'pending', 'spokenFidelity': 'pending', 'audioQuality': 'pending'}})
        artifacts = [catalog_module.dump(s) for s in media.SCENES.get(concept_id, lambda *_: [])(source, lesson)]
        if not artifacts:
            excluded.append({'kind': 'scene', 'reason': 'App currently allowlists coherent-phase-recovery/v1 only; original scene retained in SQLite'})
        body = {'schema': 'concept-media-manifest/v1', 'planId': saved['planId'], 'conceptId': concept_id, 'catalogVersion': catalog.version,
            'release': 'sample_unreviewed', 'narration': narration, 'artifacts': artifacts}
        revision = 'cm-' + catalog_module.digest({'projectionSchema': 1, 'manifest': body})[:24]
        manifest = MediaManifest.model_validate({**body, 'mediaRevision': revision})
        media.bind(manifest, lesson, source)
        record = {'schema': 'concept-media-revision/v1', 'manifest': catalog_module.dump(manifest),
            'assets': {r.assetId: {'path': media.asset_path(r.assetId), 'mimeType': r.mimeType, 'bytes': r.bytes} for r in manifest.narration}}
        return media.MediaPackage(manifest, record, assets), excluded
    finally:
        if owns_library:
            library.close()
