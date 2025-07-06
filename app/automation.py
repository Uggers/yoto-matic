import os
import time
import shutil
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from scraper import get_selenium_driver, login_to_yoto # Reuse driver and login logic

def upload_new_playlist(title, description, cover_file_path, audio_file_paths, temp_dir):
    """Automates the creation of a single new playlist and cleans up temp files."""
    driver = get_selenium_driver()
    print(f"Starting upload for: {title}")
    
    try:
        login_to_yoto(driver)
        wait = WebDriverWait(driver, 30)
        
        driver.get("https://my.yotoplay.com/my-cards")
        # Click "Add Playlist" button
        wait.until(EC.element_to_be_clickable((By.XPATH, "//a[contains(., 'Add Playlist')]"))).click()

        # --- On the "Edit your playlist" page ---
        title_field = wait.until(EC.presence_of_element_located((By.XPATH, "//label[contains(text(), 'Give me a name')]/following-sibling::input")))
        title_field.send_keys(title)

        if description:
            desc_field = driver.find_element(By.XPATH, "//label[contains(text(), 'Add a description')]/following-sibling::textarea")
            desc_field.send_keys(description)
        
        # --- Upload Cover Artwork ---
        # The file input is often hidden. We find the one for artwork.
        artwork_input = wait.until(EC.presence_of_element_located((By.XPATH, "//input[@type='file']")))
        artwork_input.send_keys(cover_file_path)
        print("Uploading cover art...")
        wait.until(EC.presence_of_element_located((By.XPATH, f"//img[contains(@src, 'blob:')]")), "Artwork preview did not appear.")
        print("Cover art uploaded.")

        # --- Upload Audio Files ---
        for i, audio_path in enumerate(audio_file_paths):
            # Find the file input for adding new audio tracks.
            # It's usually the last file input on the page after the artwork one.
            audio_inputs = driver.find_elements(By.XPATH, "//input[@type='file']")
            audio_input = audio_inputs[-1]
            
            audio_input.send_keys(audio_path)
            print(f"Uploading track {i+1}: {os.path.basename(audio_path)}")
            # Wait for the track to appear in the list.
            wait.until(EC.presence_of_element_located((By.XPATH, f"//li[contains(., '{os.path.splitext(os.path.basename(audio_path))[0]}')]")), f"Track {i+1} did not appear in the list.")
            print(f"Track {i+1} uploaded.")
        
        # --- Click Create/Update Button ---
        create_btn = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Update') or contains(text(), 'Create')]")))
        create_btn.click()

        wait.until(EC.url_contains("/my-cards"))
        print(f"Successfully created playlist: {title}")

    except Exception as e:
        print(f"An error occurred during upload for '{title}': {e}")
        driver.save_screenshot(f"data/error_upload_{title}.png")
    finally:
        driver.quit()
        # Clean up the temporary directory for this upload
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
            print(f"Cleaned up temporary files for: {title}")