import os, json, time, shutil
from flask import Flask, render_template, jsonify, request, redirect, url_for, flash, send_file
from threading import Thread

import database as db
import scraper
import automation
import parser
import image_generator

app = Flask(__name__)
app.config['SECRET_KEY'] = 'the-final-secret-key-for-real-this-time'
app.config['MAX_CONTENT_LENGTH'] = 500 * 1024 * 1024 # 500 MB upload limit

# --- Context Processor to make queue count available to all templates ---
@app.context_processor
def inject_print_queue_count():
    return dict(print_queue_count=db.get_print_queue_count())

# --- Initialization & Helpers ---
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

@app.route('/settings', methods=['GET', 'POST'])
def settings_page():
    # (This function is unchanged)
    settings_path = os.path.join('data', 'settings.json')
    if request.method == 'POST':
        settings = {"yoto_email": request.form.get('yoto_email'), "yoto_password": request.form.get('yoto_password')}
        with open(settings_path, 'w') as f: json.dump(settings, f)
        flash('Settings saved successfully!', 'success')
        return redirect(url_for('settings_page'))
    current_settings = {}
    if os.path.exists(settings_path):
        with open(settings_path, 'r') as f: current_settings = json.load(f)
    return render_template('settings.html', settings=current_settings)

# NEW ROUTE FOR THE PRINT QUEUE PAGE
@app.route('/print-queue')
def print_queue_page():
    items = db.get_print_queue_items()
    return render_template('print_queue.html', items=items)

# --- APIs ---
@app.route('/temp-image/<path:filename>')
def temp_image(filename):
    # (This function is unchanged)
    safe_base_path = os.path.abspath(os.path.join(os.getcwd(), 'data', 'temp'))
    requested_path = os.path.abspath(os.path.join(safe_base_path, filename.replace('\\', '/')))
    if not requested_path.startswith(safe_base_path): return "Forbidden", 403
    return send_from_directory(os.path.dirname(requested_path), os.path.basename(requested_path))

# --- NEW PRINT QUEUE API ENDPOINTS ---
@app.route('/api/print-queue/add/<int:playlist_id>', methods=['POST'])
def add_to_queue_api(playlist_id):
    db.add_to_print_queue(playlist_id)
    return jsonify({"success": True, "queue_count": db.get_print_queue_count()})

@app.route('/api/print-queue/remove/<int:playlist_id>', methods=['POST'])
def remove_from_queue_api(playlist_id):
    db.remove_from_print_queue(playlist_id)
    return jsonify({"success": True, "queue_count": db.get_print_queue_count()})

@app.route('/api/print-queue/clear', methods=['POST'])
def clear_queue_api():
    db.clear_print_queue()
    return jsonify({"success": True, "queue_count": 0})

@app.route('/api/generate-print-sheet', methods=['POST'])
def generate_print_sheet_api():
    # This now gets URLs from the DB queue instead of the request body
    queue_items = db.get_print_queue_items()
    image_urls = [item['cover_image_url'] for item in queue_items]
    
    if not image_urls: return "Print queue is empty.", 400
        
    try:
        image_buffer = image_generator.generate_print_sheet(image_urls)
        db.clear_print_queue() # Clear the queue after successful generation
        return send_file(image_buffer, mimetype='image/png', as_attachment=True, download_name='yoto-matic-print-sheet.png')
    except Exception as e:
        print(f"Error generating print sheet: {e}")
        return "Error generating image", 500

# --- Other APIs (Unchanged) ---
@app.route('/api/stage-folder', methods=['POST'])
def stage_folder_api():
    # (This function is unchanged)
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
    # (This function is unchanged)
    playlists_to_upload = request.json.get('playlists')
    for playlist_data in playlists_to_upload:
        db.log_activity(playlist_data['data']['Title'], "Queued")
        run_in_background(automation.upload_playlist_task, playlist_data)
    return jsonify({"status": "success"})

@app.route('/api/test-credentials', methods=['POST'])
def test_credentials_api():
    # (This function is unchanged)
    email, password = request.json.get('email'), request.json.get('password')
    if not email or not password:
        flash("Email and Password cannot be empty.", "warning")
        return jsonify({"status": "error"}), 400
    run_in_background(scraper.test_login_task, email, password)
    flash("Credential test started. See the Activity page for progress.", "info")
    return jsonify({"status": "success"})
    
@app.route('/api/sync-library', methods=['POST'])
def trigger_sync():
    # (This function is unchanged)
    if not os.path.exists(os.path.join('data', 'settings.json')):
        flash("Please save your credentials on the Settings page before syncing.", "warning")
        return jsonify({"status": "error"}), 400
    run_in_background(scraper.sync_library_task)
    flash("Library sync started. See the Activity page for progress.", "info")
    return jsonify({"status": "success"})