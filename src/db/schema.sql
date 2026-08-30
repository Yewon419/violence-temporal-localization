-- Movie rating assistance — frame-level multi-label DB
-- PostgreSQL-compatible DDL. Runs on SQLite with minor caveats:
--   * SQLite ignores type lengths (TEXT vs VARCHAR(n) treated the same)
--   * SQLite stores ENUM as TEXT — CHECK constraints enforce the value set
--   * SQLite needs `PRAGMA foreign_keys = ON;` at connection time

CREATE TABLE IF NOT EXISTS videos (
    video_id        TEXT PRIMARY KEY,
    dataset_source  TEXT NOT NULL,
    title           TEXT,
    source_url      TEXT,
    duration_sec    INTEGER,
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_videos_source ON videos(dataset_source);

CREATE TABLE IF NOT EXISTS frames (
    video_id      TEXT NOT NULL REFERENCES videos(video_id) ON DELETE CASCADE,
    keyframe_idx  INTEGER NOT NULL,
    frame_time    TEXT NOT NULL,            -- HH:MM:SS.ms
    frame_path    TEXT NOT NULL,
    PRIMARY KEY (video_id, keyframe_idx)
);

CREATE INDEX IF NOT EXISTS idx_frames_video ON frames(video_id);

CREATE TABLE IF NOT EXISTS labels (
    video_id        TEXT NOT NULL,
    keyframe_idx    INTEGER NOT NULL,
    annotator_id    TEXT NOT NULL,
    violence        INTEGER NOT NULL DEFAULT 0 CHECK (violence IN (0, 1)),
    sexual          INTEGER NOT NULL DEFAULT 0 CHECK (sexual IN (0, 1)),
    smoking         INTEGER NOT NULL DEFAULT 0 CHECK (smoking IN (0, 1)),
    drinking        INTEGER NOT NULL DEFAULT 0 CHECK (drinking IN (0, 1)),
    horror          INTEGER NOT NULL DEFAULT 0 CHECK (horror IN (0, 1)),
    drug            INTEGER NOT NULL DEFAULT 0 CHECK (drug IN (0, 1)),
    tier            TEXT NOT NULL CHECK (tier IN ('strong', 'weak', 'human')),
    dataset_source  TEXT NOT NULL,
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (video_id, keyframe_idx, annotator_id),
    FOREIGN KEY (video_id, keyframe_idx) REFERENCES frames(video_id, keyframe_idx) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_labels_tier ON labels(tier);
CREATE INDEX IF NOT EXISTS idx_labels_source ON labels(dataset_source);

-- Raw segment-level human annotation (eval set only, pre-frame-conversion)
CREATE TABLE IF NOT EXISTS segment_labels (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    video_id        TEXT NOT NULL REFERENCES videos(video_id) ON DELETE CASCADE,
    annotator_id    TEXT NOT NULL,
    category        TEXT NOT NULL CHECK (category IN ('violence','sexual','smoking','drinking','horror','drug')),
    start_time      TEXT NOT NULL,
    end_time        TEXT NOT NULL,
    notes           TEXT
);

CREATE INDEX IF NOT EXISTS idx_segment_video ON segment_labels(video_id);
