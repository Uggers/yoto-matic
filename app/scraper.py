import os, json, time
from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import database as db

log_to_stream = print
AUTH_STATE_PATH = os.path.join('data', 'auth_state.json')

def get_selenium_driver():
    """Configures and returns a Selenium WebDriver instance."""
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    driver = webdriver.Chrome(options=options)
    return driver

def login_to_yoto(driver):
    # ... (This internal function is the same as the last version) ...
    try:
        if os.path.exists(AUTH_STATE_PATH):
            log_to_stream("Found saved session. Attempting to use it...")
            with open(AUTH_STATE_PATH, 'r') as f: cookies = json.load(f)
            driver.get("https://my.yotoplay.com/")
            for cookie in cookies: driver.add_cookie(cookie)
            driver.get("https://my.yotoplay.com/my-cards")
            WebDriverWait(driver, 5).until(EC.url_contains("/my-cards"))
            log_to_stream("Saved session is valid. Login successful.")
            return
    except Exception:
        log_to_stream("Saved session failed or is expired. Proceeding to full login.")

    settings_path = os.path.join('data', 'settings.json')
    if not os.path.exists(settings_path): raise ValueError("Settings not found.")
    with open(settings_path, 'r') as f: settings = json.load(f)
    yoto_email = settings.get('yoto_email')
    yoto_password = settings.get('yoto_password')
    if not yoto_email or not yoto_password: raise ValueError("Yoto credentials not set in settings.")

    driver.get("https://my.yotoplay.com/login")
    wait = WebDriverWait(driver, 20)
    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='email']"))).send_keys(yoto_email)
    driver.find_element(By.CSS_SELECTOR, "input[type='password']").send_keys(yoto_password)
    driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
    wait.until(EC.url_contains("/my-cards"))
    log_to_stream("Full login successful.")

    cookies = driver.get_cookies()
    with open(AUTH_STATE_PATH, 'w') as f: json.dump(cookies, f)
    log_to_stream("New session state has been saved.")

def test_login_task(email, password):
    """The complete task for testing credentials, with full error trapping."""
    log_to_stream("--- Starting Credential Test ---")
    if not email or not password:
        log_to_stream("ERROR: Email and password cannot be empty.")
        log_to_stream("--- Credential Test Finished ---")
        return
    
    driver = None
    try:
        log_to_stream("Initializing browser...")
        driver = get_selenium_driver()
        log_to_stream("Navigating to login page...")
        driver.get("https://my.yotoplay.com/login")
        wait = WebDriverWait(driver, 15)
        log_to_stream("Entering credentials...")
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='email']"))).send_keys(email)
        driver.find_element(By.CSS_SELECTOR, "input[type='password']").send_keys(password)
        driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
        log_to_stream("Submitting login form...")
        wait.until(EC.url_contains("/my-cards"))
        log_to_stream("SUCCESS: Login successful!")
    except Exception as e:
        log_to_stream(f"ERROR: Login failed. Please check credentials and server logs. Details: {e}")
    finally:
        if driver: driver.quit()
        log_to_stream("--- Credential Test Finished ---")

def sync_library_task():
    """The complete task for syncing the library, with full error trapping."""
    log_to_stream("--- Starting Library Sync ---")
    driver = None
    try:
        driver = get_selenium_driver()
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
            if "Add Playlist" in title or not title.strip(): continue
            try:
                cover_image_url = link.find_element(By.TAG_NAME, "img").get_attribute('src')
            except:
                cover_image_url = ''
            scraped_playlists.append({"title": title, "cover_image_url": cover_image_url})
        db.sync_scraped_playlists(scraped_playlists)
        log_to_stream(f"SUCCESS: Library sync complete. Saved {len(scraped_playlists)} playlists.")
    except Exception as e:
        log_to_stream(f"ERROR: An error occurred during library sync. Details: {e}")
        if driver: driver.save_screenshot("data/error_sync.png")
    finally:
        if driver: driver.quit()
        log_to_stream("--- Library Sync Finished ---")