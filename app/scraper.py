import os, json, time
from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import database as db

# This is a fallback if the app doesn't assign the real function
log_to_stream = print

def get_selenium_driver():
    """Configures and returns a Selenium WebDriver instance."""
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    driver = webdriver.Chrome(options=options)
    return driver

def test_login(email, password):
    """A quick, targeted function to test credentials."""
    if not email or not password:
        return {"status": "error", "message": "Email and password cannot be empty."}
    
    log_to_stream("--- Starting Credential Test ---")
    log_to_stream("Initializing browser...")
    driver = get_selenium_driver()
    try:
        log_to_stream("Navigating to login page...")
        driver.get("https://my.yotoplay.com/login")
        wait = WebDriverWait(driver, 15)
        log_to_stream("Entering email and password...")
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='email']"))).send_keys(email)
        driver.find_element(By.CSS_SELECTOR, "input[type='password']").send_keys(password)
        driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
        log_to_stream("Submitting login form...")
        wait.until(EC.url_contains("/my-cards"))
        log_to_stream("Login successful!")
        return {"status": "success", "message": "Login successful!"}
    except TimeoutException:
        log_to_stream("Login failed: Timeout. Please check your credentials.")
        return {"status": "error", "message": "Login failed. Please check credentials."}
    except Exception as e:
        log_to_stream(f"An unexpected error occurred: {e}")
        return {"status": "error", "message": f"An unexpected error occurred: {e}"}
    finally:
        log_to_stream("--- Credential Test Finished ---")
        driver.quit()

def login_to_yoto(driver):
    """Handles the login process for real operations."""
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
    log_to_stream("Login successful for operation.")

def sync_library_from_yoto():
    """Logs into Yoto, scrapes all existing playlists, and saves them to the local DB."""
    log_to_stream("--- Starting Library Sync ---")
    driver = get_selenium_driver()
    try:
        login_to_yoto(driver)
        driver.get("https://my.yotoplay.com/my-cards")
        log_to_stream("Navigated to 'My Playlists' page.")
        wait = WebDriverWait(driver, 20)
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "a[href^='/card/']")))
        time.sleep(3)
        playlist_links = driver.find_elements(By.CSS_SELECTOR, "a[href^='/card/']")
        log_to_stream(f"Found {len(playlist_links)} potential playlist(s) on the page.")
        scraped_playlists = []
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
        log_to_stream(f"Library sync complete. Saved {len(scraped_playlists)} valid playlists.")
    except Exception as e:
        log_to_stream(f"An error occurred during library sync: {e}")
        driver.save_screenshot("data/error_sync.png")
    finally:
        log_to_stream("--- Library Sync Finished ---")
        driver.quit()