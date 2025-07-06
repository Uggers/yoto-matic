<p align="center">
  <svg height="80" width="400" xmlns="http://www.w3.org/2000/svg">
    <image href="https://www.datocms-assets.com/48136/1633095990-logotype-3x.png" x="0" y="15" height="50" width="150" />
    <text x="160" y="50" style="font-family: 'Inter', sans-serif; font-weight: 700; font-size: 56px; fill: #FF6A1F;">-Matic</text>
  </svg>
</p>

<p align="center">
  <strong>A self-hosted web application to manage, automate, and print your Yoto Make-Your-Own library.</strong>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Project%20Status-Active-brightgreen" alt="Project Status: Active">
  <img src="https://img.shields.io/badge/Python-3.9+-blue" alt="Python Version">
  <img src="https://img.shields.io/badge/License-MIT-yellow" alt="License: MIT">
</p>

---

Yoto-Matic is a lightweight, Docker-based web application inspired by the *arr stack (Radarr, Sonarr). It provides a beautiful web interface to automate the creation of Yoto playlists, sync your existing library for a local view, and generate perfect, print-ready A4 sheets for your physical cards.

***

### ✨ Core Features

*   **🎨 Yoto-Themed Interface:** A clean, responsive UI with light/dark modes and a look that feels right at home.
*   **📚 Library Dashboard:** Syncs with your `my.yotoplay.com` account to display all your existing playlists in a beautiful grid.
*   **🚀 Powerful Uploader:** Select a parent folder from your computer, and the app intelligently finds all valid playlist subfolders within it.
*   **🔍 Staging & Review Area:** Before uploading, review all found playlists, see their cover art and track lists, and make last-minute edits to titles and descriptions.
*   **🤖 Fully Automated Uploads:** The app uses Selenium to programmatically log in and create new playlists, upload cover art, and add all audio tracks.
*   **🖨️ Persistent Print Queue:** Add any card from your library to a print queue. When you're ready, generate a pixel-perfect, A4-sized PNG with 9 cards, correctly sized and with rounded corners, ready to be printed on sticker paper.
*   **📝 Activity Log:** A dedicated page to see the status of all past and current uploads, including success and failure details.
*   **🔒 Secure & Self-Contained:** Your credentials and library data are stored locally on your server. Runs entirely within Docker.

***

### 🔧 Getting Started

Yoto-Matic is designed to be run with Docker and Docker Compose, making installation incredibly simple.

#### Prerequisites

*   **Docker:** [Install Docker](https://docs.docker.com/get-docker/)
*   **Docker Compose:** Usually included with Docker Desktop. For Linux servers, [install the plugin](https://docs.docker.com/compose/install/).
*   **Git:** [Install Git](https://git-scm.com/book/en/v2/Getting-Started-Installing-Git)

#### Installation Steps

1.  **Clone the Repository**
    Open a terminal and clone this repository to your machine (e.g., your Raspberry Pi).
    ```bash
    git clone https://github.com/your-username/yoto-matic.git
    cd yoto-matic
    ```

2.  **Configure Your Media Folder**
    You need to tell Docker where your Yoto playlist folders are located on your server. Open the `docker-compose.yml` file with a text editor:
    ```bash
    nano docker-compose.yml
    ```
    Find the `volumes` section and change the line `- /path/to/your/audiobooks:/media/audiobooks:ro` to point to the correct path on your machine.

    **Example for Raspberry Pi with an external drive:**
    ```yaml
    volumes:
      - ./data:/app/data
      - /mnt/usbdrive/YotoLibrary:/media/audiobooks:ro
    ```
    **Example for Windows (if testing locally):**
    ```yaml
    volumes:
      - ./data:/app/data
      - C:/Users/YourUser/Desktop/YotoPlaylists:/media/audiobooks:ro
    ```
    Save the file and exit the editor (for `nano`, press `Ctrl+X`, then `Y`, then `Enter`).

3.  **Build and Run the Container**
    From the root `yoto-matic` folder, run the following command:
    ```bash
    docker-compose up --build -d
    ```
    This will download the necessary base images, build your application container, and start it in the background.

***

### 🚀 Usage Workflow

1.  **Access the App:** Open a web browser on any computer on your network and navigate to `http://<your-pi-ip-address>:6969`.

2.  **Configure Settings:**
    *   Go to the **Settings** page from the navigation bar.
    *   Enter your `my.yotoplay.com` email and password.
    *   Click **"Save Settings"**.
    *   Click **"Test Credentials"** to verify that the app can log in successfully. You will be taken to the Activity page to see the real-time log.

3.  **Sync Your Library:**
    *   Go to the **Dashboard**.
    *   Click the **"Sync from Yoto"** button. You will be redirected to the Activity page to watch the progress.
    *   Once complete, return to the Dashboard to see all your existing Yoto playlists.

4.  **Upload New Playlists:**
    *   Go to the **Upload** page.
    *   Click **"Add Folder(s)"** and select a parent folder from your computer that contains one or more valid playlist folders.
    *   The app will parse the contents and display them in a staging area.
    *   Review the playlists, make any edits to titles or descriptions, and click **"Start Upload Batch"**.
    *   You will be redirected to the Activity page to monitor the uploads.

5.  **Use the Print Queue:**
    *   On the **Dashboard**, click the `<i class="bi bi-printer"></i> Add to Print Queue` button on any card you want to print.
    *   The badge on the "Print Queue" navigation link will update.
    *   Go to the **Print Queue** page to see your selected cards.
    *   Click **"Generate Print Sheet"** to download a ready-to-print A4 PNG file. The queue will be cleared automatically.

***

### 📁 Required Folder Structure for Uploads

For the uploader to recognize a playlist, the folder must follow this structure:
MyAwesomePlaylist/
├── audio_files/
│ ├── 01 - First Track.mp3
│ ├── 02 - Another Song.m4a
│ └── 03 - The End.ogg
│
├── images/
│ └── cover_image.png (This is the main artwork for the playlist)
│
└── card.txt (An optional file for metadata)


**`card.txt` Format (Optional):**
This file uses a simple `Key:: Value` format.
Title:: My Awesome Playlist Title
Author:: The Author Name
Description:: This is a great playlist full of awesome songs.


If `card.txt` is missing, the app will use the folder name as the title.

***

### License

This project is licensed under the MIT License. See the `LICENSE` file for details.