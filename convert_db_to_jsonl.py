#!/usr/bin/env python3
import sqlite3, json, os
def convert_db(db_path, out_dir):
    if not os.path.exists(db_path): return False
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [r[0] for r in cursor.fetchall()]
    out_path = os.path.join(out_dir, os.path.basename(db_path).replace('.db','.jsonl'))
    with open(out_path, 'w') as f:
        for t in tables:
            for row in conn.execute(f"SELECT * FROM {t}"):
                f.write(json.dumps(dict(row), ensure_ascii=False)+'\n')
    conn.close()
    return True
