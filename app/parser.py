import os

def parse_key_value_file(file_path):
    # ... (code is the same as the previous version) ...
    data = {}
    if not os.path.exists(file_path):
        return data
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            if '::' in line:
                key, value = line.split('::', 1)
                data[key.strip()] = value.strip()
    return data

def parse_playlist_folder(path):
    """
    Parses a single, specific folder path to see if it's a valid playlist.
    Returns a single parsed playlist data object or None.
    """
    folder_name = os.path.basename(path)
    errors = []
    data = {'Title': folder_name, 'Author': 'Unknown', 'Description': ''}

    card_txt_path = os.path.join(path, 'card.txt')
    cover_image_path = os.path.join(path, 'images', 'cover_image.png')
    audio_files_path = os.path.join(path, 'audio_files')

    if not os.path.isdir(path): return None
    if not os.path.exists(cover_image_path): errors.append("Missing: images/cover_image.png")
    if not os.path.exists(audio_files_path): errors.append("Missing: audio_files/ directory")

    if os.path.exists(card_txt_path):
        data.update(parse_key_value_file(card_txt_path))
    else:
        errors.append("Missing: card.txt")
    
    tracks = []
    if os.path.exists(audio_files_path):
        audio_files = sorted([f for f in os.listdir(audio_files_path) if f.lower().endswith(('.mp3', '.m4a', '.ogg'))])
        for i, audio_file in enumerate(audio_files, 1):
            track_title = os.path.splitext(audio_file)[0].replace('_', ' ').replace('-', ' ')
            icon_path = os.path.join(path, 'images', f'{i}.png')
            if not os.path.exists(icon_path):
                errors.append(f"Missing icon: images/{i}.png")
            
            tracks.append({
                'trackNumber': i,
                'title': track_title,
                'audio_file_path': os.path.join(audio_files_path, audio_file),
            })
    data['tracks'] = tracks
    data['cover_image_path'] = cover_image_path
    
    return {
        "folderName": folder_name,
        "folderPath": path,
        "isValid": len(errors) == 0,
        "validationErrors": errors,
        "data": data
    }