PRAGMA application_id = 1097627721;
PRAGMA user_version = 1;

CREATE TABLE metadata (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
) WITHOUT ROWID;

CREATE TABLE releases (
    release_id TEXT PRIMARY KEY,
    source_release_id TEXT NOT NULL,
    path TEXT NOT NULL,
    manifest_sha256 TEXT NOT NULL,
    release_name TEXT NOT NULL,
    created_at TEXT NOT NULL,
    active INTEGER NOT NULL CHECK (active IN (0, 1)),
    manifest_json TEXT NOT NULL
) WITHOUT ROWID;

CREATE TABLE captures (
    release_id TEXT NOT NULL REFERENCES releases(release_id),
    capture_id TEXT NOT NULL,
    source_release_id TEXT NOT NULL,
    component TEXT NOT NULL,
    component_sha256 TEXT NOT NULL,
    venue TEXT NOT NULL,
    chain TEXT NOT NULL,
    evidence_class TEXT NOT NULL,
    scope_kind TEXT NOT NULL,
    capture_json TEXT NOT NULL,
    mapping_json TEXT NOT NULL,
    PRIMARY KEY (release_id, capture_id)
) WITHOUT ROWID;

CREATE TABLE credit_events (
    release_id TEXT NOT NULL REFERENCES releases(release_id),
    row_id TEXT NOT NULL,
    source_release_id TEXT NOT NULL,
    component TEXT NOT NULL,
    component_sha256 TEXT NOT NULL,
    capture_id TEXT NOT NULL,
    venue TEXT NOT NULL,
    chain TEXT NOT NULL,
    subject TEXT NOT NULL,
    address TEXT NOT NULL,
    event_family TEXT NOT NULL,
    observed_at INTEGER,
    block_number INTEGER,
    row_json TEXT NOT NULL,
    PRIMARY KEY (release_id, row_id)
) WITHOUT ROWID;

CREATE INDEX credit_events_address
ON credit_events(address, venue, chain, observed_at, row_id);

CREATE TABLE position_observations (
    release_id TEXT NOT NULL REFERENCES releases(release_id),
    row_id TEXT NOT NULL,
    source_release_id TEXT NOT NULL,
    component TEXT NOT NULL,
    component_sha256 TEXT NOT NULL,
    capture_id TEXT NOT NULL,
    venue TEXT NOT NULL,
    chain TEXT NOT NULL,
    subject TEXT NOT NULL,
    address TEXT NOT NULL,
    property TEXT NOT NULL,
    observed_at INTEGER,
    block_number INTEGER,
    row_json TEXT NOT NULL,
    PRIMARY KEY (release_id, row_id)
) WITHOUT ROWID;

CREATE INDEX position_observations_address
ON position_observations(address, venue, chain, observed_at, row_id);
