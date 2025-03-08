# AI News Social Media Poster

An automated tool that monitors a Gmail inbox for AI news from ButtonDown newsletters, generates professional LinkedIn posts using Claude, and schedules them over a 3-day period.

## Features

- **Email Monitoring**: Automatically checks for new emails from `ainews@buttondown.email`
- **Content Extraction**: Extracts key points from AI news newsletters
- **AI-Powered Post Generation**: Uses Anthropic's Claude to create authentic, first-person LinkedIn posts
- **Intelligent Scheduling**: Distributes posts over a 3-day period at optimal times for engagement
- **Automated Posting**: Handles the entire workflow from email to published LinkedIn post
- **Pydantic AI Integration**: Uses Pydantic AI for structured agent development with type safety
- **Interactive Mode**: Choose which posts to publish immediately from the command line

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
5. **Agent Flow** (`agent_flow.py`): Main script that orchestrates the entire process
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

### Running the Agent Flow

The main script is `agent_flow.py`, which can be run with various command-line options:

```bash
python agent_flow.py [options]
```

#### Command Line Options

- `--topics N`: Number of topics to extract (default: 5)
- `--days N`: Number of days to schedule posts over (default: 3)
- `--sender EMAIL`: Email address of the newsletter sender (default: uses value from .env file)
- `--use-saved`: Use previously saved posts instead of generating new ones
- `--quiet`: Disable console logging (only log to file)

#### Examples

Generate new posts from a specific sender:
```bash
python agent_flow.py --sender newsletter@example.com --topics 6
```

Use previously saved posts:
```bash
python agent_flow.py --use-saved
```

Generate fewer topics and schedule over more days:
```bash
python agent_flow.py --topics 3 --days 5
```

#### What Happens When You Run It

When you run the script:

1. It either loads previously saved posts (if `--use-saved` is specified) or generates new ones by:
   - Fetching the latest email from the specified sender
   - Extracting interesting topics using Claude
   - Generating LinkedIn posts for each topic
   - Scheduling these posts over the specified number of days

2. It displays all the scheduled posts with their content and scheduled times

3. It shows any posts that are scheduled for today

4. It saves the generated posts to `scheduled_posts.json` (if they're newly generated)

5. It prompts you to choose a post to publish immediately or exit

6. If you choose a post, it asks for confirmation before publishing it to LinkedIn

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

You can customize the agent by editing the configuration parameters:

- Change the sender email to match your newsletter source
- Adjust the number of topics to extract
- Modify the scheduling period to match your posting frequency
- Edit the posting times by changing the business hours in the code

## Advanced Features

### Posting Schedule

By default, posts are scheduled across 3 days at optimal times:
- 9:00 AM: When people check LinkedIn in the morning
- 12:00 PM: During lunch breaks
- 3:00 PM: Mid-afternoon engagement
- 5:00 PM: End of workday engagement

### Post Format

Each post is carefully crafted to:
- Sound authentic and conversational
- Include your perspective on the topic
- End with relevant hashtags for better discoverability
- Be the optimal length for LinkedIn engagement (150-200 words)

### Saved Posts Management

The tool saves all generated posts to a JSON file (`scheduled_posts.json`), allowing you to:
- Track which posts have been published
- Reuse previously generated posts without calling the API again
- Maintain a history of your LinkedIn content

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