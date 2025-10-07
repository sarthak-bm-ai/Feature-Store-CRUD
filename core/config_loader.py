"""
Configuration loader for different environments.
Automatically loads the appropriate .env file based on ENVIRONMENT variable.
"""
import os
from dotenv import load_dotenv

def load_environment_config():
    """
    Load environment-specific configuration.
    Priority: .env.{ENVIRONMENT} > .env > defaults
    """
    environment = os.getenv("ENVIRONMENT", "development")
    
    # Try to load environment-specific .env file first
    env_file = f".env.{environment}"
    if os.path.exists(env_file):
        print(f"Loading configuration from {env_file}")
        load_dotenv(env_file, override=True)
    elif os.path.exists(".env"):
        print("Loading configuration from .env")
        load_dotenv(".env")
    else:
        print("No .env file found, using default values")
    
    return environment

# Load configuration on import
ENVIRONMENT = load_environment_config()
