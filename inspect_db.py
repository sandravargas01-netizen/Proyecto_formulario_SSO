import sqlite3
from pathlib import Path
for db_path in [Path('salud_ocupacional.db'), Path('instance') / 'salud_ocupacional.db']:
    print('---', db_path)
    print('exists', db_path.exists())
    if not db_path.exists():
        continue
    conn = sqlite3.connect(str(db_path))
    cur = conn.cursor()
    print('tables', [row[0] for row in cur.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()])
    try:
        cols = cur.execute('PRAGMA table_info(examenes)').fetchall()
        print('cols', cols)
        rows = cur.execute("SELECT rowid, fecha_examen, fecha_nuevo_control, fecha_registro FROM examenes WHERE fecha_examen = '' OR fecha_nuevo_control = '' OR fecha_registro = ''").fetchmany(20)
        print('invalid rows', rows)
    except sqlite3.OperationalError as e:
        print('error', e)
    conn.close()
cur = conn.cursor()
print('tables', [row[0] for row in cur.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()])
try:
    cols = cur.execute('PRAGMA table_info(examenes)').fetchall()
    print('cols', cols)
    rows = cur.execute("SELECT rowid, fecha_examen, fecha_nuevo_control, fecha_registro FROM examenes WHERE fecha_examen = '' OR fecha_nuevo_control = '' OR fecha_registro = ''").fetchmany(20)
    print('invalid rows', rows)
except sqlite3.OperationalError as e:
    print('error', e)
conn.close()
