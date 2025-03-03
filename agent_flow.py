import os
import json
import time
import logging
import anthropic
from dotenv import load_dotenv
from google_api.google_main import process_latest_email_from_sender
from pydantic import BaseModel, Field
from typing import List, Optional
import random
from functools import wraps

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("newsletter_agent.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("newsletter_agent")

# Load environment variables
load_dotenv()
logger.info("Environment variables loaded")

def retry_anthropic_api(max_retries=3, initial_delay=2):
    """
    Decorator that implements retry logic with exponential backoff for Anthropic API calls.
    Specifically handles 529 Overloaded errors.
    
    Args:
        max_retries (int): Maximum number of retry attempts
        initial_delay (int): Initial delay in seconds before first retry
        
    Returns:
        The decorated function with retry logic
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            retries = 0
            delay = initial_delay
            
            while True:
                try:
                    return func(*args, **kwargs)
                except anthropic._exceptions.OverloadedError as e:
                    retries += 1
                    if retries > max_retries:
                        logger.error(f"Max retries ({max_retries}) exceeded for Anthropic API call")
                        raise e
                    
                    # Add jitter to avoid thundering herd problem
                    jitter = random.uniform(0.8, 1.2)
                    sleep_time = delay * jitter
                    
                    logger.warning(f"Anthropic API overloaded (529). Retrying in {sleep_time:.2f} seconds (attempt {retries}/{max_retries})")
                    time.sleep(sleep_time)
                    
                    # Exponential backoff
                    delay *= 2
                    
        return wrapper
    return decorator

class NewsletterTopic(BaseModel):
    """Model for a newsletter topic extracted from an email."""
    title: str = Field(description="Catchy title summarizing the topic")
    summary: str = Field(description="Brief summary of the topic, 2-3 sentences")
    key_points: List[str] = Field(description="Key points about why this topic is interesting or relevant")
    thoughts: str = Field(description="Personal thoughts that could be shared about this topic")
    references: List[str] = Field(description="Relevant references like people, companies, or organizations mentioned in relation to this topic")
    
class NewsletterContent(BaseModel):
    """Model for the extracted newsletter content."""
    newsletter_name: str = Field(description="Name of the newsletter")
    date: str = Field(description="Date of the newsletter")
    topics: List[NewsletterTopic] = Field(description="List of interesting topics from the newsletter")

class LinkedInPost(BaseModel):
    """Model for a LinkedIn post generated from a newsletter topic."""
    topic_title: str = Field(description="Title of the topic the post is about")
    content: str = Field(description="The actual content of the LinkedIn post")
    generated_at: str = Field(description="Timestamp when the post was generated")
    scheduled_for: Optional[str] = Field(None, description="Timestamp when the post is scheduled to be published")
    published: bool = Field(False, description="Whether the post has been published")
    
def extract_newsletter_content(sender_email=None):
    """
    Extract the title, subject, and body from the latest email newsletter.
    
    Args:
        sender_email (str, optional): Email address of newsletter sender. 
                                      If None, uses NEWSLETTER_SENDER from env.
    
    Returns:
        dict: Dictionary containing the email data with keys:
            - newsletter_name: Extracted from subject or headers
            - date: Date of the newsletter
            - subject: Email subject
            - body: Decoded email body
        Returns None if no email is found.
    """
    logger.info(f"Extracting newsletter content from {sender_email or os.getenv('NEWSLETTER_SENDER')}")
    
    try:
        email_data = process_latest_email_from_sender(sender_email=sender_email)
        
        if not email_data:
            logger.warning(f"No email found from {sender_email or os.getenv('NEWSLETTER_SENDER')}")
            return None
        
        logger.debug(f"Email retrieved successfully with subject: {email_data['subject']}")
        logger.debug(f"Email body length: {len(email_data['body'])} characters")
        
        # Extract newsletter name from subject if possible
        subject = email_data['subject']
        newsletter_name = subject.split(':', 1)[0] if ':' in subject else "Newsletter"
        logger.debug(f"Extracted newsletter name: {newsletter_name}")
        
        # Extract date from headers or use current date
        date_header = next((header['value'] for header in email_data['headers'] 
                            if header['name'] in ['Date', 'Received']), None)
        
        if date_header:
            logger.debug(f"Found date header: {date_header}")
            # Simple date extraction - could be improved with proper parsing
            date = date_header.split(',')[1].strip() if ',' in date_header else time.strftime("%B %d, %Y")
        else:
            logger.debug("No date header found, using current date")
            date = time.strftime("%B %d, %Y")
        
        logger.debug(f"Using date: {date}")
        
        result = {
            'newsletter_name': newsletter_name,
            'date': date,
            'subject': subject,
            'body': email_data['body']
        }
        
        logger.info(f"Successfully extracted newsletter content: {newsletter_name} ({date})")
        return result
        
    except Exception as e:
        logger.error(f"Error extracting newsletter content: {str(e)}", exc_info=True)
        return None

@retry_anthropic_api(max_retries=2, initial_delay=2)
def extract_topics_with_anthropic(newsletter_content, num_topics=5):
    """
    Extract interesting topics from newsletter content using Anthropic's Claude API.
    
    Args:
        newsletter_content (dict): Dictionary containing newsletter content
        num_topics (int): Number of topics to extract
    
    Returns:
        str: JSON string containing extracted topics
    """
    logger.info(f"Extracting {num_topics} topics from {newsletter_content['newsletter_name']}")
    
    try:
        # Initialize Anthropic client
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            logger.error("ANTHROPIC_API_KEY not found in environment variables")
            return None
            
        logger.debug("Initializing Anthropic client")
        client = anthropic.Anthropic(api_key=api_key)
        
        # Construct prompt for Claude
        logger.debug(f"Constructing system prompt for {num_topics} topics")
        system_prompt = f"""
        You are an expert content analyst specializing in extracting the most interesting and 
        engaging topics from newsletters. Your task is to analyze the provided newsletter content
        and extract exactly {num_topics} of the most interesting topics.
        
        For each topic, please provide:
        1. A catchy title
        2. A brief summary (2-3 sentences)
        3. 3-4 key points about why this topic is interesting or relevant
        4. Some personal thoughts that could be shared about this topic
        5. A list of relevant references (people, companies, organizations, products) mentioned in relation to this topic

        Be sure to extract specific names of people, companies, organizations, and products that are mentioned in the newsletter for each topic. These references are important for providing context and credibility to the LinkedIn posts.
        
        Format your response as valid JSON that matches the following Pydantic model structure:
        
        ```python
        class NewsletterTopic(BaseModel):
            title: str 
            summary: str
            key_points: List[str]
            thoughts: str
            references: List[str]
            
        class NewsletterContent(BaseModel):
            newsletter_name: str
            date: str
            topics: List[NewsletterTopic]
        ```
        
        Your output should be ONLY the JSON string, with no additional text before or after.
        """
        
        logger.debug("Constructing user message with newsletter content")
        user_message = f"""
        Newsletter Name: {newsletter_content['newsletter_name']}
        Date: {newsletter_content['date']}
        Subject: {newsletter_content['subject']}
        
        Newsletter Content:
        {newsletter_content['body']}
        """
        
        logger.debug(f"User message length: {len(user_message)} characters")
        
        # Call Anthropic API
        logger.info("Calling Anthropic API with claude-3-5-sonnet-20241022 model")
        start_time = time.time()
        
        message = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            system=system_prompt,
            max_tokens=4000,
            messages=[
                {"role": "user", "content": user_message}
            ]
        )
        
        elapsed_time = time.time() - start_time
        logger.info(f"Anthropic API call completed in {elapsed_time:.2f} seconds")
        
        # Extract JSON from response
        response_content = message.content[0].text
        logger.debug(f"Response content length: {len(response_content)} characters")
        
        # Validate response with Pydantic
        try:
            logger.debug("Parsing JSON response")
            content_json = json.loads(response_content)
            
            logger.debug("Validating response with Pydantic models")
            validated_content = NewsletterContent(**content_json)
            
            logger.info(f"Successfully extracted and validated {len(validated_content.topics)} topics")
            return json.dumps(validated_content.dict(), indent=2)
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error: {str(e)}")
            logger.debug(f"Raw response content: {response_content[:500]}...")
            return response_content
            
        except Exception as e:
            logger.error(f"Error validating response: {str(e)}", exc_info=True)
            return response_content
        
    except Exception as e:
        logger.error(f"Error calling Anthropic API: {str(e)}", exc_info=True)
        return None

def process_newsletter(sender_email=None, num_topics=5):
    """
    Process a newsletter email and extract interesting topics.
    
    Args:
        sender_email (str, optional): Email address of the sender to filter by
        num_topics (int, optional): Number of topics to extract
        
    Returns:
        dict: Dictionary containing extracted newsletter content and topics
    """
    logger.info("Starting newsletter processing pipeline")
    
    try:
        # Extract newsletter content
        newsletter_content = extract_newsletter_content(sender_email)
        if not newsletter_content:
            logger.error("Failed to extract newsletter content")
            return None
            
        # Extract topics with Anthropic
        topics_json = extract_topics_with_anthropic(newsletter_content, num_topics)
        if not topics_json:
            logger.error("Failed to extract topics")
            return None
            
        # Parse JSON
        try:
            topics_data = json.loads(topics_json)
            logger.info(f"Successfully extracted {len(topics_data['topics'])} topics")
            return topics_data
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing topics JSON: {str(e)}")
            return None
            
    except Exception as e:
        logger.error(f"Error in newsletter processing pipeline: {str(e)}", exc_info=True)
        return None

@retry_anthropic_api(max_retries=2, initial_delay=2)
def generate_linkedin_post(topic):
    """
    Generate a LinkedIn post from a newsletter topic using Anthropic's Claude API.
    
    Args:
        topic (dict): A topic dictionary extracted from the newsletter with keys:
                     title, summary, key_points, thoughts, references
        
    Returns:
        LinkedInPost: A Pydantic model containing the LinkedIn post and metadata
    """
    logger.info(f"Generating LinkedIn post for topic: {topic['title']}")
    
    try:
        # Initialize Anthropic client
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            logger.error("ANTHROPIC_API_KEY not found in environment variables")
            return None
            
        logger.debug("Initializing Anthropic client")
        client = anthropic.Anthropic(api_key=api_key)
        
        # Construct prompt for Claude
        logger.debug("Constructing system prompt for LinkedIn post generation")
        system_prompt = """
        You are a professional content writer specializing in creating authentic, engaging LinkedIn posts.
        Your task is to write a LinkedIn post in first person that sounds like it was written by a real person
        sharing their thoughts on a topic they found interesting.
        
        The post should:
        1. Be written in a conversational, authentic first-person voice
        2. Include personal thoughts and opinions on the topic
        3. Be professionally written but not overly formal
        4. Include relevant hashtags (3-5) at the end
        5. Be between 150-200 words
        6. Mention any relevant people, companies, or organizations provided in the references
        7. Avoid common AI LLm generated jargon and be more human like. Avoid phrases like "as we all know" or "in this day and age" or "In this fast-paced world"
        8. Avoid using "-" in sentences and words like "crossroads" or "Tapestry".
        8. Remember to not make up sentences like "I spoke to my fellow researches etc. because you arent a researcher.
        9. Don't use these kind of sentence patterns: "Open source isn't just about sharing code - it's about creating a foundation for collective progress." or "here's the catch - ".\
              Dont use the " - " pattern. and Don't use the "isnt about, its about" or "not only, but also" pattern.
        
        Your output should be ONLY the LinkedIn post text, with no additional formatting or explanation.
        """
        
        # Prepare topic information for the prompt
        references_text = ", ".join(topic['references']) if topic['references'] else "None specified"
        
        user_message = f"""
        Topic Title: {topic['title']}
        
        Summary: {topic['summary']}
        
        Key Points:
        {chr(10).join(f"- {point}" for point in topic['key_points'])}
        
        Personal Thoughts: {topic['thoughts']}
        
        References (people, companies, organizations): {references_text}
        
        Please write an authentic, first-person LinkedIn post about this topic.
        """
        
        logger.debug(f"User message length: {len(user_message)} characters")
        
        # Call Anthropic API
        logger.info("Calling Anthropic API to generate LinkedIn post")
        start_time = time.time()
        
        message = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            system=system_prompt,
            max_tokens=1000,
            messages=[
                {"role": "user", "content": user_message}
            ]
        )
        
        elapsed_time = time.time() - start_time
        logger.info(f"LinkedIn post generation completed in {elapsed_time:.2f} seconds")
        
        # Extract post from response
        post_content = message.content[0].text.strip()
        logger.debug(f"Generated LinkedIn post ({len(post_content)} characters)")
        
        # Create LinkedInPost object
        linkedin_post = LinkedInPost(
            topic_title=topic['title'],
            content=post_content,
            generated_at=time.strftime("%Y-%m-%d %H:%M:%S"),
            published=False
        )
        
        return linkedin_post
        
    except Exception as e:
        logger.error(f"Error generating LinkedIn post: {str(e)}", exc_info=True)
        return None


def schedule_linkedin_posts(posts, days=3):
    """
    Schedule LinkedIn posts over the next specified number of days.
    
    Args:
        posts (List[LinkedInPost]): List of LinkedIn posts to schedule
        days (int): Number of days to spread the posts over
        
    Returns:
        List[LinkedInPost]: The same posts with scheduled_for timestamps added
    """
    if not posts:
        logger.warning("No posts to schedule")
        return []
    
    logger.info(f"Scheduling {len(posts)} LinkedIn posts over {days} days")
    
    # Get current time
    current_time = time.time()
    day_seconds = 24 * 60 * 60  # Seconds in a day
    
    # Business hours
    business_hours = [9, 12, 15, 17]  # 9am, 12pm, 3pm, 5pm
    
    scheduled_posts = []
    for i, post in enumerate(posts):
        # Calculate which day to post (0 to days-1)
        day_offset = min(i * days // len(posts), days - 1)
        
        # Select hour based on position in sequence
        hour_index = i % len(business_hours)
        target_hour = business_hours[hour_index]
        
        # Get the target day's date
        target_day = current_time + (day_offset * day_seconds)
        target_struct = time.localtime(target_day)
        
        # Create scheduled time
        scheduled_time = time.mktime((
            target_struct.tm_year,
            target_struct.tm_mon,
            target_struct.tm_mday,
            target_hour,
            0,  # 0 minutes
            0,  # 0 seconds
            target_struct.tm_wday,
            target_struct.tm_yday,
            target_struct.tm_isdst
        ))
        
        # Format the time
        formatted_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(scheduled_time))
        
        # Update the post
        post.scheduled_for = formatted_time
        scheduled_posts.append(post)
        
        logger.debug(f"Scheduled post '{post.topic_title}' for {formatted_time}")
    
    logger.info(f"Successfully scheduled {len(scheduled_posts)} posts")
    return scheduled_posts

# Example usage
if __name__ == "__main__":
    logger.info("Starting newsletter agent")
    
    # Set debug=True to see more details
    start_time = time.time()
    topics_data = process_newsletter(num_topics=2)
    
    if topics_data and 'topics' in topics_data:
        logger.info(f"Successfully extracted {len(topics_data['topics'])} topics from {topics_data['newsletter_name']}")
        
        # Generate LinkedIn posts for each topic
        linkedin_posts = []
        for i, topic in enumerate(topics_data['topics'], 1):
            logger.info(f"Generating LinkedIn post for topic {i}: {topic['title']}")
            linkedin_post = generate_linkedin_post(topic)
            
            if linkedin_post:
                linkedin_posts.append(linkedin_post)
                print(f"\nLinkedIn Post {i} - {linkedin_post.topic_title}")
                print(f"Generated at: {linkedin_post.generated_at}")
                print("-" * 50)
                print(linkedin_post.content)
                print("-" * 50)
                print(f"Status: {'Published' if linkedin_post.published else 'Not published'}")
                if linkedin_post.scheduled_for:
                    print(f"Scheduled for: {linkedin_post.scheduled_for}")
                print()
            else:
                logger.error(f"Failed to generate LinkedIn post for topic {i}")
        
        # Schedule the posts over the next 3 days
        if linkedin_posts:
            scheduled_posts = schedule_linkedin_posts(linkedin_posts)
            
            # Display scheduled posts
            print("\nScheduled LinkedIn Posts:")
            print("=" * 50)
            for i, post in enumerate(scheduled_posts, 1):
                print(f"{i}. {post.topic_title}")
                print(f"   Scheduled for: {post.scheduled_for}")
            print("=" * 50)
        
        elapsed_time = time.time() - start_time
        logger.info(f"Total processing time: {elapsed_time:.2f} seconds")
        
    else:
        logger.error("Failed to process newsletter")
        print("Failed to process newsletter")
        
    logger.info("Newsletter agent completed")

