import unittest
import time
from datetime import datetime
import sys
import os

# Add parent directory to path to import agent_flow
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from agent_flow import LinkedInPost, schedule_linkedin_posts

class TestScheduler(unittest.TestCase):
    """Test cases for the LinkedIn post scheduler function."""
    
    def test_schedule_posts_empty_list(self):
        """Test scheduling with an empty list of posts."""
        result = schedule_linkedin_posts([])
        self.assertEqual(len(result), 0)
    
    def test_schedule_single_post(self):
        """Test scheduling a single post."""
        post = LinkedInPost(
            topic_title="Test Topic",
            content="This is a test post",
            generated_at=time.strftime("%Y-%m-%d %H:%M:%S"),
            published=False
        )
        
        result = schedule_linkedin_posts([post])
        
        self.assertEqual(len(result), 1)
        self.assertIsNotNone(result[0].scheduled_for)
        
        # Parse the scheduled time
        scheduled_time = datetime.strptime(result[0].scheduled_for, "%Y-%m-%d %H:%M:%S")
        
        # Verify scheduled hour is between 9 AM and 5 PM
        hour = scheduled_time.hour
        self.assertGreaterEqual(hour, 9)
        self.assertLessEqual(hour, 17)
    
    def test_schedule_multiple_posts(self):
        """Test scheduling multiple posts over 3 days."""
        posts = []
        for i in range(5):
            post = LinkedInPost(
                topic_title=f"Test Topic {i+1}",
                content=f"This is test post {i+1}",
                generated_at=time.strftime("%Y-%m-%d %H:%M:%S"),
                published=False
            )
            posts.append(post)
        
        result = schedule_linkedin_posts(posts)
        
        # Verify all posts are scheduled
        self.assertEqual(len(result), 5)
        for post in result:
            self.assertIsNotNone(post.scheduled_for)
        
        # Verify all scheduled hours are between 9 AM and 5 PM
        scheduled_times = []
        for post in result:
            scheduled_time = datetime.strptime(post.scheduled_for, "%Y-%m-%d %H:%M:%S")
            hour = scheduled_time.hour
            self.assertGreaterEqual(hour, 9)
            self.assertLessEqual(hour, 17)
            scheduled_times.append(scheduled_time)
        
        # Verify posts are distributed across multiple days
        days = set([time.day for time in scheduled_times])
        self.assertGreaterEqual(len(days), 2, "Posts should be distributed across at least 2 days")

if __name__ == "__main__":
    unittest.main() 