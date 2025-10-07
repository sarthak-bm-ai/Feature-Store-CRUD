"""
Centralized configuration management using environment variables.
Supports different environments (development, staging, production).
"""
import os
from typing import Optional
from .config_loader import load_environment_config

# Load environment-specific configuration
ENVIRONMENT = load_environment_config()

class Settings:
    """Application settings loaded from environment variables."""
    
    def __init__(self):
        # Environment
        self.ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
        
        # AWS Configuration
        self.AWS_REGION = os.getenv("AWS_REGION", "us-west-2")
        self.TABLE_NAME_BRIGHT_UID = os.getenv("TABLE_NAME_BRIGHT_UID", "featuers_poc")
        self.TABLE_NAME_ACCOUNT_ID = os.getenv("TABLE_NAME_ACCOUNT_ID", "features_account_id")
        
        # StatsD Configuration
        self.STATSD_HOST = os.getenv("STATSD_HOST", "localhost")
        self.STATSD_PORT = int(os.getenv("STATSD_PORT", "8125"))
        self.STATSD_PREFIX = os.getenv("STATSD_PREFIX", "feature_store")
        
        # Application Configuration
        self.APP_NAME = os.getenv("APP_NAME", "Feature Store API")
        self.APP_VERSION = os.getenv("APP_VERSION", "1.0.0")
        self.DEBUG = os.getenv("DEBUG", "false").lower() == "true"
        
        # Logging Configuration
        self.LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
        
    def get_table_name(self, table_type: str) -> str:
        """Get table name based on table type."""
        if table_type == "bright_uid":
            return self.TABLE_NAME_BRIGHT_UID
        elif table_type == "account_id":
            return self.TABLE_NAME_ACCOUNT_ID
        else:
            raise ValueError(f"Invalid table_type: {table_type}")
    
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.ENVIRONMENT.lower() == "production"
    
    def is_development(self) -> bool:
        """Check if running in development environment."""
        return self.ENVIRONMENT.lower() == "development"
    
    def is_staging(self) -> bool:
        """Check if running in staging environment."""
        return self.ENVIRONMENT.lower() == "staging"

# Global settings instance
settings = Settings()
