# This script will be served by the Yoto-Matic app for you to run locally.
# It helps you securely generate the yoto_session.json file.

from playwright.sync_api import sync_playwright
import os
import json
import sys

def main():
    print("--- Yoto-Matic Session Export Tool ---")
    print("\nA new Chrome window will open.")
    print("\n[INSTRUCTIONS]")
    print("1. Please log in to your Yoto account as you normally would.")
    print("2. After you are successfully logged in and see your library dashboard,")
    print("3. come back to THIS terminal window and press the 'Enter' key.")
    print("-" * 40)

    try:
        with sync_playwright() as p:
            # We launch a real, visible browser window
            browser = p.chromium.launch(headless=False)
            context = browser.new_context()
            page = context.new_page()
            
            # Go to the login page
            page.goto("https://my.yotoplay.com/login")
            
            # Pause the script and wait for the user to log in and press Enter
            input("Press Enter here after you have logged in through the browser window...")
            
            # Save the entire browser state (cookies, local storage, etc.)
            storage_state = context.storage_state()
            browser.close()
            
            # Define the output path on the user's Desktop
            desktop_path = os.path.join(os.path.expanduser("~"), "Desktop")
            file_path = os.path.join(desktop_path, "yoto_session.json")
            
            with open(file_path, 'w') as f:
                json.dump(storage_state, f, indent=2)
                
            print(f"\nSUCCESS! Session saved to your Desktop as 'yoto_session.json'")
            print("You can now go back to the Yoto-Matic web UI and upload this file on the Settings page.")

    except Exception as e:
        print("\n--- AN ERROR OCCURRED ---")
        print(f"Error: {e}")
        print("\nThis might have happened because Playwright is not installed correctly.")
        print("Please try running these two commands in your local terminal and then run this script again:")
        print("1. pip install playwright")
        print("2. playwright install")

    print("-" * 40)
    input("Press Enter to exit.")

if __name__ == "__main__":
    main()