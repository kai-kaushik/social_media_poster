"""
LinkedIn Post Scheduler

This script runs in the background to:
1. Check for and process new newsletter emails
2. Schedule LinkedIn posts from the generated content
3. Post content at the scheduled times

Usage:
    python scheduler.py

The script will run continuously, checking for new emails and posting
content according to the schedule.
"""

import os
import json
import asyncio
import time
from datetime import datetime, timedelta
import schedule
import logging
from pathlib import Path

from agent import process_newsletter_and_generate_posts, post_to_linkedin

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("linkedin_poster.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("linkedin_poster")

# Create a directory for post data if it doesn't exist
POSTS_DIR = Path("scheduled_posts")
POSTS_DIR.mkdir(exist_ok=True)

# Global variables
CHECKING_INTERVAL_HOURS = 6  # Check for new emails every 6 hours
POSTED_MARKER = "_POSTED"  # Marker to indicate a post has been published


async def check_for_new_content():
    """Check for new newsletter emails and generate posts."""
    try:
        logger.info("Checking for new newsletter content...")
        result = await process_newsletter_and_generate_posts()
        
        # If we have posts, save them for scheduled posting
        if result and result.posts:
            logger.info(f"Generated {len(result.posts)} new posts")
            
            # Save posts to individual files for scheduled posting
            for i, post in enumerate(result.posts):
                if not post.scheduled_time:
                    logger.warning(f"Post #{i+1} has no scheduled time, skipping")
                    continue
                
                # Create a filename with the scheduled time for easy sorting
                scheduled_time_str = post.scheduled_time.strftime("%Y%m%d_%H%M")
                filename = POSTS_DIR / f"{scheduled_time_str}_post_{i+1}.json"
                
                # Convert to dict for JSON serialization
                post_data = {
                    "content": post.content,
                    "topic": {
                        "title": post.topic.title,
                        "summary": post.topic.summary,
                        "key_points": post.topic.key_points,
                        "relevance": post.topic.relevance
                    },
                    "scheduled_time": post.scheduled_time.isoformat()
                }
                
                # Save to file
                with open(filename, "w") as f:
                    json.dump(post_data, f, indent=2)
                
                logger.info(f"Saved post for {scheduled_time_str} to {filename}")
            
            return True
        else:
            logger.info("No new posts generated")
            return False
    
    except Exception as e:
        logger.error(f"Error checking for new content: {str(e)}")
        return False


async def post_scheduled_content():
    """Post content that's scheduled for now."""
    try:
        logger.info("Checking for scheduled posts to publish...")
        now = datetime.now()
        
        # Get all post files that don't have the POSTED_MARKER
        pending_post_files = [f for f in POSTS_DIR.glob("*.json") if POSTED_MARKER not in f.name]
        
        for post_file in pending_post_files:
            # Load the post data
            with open(post_file, "r") as f:
                post_data = json.load(f)
            
            # Parse the scheduled time
            scheduled_time = datetime.fromisoformat(post_data["scheduled_time"])
            
            # If it's time to post (or past time), post it
            if scheduled_time <= now:
                logger.info(f"Posting content scheduled for {scheduled_time}")
                
                # Post to LinkedIn
                success = await post_to_linkedin(post_data["content"])
                
                if success:
                    logger.info("Post published successfully!")
                    
                    # Rename the file to mark it as posted
                    posted_file = post_file.with_name(f"{post_file.stem}{POSTED_MARKER}{post_file.suffix}")
                    post_file.rename(posted_file)
                    
                    logger.info(f"Marked post as published: {posted_file}")
                else:
                    logger.error("Failed to publish post")
    
    except Exception as e:
        logger.error(f"Error posting scheduled content: {str(e)}")


def schedule_tasks():
    """Set up the schedule for checking emails and posting content."""
    # Check for new emails every X hours
    schedule.every(CHECKING_INTERVAL_HOURS).hours.do(
        lambda: asyncio.run(check_for_new_content())
    )
    
    # Check for scheduled posts to publish every 5 minutes
    schedule.every(5).minutes.do(
        lambda: asyncio.run(post_scheduled_content())
    )
    
    # Also check immediately on startup
    asyncio.run(check_for_new_content())


def main():
    """Main function to run the scheduler."""
    logger.info("Starting LinkedIn Post Scheduler")
    
    # Set up scheduled tasks
    schedule_tasks()
    
    # Run the scheduler loop
    while True:
        try:
            schedule.run_pending()
            time.sleep(60)  # Sleep for 1 minute between checks
        except KeyboardInterrupt:
            logger.info("Scheduler stopped by user")
            break
        except Exception as e:
            logger.error(f"Error in scheduler loop: {str(e)}")
            # Sleep a bit longer if there's an error
            time.sleep(300)


if __name__ == "__main__":
    main() 