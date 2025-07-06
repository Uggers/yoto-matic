import os, json, time, shutil
from flask import Flask, render_template, jsonify, request, redirect, url_for, flash, Response, stream_with_context, send_from_directory
from werkzeug.utils import secure_filename
from threading import Thread
from queue import Queue

import database as db
import scraper
import automation
import parser

app = Flask(__name__)
app.config['SECRET_KEY'] = 'the-final-secret-key-for-real-this-time'

# --- LIVE LOG STREAMING SETUP ---
log_queue = Queue()

def log_to_stream(message):
    log_queue.put(f"data: {message}\n\n")

scraper.log_to_stream = log_to_stream
automation.log_to_stream = log_to_stream

@app.route('/stream-logs')
def stream_logs():
    def generate():
        while True:
            message = log_queue.get()
            yield message
    return Response(stream_with_context(generate()), mimetype='text/event-stream')
# --- END LIVE LOG ---

db.init_db()

def run_in_background(target, *args):
    Thread(target=target, args=args, daemon=True).start()

# --- Frontend Routes ---
@app.route('/')
def dashboard(): return render_template('dashboard.html', playlists=db.get_all_playlists())

@app.route('/upload')
def upload_page(): return render_template('upload.html')

@app.route('/activity')
def activity_page(): return render_template('activity.html', logs=db.get_activity_logs())

@app.route('/settings', methods=['GET', 'POST'])
def settings_page():
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

# --- APIs ---
@app.route('/temp-image/<path:filename>')
def temp_image(filename):
    return send_from_directory(os.path.join(os.getcwd(), 'data', 'temp'), filename.replace('\\', '/'))

@app.route('/api/stage-folder', methods=['POST'])
def stage_folder_api():
    files = request.files.getlist('files[]')
    if not files:
        return jsonify({"error": "No files were uploaded."}), 400

    upload_id = str(int(time.time()))
    batch_dir = os.path.join('data', 'temp', upload_id)
    os.makedirs(batch_dir)

    top_level_folder_name = files[0].filename.split('/')[0]
    root_parse_dir = os.path.join(batch_dir, top_level_folder_name)

    for f in files:
        save_path = os.path.join(batch_dir, secure_filename(f.filename))
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        f.save(save_path)
    
    found_playlists = parser.smart_parse_folder(root_parse_dir)
    
    for playlist in found_playlists:
        if playlist['data'].get('cover_image_path'):
            relative_path = os.path.relpath(playlist['data']['cover_image_path'], os.path.join(os.getcwd(), 'data', 'temp'))
            playlist['data']['cover_image_url'] = url_for('temp_image', filename=relative_path)
    
    return jsonify(found_playlists)

@app.route('/api/start-upload-batch', methods=['POST'])
def upload_batch_api():
    playlists_to_upload = request.json.get('playlists')
    for playlist_data in playlists_to_upload:
        db.log_activity(playlist_data['data']['Title'], "Queued")
        run_in_background(automation.upload_playlist, playlist_data)
    
    return jsonify({"status": "success", "message": f"{len(playlists_to_upload)} playlist(s) queued."})

@app.route('/api/test-credentials', methods=['POST'])
def test_credentials_api():
    email = request.json.get('email')
    password = request.json.get('password')
    run_in_background(scraper.test_login, email, password)
    return jsonify({"status": "success", "message": "Test started. See live log for details."})
    
@app.route('/api/sync-library', methods=['POST'])
def trigger_sync():
    run_in_background(scraper.sync_library_from_yoto)
    return jsonify({"status": "Sync started. See live log for details."})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)