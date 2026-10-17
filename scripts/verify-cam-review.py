#!/usr/bin/env python3
"""Verify recovered, versioned C-AM review assets without provider calls."""
import hashlib
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from prototypes.mixed_script.speech import inspect_wav


def main():
    root = Path(__file__).resolve().parents[1] / 'artifacts/cam-review'
    manifest = json.loads((root / 'recovery-manifest.json').read_text())
    site = root / 'site'
    for entry in manifest['files']:
        path = site / entry['path']
        data = path.read_bytes()
        assert len(data) == entry['bytes'], path
        assert hashlib.sha256(data).hexdigest() == entry['sha256'], path
    total, clips, cards = 0, 0, 0
    records = []
    for i in range(1, 11):
        cid = f'C-AM-{i:02}'
        folder = site / 'dist/concepts' / cid
        packet = json.loads((folder / 'packet.json').read_text())
        assert packet['conceptId'] == cid
        assert packet['contentVersion'] == 'am-51187527300cba2fa3cca868'
        assert packet['sourceGitRevision'] == 'ba40218d7bf07637debe530019bcf8faf6afb61a'
        assert packet['scene'] == json.loads((folder / 'scene.json').read_text())
        assert [p['kind'] for p in packet['placards']] == ['definition', 'concept', 'application', 'recap']
        assert packet['alignment'] == 'not_performed'
        assert packet['publication']['firestore'] == 'not_written'
        for card in packet['placards']:
            mixed = card['generatedMixed']
            assert mixed['displayText'] == card['body']['or']
            assert ''.join(s['text'] for s in mixed['spans']) == mixed['displayText']
        covered = []
        for audio in packet['narration']:
            filename = audio['localFile']
            assert Path(filename).name == filename
            measured = inspect_wav((folder / filename).read_bytes())
            assert measured['sha256'] == audio['audioSha256']
            assert measured['bytes'] == audio['bytes']
            assert measured['duration_seconds'] == audio['durationSeconds']
            rows = [r for r in packet['placards'] if r['id'] in audio['placardIds']]
            for field, key in [('speechText', 'speechTextSha256'), ('displayText', 'displayTextSha256')]:
                text = ' '.join(r['generatedMixed'][field] for r in rows)
                assert hashlib.sha256(text.encode()).hexdigest() == audio[key]
            covered.extend(audio['placardIds'])
            total += audio['durationSeconds']
            clips += 1
        assert sorted(covered) == sorted(r['id'] for r in packet['placards'])
        assert (folder / 'models.js').read_bytes() == (site / 'dist/concepts/C-AM-01/models.js').read_bytes()
        assert (folder / 'player.js').read_bytes() == (site / 'dist/concepts/C-AM-01/player.js').read_bytes()
        cards += len(packet['placards'])
        records.append({'conceptId': cid, 'title': packet['title'], 'experienceRevision': packet['experienceRevision']})
    assert (clips, cards) == (22, 40)
    assert abs(total - 793.8) < .001
    print(json.dumps({'status': 'passed', 'files': len(manifest['files']), 'concepts': len(records), 'placards': cards,
        'audioClips': clips, 'durationSeconds': round(total, 2), 'providerCalls': 0}))


if __name__ == '__main__':
    main()
