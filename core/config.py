import boto3
import threading
from typing import Dict, Optional
from .settings import settings
from .logging_config import get_logger

# Configure logger
logger = get_logger("dynamodb_config")

class DynamoDBSingleton:
    """
    Singleton pattern for DynamoDB connections to ensure efficient connection pooling.
    Thread-safe implementation with lazy initialization.
    """
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super(DynamoDBSingleton, cls).__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if not self._initialized:
            self._dynamodb = None
            self._tables = {}
            self._initialized = True
            logger.info("DynamoDB Singleton initialized")
    
    def get_dynamodb_resource(self):
        """Get or create DynamoDB resource with connection pooling."""
        if self._dynamodb is None:
            with self._lock:
                if self._dynamodb is None:
                    try:
                        # Create session with optimized configuration
                        session = boto3.Session()
                        
                        # Configure DynamoDB resource with connection pooling
                        self._dynamodb = session.resource(
                            "dynamodb",
                            region_name=settings.AWS_REGION,
                            # Connection pool configuration
                            config=boto3.session.Config(
                                max_pool_connections=50,  # Maximum connections in pool
                                retries={
                                    'max_attempts': 3,
                                    'mode': 'adaptive'
                                },
                                # Connection timeout settings
                                connect_timeout=60,
                                read_timeout=60
                            )
                        )
                        logger.info(f"DynamoDB resource created for region: {settings.AWS_REGION}")
                    except Exception as e:
                        logger.error(f"Failed to create DynamoDB resource: {e}")
                        raise
        return self._dynamodb
    
    def get_table(self, table_type: str):
        """Get table instance with caching."""
        if table_type not in self._tables:
            with self._lock:
                if table_type not in self._tables:
                    try:
                        dynamodb = self.get_dynamodb_resource()
                        
                        if table_type == "bright_uid":
                            table_name = settings.TABLE_NAME_BRIGHT_UID
                        elif table_type == "account_pid":
                            table_name = settings.TABLE_NAME_ACCOUNT_PID
                        else:
                            raise ValueError(f"Invalid table_type: {table_type}")
                        
                        table = dynamodb.Table(table_name)
                        self._tables[table_type] = table
                        logger.info(f"Table '{table_name}' cached for type '{table_type}'")
                    except Exception as e:
                        logger.error(f"Failed to get table '{table_type}': {e}")
                        raise
        
        return self._tables[table_type]
    
    def get_all_tables(self) -> Dict[str, any]:
        """Get all table instances."""
        tables = {}
        for table_type in ["bright_uid", "account_pid"]:
            tables[table_type] = self.get_table(table_type)
        return tables
    
    def health_check(self) -> bool:
        """Check if DynamoDB connection is healthy."""
        try:
            dynamodb = self.get_dynamodb_resource()
            # Simple health check - list tables
            list(dynamodb.tables.all())
            logger.debug("DynamoDB health check passed")
            return True
        except Exception as e:
            logger.error(f"DynamoDB health check failed: {e}")
            return False
    
    def reset_connection(self):
        """Reset connection (useful for testing or connection issues)."""
        with self._lock:
            self._dynamodb = None
            self._tables = {}
            logger.info("DynamoDB connection reset")

# Global singleton instance
dynamodb_singleton = DynamoDBSingleton()

# Convenience functions for backward compatibility
def get_dynamodb_resource():
    """Get DynamoDB resource instance."""
    return dynamodb_singleton.get_dynamodb_resource()

def get_table(table_type: str):
    """Get table instance by type."""
    return dynamodb_singleton.get_table(table_type)

def get_all_tables():
    """Get all table instances."""
    return dynamodb_singleton.get_all_tables()

def health_check():
    """Check DynamoDB connection health."""
    return dynamodb_singleton.health_check()

def reset_connection():
    """Reset DynamoDB connection."""
    dynamodb_singleton.reset_connection()

# Table mapping for easy access (backward compatibility)
TABLES = {
    "bright_uid": lambda: get_table("bright_uid"),
    "account_pid": lambda: get_table("account_pid")
}
