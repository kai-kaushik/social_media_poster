import os
import time
import json
import logging
import unittest
from dotenv import load_dotenv
from agent_flow import generate_linkedin_post, LinkedInPost

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("test_linkedin_post.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("test_linkedin_post")

# Load environment variables
load_dotenv()

class TestLinkedInPostGeneration(unittest.TestCase):
    """Test class for LinkedIn post generation functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create a sample topic for testing
        self.sample_topic = {
            "title": "AI Assistants Revolutionizing Content Creation",
            "summary": "New AI tools are transforming how professionals create and distribute content. These tools can now generate high-quality, contextually relevant content that sounds authentically human.",
            "key_points": [
                "AI content generation has improved dramatically in quality and relevance",
                "Professionals are using AI to streamline their content workflows",
                "The best results come from human-AI collaboration rather than full automation",
                "Ethical considerations around disclosure and authenticity are becoming important"
            ],
            "thoughts": "While AI tools are impressive, they work best when guided by human expertise and creativity. The future likely involves collaboration rather than replacement.",
            "references": ["OpenAI", "Anthropic", "Content Marketing Institute", "LinkedIn Creator Accelerator Program"]
        }
        
        # Create another sample topic with different content
        self.tech_topic = {
            "title": "The Rise of Edge Computing in IoT Applications",
            "summary": "Edge computing is gaining traction in IoT deployments, bringing computation closer to data sources. This approach reduces latency and bandwidth usage while improving privacy and reliability.",
            "key_points": [
                "Edge computing reduces the need to send data to cloud servers for processing",
                "IoT devices benefit from faster response times and reduced bandwidth costs",
                "Privacy concerns are addressed by processing sensitive data locally",
                "The market for edge computing solutions is growing rapidly across industries"
            ],
            "thoughts": "Edge computing represents a significant shift in how we think about distributed systems. The combination of 5G and edge computing will enable entirely new categories of applications.",
            "references": ["AWS", "Microsoft Azure", "Cisco", "Gartner", "IDC"]
        }
    
    def test_generate_linkedin_post(self):
        """Test that a LinkedIn post can be generated from a topic."""
        logger.info("Testing LinkedIn post generation with sample topic")
        
        # Generate a LinkedIn post from the sample topic
        start_time = time.time()
        linkedin_post = generate_linkedin_post(self.sample_topic)
        elapsed_time = time.time() - start_time
        
        # Verify the result
        self.assertIsNotNone(linkedin_post, "LinkedIn post generation failed")
        self.assertIsInstance(linkedin_post, LinkedInPost, "Result is not a LinkedInPost object")
        self.assertEqual(linkedin_post.topic_title, self.sample_topic["title"], "Topic title mismatch")
        self.assertGreater(len(linkedin_post.content), 100, "Post content is too short")
        self.assertLess(len(linkedin_post.content), 1500, "Post content is too long")
        self.assertFalse(linkedin_post.published, "Post should not be marked as published")
        
        # Display the generated post
        logger.info(f"Successfully generated LinkedIn post in {elapsed_time:.2f} seconds")
        print(f"\nTopic: {linkedin_post.topic_title}")
        print(f"Generated at: {linkedin_post.generated_at}")
        print("-" * 50)
        print(linkedin_post.content)
        print("-" * 50)
        print(f"Character count: {len(linkedin_post.content)}")
    
    def test_generate_linkedin_post_tech_topic(self):
        """Test LinkedIn post generation with a technology-focused topic."""
        logger.info("Testing LinkedIn post generation with tech topic")
        
        # Generate a LinkedIn post from the tech topic
        linkedin_post = generate_linkedin_post(self.tech_topic)
        
        # Verify the result
        self.assertIsNotNone(linkedin_post, "LinkedIn post generation failed")
        self.assertEqual(linkedin_post.topic_title, self.tech_topic["title"], "Topic title mismatch")
        
        # Check that the content includes some of the key terms from the topic
        content_lower = linkedin_post.content.lower()
        self.assertTrue(
            any(term in content_lower for term in ["edge", "computing", "iot"]), 
            "Post content doesn't mention key terms from the topic"
        )
        
        # Display the generated post
        print(f"\nTopic: {linkedin_post.topic_title}")
        print("-" * 50)
        print(linkedin_post.content)
        print("-" * 50)
    
    def test_references_inclusion(self):
        """Test that references from the topic are included in the post."""
        logger.info("Testing references inclusion in LinkedIn post")
        
        # Generate a LinkedIn post
        linkedin_post = generate_linkedin_post(self.sample_topic)
        
        # Check that at least one reference is mentioned in the post
        content_lower = linkedin_post.content.lower()
        references_mentioned = [
            ref for ref in self.sample_topic["references"] 
            if ref.lower() in content_lower
        ]
        
        self.assertTrue(
            len(references_mentioned) > 0,
            f"None of the references {self.sample_topic['references']} were mentioned in the post"
        )
        
        logger.info(f"References mentioned in post: {references_mentioned}")

if __name__ == "__main__":
    logger.info("Starting LinkedIn post generation tests")
    unittest.main() 