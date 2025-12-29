
This project is a **Graphical User Interface fork** of the original [Fitgirl-Easy-Downloader](https://github.com/JOY6IX9INE/Fucking-Fast-Multi-Downloader) tool.

The core functionality remains the same: it helps to download multiple files easily from **fitgirl-repacks.site** by processing the links through **fuckingfast.co**. The major change is the replacement of the Command Line Interface (CLI) with a **minimalist, dark mode GUI** built using Tkinter for better usability and real-time monitoring.

---

## **Direct download the executable [HERE](https://github.com/Chaksz/Fitgirl-Easy-Downloader/releases/download/Executable/Fitgirl.Downloader.exe) <---**

---

## New GUI Features 

* **Real-time Progress:** A dedicated progress bar displays the download **percentage** and **speed (MB/s)** for the currently active file.
* **Download Folder Selection:** A built-in **`Browse`** button allows you to easily select and change the download directory.
* **Link Management:** The input links are edited and saved directly within the application. The **`Save`** button manages the `input.txt` file content and is disabled when no changes are made.
* **Non-Blocking UI:** Utilizes multi-threading to ensure the GUI remains responsive while scraping and downloading files in the background.
* **Download management:** A built-in stop and skip download feature.
* *(The need for `tqdm` and `colorama` is eliminated in the GUI version.)*

---
