"""
Utility functions for the job tracker bot.
"""

import json
import logging
import sys
from pathlib import Path
from typing import Any, Dict

import yaml


def get_logger(name: str) -> logging.Logger:
    """
    Configure and return a logger with the specified name.
    
    Args:
        name: Name of the logger
        
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    
    # Only add handler if logger doesn't have one
    if not logger.handlers:
        logger.setLevel(logging.INFO)
        
        # Create console handler
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(logging.INFO)
        
        # Create formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        handler.setFormatter(formatter)
        
        # Add handler to logger
        logger.addHandler(handler)
    
    return logger


def load_config(config_path: str = "config.yaml") -> Dict[str, Any]:
    """
    Load YAML configuration file with defaults.
    
    Args:
        config_path: Path to the configuration file
        
    Returns:
        Dictionary containing configuration
    """
    logger = get_logger(__name__)
    
    try:
        config_file = Path(config_path)
        if not config_file.exists():
            logger.warning(f"Config file {config_path} not found, using defaults")
            return get_default_config()
        
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        logger.info(f"Configuration loaded from {config_path}")
        return config
    
    except Exception as e:
        logger.error(f"Error loading config: {e}")
        logger.info("Using default configuration")
        return get_default_config()


def get_default_config() -> Dict[str, Any]:
    """
    Return default configuration.
    
    Returns:
        Dictionary containing default configuration
    """
    return {
        'search_keywords': [
            'Project Manager',
            'Programme Manager',
            'Program Manager',
            'PM',
            'Technical Project Manager',
            'TPM',
            'Senior Project Manager',
            'Junior Project Manager'
        ],
        'scraping': {
            'timeout': 10,
            'retry_attempts': 3,
            'retry_delay': 2,
            'request_delay': 2,
            'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        },
        'notifications': {
            'enabled': True,
            'send_summary': True,
            'max_jobs_per_notification': 10
        },
        'database': {
            'path': 'jobs_database.json',
            'backup_enabled': False
        }
    }


def load_job_database(db_path: str = "jobs_database.json") -> Dict[str, Any]:
    """
    Load job database from JSON file.
    
    Args:
        db_path: Path to the database file
        
    Returns:
        Dictionary containing job database
    """
    logger = get_logger(__name__)
    
    try:
        db_file = Path(db_path)
        if not db_file.exists():
            logger.info(f"Database file {db_path} not found, creating new database")
            return {'jobs': {}, 'metadata': {'last_updated': None, 'total_jobs': 0}}
        
        with open(db_path, 'r', encoding='utf-8') as f:
            database = json.load(f)
        
        logger.info(f"Loaded {len(database.get('jobs', {}))} jobs from database")
        return database
    
    except json.JSONDecodeError as e:
        logger.error(f"Error parsing JSON database: {e}")
        logger.info("Creating new database")
        return {'jobs': {}, 'metadata': {'last_updated': None, 'total_jobs': 0}}
    
    except Exception as e:
        logger.error(f"Error loading database: {e}")
        logger.info("Creating new database")
        return {'jobs': {}, 'metadata': {'last_updated': None, 'total_jobs': 0}}


def save_job_database(database: Dict[str, Any], db_path: str = "jobs_database.json") -> bool:
    """
    Save job database to JSON file.
    
    Args:
        database: Dictionary containing job database
        db_path: Path to the database file
        
    Returns:
        True if successful, False otherwise
    """
    logger = get_logger(__name__)
    
    try:
        # Update metadata
        if 'metadata' not in database:
            database['metadata'] = {}
        
        from datetime import datetime
        database['metadata']['last_updated'] = datetime.utcnow().isoformat()
        database['metadata']['total_jobs'] = len(database.get('jobs', {}))
        
        # Save to file
        with open(db_path, 'w', encoding='utf-8') as f:
            json.dump(database, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Database saved successfully to {db_path}")
        return True
    
    except Exception as e:
        logger.error(f"Error saving database: {e}")
        return False
