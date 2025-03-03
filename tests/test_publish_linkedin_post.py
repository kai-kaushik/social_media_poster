import os
import time
import unittest
import sys
import logging
from unittest.mock import patch, MagicMock
from datetime import datetime
from dotenv import load_dotenv

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from agent_flow import publish_linkedin_post, LinkedInPost

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("tests/test_publish_linkedin_post.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("test_publish_linkedin_post")

# Load environment variables
load_dotenv()

class TestPublishLinkedInPost(unittest.TestCase):
    """Test class for LinkedIn post publishing functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create a sample LinkedIn post for testing
        self.test_post = LinkedInPost(
            topic_title="GPT-4.5 Launch: Mixed Reception and High Pricing",
            content="""Just explored OpenAI's new GPT-4.5, and I have some mixed feelings to share. The improved natural conversation abilities are impressive, but I'm struggling to justify the steep pricing ($75/M input tokens, $150/M output tokens) for my projects. 

Sam Altman and the OpenAI team have clearly pushed boundaries with this release, but the 3+ minute response times in moderate prompt loops are concerning. While Andrej Karpathy's testing showed promising results, I found myself agreeing with Jeremy Howard's observations about GPT-4 still holding its ground in most scenarios.

The benchmarks placing GPT-4.5 below Claude 3.5 Sonnet raise interesting questions about where we're heading in AI development. Bigger models with higher price tags don't automatically translate to better real-world solutions. For my daily work, I'm finding that speed and cost-effectiveness often matter more than marginal improvements in capability.

I'm curious to hear from others using these models in production. What's your take on the pricing structure? Are the improvements worth the premium?

#ArtificialIntelligence #GPT45 #OpenAI #TechInnovation""",
            generated_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            scheduled_for="2025-03-03 09:00:00",
            published=False
        )
    
    @patch('agent_flow.LinkedInAuth')
    @patch('agent_flow.LinkedInPoster')
    def test_publish_linkedin_post_success(self, mock_poster_class, mock_auth_class):
        """Test successful publishing of a LinkedIn post."""
        logger.info("Testing successful LinkedIn post publishing")
        
        # Configure mocks
        mock_auth = MagicMock()
        mock_auth.authenticate.return_value = True
        mock_auth.access_token = "mock_access_token"
        mock_auth.person_id = "mock_person_id"
        mock_auth_class.return_value = mock_auth
        
        mock_poster = MagicMock()
        mock_poster.post_message.return_value = True
        mock_poster_class.return_value = mock_poster
        
        # Call the function
        result = publish_linkedin_post(self.test_post)
        
        # Verify the result
        self.assertTrue(result, "Publishing should return True on success")
        self.assertTrue(self.test_post.published, "Post should be marked as published")
        
        # Verify the mocks were called correctly
        mock_auth.authenticate.assert_called_once()
        mock_poster_class.assert_called_once_with(mock_auth.access_token, mock_auth.person_id)
        mock_poster.post_message.assert_called_once_with(self.test_post.content)
        
        logger.info("Successfully tested LinkedIn post publishing")
    
    @patch('agent_flow.LinkedInAuth')
    @patch('agent_flow.LinkedInPoster')
    def test_publish_linkedin_post_auth_failure(self, mock_poster_class, mock_auth_class):
        """Test LinkedIn post publishing with authentication failure."""
        logger.info("Testing LinkedIn post publishing with authentication failure")
        
        # Configure mocks
        mock_auth = MagicMock()
        mock_auth.authenticate.return_value = False
        mock_auth_class.return_value = mock_auth
        
        # Call the function
        result = publish_linkedin_post(self.test_post)
        
        # Verify the result
        self.assertFalse(result, "Publishing should return False on auth failure")
        self.assertFalse(self.test_post.published, "Post should not be marked as published")
        
        # Verify the mocks were called correctly
        mock_auth.authenticate.assert_called_once()
        mock_poster_class.assert_not_called()
        
        logger.info("Successfully tested LinkedIn post publishing with authentication failure")
    
    @patch('agent_flow.LinkedInAuth')
    @patch('agent_flow.LinkedInPoster')
    def test_publish_linkedin_post_posting_failure(self, mock_poster_class, mock_auth_class):
        """Test LinkedIn post publishing with posting failure."""
        logger.info("Testing LinkedIn post publishing with posting failure")
        
        # Configure mocks
        mock_auth = MagicMock()
        mock_auth.authenticate.return_value = True
        mock_auth.access_token = "mock_access_token"
        mock_auth.person_id = "mock_person_id"
        mock_auth_class.return_value = mock_auth
        
        mock_poster = MagicMock()
        mock_poster.post_message.return_value = False
        mock_poster_class.return_value = mock_poster
        
        # Call the function
        result = publish_linkedin_post(self.test_post)
        
        # Verify the result
        self.assertFalse(result, "Publishing should return False on posting failure")
        self.assertFalse(self.test_post.published, "Post should not be marked as published")
        
        # Verify the mocks were called correctly
        mock_auth.authenticate.assert_called_once()
        mock_poster_class.assert_called_once_with(mock_auth.access_token, mock_auth.person_id)
        mock_poster.post_message.assert_called_once_with(self.test_post.content)
        
        logger.info("Successfully tested LinkedIn post publishing with posting failure")
    
    @patch('agent_flow.LinkedInAuth')
    def test_publish_linkedin_post_exception(self, mock_auth_class):
        """Test LinkedIn post publishing with an exception."""
        logger.info("Testing LinkedIn post publishing with an exception")
        
        # Configure mock to raise an exception
        mock_auth = MagicMock()
        mock_auth.authenticate.side_effect = Exception("Test exception")
        mock_auth_class.return_value = mock_auth
        
        # Call the function
        result = publish_linkedin_post(self.test_post)
        
        # Verify the result
        self.assertFalse(result, "Publishing should return False on exception")
        self.assertFalse(self.test_post.published, "Post should not be marked as published")
        
        # Verify the mock was called
        mock_auth.authenticate.assert_called_once()
        
        logger.info("Successfully tested LinkedIn post publishing with an exception")

if __name__ == "__main__":
    logger.info("Starting LinkedIn post publishing tests")
    unittest.main() 