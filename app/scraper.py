import os, json, time
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import database as db
from automation import get_selenium_driver # Reuse driver function

def test_login(email, password):
    """A quick, targeted function to test credentials."""
    if not email or not password:
        return {"status": "error", "message": "Email and password cannot be empty."}
    
    driver = get_selenium_driver()
    try:
        driver.get("https://my.yotoplay.com/login")
        wait = WebDriverWait(driver, 15)
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='email']"))).send_keys(email)
        driver.find_element(By.CSS_SELECTOR, "input[type='password']").send_keys(password)
        driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
        wait.until(EC.url_contains("/my-cards"))
        return {"status": "success", "message": "Login successful!"}
    except TimeoutException:
        return {"status": "error", "message": "Login failed. Please check credentials."}
    except Exception as e:
        return {"status": "error", "message": f"An unexpected error occurred: {e}"}
    finally:
        driver.quit()

def login_to_yoto(driver):
    # ... (code is the same as before) ...
    # This function is now used by the real sync and upload processes
    settings_path = os.path.join('data', 'settings.json')
    if not os.path.exists(settings_path):
        raise ValueError("Settings not found. Configure credentials in the Settings page.")
    with open(settings_path, 'r') as f:
        settings = json.load(f)
        yoto_email = settings.get('yoto_email')
        yoto_password = settings.get('yoto_password')
    if not yoto_email or not yoto_password:
        raise ValueError("Yoto credentials not set in settings.")
    driver.get("https://my.yotoplay.com/login")
    wait = WebDriverWait(driver, 20)
    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='email']"))).send_keys(yoto_email)
    driver.find_element(By.CSS_SELECTOR, "input[type='password']").send_keys(yoto_password)
    driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
    wait.until(EC.url_contains("/my-cards"))

def sync_library_from_yoto():
    # ... (code is the same as before) ...
    driver = get_selenium_driver()
    print("Starting library sync...")
    scraped_playlists = []
    
    try:
        login_to_yoto(driver)
        driver.get("https://my.yotoplay.com/my-cards")
        wait = WebDriverWait(driver, 20)
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "a[href^='/card/']")))
        time.sleep(3)

        playlist_links = driver.find_elements(By.CSS_SELECTOR, "a[href^='/card/']")
        print(f"Found {len(playlist_links)} potential playlist(s) on the page.")

        for link in playlist_links:
            title = link.text
            if "Add Playlist" in title or not title.strip():
                continue
            
            try:
                cover_img_element = link.find_element(By.TAG_NAME, "img")
                cover_image_url = cover_img_element.get_attribute('src')
            except:
                cover_image_url = ''

            scraped_playlists.append({"title": title, "cover_image_url": cover_image_url})
        
        db.sync_scraped_playlists(scraped_playlists)
        print(f"Library sync complete. Found {len(scraped_playlists)} valid playlists.")
    except Exception as e:
        print(f"An error occurred during library sync: {e}")
        driver.save_screenshot("data/error_sync.png")
    finally:
        driver.quit()