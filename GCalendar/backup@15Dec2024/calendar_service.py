from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from datetime import datetime, timedelta
import logging
import asyncio
import os
import json
from zoneinfo import ZoneInfo

# Set up logging
log_formatter = logging.Formatter(
    '[%(asctime)s] %(levelname)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# Console handler
console_handler = logging.StreamHandler()
console_handler.setFormatter(log_formatter)

# File handler
log_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'logs', 'calendar_service.log')
file_handler = logging.FileHandler(log_file, mode='a', encoding='utf-8')
file_handler.setFormatter(log_formatter)

# Set up logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logger.addHandler(console_handler)
logger.addHandler(file_handler)

class CalendarService:
    SCOPES = ['https://www.googleapis.com/auth/calendar']
    TIMEZONE = 'Asia/Bangkok'
    
    def __init__(self, credentials_path: str, token_path: str):
        self.credentials_path = credentials_path
        self.token_path = token_path
        self.creds = None
        self.service = None
        self.tz = ZoneInfo(self.TIMEZONE)
        self.events_cache = {}  # Initialize events cache

    async def authenticate(self):
        """Authenticate with Google Calendar API"""
        try:
            self.creds = Credentials.from_authorized_user_file(self.token_path, self.SCOPES)
            
            # Check if credentials are expired and refresh if needed
            if self.creds and self.creds.expired and self.creds.refresh_token:
                logger.info("Token expired, refreshing...")
                self.creds.refresh(Request())
                # Save refreshed credentials
                with open(self.token_path, 'w') as token:
                    token.write(self.creds.to_json())
                logger.info("Token refreshed and saved")
                    
            self.service = build('calendar', 'v3', credentials=self.creds)
            logger.info("Authentication successful")
            return True
        except Exception as e:
            logger.error(f"Authentication error: {str(e)}")
            raise

    async def list_events(self, max_results: int = 1000):
        """List calendar events and cache their IDs"""
        try:
            if not self.service:
                await self.authenticate()

            logger.info("Fetching calendar events...")
            
            now = datetime.now(self.tz)
            two_years_ago = now - timedelta(days=730)
            one_year_later = now + timedelta(days=365)
            
            events_result = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self.service.events().list(
                    calendarId='primary',
                    timeMin=two_years_ago.isoformat(),
                    timeMax=one_year_later.isoformat(),
                    maxResults=max_results,
                    singleEvents=True,
                    orderBy='startTime',
                    timeZone=self.TIMEZONE
                ).execute()
            )
            
            events = events_result.get('items', [])
            logger.info(f"Found {len(events)} events")

            if not events:
                return "No events found."

            # Reset and update cache
            self.events_cache = {}
            formatted_text = ""
            
            for event in events:
                start_time = self._format_event_time(event)
                summary = event.get('summary', 'No title')
                cache_key = f"{start_time} {summary}"
                
                formatted_text += f"{cache_key}\n"
                self.events_cache[cache_key] = event['id']
            
            return formatted_text

        except HttpError as error:
            error_msg = f"An error occurred: {str(error)}"
            logger.error(error_msg)
            return error_msg

    def _format_event_time(self, event: dict) -> str:
        """Format event time consistently with timezone"""
        start = event['start'].get('dateTime', event['start'].get('date'))
        if 'T' in start:  # This is a datetime
            dt = datetime.fromisoformat(start)
            if dt.tzinfo is None:  # Add timezone if not present
                dt = dt.replace(tzinfo=self.tz)
            formatted_time = dt.strftime('%Y-%m-%dT%H:%M:%S%z')
        else:  # This is a date
            formatted_time = start
        return formatted_time

    async def delete_single_event(self, event_time: str, event_summary: str):
        """
        Delete a specific event by its time and summary
        
        Parameters:
        - event_time: Event time in format matching list output
        - event_summary: Event title to match
        
        Returns:
        - Status message
        """
        try:
            if not self.service:
                await self.authenticate()

            # First update the cache
            await self.list_events()
            
            # Get event ID from cache
            cache_key = f"{event_time} {event_summary}"
            event_id = self.events_cache.get(cache_key)
            
            if not event_id:
                return f"Event not found: {cache_key}"
            
            # Delete the event
            await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self.service.events().delete(
                    calendarId='primary',
                    eventId=event_id
                ).execute()
            )
            
            logger.info(f"Deleted event: {event_id} - {cache_key}")
            return f"Successfully deleted event: {cache_key}"

        except HttpError as error:
            error_msg = f"An error occurred: {str(error)}"
            logger.error(error_msg)
            return error_msg
        except Exception as error:
            error_msg = f"Unexpected error: {str(error)}"
            logger.error(error_msg)
            return error_msg

    # [Previous methods: create_event, delete_duplicate_events, etc. remain unchanged]

    def close(self):
        """Clean up resources"""
        if self.service:
            logger.info("Closing calendar service")
            self.service.close()
