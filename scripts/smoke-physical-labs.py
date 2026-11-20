"""Synthetic HTTP acceptance through the actual unified backend; no provider calls.

Answers are read from authoring content ONLY in this developer smoke script.
The browser/API never receives answer keys. Output is labelled synthetic.
"""
import json
from pathlib import Path
import sys
import tempfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from fastapi.testclient import TestClient
from prototypes.backend.app import create_app
from prototypes.physical_labs.service import load_packs


def main():
    pack = load_packs()['dsb-sc-trainer']
    with tempfile.TemporaryDirectory() as directory:
        app = create_app(Path(directory), proxy_secret='')
        with TestClient(app) as client:
            client.get('/')
            headers = {'Origin': 'http://testserver', 'Idempotency-Key': 'synthetic-dsb-sc'}
            response = client.post('/v1/physical-labs/sessions', json={'experiment_id': pack['id']}, headers=headers)
            response.raise_for_status(); state = response.json()
            stages = [state['stage']]
            def send(kind, **fields):
                nonlocal state
                response = client.post(state['links']['events'], headers=headers, json={
                    'event_id': f'synthetic-{state["revision"]}', 'revision': state['revision'], 'kind': kind, **fields})
                response.raise_for_status(); state = response.json()
                if stages[-1] != state['stage']: stages.append(state['stage'])
            answers = lambda questions: {q['id']: q['correct'] for q in questions}
            for target in pack['orientation']: send('select', target=target)
            send('advance')
            for c in pack['concepts']: send('answer', target=c['id'], answers=answers(c['questions']))
            send('advance')
            for _ in pack['steps']: send('advance')
            for s in pack['steps']:
                rule = {k: v for k, v in s['rule'].items() if k != 'tolerance'}
                send(rule.pop('kind'), **rule)
            for f in pack['faults']: send('answer', target=f['id'], answers=answers([f['question']]))
            send('advance')
            send('answer', target='readiness', answers=answers(pack['assessment']))
            receipt = client.get(state['activity']['receipt_url']); receipt.raise_for_status()
            observation = client.get(state['links']['observations']); observation.raise_for_status()
            assert state['stage'] == 'prepared'
            assert receipt.json()['physical_execution'] == 'not_performed'
            result = {'evidence_type': 'synthetic_http_acceptance', 'provider_calls': 0, 'stages': stages,
                      'revision': state['revision'], 'status': state['stage'], 'pack_sha256': state['pack_sha256'],
                      'readings': observation.json()['readings'], 'physical_execution': 'not_performed'}
            print(json.dumps(result, indent=2))
        app.state.store.db.close(); app.state.lab.store.db.close(); app.state.lab_keys.db.close()
        app.state.mixed_language.db.close()


if __name__ == '__main__':
    main()
