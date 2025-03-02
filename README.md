# AI News Social Media Poster

An automated tool that monitors a Gmail inbox for AI news from ButtonDown newsletters, generates professional LinkedIn posts using Claude Sonnet 3.5, and schedules them over a 3-day period.

## Features

- **Email Monitoring**: Automatically checks for new emails from `ainews@buttondown.email`
- **Content Extraction**: Extracts key points from AI news newsletters
- **AI-Powered Post Generation**: Uses Anthropic's Claude Sonnet 3.5 to create authentic, first-person LinkedIn posts
- **Intelligent Scheduling**: Distributes posts over a 3-day period at optimal times for engagement
- **Automated Posting**: Handles the entire workflow from email to published LinkedIn post

## Prerequisites

- Python 3.8+
- Virtual environment (already created with `mkvirtualenv social_media_poster`)
- Google account with OAuth 2.0 client credentials
- LinkedIn developer account with API access
- Anthropic API key (for Claude access)

## Installation

1. Activate your virtual environment:
```bash
workon social_media_poster
```

2. Install the required packages:
```bash
pip install -r requirements.txt
```

3. Create a `.env` file based on the `.env.example` template:
```bash
cp .env.example .env
```

4. Fill in your credentials in the `.env` file:
```
# Google OAuth credentials
GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_client_secret
GOOGLE_REFRESH_TOKEN=your_google_refresh_token

# LinkedIn OAuth credentials
LINKEDIN_CLIENT_ID=your_linkedin_client_id
LINKEDIN_CLIENT_SECRET=your_linkedin_client_secret
LINKEDIN_ACCESS_TOKEN=your_linkedin_access_token
LINKEDIN_PERSON_ID=your_linkedin_person_id

# Anthropic API key
ANTHROPIC_API_KEY=your_anthropic_api_key

# Email configuration
SENDER_EMAIL=ainews@buttondown.email
```

## Getting API Credentials

### Google OAuth Credentials
1. Go to the [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Enable the Gmail API
4. Create OAuth 2.0 credentials
5. Set up the OAuth consent screen
6. Generate a refresh token using the OAuth 2.0 Playground

### LinkedIn API Credentials
1. Go to the [LinkedIn Developer Portal](https://www.linkedin.com/developers/)
2. Create a new app
3. Request the necessary permissions for posting content
4. Generate an access token with the required scopes
5. Find your LinkedIn Person ID (usually in your profile URL)

### Anthropic API Key
1. Sign up at [Anthropic's website](https://www.anthropic.com/)
2. Request API access
3. Generate an API key from your account dashboard

## Usage

1. Activate your virtual environment:
```bash
workon social_media_poster
```

2. Run the script:
```bash
python social_media_poster.py
```

3. The script will:
   - Check for new emails from the specified sender
   - Extract key points using Claude
   - Generate LinkedIn posts
   - Schedule and post them over a 3-day period

4. To run the script as a background service:
```bash
nohup python social_media_poster.py > output.log 2>&1 &
```

5. To stop the script:
```bash
ps aux | grep social_media_poster.py
kill [PID]
```

## Customization

You can modify the following aspects of the script:

- Email sender address in the `.env` file
- Posting frequency by changing the schedule settings
- Post style by modifying the Claude prompt
- Number of posts generated per email

## Troubleshooting

- **Authentication Errors**: Ensure all credentials in the `.env` file are correct and not expired
- **Rate Limits**: Check if you've hit API rate limits for LinkedIn or Anthropic
- **Email Access Issues**: Verify Gmail API is enabled and has proper permissions
- **Scheduling Problems**: Check system time and confirm schedule settings

## License

This project is licensed under the MIT License - see the LICENSE file for details.