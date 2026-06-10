import sqlite3
import os
from flask import Flask, request, jsonify, send_from_directory

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
app = Flask(__name__)
DB_PATH = os.path.join(BASE_DIR, 'records.db')

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn

def init_db():
    conn = get_db()
    conn.execute('''
        CREATE TABLE IF NOT EXISTS records (
            id TEXT PRIMARY KEY,
            datetime TEXT NOT NULL,
            gun TEXT NOT NULL,
            time_str TEXT NOT NULL,
            time_ms INTEGER NOT NULL,
            kpm REAL NOT NULL,
            created_at TEXT DEFAULT (datetime('now','localtime'))
        )
    ''')
    conn.commit()
    conn.close()

@app.route('/')
def index():
    return send_from_directory(BASE_DIR, 'index.html')

@app.route('/<path:filename>')
def static_files(filename):
    return send_from_directory(BASE_DIR, filename)

@app.route('/api/records', methods=['GET'])
def list_records():
    conn = get_db()
    rows = conn.execute('SELECT id, datetime, gun, time_str, time_ms, kpm FROM records').fetchall()
    conn.close()
    return jsonify([{
        'id': r['id'],
        'datetime': r['datetime'],
        'gun': r['gun'],
        'timeStr': r['time_str'],
        'timeMs': r['time_ms'],
        'kpm': r['kpm']
    } for r in rows])

@app.route('/api/records', methods=['POST'])
def add_record():
    data = request.get_json()
    if not data:
        return jsonify({'error': 'invalid json'}), 400

    required = ['id', 'datetime', 'gun', 'timeStr', 'timeMs', 'kpm']
    for field in required:
        if field not in data:
            return jsonify({'error': f'missing field: {field}'}), 400

    conn = get_db()
    try:
        conn.execute(
            'INSERT INTO records (id, datetime, gun, time_str, time_ms, kpm) VALUES (?, ?, ?, ?, ?, ?)',
            (data['id'], data['datetime'], data['gun'], data['timeStr'], data['timeMs'], data['kpm'])
        )
        conn.commit()
        return jsonify({'ok': True}), 201
    except sqlite3.IntegrityError:
        return jsonify({'error': 'duplicate id'}), 409
    finally:
        conn.close()

@app.route('/api/records/<record_id>', methods=['DELETE'])
def delete_record(record_id):
    conn = get_db()
    cursor = conn.execute('DELETE FROM records WHERE id = ?', (record_id,))
    conn.commit()
    if cursor.rowcount == 0:
        conn.close()
        return jsonify({'error': 'not found'}), 404
    conn.close()
    return jsonify({'ok': True})

if __name__ == '__main__':
    init_db()
    print(f'Database: {DB_PATH}')
    print('Server running at http://localhost:8520')
    app.run(host='0.0.0.0', port=8520, debug=False)
