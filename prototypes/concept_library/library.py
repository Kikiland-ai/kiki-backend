"""SQLite metadata and immutable file assets. No generation, credentials or cloud writes."""
import hashlib
import json
from pathlib import Path
import sqlite3

from prototypes.mixed_script.speech import inspect_wav

ROOT = Path(__file__).resolve().parents[2] / 'artifacts/cam-review'
DATABASE = ROOT / 'concept-library.sqlite3'


def sha(data):
    return hashlib.sha256(data).hexdigest()


def encoded(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'), allow_nan=False)


def validate(folder):
    folder = Path(folder)
    p = json.loads((folder / 'packet.json').read_text())
    if p.get('schema') != 'cam-concept-packet/v1':
        raise ValueError('Unsupported packet schema')
    if [c['kind'] for c in p['placards']] != ['definition', 'concept', 'application', 'recap']:
        raise ValueError('Expected four ordered placards')
    for card in p['placards']:
        text = card['generatedMixed']
        if text['displayText'] != card['body']['or'] or ''.join(s['text'] for s in text['spans']) != text['displayText']:
            raise ValueError('Mixed text differs from its authored placard')
    covered = []
    for a in p['narration']:
        name = a['localFile']
        if Path(name).name != name:
            raise ValueError('Unsafe asset filename')
        data = (folder / name).read_bytes()
        measured = inspect_wav(data)
        if measured['sha256'] != a['audioSha256'] or measured['bytes'] != a['bytes'] or measured['duration_seconds'] != a['durationSeconds']:
            raise ValueError('WAV differs from its saved measurements')
        rows = [r for r in p['placards'] if r['id'] in a['placardIds']]
        for field, key in [('speechText', 'speechTextSha256'), ('displayText', 'displayTextSha256')]:
            if sha(' '.join(r['generatedMixed'][field] for r in rows).encode()) != a[key]:
                raise ValueError('Narration text hash differs')
        covered.extend(a['placardIds'])
    if sorted(covered) != sorted(c['id'] for c in p['placards']):
        raise ValueError('Narration does not cover the four placards exactly once')
    if p['scene'] != json.loads((folder / 'scene.json').read_text()):
        raise ValueError('Scene differs from packet')
    return p


def build(database=DATABASE, root=ROOT):
    """Build a complete snapshot offline; atomically replace only after all inputs validate."""
    database, root = Path(database), Path(root).resolve()
    packets = [(folder.parent, validate(folder.parent)) for folder in sorted((root / 'site/dist/concepts').glob('C-AM-*/packet.json'))]
    if not packets:
        raise ValueError('No concept packets found')
    database.parent.mkdir(parents=True, exist_ok=True)
    temporary = database.with_name(database.name + '.tmp')
    if temporary.exists():
        raise ValueError('An unfinished build exists; inspect it before retrying')
    try:
        with sqlite3.connect(temporary) as conn:
            conn.executescript('''
                PRAGMA foreign_keys=ON;
                CREATE TABLE library_meta(key TEXT PRIMARY KEY,value TEXT NOT NULL);
                CREATE TABLE packets(concept_id TEXT NOT NULL,catalog_version TEXT NOT NULL,revision TEXT NOT NULL,title TEXT NOT NULL,packet_json TEXT NOT NULL,packet_sha256 TEXT NOT NULL,PRIMARY KEY(concept_id,catalog_version,revision));
                CREATE TABLE current_packets(concept_id TEXT PRIMARY KEY,catalog_version TEXT NOT NULL,revision TEXT NOT NULL,FOREIGN KEY(concept_id,catalog_version,revision) REFERENCES packets(concept_id,catalog_version,revision));
                CREATE TABLE assets(asset_id TEXT PRIMARY KEY,relative_path TEXT NOT NULL,mime_type TEXT NOT NULL,bytes INTEGER NOT NULL);
                CREATE TABLE narration(concept_id TEXT NOT NULL,revision TEXT NOT NULL,asset_id TEXT NOT NULL,scope TEXT NOT NULL,language TEXT NOT NULL,placard_ids_json TEXT NOT NULL,metadata_json TEXT NOT NULL,FOREIGN KEY(asset_id) REFERENCES assets(asset_id));
                CREATE TABLE artifacts(concept_id TEXT NOT NULL,revision TEXT NOT NULL,role TEXT NOT NULL,asset_id TEXT NOT NULL,FOREIGN KEY(asset_id) REFERENCES assets(asset_id));
            ''')
            conn.execute('INSERT INTO library_meta VALUES(?,?)', ('schema', 'kiki-concept-library/v1'))
            def asset(path, mime):
                data = path.read_bytes()
                identifier = sha(data)
                conn.execute('INSERT OR IGNORE INTO assets VALUES(?,?,?,?)', (identifier, str(path.resolve().relative_to(root)), mime, len(data)))
                return identifier
            for folder, p in packets:
                cid, version, revision = p['conceptId'], p['contentVersion'], p['experienceRevision']
                raw = encoded(p)
                conn.execute('INSERT INTO packets VALUES(?,?,?,?,?,?)', (cid, version, revision, p['title'], raw, sha(raw.encode())))
                conn.execute('INSERT INTO current_packets VALUES(?,?,?)', (cid, version, revision))
                for audio in p['narration']:
                    identifier = asset(folder / audio['localFile'], 'audio/wav')
                    conn.execute('INSERT INTO narration VALUES(?,?,?,?,?,?,?)', (cid, revision, identifier, audio['scope'], audio['language'], encoded(audio['placardIds']), encoded(audio)))
                for name, mime in [('scene.json', 'application/json'), ('poster.svg', 'image/svg+xml'), ('models.js', 'text/javascript'), ('player.js', 'text/javascript')]:
                    identifier = asset(folder / name, mime)
                    conn.execute('INSERT INTO artifacts VALUES(?,?,?,?)', (cid, revision, name, identifier))
            if conn.execute('PRAGMA integrity_check').fetchone()[0] != 'ok':
                raise ValueError('SQLite integrity check failed')
        conn.close()
        temporary.replace(database)
    except Exception:
        if 'conn' in locals():
            conn.close()
        if temporary.exists():
            temporary.unlink()
        raise
    return database


class ConceptLibrary:
    def __init__(self, database=DATABASE, root=ROOT):
        self.root = Path(root).resolve()
        self.connection = sqlite3.connect(Path(database).resolve().as_uri() + '?mode=ro', uri=True)
        self.connection.row_factory = sqlite3.Row
        if self.connection.execute("SELECT value FROM library_meta WHERE key='schema'").fetchone()[0] != 'kiki-concept-library/v1':
            raise ValueError('Unsupported library schema')

    def close(self):
        self.connection.close()

    def concepts(self):
        rows = self.connection.execute('SELECT p.concept_id,p.catalog_version,p.revision,p.title FROM packets p JOIN current_packets c USING(concept_id,catalog_version,revision) ORDER BY p.concept_id')
        return [dict(r) for r in rows]

    def packet(self, concept_id):
        row = self.connection.execute('SELECT p.packet_json,p.packet_sha256 FROM packets p JOIN current_packets c USING(concept_id,catalog_version,revision) WHERE concept_id=?', (concept_id,)).fetchone()
        if row is None:
            raise KeyError(concept_id)
        if sha(row['packet_json'].encode()) != row['packet_sha256']:
            raise ValueError('Stored packet checksum differs')
        return json.loads(row['packet_json'])

    def asset(self, asset_id):
        row = self.connection.execute('SELECT * FROM assets WHERE asset_id=?', (asset_id,)).fetchone()
        if row is None:
            raise KeyError(asset_id)
        path = (self.root / row['relative_path']).resolve()
        if not path.is_relative_to(self.root):
            raise ValueError('Asset path escapes the library')
        data = path.read_bytes()
        if len(data) != row['bytes'] or sha(data) != asset_id:
            raise ValueError('Asset checksum differs')
        return data, row['mime_type']
