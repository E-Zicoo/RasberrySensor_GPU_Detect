CREATE TABLE IF NOT EXISTS readings (
  id          INTEGER PRIMARY KEY AUTOINCREMENT,
  ts          DATETIME NOT NULL DEFAULT (datetime('now')),
  light       REAL,
  temperature REAL,
  distance    REAL
);
CREATE INDEX IF NOT EXISTS idx_readings_ts ON readings(ts);
