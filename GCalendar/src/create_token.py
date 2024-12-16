from google_auth_oauthlib.flow import InstalledAppFlow
import os

def create_new_token():
    # กำหนด scopes ที่ต้องการ
    SCOPES = ['https://www.googleapis.com/auth/calendar']
    
    # กำหนด path
    current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    credentials_path = os.path.join(current_dir, "credentials", "credentials.json")
    token_path = os.path.join(current_dir, "credentials", "token.json")
    
    try:
        # สร้าง flow สำหรับ OAuth
        flow = InstalledAppFlow.from_client_secrets_file(credentials_path, SCOPES)
        
        # เริ่มกระบวนการ authentication (จะเปิดเบราว์เซอร์)
        creds = flow.run_local_server(port=0)
        
        # บันทึก token
        with open(token_path, 'w') as token:
            token.write(creds.to_json())
            
        print(f"Token created successfully and saved to {token_path}")
        print("You can now use the calendar service with the new account")
        
    except Exception as e:
        print(f"Error creating token: {str(e)}")

if __name__ == "__main__":
    create_new_token()