"""
Google Calendar service for checking availability and creating appointments
"""
from google.oauth2 import service_account
from googleapiclient.discovery import build
from datetime import datetime, timedelta
from decouple import config
import pytz
import logging

logger = logging.getLogger(__name__)


class CalendarService:
    """Handle Google Calendar operations"""
    
    SCOPES = ['https://www.googleapis.com/auth/calendar']
    
    def __init__(self):
        self.calendar_id = config('GOOGLE_CALENDAR_ID')
        self.credentials_file = config('GOOGLE_CREDENTIALS_FILE')
        self.timezone = pytz.timezone(config('TIMEZONE', default='America/Sao_Paulo'))
        self.service = self._authenticate()
    
    def _authenticate(self):
        """Authenticate with Google Calendar API"""
        try:
            credentials = service_account.Credentials.from_service_account_file(
                self.credentials_file,
                scopes=self.SCOPES
            )
            service = build('calendar', 'v3', credentials=credentials)
            logger.info("Successfully authenticated with Google Calendar")
            return service
        except Exception as e:
            logger.error(f"Failed to authenticate with Google Calendar: {str(e)}")
            raise
    
    def get_available_dates(self, days_ahead=7):
        """
        Get list of dates with availability in the next N days
        
        Args:
            days_ahead: Number of days to look ahead
            
        Returns:
            list: List of date objects with availability
        """
        available_dates = []
        today = datetime.now(self.timezone).replace(hour=0, minute=0, second=0, microsecond=0)
        
        for day_offset in range(1, days_ahead + 1):
            check_date = today + timedelta(days=day_offset)
            
            # Skip weekends (optional - remove if doctor works weekends)
            if check_date.weekday() >= 5:  # Saturday=5, Sunday=6
                continue
            
            # Check if there are any available slots
            available_slots = self.get_available_slots(check_date)
            if available_slots:
                available_dates.append(check_date)
        
        return available_dates[:3]  # Return max 3 dates for WhatsApp buttons
    
    def get_available_slots(self, date, slot_duration=30, work_start=9, work_end=17):
        """
        Get available time slots for a specific date
        
        Args:
            date: datetime object for the date to check
            slot_duration: Duration of each appointment in minutes
            work_start: Work start hour (24h format)
            work_end: Work end hour (24h format)
            
        Returns:
            list: List of available time slots as datetime objects
        """
        # Define working hours
        start_time = date.replace(hour=work_start, minute=0, second=0, microsecond=0)
        end_time = date.replace(hour=work_end, minute=0, second=0, microsecond=0)
        
        # Get existing events for the day
        events = self._get_events(start_time, end_time)
        
        # Generate all possible slots
        all_slots = []
        current_slot = start_time
        while current_slot < end_time:
            all_slots.append(current_slot)
            current_slot += timedelta(minutes=slot_duration)
        
        # Filter out occupied slots
        available_slots = []
        for slot in all_slots:
            slot_end = slot + timedelta(minutes=slot_duration)
            is_available = True
            
            for event in events:
                event_start = datetime.fromisoformat(event['start'].get('dateTime', event['start'].get('date')))
                event_end = datetime.fromisoformat(event['end'].get('dateTime', event['end'].get('date')))
                
                # Check for overlap
                if not (slot_end <= event_start or slot >= event_end):
                    is_available = False
                    break
            
            if is_available:
                available_slots.append(slot)
        
        return available_slots[:3]  # Return max 3 slots for WhatsApp buttons
    
    def _get_events(self, start_time, end_time):
        """
        Get events from calendar between start and end time
        
        Args:
            start_time: datetime object
            end_time: datetime object
            
        Returns:
            list: List of calendar events
        """
        try:
            events_result = self.service.events().list(
                calendarId=self.calendar_id,
                timeMin=start_time.isoformat(),
                timeMax=end_time.isoformat(),
                singleEvents=True,
                orderBy='startTime'
            ).execute()
            
            events = events_result.get('items', [])
            logger.info(f"Found {len(events)} events between {start_time} and {end_time}")
            return events
            
        except Exception as e:
            logger.error(f"Error fetching events: {str(e)}")
            return []
    
    def create_appointment(self, patient_name, patient_phone, appointment_type, start_time, duration=30):
        """
        Create an appointment in Google Calendar
        
        Args:
            patient_name: Name of the patient
            patient_phone: WhatsApp number of patient
            appointment_type: Type of appointment
            start_time: datetime object for appointment start
            duration: Duration in minutes
            
        Returns:
            dict: Created event details or None if failed
        """
        end_time = start_time + timedelta(minutes=duration)
        
        event = {
            'summary': f'{appointment_type} - {patient_name}',
            'description': f'Patient: {patient_name}\nPhone: {patient_phone}\nType: {appointment_type}',
            'start': {
                'dateTime': start_time.isoformat(),
                'timeZone': str(self.timezone),
            },
            'end': {
                'dateTime': end_time.isoformat(),
                'timeZone': str(self.timezone),
            },
            'reminders': {
                'useDefault': False,
                'overrides': [
                    {'method': 'popup', 'minutes': 24 * 60},  # 1 day before
                    {'method': 'popup', 'minutes': 60},  # 1 hour before
                ],
            },
        }
        
        try:
            created_event = self.service.events().insert(
                calendarId=self.calendar_id,
                body=event
            ).execute()
            
            logger.info(f"Created appointment: {created_event.get('id')}")
            return created_event
            
        except Exception as e:
            logger.error(f"Error creating appointment: {str(e)}")
            return None
    
    def format_date(self, date):
        """Format date for display in Portuguese"""
        weekdays = ['Segunda', 'Terça', 'Quarta', 'Quinta', 'Sexta', 'Sábado', 'Domingo']
        months = ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun', 'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez']
        
        weekday = weekdays[date.weekday()]
        day = date.day
        month = months[date.month - 1]
        
        return f"{weekday}, {day} {month}"
    
    def format_time(self, time):
        """Format time for display"""
        return time.strftime("%H:%M")