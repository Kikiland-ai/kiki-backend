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


def package(concept_id, web_root, library=None, *, contract='v1'):
    """Return an app-native package and explicit exclusions; never relabel concept audio."""
    root, media, catalog_module = connect(web_root)
    from kiki_api.learning_models import Lesson
    from kiki_api.media_models import MediaManifest

    if contract not in ('v1', 'candidate-signal', 'candidate-cam'):
        raise ValueError('Unsupported media contract')
    if contract != 'v1':
        from .candidate_contract import candidate_manifest_model
        from kiki_api import media_models
        MediaManifest = candidate_manifest_model(media_models, signal=contract == 'candidate-signal')

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
        if contract == 'candidate-cam' and concept_id == 'C-AM-08':
            # Keep the app's complete bilingual package and phase renderer intact.
            return media.build_package(lesson, source, catalog.version, root/'data-model/media/C-AM-08'), []
        narration, assets, excluded = [], {}, []
        for clip in saved['narration']:
            if clip['scope'] != 'placard' and contract != 'candidate-cam':
                excluded.append({'kind': 'narration', 'assetId': clip['audioSha256'], 'reason': 'App contract requires per-placard recordings; original concept recording retained in SQLite'})
                continue
            if clip['scope'] == 'concept':
                expected = [c.id for c in lesson.placards]
                text = ' '.join(getattr(c.body, 'or_' if clip['language'] == 'or' else 'en') for c in lesson.placards)
                speech = ' '.join(c['generatedMixed']['speechText'] for c in saved['placards'])
                if clip['placardIds'] != expected or media.sha256(text) != clip['displayTextSha256'] or media.sha256(speech) != clip['speechTextSha256']:
                    raise ValueError('Concept narration differs from its complete ordered source scope')
                identity = {'scope':'concept', 'conceptId':concept_id, 'placardIds':expected,
                            'renditionId':f"{concept_id}.concept.{clip['language']}"}
            elif clip['scope'] == 'placard':
                identity = {'renditionId': clip['placardId']+'.'+clip['language'], 'placardId':clip['placardId']}
            else:
                raise ValueError('Unsupported narration scope')
            identifier = clip['audioSha256']
            data, mime = library.asset(identifier)
            assets[identifier] = data
            narration.append({**identity,
                'lang': clip['language'], 'assetId': identifier, 'mimeType': mime, 'bytes': len(data), 'durationSeconds': clip['durationSeconds'],
                'sourceTextSha256': clip['displayTextSha256'], 'speechScriptSha256': clip['speechTextSha256'], 'audioSha256': identifier,
                'narrationKind': 'generated', 'speech': {'provider': 'Gemini Developer API', 'model': clip['providerModel'],
                    'voice': 'Kore', 'style': 'clear, patient Odia-English teaching narration',
                    'generator': 'kiki-backend prototypes/mixed_script/speech.py; recovered packet import',
                    'generatedAt': 'not_recorded_in_recovered_packet'},
                'timing': {'kind': 'clip_duration_only', 'alignment': 'not_performed'},
                'review': {'status': 'unreviewed', 'pronunciation': 'pending', 'nativeOdia': 'pending', 'spokenFidelity': 'pending', 'audioQuality': 'pending'}})
        artifacts = [catalog_module.dump(s) for s in media.SCENES.get(concept_id, lambda *_: [])(source, lesson)]
        if contract == 'candidate-signal' and concept_id == 'C-AM-01':
            from .signal_scene import project_signal
            artifacts = [catalog_module.dump(project_signal(saved, source, lesson, media, library))]
        if contract == 'candidate-cam':
            from .canvas import project_canvas
            artifacts = [catalog_module.dump(project_canvas(saved, source, lesson, media, library))]
        if not artifacts:
            excluded.append({'kind': 'scene', 'reason': 'App currently allowlists coherent-phase-recovery/v1 only; original scene retained in SQLite'})
        body = {'schema': 'concept-media-manifest/v1', 'planId': saved['planId'], 'conceptId': concept_id, 'catalogVersion': catalog.version,
            'release': 'sample_unreviewed', 'narration': narration, 'artifacts': artifacts}
        revision = 'cm-' + catalog_module.digest({'projectionSchema': 1, 'manifest': body})[:24]
        manifest = MediaManifest.model_validate({**body, 'mediaRevision': revision})
        if contract == 'candidate-cam':
            from kiki_api import media_models
            legacy_part = media_models.MediaManifest.model_validate({**body, 'mediaRevision':revision,
                'narration':[r for r in narration if r.get('scope') != 'concept'], 'artifacts':[]})
            media.bind(legacy_part, lesson, source)
            cards = {c.id for c in lesson.placards}
            for artifact in manifest.artifacts:
                if any(p not in cards for p in artifact.placardIds) or [catalog_module.dump(b) for b in artifact.bindings] != media.scene_bindings(source):
                    raise ValueError('Canvas placement or authored source binding differs')
        else:
            media.bind(manifest, lesson, source)
        record = {'schema': 'concept-media-revision/v1', 'manifest': catalog_module.dump(manifest),
            'assets': {r.assetId: {'path': media.asset_path(r.assetId), 'mimeType': r.mimeType, 'bytes': r.bytes} for r in manifest.narration}}
        return media.MediaPackage(manifest, record, assets), excluded
    finally:
        if owns_library:
            library.close()
