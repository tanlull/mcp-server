import asyncio
import os
from calendar_service import CalendarService

async def main():
    # กำหนด path ของ credentials และ token
    current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    credentials_path = os.path.join(current_dir, "credentials", "credentials.json")
    token_path = os.path.join(current_dir, "credentials", "token.json")
    
    # สร้าง CalendarService instance
    service = CalendarService(credentials_path, token_path)
    
    # ต่ออายุ token
    await service.renew_token()

if __name__ == "__main__":
    asyncio.run(main())