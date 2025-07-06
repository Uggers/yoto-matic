import os

def parse_key_value_file(file_path):
    """Generic parser for files with 'Key:: Value' format."""
    data = {}
    if not os.path.exists(file_path):
        return data
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                if '::' in line:
                    key, value = line.split('::', 1)
                    data[key.strip()] = value.strip()
    except Exception:
        with open(file_path, 'r', encoding='latin-1') as f:
            for line in f:
                if '::' in line:
                    key, value = line.split('::', 1)
                    data[key.strip()] = value.strip()
    return data

def smart_parse_folder(path):
    """
    Intelligently parses a directory. If it's a playlist, returns it.
    If it's a parent, returns all valid playlists inside.
    """
    def parse_single_playlist(playlist_path):
        folder_name = os.path.basename(playlist_path)
        errors = []
        data = {'Title': folder_name, 'Author': 'Unknown', 'Description': ''}

        if not os.path.isdir(playlist_path): return None

        card_txt_path = os.path.join(playlist_path, 'card.txt')
        cover_image_path = os.path.join(playlist_path, 'images', 'cover_image.png')
        audio_files_path = os.path.join(playlist_path, 'audio_files')

        if os.path.exists(card_txt_path):
            data.update(parse_key_value_file(card_txt_path))
        else:
            errors.append("Warning: Missing card.txt. Using folder name as title.")

        if os.path.exists(cover_image_path):
            data['cover_image_path'] = cover_image_path
        else:
            data['cover_image_path'] = None
            errors.append("Warning: Missing images/cover_image.png.")
        
        tracks = []
        is_valid = True
        if os.path.exists(audio_files_path):
            audio_files = sorted([f for f in os.listdir(audio_files_path) if f.lower().endswith(('.mp3', '.m4a', '.ogg'))])
            if not audio_files:
                is_valid = False
                errors.append("Error: No audio files found in audio_files/.")
            for f in audio_files:
                tracks.append({'title': os.path.splitext(f)[0].replace('_', ' ').title(), 'audio_file_path': os.path.join(audio_files_path, f)})
        else:
            is_valid = False
            errors.append("Error: audio_files/ directory is missing.")
            
        data['tracks'] = tracks
        
        if is_valid:
            return { "folderName": folder_name, "folderPath": playlist_path, "isValid": is_valid, "validationErrors": errors, "data": data }
        return None

    found_playlists = []
    root_playlist = parse_single_playlist(path)
    if root_playlist:
        found_playlists.append(root_playlist)
    else:
        for item in os.listdir(path):
            item_path = os.path.join(path, item)
            sub_playlist = parse_single_playlist(item_path)
            if sub_playlist:
                found_playlists.append(sub_playlist)
    
    return found_playlists