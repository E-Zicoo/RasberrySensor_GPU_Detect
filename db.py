import os, sqlite3
from contextlib import closing

DB_PATH = os.environ.get("ENV_DB_PATH", os.path.abspath("./gpu.sqlite"))

def get_conn():
    conn = sqlite3.connect(DB_PATH, detect_types=sqlite3.PARSE_DECLTYPES|sqlite3.PARSE_COLNAMES)
    conn.row_factory = sqlite3.Row
    return conn

def latest_points(limit=180):
    with closing(get_conn()) as conn, closing(conn.cursor()) as cur:
        cur.execute("""            SELECT ts, light, temperature, distance
            FROM readings
            ORDER BY ts DESC
            LIMIT ?
        """, (limit,))
        rows = cur.fetchall()
        return list(reversed([dict(r) for r in rows]))

def points_between(start_iso, end_iso):
    with closing(get_conn()) as conn, closing(conn.cursor()) as cur:
        cur.execute("""            SELECT ts, light, temperature, distance
            FROM readings
            WHERE ts >= ? AND ts <= ?
            ORDER BY ts ASC
        """, (start_iso, end_iso))
        return [dict(r) for r in cur.fetchall()]

def list_dates():
    with closing(get_conn()) as conn, closing(conn.cursor()) as cur:
        cur.execute("""            SELECT substr(ts,1,10) AS d, COUNT(*) AS n
            FROM readings
            GROUP BY substr(ts,1,10)
            ORDER BY d DESC
        """ )
        return [dict(r) for r in cur.fetchall()]
