# Cloud lab release

This separate composition uses a named Firestore database for lab projections,
transactional events/create receipts, capture producer fences, latest redacted
frames, provider leases/cooldown and sanitized attempt metadata. It does not start
mixed-language workers or local SQLite services. Run `python -m prototypes.cloud_lab`.

Require KIKI_GCP_PROJECT=kiki-512012, KIKI_FIRESTORE_DATABASE=kiki-firedb,
KIKI_PROXY_SECRET from pinned Secret Manager version, GEMINI_API_KEYS from the
approved JSON-array secret, KIKI_REQUIRE_PROXY=1. PORT defaults to8080.
Use the dedicated kiki-lab runtime identity. Engine ingress requires Cloud Run IAM;
only kiki-api may invoke it. Application proxy/owner checks remain mandatory.

Frames are private transient Firestore chunks, isolated from immutable CAM media.
Only the latest redacted upload and checked image are held. Access expires after
30 seconds; capture freshness and lease fences further restrict reads. Replacement
and Stop delete pixels immediately. Configure expires_at TTL for the four collection
groups in firestore-retention.json; TTL is asynchronous cleanup after process death,
never an access-control mechanism. Disable indexing of raw byte fields.
No backups/PITR/export/archive for these frame collections is enabled by this release.

Build only after source is reviewed and merged to main. Submit Cloud Build with
cloudbuild.lab.yaml, explicit existing kiki-build identity, CLOUD_LOGGING_ONLY,
source staging gs://kiki-512012-build-source/source and immutable commit tags.
Record actual image digest/revision. Deploy initially min0/max1, one worker and
concurrency16; this bound is a cost control, not proof of durability. Independent
clients/replacement tests remain required. Fresh Share is required after a producer
lease expires or the worker is replaced. Do not silently restore capture.

Offline unit tests are separate from KIKI_CLOUD_CONTRACT=1 real named-database tests.
Those use unique contract prefixes and delete only their own fixture documents.
Real provider/student progress, native extension and hosted audio acceptance must be
recorded independently; no synthetic pass/evidence is a student result.
