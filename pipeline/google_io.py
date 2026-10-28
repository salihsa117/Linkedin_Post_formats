"""Drive + Sheets via a user OAuth refresh token (service accounts have no My-Drive quota)."""
import io
import os

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload

SCOPES = ["https://www.googleapis.com/auth/drive", "https://www.googleapis.com/auth/spreadsheets"]


def _creds():
    c = Credentials(
        None, refresh_token=os.environ["GOOGLE_REFRESH_TOKEN"],
        client_id=os.environ["GOOGLE_CLIENT_ID"], client_secret=os.environ["GOOGLE_CLIENT_SECRET"],
        token_uri="https://oauth2.googleapis.com/token", scopes=SCOPES)
    c.refresh(Request())
    return c


def enabled():
    return all(os.environ.get(k) for k in
               ("GOOGLE_REFRESH_TOKEN", "GOOGLE_CLIENT_ID", "GOOGLE_CLIENT_SECRET"))


def download(file_id, dest):
    drive = build("drive", "v3", credentials=_creds(), cache_discovery=False)
    meta = drive.files().get(fileId=file_id, fields="name").execute()
    req = drive.files().get_media(fileId=file_id)
    with io.FileIO(dest, "wb") as fh:
        dl = MediaIoBaseDownload(fh, req, chunksize=32 * 1024 * 1024)
        done = False
        while not done:
            _, done = dl.next_chunk()
    return meta["name"]


def upload(path, folder_id):
    drive = build("drive", "v3", credentials=_creds(), cache_discovery=False)
    f = drive.files().create(
        body={"name": os.path.basename(path), "parents": [folder_id]},
        media_body=MediaFileUpload(path, mimetype="video/mp4", resumable=True),
        fields="id,webViewLink").execute()
    return f["id"], f["webViewLink"]


def append_rows(sheet_id, rows, tab="Posts"):
    sh = build("sheets", "v4", credentials=_creds(), cache_discovery=False)
    sh.spreadsheets().values().append(
        spreadsheetId=sheet_id, range=f"{tab}!A1", valueInputOption="USER_ENTERED",
        insertDataOption="INSERT_ROWS", body={"values": rows}).execute()
