"""
Job scraper for tracking Project Manager positions.
"""

import time
from datetime import datetime
from typing import Dict, List, Any, Set
from urllib.parse import urljoin, urlparse
import traceback

import pandas as pd
import requests
from bs4 import BeautifulSoup

from utils import get_logger, load_config, load_job_database, save_job_database
from notifier import TelegramNotifier


class JobScraper:
    """
    Scrape job postings from company career websites.
    """
    
    def __init__(self, config_path: str = "config.yaml"):
        """
        Initialize the job scraper.
        
        Args:
            config_path: Path to the configuration file
        """
        self.logger = get_logger(__name__)
        self.config = load_config(config_path)
        self.notifier = TelegramNotifier()
        self.session = requests.Session()
        
        # Configure session with user agent
        user_agent = self.config.get('scraping', {}).get(
            'user_agent',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        )
        self.session.headers.update({'User-Agent': user_agent})
        
        self.logger.info("JobScraper initialized")
    
    def scrape_website(self, url: str, company_name: str) -> List[Dict[str, Any]]:
        """
        Scrape a single website for job postings.
        
        Args:
            url: URL of the career website
            company_name: Name of the company
            
        Returns:
            List of job dictionaries found on the website
        """
        self.logger.info(f"Scraping {company_name}: {url}")
        
        jobs = []
        scraping_config = self.config.get('scraping', {})
        timeout = scraping_config.get('timeout', 10)
        retry_attempts = scraping_config.get('retry_attempts', 3)
        retry_delay = scraping_config.get('retry_delay', 2)
        
        for attempt in range(retry_attempts):
            try:
                response = self.session.get(url, timeout=timeout)
                response.raise_for_status()
                
                # Parse HTML
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Search for job postings
                jobs = self._extract_jobs(soup, url, company_name)
                
                self.logger.info(f"Found {len(jobs)} potential jobs at {company_name}")
                return jobs
            
            except requests.exceptions.Timeout:
                self.logger.warning(
                    f"Timeout scraping {company_name} (attempt {attempt + 1}/{retry_attempts})"
                )
                
            except requests.exceptions.RequestException as e:
                self.logger.error(
                    f"Error scraping {company_name} (attempt {attempt + 1}/{retry_attempts}): {e}"
                )
                
            except Exception as e:
                self.logger.error(
                    f"Unexpected error scraping {company_name}: {e}\n{traceback.format_exc()}"
                )
                break
            
            # Exponential backoff for retries
            if attempt < retry_attempts - 1:
                wait_time = retry_delay * (2 ** attempt)
                self.logger.info(f"Retrying in {wait_time} seconds...")
                time.sleep(wait_time)
        
        return jobs
    
    def _extract_jobs(self, soup: BeautifulSoup, base_url: str, company_name: str) -> List[Dict[str, Any]]:
        """
        Extract job postings from parsed HTML.
        
        Args:
            soup: BeautifulSoup object containing parsed HTML
            base_url: Base URL of the website
            company_name: Name of the company
            
        Returns:
            List of job dictionaries
        """
        jobs = []
        search_keywords = self.config.get('search_keywords', [])
        
        # Look for common job posting elements
        # This is a generic approach - different sites structure their HTML differently
        selectors = [
            'a[href*="job"]',
            'a[href*="career"]',
            'a[href*="position"]',
            'a.job-title',
            'a.career-link',
            '[class*="job"] a',
            '[class*="career"] a',
            '[class*="position"] a'
        ]
        
        links = set()
        for selector in selectors:
            elements = soup.select(selector)
            for element in elements:
                href = element.get('href')
                if href:
                    # Make URL absolute
                    full_url = urljoin(base_url, href)
                    links.add((full_url, element.get_text(strip=True)))
        
        # Filter by keywords
        for url, title in links:
            if self._matches_keywords(title, search_keywords):
                job = {
                    'company': company_name,
                    'title': title,
                    'url': url,
                    'first_seen': datetime.utcnow().isoformat(),
                    'last_seen': datetime.utcnow().isoformat()
                }
                jobs.append(job)
        
        return jobs
    
    def _matches_keywords(self, text: str, keywords: List[str]) -> bool:
        """
        Check if text contains any of the search keywords.
        
        Args:
            text: Text to search in
            keywords: List of keywords to search for
            
        Returns:
            True if any keyword is found, False otherwise
        """
        if not text:
            return False
        
        text_lower = text.lower()
        for keyword in keywords:
            if keyword.lower() in text_lower:
                return True
        
        return False
    
    def process_companies(self, excel_path: str = "companies.xlsx") -> List[Dict[str, Any]]:
        """
        Read Excel file and scrape all companies.
        
        Args:
            excel_path: Path to the Excel file containing company data
            
        Returns:
            List of all jobs found
        """
        self.logger.info(f"Processing companies from {excel_path}")
        
        try:
            df = pd.read_excel(excel_path)
            self.logger.info(f"Loaded {len(df)} companies from Excel")
            
            all_jobs = []
            request_delay = self.config.get('scraping', {}).get('request_delay', 2)
            
            for idx, row in df.iterrows():
                company_name = row.get('Company Name', 'Unknown')
                url = row.get('Career Website URL', '')
                
                if not url:
                    self.logger.warning(f"Skipping {company_name}: No URL provided")
                    continue
                
                jobs = self.scrape_website(url, company_name)
                all_jobs.extend(jobs)
                
                # Be respectful - delay between requests
                if idx < len(df) - 1:
                    self.logger.info(f"Waiting {request_delay} seconds before next request...")
                    time.sleep(request_delay)
            
            self.logger.info(f"Total jobs found across all companies: {len(all_jobs)}")
            return all_jobs
        
        except FileNotFoundError:
            self.logger.error(f"Excel file not found: {excel_path}")
            return []
        
        except Exception as e:
            self.logger.error(f"Error processing companies: {e}\n{traceback.format_exc()}")
            return []
    
    def identify_new_jobs(self, current_jobs: List[Dict[str, Any]], database: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Compare current jobs with database to identify new postings.
        
        Args:
            current_jobs: List of jobs found in current scrape
            database: Existing job database
            
        Returns:
            List of new jobs not in the database
        """
        new_jobs = []
        existing_jobs = database.get('jobs', {})
        
        for job in current_jobs:
            # Create unique key from company + URL
            job_key = f"{job['company']}||{job['url']}"
            
            if job_key not in existing_jobs:
                new_jobs.append(job)
                self.logger.info(f"New job: {job['title']} at {job['company']}")
            else:
                # Update last_seen timestamp for existing job
                existing_jobs[job_key]['last_seen'] = datetime.utcnow().isoformat()
        
        self.logger.info(f"Identified {len(new_jobs)} new jobs")
        return new_jobs
    
    def update_database(self, new_jobs: List[Dict[str, Any]], database: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update database with new jobs.
        
        Args:
            new_jobs: List of new jobs to add
            database: Existing job database
            
        Returns:
            Updated database
        """
        if 'jobs' not in database:
            database['jobs'] = {}
        
        for job in new_jobs:
            job_key = f"{job['company']}||{job['url']}"
            database['jobs'][job_key] = job
        
        return database
    
    def run(self, excel_path: str = "companies.xlsx", db_path: str = None) -> Dict[str, Any]:
        """
        Main execution flow for the job scraper.
        
        Args:
            excel_path: Path to the Excel file with companies
            db_path: Path to the job database file
            
        Returns:
            Dictionary with run statistics
        """
        self.logger.info("=" * 60)
        self.logger.info("Starting Job Tracker Bot")
        self.logger.info("=" * 60)
        
        # Use database path from config if not provided
        if db_path is None:
            db_path = self.config.get('database', {}).get('path', 'jobs_database.json')
        
        stats = {
            'new_jobs': 0,
            'total_jobs': 0,
            'errors': 0
        }
        
        try:
            # Load existing database
            database = load_job_database(db_path)
            
            # Scrape all companies
            current_jobs = self.process_companies(excel_path)
            
            if not current_jobs:
                self.logger.warning("No jobs found in current scrape")
            
            # Identify new jobs
            new_jobs = self.identify_new_jobs(current_jobs, database)
            
            # Update database
            database = self.update_database(new_jobs, database)
            
            # Save database
            save_job_database(database, db_path)
            
            # Send notifications for new jobs
            max_notifications = self.config.get('notifications', {}).get('max_jobs_per_notification', 10)
            
            for idx, job in enumerate(new_jobs):
                if idx >= max_notifications:
                    self.logger.info(
                        f"Reached max notifications limit ({max_notifications}), "
                        f"skipping remaining {len(new_jobs) - idx} jobs"
                    )
                    break
                
                self.notifier.send_job_notification(job)
                time.sleep(1)  # Small delay between notifications
            
            # Update stats
            stats['new_jobs'] = len(new_jobs)
            stats['total_jobs'] = len(database.get('jobs', {}))
            
            # Send summary if enabled
            if self.config.get('notifications', {}).get('send_summary', True):
                self.notifier.send_summary(
                    stats['new_jobs'],
                    stats['total_jobs'],
                    stats['errors']
                )
            
            self.logger.info("=" * 60)
            self.logger.info(f"Job Tracker Bot Completed")
            self.logger.info(f"New jobs: {stats['new_jobs']}, Total jobs: {stats['total_jobs']}")
            self.logger.info("=" * 60)
            
        except Exception as e:
            self.logger.error(f"Critical error in run: {e}\n{traceback.format_exc()}")
            stats['errors'] = 1
            self.notifier.send_error_notification(f"Critical error: {str(e)}")
        
        return stats


if __name__ == "__main__":
    scraper = JobScraper()
    scraper.run()
