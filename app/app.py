import os, json, time, shutil
from flask import Flask, render_template, jsonify, request, redirect, url_for, flash, send_from_directory
from threading import Thread

import database as db
import scraper
import automation
import parser

app = Flask(__name__)
app.config['SECRET_KEY'] = 'the-final-secret-key-for-real-this-time-v3'
app.config['MAX_CONTENT_LENGTH'] = 500 * 1024 * 1024

# --- Context Processor to make queue count available to all templates ---
@app.context_processor
def inject_print_queue_count():
    return dict(print_queue_count=db.get_print_queue_count())

db.init_db()
def run_in_background(target, *args):
    Thread(target=target, args=args, daemon=True).start()

# --- Frontend Routes ---
@app.route('/favicon.ico')
def favicon(): return '', 204

@app.route('/')
def dashboard(): return render_template('dashboard.html', playlists=db.get_all_playlists())

@app.route('/upload')
def upload_page(): return render_template('upload.html')

@app.route('/activity')
def activity_page(): return render_template('activity.html', logs=db.get_activity_logs())

@app.route('/print-queue')
def print_queue_page():
    items = db.get_print_queue_items()
    return render_template('print_queue.html', items=items)

@app.route('/settings', methods=['GET', 'POST'])
def settings_page():
    session_file_path = os.path.join('data', 'yoto_session.json')
    if request.method == 'POST':
        if 'session_file' in request.files:
            file = request.files['session_file']
            if file and file.filename.endswith('.json'):
                file.save(session_file_path)
                flash('Yoto session file uploaded successfully! Please test it below.', 'success')
            else:
                flash('Invalid file. Please upload the yoto_session.json file.', 'danger')
        return redirect(url_for('settings_page'))
    
    session_exists = os.path.exists(session_file_path)
    return render_template('settings.html', session_exists=session_exists)

# --- NEW ROUTE TO SERVE THE HELPER SCRIPT ---
@app.route('/download-helper')
def download_helper_script():
    return send_from_directory(
        os.path.join(os.getcwd(), 'app'), 
        'local_login_helper.py', 
        as_attachment=True
    )

# --- APIs ---
@app.route('/temp-image/<path:filename>')
def temp_image(filename):
    safe_base_path = os.path.abspath(os.path.join(os.getcwd(), 'data', 'temp'))
    requested_path = os.path.abspath(os.path.join(safe_base_path, filename.replace('\\', '/')))
    if not requested_path.startswith(safe_base_path): return "Forbidden", 403
    return send_from_directory(os.path.dirname(requested_path), os.path.basename(requested_path))

@app.route('/api/stage-folder', methods=['POST'])
def stage_folder_api():
    files = request.files.getlist('files[]')
    if not files: return jsonify({"error": "No files were uploaded."}), 400
    upload_id = str(int(time.time()))
    batch_dir = os.path.join('data', 'temp', upload_id)
    os.makedirs(batch_dir)
    for f in files:
        save_path = os.path.join(batch_dir, f.filename)
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        f.save(save_path)
    top_level_folder_name = files[0].filename.split('/')[0]
    root_parse_dir = os.path.join(batch_dir, top_level_folder_name)
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
        run_in_background(automation.upload_playlist_task, playlist_data)
    return jsonify({"status": "success"})

@app.route('/api/test-session', methods=['POST'])
def test_session_api():
    if not os.path.exists(os.path.join('data', 'yoto_session.json')):
        flash("No session file found. Please import one first.", "warning")
        return jsonify({"status": "error"}), 400
    run_in_background(scraper.test_session_task)
    flash("Session test started. See the Activity page for progress.", "info")
    return jsonify({"status": "success"})
    
@app.route('/api/sync-library', methods=['POST'])
def trigger_sync():
    if not os.path.exists(os.path.join('data', 'yoto_session.json')):
        flash("No session file found. Please import one on the Settings page before syncing.", "warning")
        return redirect(url_for('dashboard'))
    run_in_background(scraper.sync_library_task)
    flash("Library sync started. See the Activity page for progress.", "info")
    return redirect(url_for('activity_page'))