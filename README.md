# YouTube Trending Data Pipeline

An automated pipeline that fetches daily YouTube trending video data via the YouTube Data API v3, appends it to a Google Sheet, and powers a Looker Studio dashboard that stays current automatically.

## Architecture

```
GitHub Actions (cron: 8am UTC)
        │
        ▼
    fetch.py
        │
        ├── YouTube Data API v3
        │     └── Trending videos for US, GB, IN
        │
        └── Google Sheets API (gspread)
              └── "youtube_trending" sheet (append-only)
                        │
                        ▼
              Looker Studio Dashboard (live connection)
```

Each daily run appends up to 150 rows (50 videos × 3 regions) with these columns:

| Column | Description |
|---|---|
| `title` | Video title |
| `categoryId` | Numeric category ID from YouTube |
| `category` | Human-readable category name |
| `viewCount` | Total views at fetch time |
| `likeCount` | Total likes at fetch time |
| `commentCount` | Total comments at fetch time |
| `publishedAt` | Original publish timestamp (ISO 8601) |
| `country` | Region code (US, GB, IN) |
| `fetch_date` | Date the row was fetched (YYYY-MM-DD) |
| `engagement_rate` | `(likeCount + commentCount) / viewCount` |

---

## Setup

### 1. YouTube API Key

1. Go to [Google Cloud Console](https://console.cloud.google.com/).
2. Create a new project (or select an existing one).
3. Navigate to **APIs & Services → Library** and enable **YouTube Data API v3**.
4. Navigate to **APIs & Services → Credentials** and click **Create Credentials → API key**.
5. Copy the key — this is your `YOUTUBE_API_KEY`.

### 2. Google Sheets Service Account

1. In the same Google Cloud project, go to **APIs & Services → Library** and enable:
   - **Google Sheets API**
   - **Google Drive API**
2. Go to **APIs & Services → Credentials → Create Credentials → Service account**.
3. Give it a name, click through the steps, then open the newly created service account.
4. Go to the **Keys** tab → **Add Key → Create new key → JSON**.
5. Download the JSON file — this is your `GOOGLE_CREDENTIALS` value (paste the entire JSON as a single line).
6. Share your Google Sheet (or your entire Google Drive folder) with the service account's email address (found in the JSON as `client_email`) with **Editor** access.
   - If the sheet named `youtube_trending` does not exist yet, the script will create it automatically on the first run.

### 3. Local Development

Copy `.env.example` to `.env` and fill in your values:

```bash
cp .env.example .env
```

`.env`:
```
YOUTUBE_API_KEY=AIza...
GOOGLE_CREDENTIALS={"type":"service_account","project_id":"..."}
```

Install dependencies and run:

```bash
pip install -r requirements.txt
python fetch.py
```

### 4. GitHub Secrets

In your GitHub repository go to **Settings → Secrets and variables → Actions → New repository secret** and add:

| Secret name | Value |
|---|---|
| `YOUTUBE_API_KEY` | Your YouTube Data API v3 key |
| `GOOGLE_CREDENTIALS` | The full contents of your service account JSON (as one line) |

The workflow runs automatically every day at 08:00 UTC. You can also trigger it manually from the **Actions** tab using **workflow_dispatch**.

---

## Looker Studio Dashboard

Connect Looker Studio to your Google Sheet:

1. Open [Looker Studio](https://lookerstudio.google.com/).
2. Click **Create → Data source → Google Sheets**.
3. Select your `youtube_trending` spreadsheet and `Sheet1`.
4. Enable **"Use first row as headers"** and click **Connect**.

The dashboard updates automatically each time the GitHub Action appends new data.

**Dashboard link:** *(add your published Looker Studio URL here)*

---

## Project Structure

```
youtube-trending-pipeline/
├── .github/
│   └── workflows/
│       └── daily_fetch.yml   # GitHub Actions cron workflow
├── fetch.py                  # Main pipeline script
├── requirements.txt          # Python dependencies
├── .env.example              # Template for local environment variables
├── .gitignore                # Excludes .env and credentials files
└── README.md
```
