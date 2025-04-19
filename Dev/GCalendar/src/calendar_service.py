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

    async def create_event(self, summary: str, start_time: str, end_time: str = None, description: str = None):
        """
        Create a new calendar event
        
        Parameters:
        - summary: Event title
        - start_time: Start time in YYYY-MM-DDTHH:MM:SS format or date in YYYY-MM-DD format
        - end_time: End time (optional). If not provided, event will be 1 hour long
        - description: Event description (optional)
        
        Returns:
        - Status message
        """
        try:
            if not self.service:
                await self.authenticate()

            # Parse start time
            try:
                # Check if time is included
                if 'T' in start_time:
                    start_dt = datetime.fromisoformat(start_time)
                    is_datetime = True
                else:
                    start_dt = datetime.strptime(start_time, '%Y-%m-%d')
                    is_datetime = False
            except ValueError:
                return f"Invalid start time format: {start_time}. Use YYYY-MM-DDTHH:MM:SS or YYYY-MM-DD"

            # Handle end time
            if end_time:
                try:
                    if 'T' in end_time:
                        end_dt = datetime.fromisoformat(end_time)
                    else:
                        end_dt = datetime.strptime(end_time, '%Y-%m-%d')
                        if is_datetime:
                            # If start has time but end doesn't, make end time 23:59:59
                            end_dt = end_dt.replace(hour=23, minute=59, second=59)
                except ValueError:
                    return f"Invalid end time format: {end_time}. Use YYYY-MM-DDTHH:MM:SS or YYYY-MM-DD"
            else:
                # Default to 1 hour duration for datetime events, or same day for date events
                if is_datetime:
                    end_dt = start_dt + timedelta(hours=1)
                else:
                    end_dt = start_dt

            # Create event body
            event_body = {
                'summary': summary,
                'start': {
                    'dateTime' if is_datetime else 'date': start_dt.isoformat(),
                    'timeZone': self.TIMEZONE if is_datetime else None
                },
                'end': {
                    'dateTime' if is_datetime else 'date': end_dt.isoformat(),
                    'timeZone': self.TIMEZONE if is_datetime else None
                }
            }

            # Add optional description if provided
            if description:
                event_body['description'] = description

            # Create the event
            created_event = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self.service.events().insert(
                    calendarId='primary',
                    body=event_body
                ).execute()
            )
            
            logger.info(f"Created event: {created_event['id']} - {summary}")
            return f"Successfully created event: {summary}"

        except HttpError as error:
            error_msg = f"An error occurred: {str(error)}"
            logger.error(error_msg)
            return error_msg
        except Exception as error:
            error_msg = f"Unexpected error: {str(error)}"
            logger.error(error_msg)
            return error_msg

    async def delete_duplicate_events(self, target_date: str, event_summary: str):
        """
        Delete duplicate events on a specific date
        
        Parameters:
        - target_date: Target date in YYYY-MM-DD format
        - event_summary: Event title to match
        
        Returns:
        - Status message
        """
        try:
            if not self.service:
                await self.authenticate()

            # Parse target date
            try:
                target_dt = datetime.strptime(target_date, '%Y-%m-%d')
            except ValueError:
                return f"Invalid date format: {target_date}. Use YYYY-MM-DD"

            # Set time range for the target date
            start_dt = target_dt.replace(hour=0, minute=0, second=0, tzinfo=self.tz)
            end_dt = target_dt.replace(hour=23, minute=59, second=59, tzinfo=self.tz)

            # Get events for the target date
            events_result = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self.service.events().list(
                    calendarId='primary',
                    timeMin=start_dt.isoformat(),
                    timeMax=end_dt.isoformat(),
                    singleEvents=True,
                    orderBy='startTime',
                    timeZone=self.TIMEZONE
                ).execute()
            )
            
            events = events_result.get('items', [])
            
            # Find duplicate events
            duplicate_ids = []
            seen_times = set()
            
            for event in events:
                if event.get('summary') == event_summary:
                    start_time = self._format_event_time(event)
                    if start_time in seen_times:
                        duplicate_ids.append(event['id'])
                    else:
                        seen_times.add(start_time)
            
            if not duplicate_ids:
                return f"No duplicate events found for '{event_summary}' on {target_date}"

            # Delete duplicate events
            deleted_count = 0
            for event_id in duplicate_ids:
                try:
                    await asyncio.get_event_loop().run_in_executor(
                        None,
                        lambda: self.service.events().delete(
                            calendarId='primary',
                            eventId=event_id
                        ).execute()
                    )
                    deleted_count += 1
                except HttpError as error:
                    logger.error(f"Error deleting event {event_id}: {str(error)}")

            logger.info(f"Deleted {deleted_count} duplicate events for '{event_summary}' on {target_date}")
            return f"Successfully deleted {deleted_count} duplicate events for '{event_summary}' on {target_date}"

        except HttpError as error:
            error_msg = f"An error occurred: {str(error)}"
            logger.error(error_msg)
            return error_msg
        except Exception as error:
            error_msg = f"Unexpected error: {str(error)}"
            logger.error(error_msg)
            return error_msg

    async def renew_token(self):
        """Renew the authentication token"""
        try:
            if not self.creds:
                self.creds = Credentials.from_authorized_user_file(self.token_path, self.SCOPES)

            if self.creds and self.creds.expired and self.creds.refresh_token:
                logger.info("Token expired, refreshing...")
                self.creds.refresh(Request())
                # Save refreshed credentials
                with open(self.token_path, 'w') as token:
                    token.write(self.creds.to_json())
                logger.info("Token refreshed and saved")
                return "Token renewed successfully"
            else:
                return "Token is still valid"
        except Exception as e:
            error_msg = f"Error renewing token: {str(e)}"
            logger.error(error_msg)
            return error_msg

    def close(self):
        """Clean up resources"""
        if self.service:
            logger.info("Closing calendar service")
            self.service.close()