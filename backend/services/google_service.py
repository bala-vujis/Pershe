from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from google.auth.transport.requests import Request as GoogleRequest
from google.oauth2.credentials import Credentials
from datetime import datetime, timezone, timedelta
import os
import logging
import uuid
import warnings

logger = logging.getLogger(__name__)

GOOGLE_CLIENT_ID = os.environ.get('GOOGLE_CLIENT_ID', '')
GOOGLE_CLIENT_SECRET = os.environ.get('GOOGLE_CLIENT_SECRET', '')
REDIRECT_URI = os.environ.get('GOOGLE_REDIRECT_URI', '')

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive.readonly",
    "openid",
    "https://www.googleapis.com/auth/userinfo.email",
    "https://www.googleapis.com/auth/userinfo.profile"
]

class GoogleService:
    def __init__(self, db):
        self.db = db
    
    async def start_oauth(self, user_id: str):
        """Start OAuth flow and return authorization URL"""
        flow = Flow.from_client_config({
            "web": {
                "client_id": GOOGLE_CLIENT_ID,
                "client_secret": GOOGLE_CLIENT_SECRET,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token"
            }
        }, scopes=SCOPES, redirect_uri=REDIRECT_URI)
        
        auth_url, state = flow.authorization_url(
            access_type='offline',
            prompt='consent'
        )
        
        # Save state temporarily
        await self.db.oauth_states.insert_one({
            "state": state,
            "user_id": user_id,
            "created_at": datetime.now(timezone.utc),
            "expires_at": datetime.now(timezone.utc) + timedelta(minutes=10)
        })
        
        return auth_url
    
    async def handle_callback(self, code: str, state: str):
        """Handle OAuth callback and save tokens"""
        # Verify state
        state_doc = await self.db.oauth_states.find_one({"state": state})
        if not state_doc:
            raise ValueError("Invalid state")
        
        if datetime.now(timezone.utc) > state_doc['expires_at'].replace(tzinfo=timezone.utc):
            raise ValueError("State expired")
        
        user_id = state_doc['user_id']
        
        # Exchange code for tokens
        flow = Flow.from_client_config({
            "web": {
                "client_id": GOOGLE_CLIENT_ID,
                "client_secret": GOOGLE_CLIENT_SECRET,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token"
            }
        }, scopes=SCOPES, redirect_uri=REDIRECT_URI)
        
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            flow.fetch_token(code=code)
        
        creds = flow.credentials
        
        # Check required scopes
        required_scopes = {"https://www.googleapis.com/auth/spreadsheets"}
        granted_scopes = set(creds.scopes or [])
        if not required_scopes.issubset(granted_scopes):
            missing = required_scopes - granted_scopes
            logger.error(f"Missing required scopes: {missing}")
            raise ValueError(f"Missing required scopes: {', '.join(missing)}")
        
        # Save tokens
        await self.db.google_connections.delete_many({"user_id": user_id})
        await self.db.google_connections.insert_one({
            "id": str(uuid.uuid4()),
            "user_id": user_id,
            "access_token": creds.token,
            "refresh_token": creds.refresh_token,
            "token_uri": creds.token_uri,
            "client_id": creds.client_id,
            "client_secret": creds.client_secret,
            "expires_at": datetime.now(timezone.utc) + timedelta(seconds=3600),
            "created_at": datetime.now(timezone.utc).isoformat()
        })
        
        # Clean up state
        await self.db.oauth_states.delete_one({"state": state})
        
        return user_id
    
    async def get_credentials(self, user_id: str):
        """Get and refresh credentials if needed"""
        token_doc = await self.db.google_connections.find_one({"user_id": user_id})
        if not token_doc:
            raise ValueError("Not connected to Google")
        
        creds = Credentials(
            token=token_doc["access_token"],
            refresh_token=token_doc["refresh_token"],
            token_uri=token_doc["token_uri"],
            client_id=token_doc["client_id"],
            client_secret=token_doc["client_secret"]
        )
        
        # Refresh if expired
        expires_at = token_doc["expires_at"]
        if isinstance(expires_at, str):
            expires_at = datetime.fromisoformat(expires_at)
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)
        
        if datetime.now(timezone.utc) >= expires_at:
            creds.refresh(GoogleRequest())
            # Update token in DB
            await self.db.google_connections.update_one(
                {"user_id": user_id},
                {"$set": {
                    "access_token": creds.token,
                    "expires_at": datetime.now(timezone.utc) + timedelta(seconds=3600)
                }}
            )
        
        return creds
    
    async def is_connected(self, user_id: str):
        """Check if user has connected Google account"""
        token_doc = await self.db.google_connections.find_one({"user_id": user_id})
        return token_doc is not None
    
    async def disconnect(self, user_id: str):
        """Disconnect Google account"""
        await self.db.google_connections.delete_many({"user_id": user_id})
    
    async def list_spreadsheets(self, user_id: str):
        """List user's spreadsheets"""
        creds = await self.get_credentials(user_id)
        service = build('drive', 'v3', credentials=creds)
        
        results = service.files().list(
            q="mimeType='application/vnd.google-apps.spreadsheet'",
            pageSize=100,
            fields="files(id, name, modifiedTime)"
        ).execute()
        
        return results.get('files', [])
    
    async def get_sheet_tabs(self, user_id: str, spreadsheet_id: str):
        """Get tabs/sheets in a spreadsheet"""
        creds = await self.get_credentials(user_id)
        service = build('sheets', 'v4', credentials=creds)
        
        spreadsheet = service.spreadsheets().get(spreadsheetId=spreadsheet_id).execute()
        sheets = spreadsheet.get('sheets', [])
        
        return [{"name": sheet['properties']['title'], "index": sheet['properties']['index']} for sheet in sheets]
    
    async def get_sheet_values(self, user_id: str, spreadsheet_id: str, sheet_name: str, range_notation: str):
        """Get values from a sheet"""
        creds = await self.get_credentials(user_id)
        service = build('sheets', 'v4', credentials=creds)
        
        full_range = f"{sheet_name}!{range_notation}"
        result = service.spreadsheets().values().get(
            spreadsheetId=spreadsheet_id,
            range=full_range
        ).execute()
        
        return result.get('values', [])
    
    async def write_sheet_values(self, user_id: str, spreadsheet_id: str, sheet_name: str, range_notation: str, values: list):
        """Write values to a sheet"""
        creds = await self.get_credentials(user_id)
        service = build('sheets', 'v4', credentials=creds)
        
        full_range = f"{sheet_name}!{range_notation}"
        body = {"values": values}
        
        result = service.spreadsheets().values().update(
            spreadsheetId=spreadsheet_id,
            range=full_range,
            valueInputOption="RAW",
            body=body
        ).execute()
        
        return result

    async def batch_write_values(self, user_id: str, spreadsheet_id: str, data: list):
        """
        Batch write values to a sheet
        data = [
          {"range": "Sheet1!AA1:AC1", "values": [[...]]},
          ...
        ]
        """
        creds = await self.get_credentials(user_id)
        service = build("sheets", "v4", credentials=creds)

        body = {
            "valueInputOption": "RAW",
            "data": data
        }

        return service.spreadsheets().values().batchUpdate(
            spreadsheetId=spreadsheet_id,
            body=body
        ).execute()
