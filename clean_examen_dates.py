import sqlite3
from pathlib import Path

path = Path('instance') / 'salud_ocupacional.db'
if not path.exists():
    raise SystemExit('Database not found: ' + str(path))

conn = sqlite3.connect(str(path))
cur = conn.cursor()
print('tables', [r[0] for r in cur.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()])
print('cols', cur.execute('PRAGMA table_info(examenes)').fetchall())
rows = cur.execute("SELECT rowid, fecha_examen, fecha_nuevo_control, fecha_registro FROM examenes WHERE fecha_examen = '' OR fecha_nuevo_control = '' OR fecha_registro = ''").fetchall()
print('invalid rows before', rows)
if rows:
    cur.execute("UPDATE examenes SET fecha_examen = NULL WHERE fecha_examen = ''")
    cur.execute("UPDATE examenes SET fecha_nuevo_control = NULL WHERE fecha_nuevo_control = ''")
    cur.execute("UPDATE examenes SET fecha_registro = date('now') WHERE fecha_registro = ''")
    conn.commit()
    rows = cur.execute("SELECT rowid, fecha_examen, fecha_nuevo_control, fecha_registro FROM examenes WHERE fecha_examen = '' OR fecha_nuevo_control = '' OR fecha_registro = ''").fetchall()
    print('invalid rows after', rows)
conn.close()
print('done')
