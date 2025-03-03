import os
import json
import logging
from dotenv import load_dotenv
from agent_flow import extract_topics_with_anthropic, NewsletterContent

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('test_anthropic')

# Load environment variables
load_dotenv()

def test_anthropic_extraction():
    """
    Test the extract_topics_with_anthropic function with sample newsletter content.
    """
    logger.info("Starting test of extract_topics_with_anthropic function")
    
    # Sample newsletter content
    sample_newsletter = {
        'newsletter_name': 'Tech Weekly',
        'date': '2025-03-03',
        'subject': 'This Week in Tech: AI Breakthroughs and More',
        'body': """
        Hello subscribers!
        
        This week has been packed with exciting developments in the tech world. Here are some highlights:
        
        1. OpenAI announced a new breakthrough in multimodal learning, allowing their models to understand and generate content across text, images, and audio with unprecedented coherence.
        
        2. Tesla unveiled plans for a new affordable electric vehicle model priced under $30,000, potentially disrupting the mainstream auto market.
        
        3. A team of researchers at MIT developed a new type of battery that can charge to 80% capacity in just 5 minutes, with potential applications in electric vehicles and consumer electronics.
        
        4. Google Cloud introduced new sustainability features that help businesses track and reduce their carbon footprint from cloud operations.
        
        5. Apple's latest iOS update includes enhanced privacy features that give users more control over how apps access their data.
        
        6. A startup called Quantum Leap announced a working prototype of a quantum computer that operates at room temperature, potentially making quantum computing more accessible.
        
        7. The EU passed new regulations on AI development, requiring companies to disclose when content is AI-generated and setting limits on certain applications.
        
        8. A major cybersecurity firm reported a 40% increase in ransomware attacks targeting healthcare institutions over the past quarter.
        
        That's all for this week. Stay tuned for more tech updates next week!
        
        Best regards,
        Tech Weekly Team
        """
    }
    
    # Call the function
    logger.info("Calling extract_topics_with_anthropic")
    result = extract_topics_with_anthropic(sample_newsletter, num_topics=3)
    
    if result:
        logger.info("Successfully extracted topics")
        
        try:
            # Parse the result as JSON
            parsed_result = json.loads(result)
            logger.info(f"Extracted {len(parsed_result['topics'])} topics")
            
            # Print the topics
            for i, topic in enumerate(parsed_result['topics'], 1):
                logger.info(f"Topic {i}: {topic['title']}")
                logger.info(f"Summary: {topic['summary']}")
                logger.info("Key points:")
                for point in topic['key_points']:
                    logger.info(f"- {point}")
                logger.info(f"Thoughts: {topic['thoughts']}")
                logger.info("References:")
                for reference in topic['references']:
                    logger.info(f"- {reference}")
                logger.info("-" * 50)
                
        except json.JSONDecodeError:
            logger.error("Failed to parse result as JSON")
            logger.info(f"Raw result: {result[:500]}...")
    else:
        logger.error("Failed to extract topics")

if __name__ == "__main__":
    test_anthropic_extraction() 