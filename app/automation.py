import os
import time
import shutil
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from scraper import get_selenium_driver, login_to_yoto
import database as db

def upload_playlist(playlist_data):
    """Automates a single playlist upload and cleans up its temp directory."""
    title = playlist_data['data']['Title']
    temp_dir_to_clean = playlist_data.get('folderPath')

    db.log_activity(title, "Uploading", "Process started.")
    driver = get_selenium_driver()
    
    try:
        login_to_yoto(driver)
        wait = WebDriverWait(driver, 30)
        
        driver.get("https://my.yotoplay.com/my-cards")
        wait.until(EC.element_to_be_clickable((By.XPATH, "//a[contains(., 'Add Playlist')]"))).click()

        title_field = wait.until(EC.presence_of_element_located((By.XPATH, "//label[contains(text(), 'Give me a name')]/following-sibling::input")))
        title_field.send_keys(title)
        
        if playlist_data['data'].get('Description'):
            desc_field = driver.find_element(By.XPATH, "//label[contains(text(), 'Add a description')]/following-sibling::textarea")
            desc_field.send_keys(playlist_data['data']['Description'])
        
        artwork_input = wait.until(EC.presence_of_element_located((By.XPATH, "//input[@type='file']")))
        artwork_input.send_keys(playlist_data['data']['cover_image_path'])
        wait.until(EC.presence_of_element_located((By.XPATH, "//img[contains(@src, 'blob:')]")), "Artwork preview did not appear.")

        for i, track in enumerate(playlist_data['data']['tracks']):
            audio_inputs = driver.find_elements(By.XPATH, "//input[@type='file']")
            audio_input = audio_inputs[-1]
            audio_input.send_keys(track['audio_file_path'])
            # Use a more robust wait condition looking for the track title
            wait.until(EC.presence_of_element_located((By.XPATH, f"//li[contains(., \"{track['title']}\")]")), f"Track {i+1} did not appear in the list.")

        create_btn = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Update') or contains(text(), 'Create')]")))
        create_btn.click()

        wait.until(EC.url_contains("/my-cards"))
        db.log_activity(title, "Success", "Playlist created successfully on Yoto website.")

    except Exception as e:
        error_message = f"An error occurred: {str(e)[:500]}"
        db.log_activity(title, "Failed", error_message)
        driver.save_screenshot(f"data/error_upload_{title.replace(' ', '_')}.png")
    finally:
        driver.quit()
        # Clean up the parent directory of the temp folder
        if temp_dir_to_clean and os.path.exists(temp_dir_to_clean):
            shutil.rmtree(os.path.dirname(temp_dir_to_clean))
            print(f"Cleaned up temporary files for: {title}")