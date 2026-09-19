# Redogtor

Redogtor is a free, open-source privacy utility designed to safely redact sensitive documents. Built by Ben Donato-Woodger with the assistance of an LLM, the redaction engine is powered by Microsoft Presidio and Explosion AI's spaCy natural language processing models.

## Complete Privacy on Your Machine

Redogtor is designed for a true zero-trust workflow:

- **Zero Logging:** The application keeps absolutely no logs.
- **RAM-Only Processing:** Documents are processed entirely in active memory (RAM) and are never written to disk.
- **Complete Isolation:** It requires no external internet connection to analyze text once installed.

## Download the App (No Python Needed)

Most people should use this. It bundles Python, the language models and everything else into a single download, so there is nothing to install first.

1. Go to the [Releases page](https://github.com/benjamin-dw/Redogtor/releases) and download the file for your machine:
   - **Windows:** `Redogtor-windows.zip`
   - **Mac (2021 or newer):** `Redogtor-mac-apple-silicon.zip`
   - **Mac (older):** `Redogtor-mac-intel.zip`
   - **Linux:** `Redogtor-linux.tar.gz`
2. Unzip it.
3. Start it:
   - **Windows:** open the folder and double-click `Redogtor.exe`. If a blue box appears, click **More info** then **Run anyway**.
   - **Mac:** right-click `Redogtor.app`, choose **Open**, then **Open** again.
   - **Linux:** `tar -xzf Redogtor-linux.tar.gz` then `./Redogtor/Redogtor`
4. Your browser opens on its own. Press **Quit** on the page when you are finished.

Nothing listens on the network. Only your own computer can reach it.

> **Why the security warning?** The app is not signed by a certificate authority, so Windows and macOS warn you about any developer they do not recognise. The steps above get past it. On a work computer managed by an IT department, the warning may not be skippable at all — ask your IT team, or use the source version below.

## How to Install and Run (From Source)

Use this if you already have Python, or if the download above is blocked on your machine.


**Prerequisites:** You need Python 3.9 or newer installed on your system.

1. Clone or download this repository to your computer.
2. Open your terminal or command prompt inside the folder.
3. Run the startup script:
   - **Windows:** `py run.py`
   - **macOS / Linux:** `python3 run.py`

> **Note:** The first time you run Redogtor, it will take 10–25 minutes to download the natural language models and set up a private virtual environment (`.venv`). On subsequent runs, it will launch in seconds.

## How to Check My Work (Auditing)

If your IT team wants to verify the privacy claims, they can review the code directly:

- **Tracking is turned off:** Look at `app.py` for `logging.disable(logging.CRITICAL)`. This explicitly tells the program not to keep any logs.
- **No files are saved:** Look at `app.py` for `io.BytesIO(blob)`. This proves the code only uses temporary memory buffers, not permanent storage.
- **No outside sharing:** Look at `run.py`. You will see it downloads the language models straight to a private `.venv` folder to work completely offline.

## Disclaimer & GNU General Public License

Automated pattern matching and Named Entity Recognition (NER) models are helpful aids, but no automated system is 100% foolproof. Always manually review your redacted documents before public distribution or sharing.

This project is released under the GNU General Public License (GPL). It is free to use and modify, but is provided strictly "as is". The creator is not liable for any damages or privacy breaches if the tool fails to catch sensitive data. See the LICENSE file for full details.
