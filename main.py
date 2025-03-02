from gmail_auth import get_gmail_service

def process_emails_from_sender(sender_email):
    service = get_gmail_service()
    
    # Search for emails from the specific sender
    query = f"from:{sender_email}"
    results = service.users().messages().list(userId='me', q=query).execute()
    messages = results.get('messages', [])
    
    if not messages:
        print(f"No messages found from {sender_email}")
        return []
    
    print(f"Found {len(messages)} messages from {sender_email}")
    
    # Process each message
    for message in messages:
        msg = service.users().messages().get(userId='me', id=message['id']).execute()
        # Extract subject, body, etc.
        # Your email processing logic here
        
        # For demonstration, just print the subject
        headers = msg['payload']['headers']
        subject = next((header['value'] for header in headers if header['name'] == 'Subject'), 'No Subject')
        print(f"Subject: {subject}")
    
    return messages

# Example usage
if __name__ == '__main__':
    newsletter_sender = "ainews@buttondown.email"
    process_emails_from_sender(newsletter_sender)