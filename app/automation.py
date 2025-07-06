import os
import time
import shutil
# ... (other imports are the same) ...
from scraper import get_selenium_driver, login_to_yoto
import database as db

def upload_playlist(playlist_data):
    """
    Automates a single playlist upload and cleans up its temp directory.
    """
    title = playlist_data['data']['Title']
    temp_dir_to_clean = playlist_data.get('temp_dir_to_clean')

    db.log_activity(title, "Uploading", "Process started.")
    driver = get_selenium_driver()
    
    try:
        # ... (The entire Selenium logic inside the try block is UNCHANGED from the previous version) ...
        login_to_yoto(driver)
        # ... it will correctly use the temporary file paths from playlist_data ...
        # ...
        db.log_activity(title, "Success", "Playlist created successfully on Yoto website.")
    except Exception as e:
        error_message = f"An error occurred: {str(e)[:500]}"
        db.log_activity(title, "Failed", error_message)
        driver.save_screenshot(f"data/error_upload_{title}.png")
    finally:
        driver.quit()
        # Clean up the specific temporary folder for this playlist
        if temp_dir_to_clean and os.path.exists(temp_dir_to_clean):
            shutil.rmtree(os.path.dirname(temp_dir_to_clean)) # Clean the parent batch dir
            print(f"Cleaned up temporary files for: {title}")