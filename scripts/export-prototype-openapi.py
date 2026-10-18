"""Export route-derived frontend OpenAPI without network calls or worker startup."""
import json
from pathlib import Path
import sys
import tempfile
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from prototypes.backend.app import create_app

with tempfile.TemporaryDirectory() as directory:
    app=create_app(Path(directory),proxy_secret='')
    schema=app.openapi()
    schema['info']['description']='Locally implemented unified prototype. Hosted deployment and Site activation are pending. WebSocket envelopes and runtime lab projections are documented separately in docs/handoffs/frontend-api.md.'
    output=Path(__file__).resolve().parents[1]/'contracts/frontend.openapi.json'
    output.write_text(json.dumps(schema,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
    app.state.mixed_language.executor.shutdown(wait=False)
    app.state.mixed_language.db.close();app.state.store.db.close();app.state.lab.store.db.close();app.state.lab_keys.db.close()
    print('Exported',len(schema['paths']),'HTTP paths to contracts/frontend.openapi.json')
