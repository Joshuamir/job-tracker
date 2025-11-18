"""
Telegram notification handler for the job tracker bot.
"""

import os
from typing import Dict, Any, Optional
import requests

from utils import get_logger


class TelegramNotifier:
    """
    Handle Telegram notifications for new job postings.
    """
    
    def __init__(self):
        """
        Initialize the Telegram notifier with credentials from environment variables.
        """
        self.logger = get_logger(__name__)
        self.bot_token = os.environ.get('TELEGRAM_BOT_TOKEN')
        self.chat_id = os.environ.get('TELEGRAM_CHAT_ID')
        self.enabled = bool(self.bot_token and self.chat_id)
        
        if not self.enabled:
            self.logger.warning(
                "Telegram credentials not found in environment variables. "
                "Notifications will be disabled. Set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID."
            )
        else:
            self.logger.info("Telegram notifier initialized successfully")
        
        self.base_url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage" if self.bot_token else None
    
    def send_message(self, text: str, parse_mode: str = 'HTML') -> bool:
        """
        Send a message via Telegram Bot API.
        
        Args:
            text: Message text to send
            parse_mode: Parse mode for formatting (HTML or Markdown)
            
        Returns:
            True if message sent successfully, False otherwise
        """
        if not self.enabled:
            self.logger.info(f"[NOTIFICATION DISABLED] Would send: {text}")
            return False
        
        try:
            payload = {
                'chat_id': self.chat_id,
                'text': text,
                'parse_mode': parse_mode,
                'disable_web_page_preview': False
            }
            
            response = requests.post(self.base_url, json=payload, timeout=10)
            response.raise_for_status()
            
            self.logger.info("Message sent successfully via Telegram")
            return True
        
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Failed to send Telegram message: {e}")
            return False
        
        except Exception as e:
            self.logger.error(f"Unexpected error sending Telegram message: {e}")
            return False
    
    def send_job_notification(self, job: Dict[str, Any]) -> bool:
        """
        Format and send a job alert notification.
        
        Args:
            job: Dictionary containing job details
            
        Returns:
            True if notification sent successfully, False otherwise
        """
        try:
            # Format message with HTML
            message = f"""
🎯 <b>New Project Manager Position!</b>

<b>Company:</b> {job.get('company', 'Unknown')}
<b>Position:</b> {job.get('title', 'Unknown')}
<b>Discovered:</b> {job.get('first_seen', 'Unknown')}

<b>Apply here:</b> {job.get('url', '#')}

#ProjectManager #JobAlert
"""
            
            return self.send_message(message.strip())
        
        except Exception as e:
            self.logger.error(f"Error formatting job notification: {e}")
            return False
    
    def send_summary(self, new_jobs_count: int, total_jobs_count: int, errors: int = 0) -> bool:
        """
        Send a summary of the scraping run.
        
        Args:
            new_jobs_count: Number of new jobs found
            total_jobs_count: Total number of jobs in database
            errors: Number of errors encountered
            
        Returns:
            True if summary sent successfully, False otherwise
        """
        if not self.enabled:
            self.logger.info(
                f"[SUMMARY] New jobs: {new_jobs_count}, "
                f"Total jobs: {total_jobs_count}, Errors: {errors}"
            )
            return False
        
        try:
            # Only send summary if there are new jobs or errors
            if new_jobs_count == 0 and errors == 0:
                self.logger.info("No new jobs or errors, skipping summary notification")
                return True
            
            emoji = "✅" if errors == 0 else "⚠️"
            
            message = f"""
{emoji} <b>Job Tracker Summary</b>

<b>New Jobs Found:</b> {new_jobs_count}
<b>Total Jobs Tracked:</b> {total_jobs_count}
<b>Errors:</b> {errors}
"""
            
            return self.send_message(message.strip())
        
        except Exception as e:
            self.logger.error(f"Error sending summary: {e}")
            return False
    
    def send_error_notification(self, error_message: str) -> bool:
        """
        Send an error notification.
        
        Args:
            error_message: Error message to send
            
        Returns:
            True if notification sent successfully, False otherwise
        """
        try:
            message = f"""
❌ <b>Job Tracker Error</b>

{error_message}
"""
            
            return self.send_message(message.strip())
        
        except Exception as e:
            self.logger.error(f"Error sending error notification: {e}")
            return False
