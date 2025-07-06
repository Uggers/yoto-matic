import sqlite3
import os

DATABASE_PATH = os.path.join('data', 'yoto-matic.db')

def get_db_connection():
    """Creates a database connection."""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initializes the database and creates the tables if they don't exist."""
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
        conn.execute('''
            CREATE TABLE IF NOT EXISTS activity_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                playlist_title TEXT NOT NULL,
                status TEXT NOT NULL,
                details TEXT
            )
        ''')
        # NEW TABLE FOR THE PRINT QUEUE
        conn.execute('''
            CREATE TABLE IF NOT EXISTS print_queue (
                id INTEGER PRIMARY KEY,
                FOREIGN KEY (id) REFERENCES playlists (id)
            )
        ''')
    conn.close()

def log_activity(title, status, details=""):
    """Adds a new record to the activity log."""
    # (This function is unchanged)
    conn = get_db_connection()
    with conn:
        conn.execute("INSERT INTO activity_log (playlist_title, status, details) VALUES (?, ?, ?)", (title, status, details))
    conn.close()

def get_activity_logs():
    """Retrieves all activity logs, newest first."""
    # (This function is unchanged)
    conn = get_db_connection()
    logs = conn.execute('SELECT * FROM activity_log ORDER BY timestamp DESC').fetchall()
    conn.close()
    return logs

def sync_scraped_playlists(playlists_data):
    """Clears and replaces the playlists table with freshly scraped data."""
    # (This function is unchanged)
    conn = get_db_connection()
    with conn:
        conn.execute('DELETE FROM playlists')
        for playlist in playlists_data:
            conn.execute("INSERT INTO playlists (title, author, cover_image_url, status) VALUES (?, ?, ?, 'complete')",
                         (playlist['title'], "Synced from Yoto", playlist['cover_image_url']))
    conn.close()

def get_all_playlists():
    """Retrieves all playlists from the database."""
    # (This function is unchanged)
    conn = get_db_connection()
    playlists = conn.execute('SELECT * FROM playlists ORDER BY title').fetchall()
    conn.close()
    return playlists

# --- NEW PRINT QUEUE FUNCTIONS ---
def add_to_print_queue(playlist_id):
    """Adds a playlist to the print queue, ignoring duplicates."""
    conn = get_db_connection()
    with conn:
        conn.execute("INSERT OR IGNORE INTO print_queue (id) VALUES (?)", (playlist_id,))
    conn.close()

def remove_from_print_queue(playlist_id):
    """Removes a playlist from the print queue."""
    conn = get_db_connection()
    with conn:
        conn.execute("DELETE FROM print_queue WHERE id = ?", (playlist_id,))
    conn.close()

def get_print_queue_count():
    """Gets the number of items in the print queue."""
    conn = get_db_connection()
    count = conn.execute("SELECT COUNT(id) FROM print_queue").fetchone()[0]
    conn.close()
    return count

def get_print_queue_items():
    """Gets all playlist details for items in the print queue."""
    conn = get_db_connection()
    items = conn.execute("""
        SELECT p.id, p.title, p.cover_image_url 
        FROM playlists p JOIN print_queue pq ON p.id = pq.id
    """).fetchall()
    conn.close()
    return items

def clear_print_queue():
    """Empties the entire print queue."""
    conn = get_db_connection()
    with conn:
        conn.execute("DELETE FROM print_queue")
    conn.close()