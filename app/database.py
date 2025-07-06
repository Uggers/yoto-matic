import sqlite3
import os

DATABASE_PATH = os.path.join('data', 'yoto-matic.db')

def get_db_connection():
    """Creates a database connection."""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initializes the database and creates the table if it doesn't exist."""
    conn = get_db_connection()
    with conn:
        conn.execute('''
            CREATE TABLE IF NOT EXISTS playlists (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                author TEXT,
                cover_image_url TEXT,
                status TEXT
            )
        ''')
    conn.close()

def sync_scraped_playlists(playlists_data):
    """Clears and replaces the playlists table with freshly scraped data."""
    conn = get_db_connection()
    with conn:
        conn.execute('DELETE FROM playlists')
        for playlist in playlists_data:
            conn.execute('''
                INSERT INTO playlists (title, author, cover_image_url, status)
                VALUES (?, ?, ?, 'complete')
            ''', (
                playlist['title'],
                "Synced from Yoto",
                playlist['cover_image_url']
            ))
    conn.close()

def get_all_playlists():
    """Retrieves all playlists from the database."""
    conn = get_db_connection()
    playlists = conn.execute('SELECT * FROM playlists ORDER BY title').fetchall()
    conn.close()
    return playlists