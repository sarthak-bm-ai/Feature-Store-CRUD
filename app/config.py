import os
import boto3

AWS_REGION = "us-west-2"
TABLE_NAME_BRIGHT_UID = "featuers_poc"  # Using existing table for testing
TABLE_NAME_ACCOUNT_ID = "features_account_id"   # Partition key: account_id

dynamodb = boto3.resource("dynamodb", region_name=AWS_REGION)

# Two tables with different partition keys
table_bright_uid = dynamodb.Table(TABLE_NAME_BRIGHT_UID)
table_account_id = dynamodb.Table(TABLE_NAME_ACCOUNT_ID)

# Table mapping for easy access
TABLES = {
    "bright_uid": table_bright_uid,
    "account_id": table_account_id
}