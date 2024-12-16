import asyncio
import os
from calendar_service import CalendarService
from datetime import datetime, timedelta

async def list_past_events():
    # กำหนด path
    current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    credentials_path = os.path.join(current_dir, "credentials", "credentials.json")
    token_path = os.path.join(current_dir, "credentials", "token.json")
    
    # สร้าง instance ของ CalendarService
    service = CalendarService(credentials_path, token_path)
    
    try:
        # สร้าง service และ authenticate
        await service.authenticate()
        
        # กำหนดช่วงเวลา
        now = datetime.utcnow()
        
        # ดึงกิจกรรม 10 ปีย้อนหลัง (สามารถปรับจำนวนปีได้)
        ten_years_ago = now - timedelta(days=365*10)
        
        print(f"Fetching all past events from {ten_years_ago.date()} to {now.date()}")
        
        # ใช้ run_in_executor เพื่อเรียก API แบบ async
        events_result = await asyncio.get_event_loop().run_in_executor(
            None,
            lambda: service.service.events().list(
                calendarId='primary',
                timeMin=ten_years_ago.isoformat() + 'Z',
                timeMax=now.isoformat() + 'Z',
                maxResults=2500,  # ดึงข้อมูลสูงสุด
                singleEvents=True,
                orderBy='startTime'
            ).execute()
        )
        
        events = events_result.get('items', [])
        print(f"Found {len(events)} past events")
        
        # แสดงผล
        if not events:
            print("No past events found.")
            return
        
        for event in events:
            start = event['start'].get('dateTime', event['start'].get('date'))
            summary = event.get('summary', 'No title')
            print(f"{start} - {summary}")
            
    except Exception as e:
        print(f"Error: {str(e)}")
    finally:
        service.close()

if __name__ == "__main__":
    asyncio.run(list_past_events())