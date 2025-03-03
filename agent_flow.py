import os
import json
import time
import logging
import anthropic
from dotenv import load_dotenv
from google_main import process_latest_email_from_sender
from pydantic import BaseModel, Field
from typing import List, Optional

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

class NewsletterTopic(BaseModel):
    """Model for a newsletter topic extracted from an email."""
    title: str = Field(description="Catchy title summarizing the topic")
    summary: str = Field(description="Brief summary of the topic, 2-3 sentences")
    key_points: List[str] = Field(description="Key points about why this topic is interesting or relevant")
    thoughts: str = Field(description="Personal thoughts that could be shared about this topic")
    
class NewsletterContent(BaseModel):
    """Model for the extracted newsletter content."""
    newsletter_name: str = Field(description="Name of the newsletter")
    date: str = Field(description="Date of the newsletter")
    topics: List[NewsletterTopic] = Field(description="List of interesting topics from the newsletter")
    
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
        
        Format your response as valid JSON that matches the following Pydantic model structure:
        
        ```python
        class NewsletterTopic(BaseModel):
            title: str 
            summary: str
            key_points: List[str]
            thoughts: str
            
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
    End-to-end function to process a newsletter email and extract topics.
    
    Args:
        sender_email (str, optional): Email address of newsletter sender
        num_topics (int): Number of topics to extract
        
    Returns:
        dict: Validated NewsletterContent object as a dictionary
              Returns None if any stage fails
    """
    logger.info(f"Starting newsletter processing pipeline for {sender_email or os.getenv('NEWSLETTER_SENDER')}")
    logger.info(f"Requested {num_topics} topics")
    
    # Step 1: Extract newsletter content from email
    logger.info("Step 1: Extracting newsletter content")
    newsletter_content = extract_newsletter_content(sender_email)
    
    if not newsletter_content:
        logger.error("Failed to extract newsletter content")
        return None
    
    logger.info(f"Newsletter content extracted: {newsletter_content['newsletter_name']} ({newsletter_content['date']})")
    
    # Step 2: Extract topics using Anthropic
    logger.info("Step 2: Extracting topics with Anthropic")
    json_result = extract_topics_with_anthropic(newsletter_content, num_topics)
    
    if not json_result:
        logger.error("Failed to extract topics from newsletter")
        return None
    
    logger.debug(f"JSON result length: {len(json_result)} characters")
    
    # Parse JSON result
    try:
        logger.info("Parsing final JSON result")
        result_dict = json.loads(json_result)
        logger.info(f"Successfully processed newsletter with {len(result_dict['topics'])} topics")
        return result_dict
        
    except json.JSONDecodeError as e:
        logger.error(f"Failed to decode JSON result: {str(e)}")
        logger.debug(f"Raw JSON result: {json_result[:500]}...")
        return None

# Example usage
if __name__ == "__main__":
    logger.info("Starting newsletter agent")
    
    # Set debug=True to see more details
    start_time = time.time()
    result = process_newsletter(num_topics=5)
    elapsed_time = time.time() - start_time
    
    if result:
        logger.info(f"Successfully extracted {len(result['topics'])} topics from {result['newsletter_name']}")
        logger.info(f"Total processing time: {elapsed_time:.2f} seconds")
        
        for i, topic in enumerate(result['topics'], 1):
            logger.info(f"Topic {i}: {topic['title']}")
            print(f"\nTopic {i}: {topic['title']}")
            print(f"Summary: {topic['summary']}")
    else:
        logger.error("Failed to process newsletter")
        print("Failed to process newsletter")
        
    logger.info("Newsletter agent completed") 