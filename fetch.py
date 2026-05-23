import os
import json
import pandas as pd
from datetime import date
from dotenv import load_dotenv
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import gspread
from google.oauth2.service_account import Credentials

load_dotenv()

YOUTUBE_API_KEY = os.environ.get("YOUTUBE_API_KEY")
GOOGLE_CREDENTIALS = os.environ.get("GOOGLE_CREDENTIALS")
SHEET_NAME = "youtube_trending"
REGIONS = ["US", "GB", "IN"]
MAX_RESULTS = 50

CATEGORY_NAMES = {}

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]


def get_youtube_client():
    return build("youtube", "v3", developerKey=YOUTUBE_API_KEY)


def get_sheets_client():
    creds_info = json.loads(GOOGLE_CREDENTIALS)
    creds = Credentials.from_service_account_info(creds_info, scopes=SCOPES)
    return gspread.authorize(creds)


def fetch_category_names(youtube, region_code="US"):
    try:
        response = (
            youtube.videoCategories()
            .list(part="snippet", regionCode=region_code, hl="en_US")
            .execute()
        )
        return {item["id"]: item["snippet"]["title"] for item in response.get("items", [])}
    except HttpError as e:
        print(f"Error fetching category names: {e}")
        return {}


def fetch_trending_videos(youtube, region_code):
    videos = []
    next_page_token = None

    try:
        while True:
            request = youtube.videos().list(
                part="snippet,statistics",
                chart="mostPopular",
                regionCode=region_code,
                maxResults=MAX_RESULTS,
                pageToken=next_page_token,
            )
            response = request.execute()

            for item in response.get("items", []):
                snippet = item.get("snippet", {})
                stats = item.get("statistics", {})

                view_count = int(stats.get("viewCount", 0) or 0)
                like_count = int(stats.get("likeCount", 0) or 0)
                comment_count = int(stats.get("commentCount", 0) or 0)

                engagement_rate = (
                    round((like_count + comment_count) / view_count, 6)
                    if view_count > 0
                    else 0.0
                )

                category_id = snippet.get("categoryId", "")
                category_name = CATEGORY_NAMES.get(category_id, "Unknown")

                videos.append(
                    {
                        "title": snippet.get("title", ""),
                        "categoryId": category_id,
                        "category": category_name,
                        "viewCount": view_count,
                        "likeCount": like_count,
                        "commentCount": comment_count,
                        "publishedAt": snippet.get("publishedAt", ""),
                        "country": region_code,
                        "fetch_date": str(date.today()),
                        "engagement_rate": engagement_rate,
                    }
                )

            next_page_token = response.get("nextPageToken")
            if not next_page_token:
                break

    except HttpError as e:
        print(f"Error fetching trending videos for region {region_code}: {e}")

    return videos


HEADERS = [
    "title", "categoryId", "category", "viewCount", "likeCount",
    "commentCount", "publishedAt", "country", "fetch_date", "engagement_rate",
]


def get_or_create_sheet(gc):
    try:
        spreadsheet = gc.open(SHEET_NAME)
        print(f"Opened existing sheet: {SHEET_NAME}")
    except gspread.SpreadsheetNotFound:
        raise SystemExit(
            f"\nERROR: Spreadsheet '{SHEET_NAME}' not found.\n"
            "Please:\n"
            "  1. Create a new Google Sheet named exactly 'youtube_trending'\n"
            "  2. Share it with the service account email (client_email in your credentials JSON)\n"
            "     with Editor access, then re-run.\n"
        )

    worksheet = spreadsheet.sheet1

    # Write header row if the sheet is empty
    if worksheet.row_count == 0 or not worksheet.row_values(1):
        worksheet.append_row(HEADERS)
        print("Added header row.")

    return worksheet


def append_rows(worksheet, rows):
    if not rows:
        print("No rows to append.")
        return

    df = pd.DataFrame(rows)
    values = df.values.tolist()

    worksheet.append_rows(values, value_input_option="USER_ENTERED")
    print(f"Appended {len(values)} rows to sheet.")


def main():
    if not YOUTUBE_API_KEY:
        print("ERROR: YOUTUBE_API_KEY environment variable is not set.")
        return
    if not GOOGLE_CREDENTIALS:
        print("ERROR: GOOGLE_CREDENTIALS environment variable is not set.")
        return

    print("Initializing YouTube client...")
    youtube = get_youtube_client()

    global CATEGORY_NAMES
    CATEGORY_NAMES = fetch_category_names(youtube)
    print(f"Loaded {len(CATEGORY_NAMES)} video categories.")

    all_videos = []
    for region in REGIONS:
        print(f"Fetching trending videos for region: {region}")
        videos = fetch_trending_videos(youtube, region)
        print(f"  Fetched {len(videos)} videos from {region}")
        all_videos.extend(videos)

    print(f"Total videos fetched: {len(all_videos)}")

    print("Connecting to Google Sheets...")
    gc = get_sheets_client()
    worksheet = get_or_create_sheet(gc)

    append_rows(worksheet, all_videos)
    print("Done.")


if __name__ == "__main__":
    main()
