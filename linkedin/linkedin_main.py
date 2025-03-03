import os
import json
import requests
from linkedin.linkedin_auth import LinkedInAuth
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class LinkedInPoster:
    def __init__(self, access_token, person_id):
        """Initialize with access token and person ID."""
        self.access_token = access_token
        self.person_id = person_id
    
    def post_message(self, message, visibility="PUBLIC"):
        """
        Post a text message to LinkedIn feed.
        
        Args:
            message (str): The text content to post
            visibility (str): Visibility of the post. Options:
                - "PUBLIC": Visible to everyone
                - "CONNECTIONS": Visible to connections only
                - "SELF": Visible only to you
                - "LOGGED_IN": Visible to all logged-in LinkedIn members
        
        Returns:
            bool: True if posting was successful, False otherwise
        """
        # Validate visibility
        valid_visibilities = ["PUBLIC", "CONNECTIONS", "SELF", "LOGGED_IN"]
        if visibility not in valid_visibilities:
            print(f"Invalid visibility: {visibility}. Using PUBLIC as default.")
            visibility = "PUBLIC"
        
        # Set API endpoint
        url = 'https://api.linkedin.com/v2/ugcPosts'
        
        # Prepare author URN
        author_urn = f"urn:li:person:{self.person_id}"
        
        # Prepare post data
        post_data = {
            "author": author_urn,
            "lifecycleState": "PUBLISHED",
            "specificContent": {
                "com.linkedin.ugc.ShareContent": {
                    "shareCommentary": {
                        "text": message
                    },
                    "shareMediaCategory": "NONE"
                }
            },
            "visibility": {
                "com.linkedin.ugc.MemberNetworkVisibility": visibility
            }
        }
        
        # Set headers
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json',
            'X-Restli-Protocol-Version': '2.0.0'
        }
        
        # Make the POST request
        response = requests.post(url, headers=headers, json=post_data)
        
        # Check response
        if response.status_code == 201:
            print("Post shared successfully on LinkedIn!")
            return True
        else:
            print(f"Error: {response.status_code}")
            print(response.text)
            return False

def main():
    # Use credentials from environment variables
    auth = LinkedInAuth()
    if auth.authenticate():
        # Get user input for post content
        message = input("Enter your LinkedIn post message: ")
        
        # Get visibility preference
        print("\nVisibility options:")
        print("1. PUBLIC - Visible to everyone")
        print("2. CONNECTIONS - Visible to connections only")
        print("3. SELF - Visible only to you")
        print("4. LOGGED_IN - Visible to all LinkedIn members")
        visibility_choice = input("Choose visibility (1-4) or press Enter for PUBLIC: ")
        
        visibility_map = {
            "1": "PUBLIC",
            "2": "CONNECTIONS", 
            "3": "SELF",
            "4": "LOGGED_IN"
        }
        
        visibility = visibility_map.get(visibility_choice, "PUBLIC")
        
        # Create poster and post message
        poster = LinkedInPoster(auth.access_token, auth.person_id)
        result = poster.post_message(message, visibility)
        
        if result:
            print(f"Successfully posted to LinkedIn with {visibility} visibility!")
        else:
            print("Failed to post to LinkedIn.")
    else:
        print("Authentication failed. Cannot post to LinkedIn.")

if __name__ == "__main__":
    main()