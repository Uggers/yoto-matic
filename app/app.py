import os
import json
import time
import shutil
from flask import Flask, render_template, jsonify, request, redirect, url_for, flash
from werkzeug.utils import secure_filename
from threading import Thread

import database as db
import scraper
import automation
import parser

app = Flask(__name__)
app.config['SECRET_KEY'] = 'a-super-secret-key-that-you-should-change-again'

# --- Initialization & Helpers ---
db.init_db()
def run_in_background(target_func, *args):
    thread = Thread(target=target_func, args=args)
    thread.daemon = True
    thread.start()

# --- Frontend Routes ---
@app.route('/')
def dashboard():
    return render_template('dashboard.html', playlists=db.get_all_playlists())

@app.route('/activity')
def activity_page():
    return render_template('activity.html', logs=db.get_activity_logs())

@app.route('/settings', methods=['GET', 'POST'])
def settings_page():
    # ... (this route's code is unchanged from the previous version) ...
    settings_path = os.path.join('data', 'settings.json')
    if request.method == 'POST':
        settings = {"yoto_email": request.form.get('yoto_email'), "yoto_password": request.form.get('yoto_password')}
        with open(settings_path, 'w') as f:
            json.dump(settings, f)
        flash('Settings saved successfully!', 'success')
        return redirect(url_for('settings_page'))
    current_settings = {}
    if os.path.exists(settings_path):
        with open(settings_path, 'r') as f: current_settings = json.load(f)
    return render_template('settings.html', settings=current_settings)

# --- THE NEW BROWSER-BASED UPLOAD ROUTE ---
@app.route('/upload', methods=['GET', 'POST'])
def upload_page():
    if request.method == 'POST':
        files = request.files.getlist('files[]')
        if not files:
            flash('No folder/files selected for upload.', 'danger')
            return redirect(url_for('upload_page'))

        # Create a unique temporary directory for this upload batch
        upload_id = str(int(time.time()))
        batch_dir = os.path.join('data', 'temp', upload_id)
        os.makedirs(batch_dir)

        # Recreate the directory structure from the uploaded files
        for f in files:
            # The browser sends the relative path, e.g., "Stick-Man/audio_files/1.mp3"
            relative_path = f.filename
            # We need to create the directories if they don't exist
            save_path = os.path.join(batch_dir, relative_path)
            os.makedirs(os.path.dirname(save_path), exist_ok=True)
            f.save(save_path)
        
        # Now, smart_parse the top-level directories within our temp batch folder
        playlists_to_upload = []
        for item in os.listdir(batch_dir):
            item_path = os.path.join(batch_dir, item)
            if os.path.isdir(item_path):
                parsed_data = parser.parse_playlist_folder(item_path)
                if parsed_data:
                    playlists_to_upload.append(parsed_data)

        if not playlists_to_upload:
            shutil.rmtree(batch_dir) # Clean up
            flash('No valid Yoto playlist structures found in the uploaded folder.', 'warning')
            return redirect(url_for('upload_page'))

        # Queue the valid playlists for background upload
        for playlist in playlists_to_upload:
            # Important: The automation function now needs to know which temp dir to clean up
            playlist['temp_dir_to_clean'] = playlist['folderPath']
            db.log_activity(playlist['data']['Title'], "Queued")
            run_in_background(automation.upload_playlist, playlist)
        
        flash(f"{len(playlists_to_upload)} playlist(s) queued for upload. See Activity page for progress.", 'info')
        return redirect(url_for('activity_page'))

    return render_template('upload.html')

# --- API Routes ---
# ... (all other API routes like /api/test-credentials and /api/sync-library are unchanged) ...
@app.route('/api/test-credentials', methods=['POST'])
def test_credentials_api():
    email = request.json.get('email')
    password = request.json.get('password')
    result = scraper.test_login(email, password)
    return jsonify(result)
    
@app.route('/api/sync-library', methods=['POST'])
def trigger_sync():
    run_in_background(scraper.sync_library_from_yoto)
    return jsonify({"status": "Sync started. Check the dashboard in a few moments."})