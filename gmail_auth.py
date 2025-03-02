import os
import pickle
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

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
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        
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