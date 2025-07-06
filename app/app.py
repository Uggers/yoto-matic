import os
import json
import time
import shutil
from flask import Flask, render_template, jsonify, request, redirect, url_for, flash
from werkzeug.utils import secure_filename
from threading import Thread

# Import our custom modules
import database as db
import scraper
import automation

app = Flask(__name__)
# A secret key is needed for flashing messages
app.config['SECRET_KEY'] = 'a-super-secret-key-that-you-should-change'

# --- App Initialization ---
# Ensure data directory exists
if not os.path.exists('data'):
    os.makedirs('data')
db.init_db() # Ensure DB table exists

def run_in_background(target_func, *args):
    """Helper to run a function in a background thread."""
    thread = Thread(target=target_func, args=args)
    thread.daemon = True
    thread.start()

# --- Frontend Routes ---
@app.route('/')
def dashboard():
    """Renders the main dashboard showing all playlists in the library."""
    all_playlists = db.get_all_playlists()
    return render_template('dashboard.html', playlists=all_playlists)

@app.route('/upload', methods=['GET', 'POST'])
def upload_page():
    if request.method == 'POST':
        # --- Form Validation ---
        title = request.form.get('title')
        cover_file = request.files.get('cover_image')
        audio_files = request.files.getlist('audio_files')

        if not title or not cover_file or not audio_files:
            flash('Title, a cover image, and at least one audio file are required.', 'danger')
            return render_template('upload.html')

        # Create a temporary directory for this upload
        upload_id = str(int(time.time()))
        temp_dir = os.path.join('data', 'temp', upload_id)
        os.makedirs(temp_dir, exist_ok=True)

        description = request.form.get('description', '')

        # Save files temporarily
        cover_path = os.path.join(temp_dir, secure_filename(cover_file.filename))
        cover_file.save(cover_path)

        audio_paths = []
        for f in audio_files:
            path = os.path.join(temp_dir, secure_filename(f.filename))
            f.save(path)
            audio_paths.append(path)
        
        # Run the automation in a background thread to not block the UI
        run_in_background(automation.upload_new_playlist, title, description, cover_path, audio_paths, temp_dir)
        
        flash(f"Upload for '{title}' has started in the background. It will appear on your Yoto account shortly.", 'info')
        return redirect(url_for('dashboard'))

    return render_template('upload.html')

@app.route('/settings', methods=['GET', 'POST'])
def settings_page():
    settings_path = os.path.join('data', 'settings.json')
    if request.method == 'POST':
        settings = {
            "yoto_email": request.form.get('yoto_email'),
            "yoto_password": request.form.get('yoto_password')
        }
        with open(settings_path, 'w') as f:
            json.dump(settings, f)
        flash('Settings saved successfully!', 'success')
        return redirect(url_for('settings_page'))
    
    current_settings = {}
    if os.path.exists(settings_path):
        with open(settings_path, 'r') as f:
            current_settings = json.load(f)
    
    return render_template('settings.html', settings=current_settings)

# --- API Routes ---
@app.route('/api/sync-library', methods=['POST'])
def trigger_sync():
    """Triggers the library sync process in the background."""
    run_in_background(scraper.sync_library_from_yoto)
    return jsonify({"status": "Sync started. Refresh the dashboard in a few moments to see updates."})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)