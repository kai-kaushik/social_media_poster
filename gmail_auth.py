import os
import pickle
import json
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Define the scopes your application needs
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

def get_gmail_service():
    """Gets authenticated Gmail API service."""
    creds = None
    
    # The file token.pickle stores the user's access and refresh tokens
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    
    # If there are no valid credentials available, let the user log in
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            # Create credentials.json dynamically from environment variables
            credentials_data = {
                "installed": {
                    "client_id": os.getenv("GOOGLE_CLIENT_ID"),
                    "project_id": os.getenv("GOOGLE_PROJECT_ID"),
                    "auth_uri": os.getenv("GOOGLE_AUTH_URI"),
                    "token_uri": os.getenv("GOOGLE_TOKEN_URI"),
                    "auth_provider_x509_cert_url": os.getenv("GOOGLE_AUTH_PROVIDER_CERT_URL"),
                    "client_secret": os.getenv("GOOGLE_CLIENT_SECRET"),
                    "redirect_uris": [os.getenv("GOOGLE_REDIRECT_URIS")]
                }
            }
            
            # Write credentials to temporary file
            with open('temp_credentials.json', 'w') as f:
                json.dump(credentials_data, f)
                
            flow = InstalledAppFlow.from_client_secrets_file(
                'temp_credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
            
            # Remove temporary credentials file
            if os.path.exists('temp_credentials.json'):
                os.remove('temp_credentials.json')
        
        # Save the credentials for the next run
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)
    
    # Build and return the Gmail service
    service = build('gmail', 'v1', credentials=creds)
    return service

# Example usage
if __name__ == '__main__':
    service = get_gmail_service()
    
    # List the user's Gmail labels
    results = service.users().labels().list(userId='me').execute()
    labels = results.get('labels', [])
    
    if not labels:
        print('No labels found.')
    else:
        print('Labels:')
        for label in labels:
            print(f"- {label['name']}")