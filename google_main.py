import os
from gmail_auth import get_gmail_service
import base64
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def get_body_data(payload):
    """
    Extract the email body data from the message payload.
    
    Args:
        payload (dict): The message payload from Gmail API
        
    Returns:
        str: The base64 encoded body data or empty string if not found
    """
    if 'parts' in payload:
        for part in payload['parts']:
            if part['mimeType'] == 'text/plain':
                return part['body'].get('data', '')
        # If no text/plain found, try the first part
        return payload['parts'][0]['body'].get('data', '')
    else:
        return payload['body'].get('data', '')

def process_latest_email_from_sender(sender_email=None, debug=False):
    """
    Retrieves and processes only the latest email from the specified sender.
    
    Args:
        sender_email (str): Email address of the sender to retrieve emails from
                           If None, will use NEWSLETTER_SENDER from env variables
        debug (bool): Whether to print debug information
        
    Returns:
        dict: Dictionary containing email data with keys:
            - headers: Email headers
            - subject: Email subject
            - body: Decoded email body
            Returns None if no email found
    """
    # Get sender email from environment if not provided
    if sender_email is None:
        sender_email = os.getenv("NEWSLETTER_SENDER")
        
    service = get_gmail_service()
    
    # Search for emails from the specific sender, sorted by date (newest first)
    query = f"from:{sender_email}"
    results = service.users().messages().list(userId='me', q=query, maxResults=1).execute()
    messages = results.get('messages', [])
    
    if not messages:
        if debug:
            print(f"No messages found from {sender_email}")
        return None
    
    if debug:
        print(f"Retrieved latest message from {sender_email}")
    
    # Get the latest message (first in the list)
    latest_message = messages[0]
    msg = service.users().messages().get(userId='me', id=latest_message['id'], format='full').execute()
    
    # Extract headers
    headers = msg['payload']['headers']
    subject = next((header['value'] for header in headers if header['name'] == 'Subject'), 'No Subject')
    
    if debug:
        print(f"Subject: {subject}")
    
    # Get the encoded body
    encoded_body = get_body_data(msg['payload'])
    
    # Decode the base64 content
    if encoded_body:
        # Add padding if necessary
        padding = len(encoded_body) % 4
        if padding:
            encoded_body += '=' * (4 - padding)
        
        # Replace URL-safe characters and decode
        body = base64.urlsafe_b64decode(encoded_body).decode('utf-8')
    else:
        body = ''

    if debug:
        print(f"\nBody preview:\n{body[:500]}\n")

    return {
        'headers': headers,
        'subject': subject,
        'body': body
    }

# Example usage
if __name__ == '__main__':
    # Get the latest email data using environment variable for the sender
    email_data = process_latest_email_from_sender(debug=True)
    
    if email_data:
        print(f"Successfully retrieved the latest email:")
        print(f"Subject: {email_data['subject']}")
        print(f"Body length: {len(email_data['body'])} characters")
        
        # TODO: Add content extraction and LinkedIn posting logic
        # 1. Parse and extract interesting topics from body
        # 2. Generate LinkedIn posts for each topic
        # 3. Schedule posts over next 3 days
    else:
        print(f"Failed to retrieve any emails from {os.getenv('NEWSLETTER_SENDER')}")