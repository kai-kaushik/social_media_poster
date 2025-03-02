# AI News Social Media Poster

An automated tool that monitors a Gmail inbox for AI news from ButtonDown newsletters, generates professional LinkedIn posts using Claude, and schedules them over a 3-day period.

## Features

- **Email Monitoring**: Automatically checks for new emails from `ainews@buttondown.email`
- **Content Extraction**: Extracts key points from AI news newsletters
- **AI-Powered Post Generation**: Uses Anthropic's Claude to create authentic, first-person LinkedIn posts
- **Intelligent Scheduling**: Distributes posts over a 3-day period at optimal times for engagement
- **Automated Posting**: Handles the entire workflow from email to published LinkedIn post
- **Pydantic AI Integration**: Uses Pydantic AI for structured agent development with type safety

## Prerequisites

- Python 3.8+
- Virtual environment (already created with `mkvirtualenv social_media_poster`)
- Google account with OAuth 2.0 client credentials
- LinkedIn developer account with API access
- Anthropic API key (for Claude access)

## Project Components

This project consists of several key components:

1. **Gmail Authentication** (`gmail_auth.py`): Handles authentication with the Gmail API
2. **LinkedIn Authentication** (`linkedin_auth.py`): Manages LinkedIn OAuth authentication flow
3. **Gmail Processing** (`google_main.py`): Fetches and processes emails from specified senders
4. **LinkedIn Posting** (`linkedin_main.py`): Posts content to LinkedIn via their API
5. **Post Generation Agent** (`agent.py`): Pydantic AI agent that extracts topics and generates posts
6. **Scheduler** (`scheduler.py`): Manages background operations for continuous posting

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/social_media_poster.git
cd social_media_poster
```

2. Create and activate your virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install the required packages:
```bash
pip install -r requirements.txt
```

4. Create a `.env` file based on the `.env.example` template:
```bash
cp .env.example .env
```

5. Fill in your credentials in the `.env` file:
```
# Google/Gmail API credentials
GOOGLE_CLIENT_ID=your-google-client-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your-google-client-secret
GOOGLE_PROJECT_ID=your-google-project-id
GOOGLE_AUTH_URI=https://accounts.google.com/o/oauth2/auth
GOOGLE_TOKEN_URI=https://oauth2.googleapis.com/token
GOOGLE_AUTH_PROVIDER_CERT_URL=https://www.googleapis.com/oauth2/v1/certs
GOOGLE_REDIRECT_URIS=http://localhost

# LinkedIn API credentials
LINKEDIN_CLIENT_ID=your-linkedin-client-id
LINKEDIN_CLIENT_SECRET=your-linkedin-client-secret
LINKEDIN_REDIRECT_URI=http://localhost:8000/callback

# Anthropic API for Claude
ANTHROPIC_API_KEY=your-anthropic-api-key

# Configuration
NEWSLETTER_SENDER=sender@example.com
```

## Getting API Credentials

### Google OAuth Credentials
1. Go to the [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Enable the Gmail API
4. Create OAuth 2.0 credentials
5. Set up the OAuth consent screen
6. Download the credentials.json file

### LinkedIn API Credentials
1. Go to the [LinkedIn Developer Portal](https://www.linkedin.com/developers/)
2. Create a new app
3. Request the necessary permissions for posting content (`w_member_social`)
4. Set up the redirect URI (e.g., `http://localhost:8000/callback`)
5. Copy your client ID and client secret

### Anthropic API Key
1. Sign up at [Anthropic's website](https://www.anthropic.com/)
2. Request API access
3. Generate an API key from your account dashboard

## Usage

### Authentication Setup

The first time you run any component, you'll need to authenticate:

1. For Gmail: The script will open a browser window for you to authenticate with your Google account
2. For LinkedIn: The script will open a browser window for you to authenticate with your LinkedIn account

OAuth tokens will be saved locally for future use.

### Running the Agent

```bash
python agent.py
```

The agent will:
1. Fetch the latest email from your specified newsletter sender
2. Extract 5-6 interesting topics using Claude
3. Generate thoughtful LinkedIn posts for each topic
4. Schedule the posts over a 3-day period
5. Give you the option to post one immediately
6. Save all generated posts to a JSON file

### Using the Scheduler

For continuous operation, you can use the scheduler:

```bash
python scheduler.py
```

The scheduler will:
1. Check for new newsletter emails every 6 hours
2. Generate and schedule posts when new content is found
3. Post content automatically at the scheduled times
4. Keep logs in `linkedin_poster.log`

To run the scheduler as a background service:

```bash
# On Linux/Mac:
nohup python scheduler.py > /dev/null 2>&1 &

# On Windows (PowerShell):
Start-Process -NoNewWindow python "scheduler.py"
```

### Customization

You can customize the agent by editing `agent.py`:

- Change the `user_interests` list to match your professional interests
- Modify `user_first_name` and `user_writing_style` to match your identity
- Adjust the `days_to_spread` parameter to change the posting schedule
- Edit the posting times by changing the `posting_times` list

## Advanced Features

### Posting Schedule

By default, posts are scheduled across 3 days at optimal times:
- 9:00 AM: When people check LinkedIn in the morning
- 12:00 PM: During lunch breaks
- 5:00 PM: End of workday engagement

### Post Format

Each post is carefully crafted to:
- Sound authentic and conversational
- Include your perspective on the topic
- End with an engaging question to encourage comments
- Be the optimal length for LinkedIn engagement (150-250 words)

## Troubleshooting

- **Authentication Errors**: Ensure all credentials in the `.env` file are correct
- **Token Expiration**: If tokens expire, delete the token files and re-authenticate
- **API Limits**: Be aware of API rate limits for Anthropic and LinkedIn
- **JSON Parsing Errors**: If the agent fails to extract topics, check the newsletter format

## Development

This project uses:
- **Pydantic AI**: For structured agent development
- **Anthropic API**: For content analysis and generation
- **Async Python**: For efficient API interactions
- **Type Annotations**: For better code reliability

## License

This project is licensed under the MIT License - see the LICENSE file for details.