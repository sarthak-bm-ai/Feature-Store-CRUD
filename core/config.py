import boto3
from .settings import settings

# Initialize DynamoDB resource using settings
dynamodb = boto3.resource("dynamodb", region_name=settings.AWS_REGION)

# Two tables with different partition keys
table_bright_uid = dynamodb.Table(settings.TABLE_NAME_BRIGHT_UID)
table_account_id = dynamodb.Table(settings.TABLE_NAME_ACCOUNT_ID)

# Table mapping for easy access
TABLES = {
    "bright_uid": table_bright_uid,
    "account_id": table_account_id
}
