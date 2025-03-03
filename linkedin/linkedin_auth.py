import os
import requests
import json
import webbrowser
from http.server import HTTPServer, BaseHTTPRequestHandler
import urllib.parse
import threading
import time
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class OAuthHandler(BaseHTTPRequestHandler):
    """Handler for the OAuth callback."""
    
    def do_GET(self):
        """Handle GET request, extract code param from the URL."""
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        
        # Parse the URL and extract the authorization code
        query_components = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
        if 'code' in query_components:
            self.server.authorization_code = query_components['code'][0]
            self.wfile.write(b'Authorization successful! You can close this window now.')
        else:
            self.wfile.write(b'Authorization failed. Please try again.')

class LinkedInAuth:
    def __init__(self, client_id=None, client_secret=None, redirect_uri=None):
        """Initialize with LinkedIn app credentials."""
        # Use provided values or fallback to environment variables
        self.client_id = client_id or os.getenv("LINKEDIN_CLIENT_ID")
        self.client_secret = client_secret or os.getenv("LINKEDIN_CLIENT_SECRET")
        self.redirect_uri = redirect_uri or os.getenv("LINKEDIN_REDIRECT_URI")
        self.access_token = None
        self.person_id = None
    
    def get_authorization_url(self):
        """Generate the authorization URL for LinkedIn OAuth."""
        scope = "w_member_social,openid,profile,email"
        return f"https://www.linkedin.com/oauth/v2/authorization?response_type=code&client_id={self.client_id}&redirect_uri={self.redirect_uri}&scope={scope}"
    
    def start_auth_server(self, port=8000):
        """Start a local HTTP server to receive the callback."""
        server = HTTPServer(('localhost', port), OAuthHandler)
        server.authorization_code = None
        
        # Run server in a separate thread
        server_thread = threading.Thread(target=server.serve_forever)
        server_thread.daemon = True
        server_thread.start()
        
        return server
    
    def get_access_token(self, authorization_code):
        """Exchange authorization code for access token."""
        url = 'https://www.linkedin.com/oauth/v2/accessToken'
        payload = {
            'grant_type': 'authorization_code',
            'code': authorization_code,
            'redirect_uri': self.redirect_uri,
            'client_id': self.client_id,
            'client_secret': self.client_secret
        }
        
        response = requests.post(url, data=payload)
        if response.status_code == 200:
            token_data = response.json()
            self.access_token = token_data['access_token']
            return self.access_token
        else:
            print(f"Error getting access token: {response.status_code}")
            print(response.text)
            return None
    
    def get_profile(self):
        """Get user profile to retrieve person ID."""
        if not self.access_token:
            print("No access token available. Please authenticate first.")
            return None
        
        # Get user profile using the OpenID userinfo endpoint
        url = 'https://api.linkedin.com/v2/userinfo'
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'X-Restli-Protocol-Version': '2.0.0'
        }
        
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            profile_data = response.json()
            # Extract LinkedIn sub field which is your LinkedIn ID
            self.person_id = profile_data.get('sub')
            return profile_data
        else:
            print(f"Error getting profile: {response.status_code}")
            print(response.text)
            return None
    
    def authenticate(self):
        """Complete OAuth flow to get access token."""
        # Start local server
        port = 8000
        server = self.start_auth_server(port)
        
        # Open browser for user authorization
        auth_url = self.get_authorization_url()
        print(f"Opening browser to: {auth_url}")
        webbrowser.open(auth_url)
        
        # Wait for the authorization code (max 2 minutes)
        timeout = time.time() + 120
        while not server.authorization_code and time.time() < timeout:
            time.sleep(1)
        
        # Shutdown the server
        server.shutdown()
        
        if not server.authorization_code:
            print("Timed out waiting for authorization.")
            return False
        
        # Exchange code for token
        print("Got authorization code. Exchanging for access token...")
        if self.get_access_token(server.authorization_code):
            # Get user profile to get person ID
            self.get_profile()
            print(f"Authentication successful!")
            print(f"Access Token: {self.access_token}")
            print(f"Person ID: {self.person_id}")
            return True
        else:
            print("Failed to get access token.")
            return False

if __name__ == "__main__":
    # Use credentials from environment variables
    auth = LinkedInAuth()
    auth.authenticate()