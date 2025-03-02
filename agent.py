"""
LinkedIn Post Generator Agent

This module uses Pydantic AI to create an agent that:
1. Extracts important topics from newsletter emails
2. Generates thoughtful LinkedIn posts based on those topics
3. Formats them as if written by the user

The agent uses Anthropic's Claude API for content analysis and generation.
"""

import os
import re
import json
import logging
from dataclasses import dataclass, field
from typing import List, Optional
from datetime import datetime, timedelta, timezone

import anthropic
from pydantic import BaseModel, Field
from pydantic_ai import Agent, RunContext, ModelRetry
from dotenv import load_dotenv

from google_main import process_latest_email_from_sender
from linkedin_main import LinkedInPoster
from linkedin_auth import LinkedInAuth

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('newsletter_agent')

# ----------------------
# Models and Data Classes
# ----------------------

class Topic(BaseModel):
    """A topic extracted from the newsletter with details."""
    title: str = Field(description="Title or main subject of the topic")
    summary: str = Field(description="Brief summary of what the topic is about")
    key_points: List[str] = Field(description="Key points or takeaways from the topic")
    relevance: str = Field(description="Why this topic might be interesting or important")


class LinkedInPost(BaseModel):
    """A LinkedIn post ready to be published."""
    content: str = Field(description="The full text content of the LinkedIn post")
    topic: Topic = Field(description="The topic this post is based on")
    scheduled_time: Optional[datetime] = Field(
        default=None, 
        description="When this post should be published"
    )


class PostGenerationResult(BaseModel):
    """The result of the post generation process."""
    posts: List[LinkedInPost] = Field(description="List of generated LinkedIn posts")
    topics: List[Topic] = Field(description="List of extracted topics from the newsletter")
    email_subject: str = Field(description="Subject of the processed email")
    email_source: str = Field(description="Source/sender of the processed email")


@dataclass
class NewsletterDependencies:
    """Dependencies for the newsletter processing agent."""
    email_data: dict
    user_first_name: str = "Kai"  # Customize with the user's actual first name
    user_professional_interests: List[str] = field(default_factory=list)
    user_writing_style: str = "Professional yet conversational, with occasional humor. Uses first-person perspective and is an AI and Tech Enthusiast."
    days_to_spread: int = 3  # Number of days to spread posts over
    max_posts: int = 5  # Maximum number of posts to generate


# ----------------------
# Agent Configuration
# ----------------------

# Update to use the latest model
CLAUDE_MODEL = "claude-3-sonnet-20240229"
# Check if CLAUDE_MODEL_OVERRIDE is set in .env
if os.getenv("CLAUDE_MODEL_OVERRIDE"):
    CLAUDE_MODEL = os.getenv("CLAUDE_MODEL_OVERRIDE")
    # Verify the model exists
    try:
        logger.info(f"Testing model override: {CLAUDE_MODEL}")
        test_client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        # Just try to get the list of models
        models = test_client.models.list()
        logger.info(f"Available models: {[m.id for m in models.data]}")
    except Exception as e:
        logger.warning(f"Model override {CLAUDE_MODEL} may not be valid: {e}")
        logger.warning("Falling back to default model: claude-3-sonnet-20240229")
        CLAUDE_MODEL = "claude-3-sonnet-20240229"

newsletter_agent = Agent(
    f'anthropic:{CLAUDE_MODEL}',
    deps_type=NewsletterDependencies,
    result_type=PostGenerationResult,
    retries=2,  # Increase default retries
    system_prompt="""
    You are a professional LinkedIn content creator who helps extract interesting topics from tech newsletters 
    and creates engaging LinkedIn posts from them.
    
    Your task is to:
    1. Analyze the provided newsletter content
    2. Identify 5-6 of the most interesting, thought-provoking topics
    3. For each topic, create a LinkedIn post that sounds like it was written by the user
    4. Ensure the posts sound authentic, conversational, and match the user's writing style
    
    Each post should:
    - Be 150-250 words (LinkedIn optimal length)
    - Include the user's thoughts or perspective on the topic
    - Be written in first person as if the user is sharing their own insights
    - Include a thoughtful question at the end to encourage engagement
    - Not mention that it was AI-generated or from a newsletter
    - Sound like a natural thought the user had about the topic
    
    Important: Posts should read as if the user had an interesting thought about the topic 
    and decided to share it with their professional network - not like a summary or newsletter forward.
    """
)


@newsletter_agent.system_prompt
async def add_user_context(ctx: RunContext[NewsletterDependencies]) -> str:
    """Adds user-specific context to the system prompt."""
    email_subject = ctx.deps.email_data.get('subject', 'recent newsletter')
    interests = ', '.join(ctx.deps.user_professional_interests) if ctx.deps.user_professional_interests else "technology and innovation"
    
    return f"""
    The user's name is {ctx.deps.user_first_name}.
    
    The user is interested in: {interests}.
    
    The user's writing style is: {ctx.deps.user_writing_style}
    
    You are analyzing an email with the subject: "{email_subject}"
    
    Create LinkedIn posts that sound authentically like {ctx.deps.user_first_name} wrote them,
    reflecting their interests and writing style.
    """


@newsletter_agent.tool(retries=3)  # Increase retries for this tool
async def analyze_newsletter_content(ctx: RunContext[NewsletterDependencies]) -> PostGenerationResult:
    """
    Analyze the newsletter content and extract interesting topics.
    
    Returns:
        PostGenerationResult: The extracted topics and generated posts
    """
    logger.info("Analyzing newsletter content")
    
    try:
        email_data = ctx.deps.email_data
        email_body = email_data.get("body", "")
        email_subject = email_data.get("subject", "Newsletter")
        email_source = email_data.get("from", "Unknown")
        
        logger.info(f"Processing email from {email_source} with subject: {email_subject}")
        
        # Use Claude to extract topics
        client = anthropic.Anthropic(
            api_key=os.getenv("ANTHROPIC_API_KEY"),
        )
        
        message = client.messages.create(
            model=CLAUDE_MODEL,
            max_tokens=4000,
            temperature=0.2,  # Lower temperature for more deterministic output
            system="""
            You are a professional content analyzer who helps extract interesting topics from newsletters.
            Your task is to identify the most substantive, thought-provoking topics that would be interesting
            to share on LinkedIn. Focus on extracting detailed information about each topic.
            
            Follow these instructions carefully:
            1. Read through the newsletter
            2. Identify 5-6 of the most interesting, substantive topics
            3. For each topic, extract a title, summary, key points, and why it's relevant
            4. Return the information in a structured JSON format as specified below
            """,
            messages=[
                {
                    "role": "user", 
                    "content": f"""
                    Please analyze this newsletter and extract the most interesting topics:
                    
                    Subject: {email_subject}
                    From: {email_source}
                    
                    {email_body[:90000]}  # Limiting content length for API limits
                    
                    For each topic, provide:
                    1. A concise title (max 10 words)
                    2. A brief summary (1-2 short sentences only)
                    3. 2-3 very brief key points (max 15 words each)
                    4. Why this topic might be interesting (1 short sentence)
                    
                    IMPORTANT RESPONSE FORMAT INSTRUCTIONS:
                    - Your response MUST be a valid JSON array
                    - DO NOT include markdown code blocks, just return raw JSON
                    - DO NOT include any explanatory text before or after the JSON
                    - Return ONLY the JSON array matching this structure:
                    
                    [
                        {{
                            "title": "Topic title",
                            "summary": "Brief summary",
                            "key_points": ["Point 1", "Point 2", "Point 3"],
                            "relevance": "Why this is interesting/important"
                        }},
                        ...
                    ]
                    
                    Focus on the most substantial, thought-provoking topics that a professional would want to share thoughts about.
                    """
                }
            ]
        )
        
        # Extract the JSON response
        response_content = message.content[0].text
        logger.info("Received response from Claude for topic extraction")
        
        try:
            # Direct JSON parsing
            topics_data = json.loads(response_content)
            logger.info(f"Successfully parsed JSON: {len(topics_data)} topics found")
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {e}")
            raise ModelRetry("Failed to parse the JSON response, please return a valid JSON structure.")
        
        # Convert to Topic objects
        try:
            topics = [Topic(**topic_data) for topic_data in topics_data]
            logger.info(f"Successfully created {len(topics)} Topic objects")
            topics = topics[:ctx.deps.max_posts]  # Limit to configured max_posts
            
            # Generate LinkedIn posts for each topic
            generated_posts = []
            for topic in topics:
                post = await generate_linkedin_post(ctx, topic)
                generated_posts.append(post)
                
            # Schedule the posts
            scheduled_posts = await schedule_posts(ctx, generated_posts)
            
            return PostGenerationResult(
                posts=scheduled_posts,
                topics=topics,
                email_subject=email_subject,
                email_source=email_source
            )
            
        except Exception as e:
            logger.error(f"Error creating Topic objects: {e}")
            raise ModelRetry(f"Error creating Topic objects: {str(e)}. Please ensure your JSON structure matches the required schema.")
            
    except Exception as e:
        logger.error(f"Error analyzing newsletter content: {e}")
        # Return a fallback topic to prevent complete failure
        logger.info("Returning fallback topic")
        fallback_topic = Topic(
            title="Technology Newsletter Insights",
            summary="The newsletter covered various technology and industry updates.",
            key_points=["Technology advancements", "Industry changes", "Future trends"],
            relevance="Following technology trends is essential for professional development."
        )
        
        # Generate a fallback post
        fallback_post = await generate_linkedin_post(ctx, fallback_topic)
        scheduled_posts = await schedule_posts(ctx, [fallback_post])
        
        return PostGenerationResult(
            posts=scheduled_posts,
            topics=[fallback_topic],
            email_subject=email_data.get("subject", "Newsletter"),
            email_source=email_data.get("from", "Unknown")
        )


async def generate_linkedin_post(
    ctx: RunContext[NewsletterDependencies], 
    topic: Topic
) -> LinkedInPost:
    """
    Generate a LinkedIn post for a specific topic.
    
    Args:
        topic: The topic to create a post about
        
    Returns:
        LinkedInPost: A LinkedIn post ready to be published
    """
    logger.info(f"Generating LinkedIn post for topic: {topic.title}")
    
    try:
        client = anthropic.Anthropic(
            api_key=os.getenv("ANTHROPIC_API_KEY"),
        )
        
        message = client.messages.create(
            model=CLAUDE_MODEL,
            max_tokens=1000,
            temperature=0.7,  # Higher temperature for more creative writing
            system=f"""
            You are {ctx.deps.user_first_name}, writing a LinkedIn post about a topic you found interesting.
            Your writing style is: {ctx.deps.user_writing_style}
            
            Write an authentic, thoughtful LinkedIn post that:
            - Sounds like you naturally had a thought about this topic
            - Is written in first-person perspective
            - Is 150-250 words long
            - Includes your personal thoughts or insights
            - Ends with an engaging question
            - Does NOT mention that it came from a newsletter or was AI-generated
            - Does NOT include any word counts, headers, or metadata in the output
            - Does NOT start with phrases like "Here is a" or "LinkedIn post on"
            
            Return ONLY the post content, with no additional explanations or meta-commentary.
            """,
            messages=[
                {
                    "role": "user", 
                    "content": f"""
                    Write a LinkedIn post about this topic:
                    
                    Title: {topic.title}
                    Summary: {topic.summary}
                    Key Points:
                    {' '.join([f"- {point}" for point in topic.key_points])}
                    Relevance: {topic.relevance}
                    
                    Make it sound completely authentic as if I (not AI) wrote it. The post should be thoughtful
                    and conversational, as if I'm sharing my perspective with my professional network.
                    """
                }
            ]
        )
        
        response_content = message.content[0].text
        logger.info(f"Successfully generated post of length {len(response_content)} characters")
        
        # Create the scheduled time (will be adjusted in the schedule_posts tool)
        now = datetime.now(timezone.utc)
        scheduled_time = now + timedelta(days=1)  # Default to next day, will be adjusted by scheduler
        
        return LinkedInPost(
            content=response_content.strip(),
            topic=topic,
            scheduled_time=scheduled_time
        )
    except Exception as e:
        logger.error(f"Error generating LinkedIn post: {e}")
        raise


@newsletter_agent.tool
async def schedule_posts(
    ctx: RunContext[NewsletterDependencies], 
    posts: List[LinkedInPost]
) -> List[LinkedInPost]:
    """
    Schedule the posts across the specified number of days.
    
    Args:
        posts: The posts to schedule
        
    Returns:
        List[LinkedInPost]: The posts with scheduled times
    """
    logger.info(f"Scheduling {len(posts)} posts over {ctx.deps.days_to_spread} days")
    
    # Base time: start tomorrow
    base_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)
    
    # Different posting times based on optimal LinkedIn engagement
    # - Morning: When professionals check LinkedIn at the start of the workday
    # - Lunch: When people browse during breaks
    # - Evening: End of workday when engagement is high
    posting_times = [9, 12, 17]  # 9 AM, 12 PM, 5 PM
    
    # Add some natural variation to avoid looking too automated
    # Add/subtract 0-15 minutes to make posting times look more natural
    import random
    
    scheduled_posts = []
    for i, post in enumerate(posts):
        # Calculate day (distributed across days_to_spread)
        day_offset = i % ctx.deps.days_to_spread
        
        # Calculate time (cycling through posting_times)
        time_index = i % len(posting_times)
        post_hour = posting_times[time_index]
        
        # Add some natural variation (0-15 minutes)
        minute_variation = random.randint(0, 15)
        
        # Set the scheduled time
        post.scheduled_time = base_date + timedelta(
            days=day_offset, 
            hours=post_hour, 
            minutes=minute_variation
        )
        scheduled_posts.append(post)
        logger.info(f"Scheduled post {i+1} for {post.scheduled_time}")
    
    return scheduled_posts


# ----------------------
# Main Functions
# ----------------------

async def process_newsletter_and_generate_posts(email_data=None, user_first_name="Kai", days_to_spread=3, max_posts=5):
    """
    Process a newsletter email and generate LinkedIn posts.
    
    Args:
        email_data: The email data (if None, will fetch the latest newsletter)
        user_first_name: The user's first name for personalization
        days_to_spread: Number of days to spread posts over
        max_posts: Maximum number of posts to generate
        
    Returns:
        PostGenerationResult: The generated posts and extracted topics
    """
    # If no email data provided, fetch the latest newsletter
    if email_data is None:
        logger.info("No email data provided, fetching latest newsletter")
        email_data = process_latest_email_from_sender(debug=False)
        if not email_data:
            logger.error("No email data found")
            raise ValueError("No email data found. Please check your NEWSLETTER_SENDER setting.")
    
    # Example professional interests - customize this
    user_interests = [
        "Artificial Intelligence", 
        "Machine Learning",
        "Large Language Models",
        "AI Ethics",
        "Software Development",
        "Product Management",
        "Data Science"
    ]
    
    # Create dependencies
    deps = NewsletterDependencies(
        email_data=email_data,
        user_first_name=user_first_name,
        user_professional_interests=user_interests,
        days_to_spread=days_to_spread,
        max_posts=max_posts
    )
    
    # Log configuration
    logger.info(f"Using Claude model: {CLAUDE_MODEL}")
    logger.info(f"Processing newsletter with subject: {email_data.get('subject', 'Newsletter')}")
    
    try:
        # Run the agent with dependencies. Using a non-empty prompt
        logger.info("Running agent to process newsletter")
        result = await newsletter_agent.run("Process newsletter", deps=deps)
        
        if not result:
            logger.error("Agent returned no result")
            raise ValueError("Failed to process newsletter")
        
        # Return the result, which now includes both topics and posts
        return result
        
    except Exception as e:
        logger.error(f"Error running agent: {e}", exc_info=True)
        raise


async def post_to_linkedin(post_content, visibility="CONNECTIONS"):
    """
    Post content to LinkedIn using the LinkedIn API.
    
    Args:
        post_content: The content to post
        visibility: Visibility setting for the post
        
    Returns:
        bool: True if posting was successful, False otherwise
    """
    logger.info("Authenticating with LinkedIn")
    auth = LinkedInAuth()
    if auth.authenticate():
        logger.info("Successfully authenticated with LinkedIn")
        poster = LinkedInPoster(auth.access_token, auth.person_id)
        logger.info("Posting message to LinkedIn")
        result = poster.post_message(post_content, visibility)
        return result
    logger.error("LinkedIn authentication failed")
    return False


async def main():
    """Main function to run the entire process."""
    try:
        print("🔍 Fetching and analyzing the latest newsletter...")
        result_full = await process_newsletter_and_generate_posts(max_posts=1)
        result = result_full.data
        
        print(f"\n✅ Successfully extracted {len(result.topics)} topics from the email.")
        print(f"✅ Generated {len(result.posts)} LinkedIn posts.\n")
        
        # Display the posts and their scheduled times
        for i, post in enumerate(result.posts, 1):
            scheduled_time = post.scheduled_time.strftime("%A, %B %d at %I:%M %p") if post.scheduled_time else "Not scheduled"
            print(f"\n--- Post #{i} (Scheduled for {scheduled_time}) ---")
            print(f"Topic: {post.topic.title}")
            print(f"Content:\n{post.content}\n")
            print("-" * 50)
        
        # Option to immediately post or save for later
        post_now = input("\nWould you like to post the first article now? (y/n): ").lower().strip() == 'y'
        
        if post_now and result.posts:
            print("\n🚀 Posting to LinkedIn...")
            success = await post_to_linkedin(result.posts[0].content)
            if success:
                print("✅ Post published successfully!")
            else:
                print("❌ Failed to publish post. Please check your LinkedIn credentials.")
        
        # Save the generated posts for later use
        from datetime import datetime
        import json
        
        # Convert to dict for JSON serialization
        posts_data = [
            {
                "content": post.content,
                "topic": post.topic.dict(),
                "scheduled_time": post.scheduled_time.isoformat() if post.scheduled_time else None
            }
            for post in result.posts
        ]
        
        # Save to file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"linkedin_posts_{timestamp}.json"
        with open(filename, "w") as f:
            json.dump(posts_data, f, indent=2)
        
        print(f"\n💾 Generated posts saved to {filename}")
        print("\n✨ Done! You can now use these posts on your LinkedIn profile.")
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        logger.error(f"Error in main: {e}", exc_info=True)


if __name__ == "__main__":
    import asyncio
    asyncio.run(main()) 