import os
import uuid
from datetime import datetime, timezone

import boto3
from botocore.exceptions import ClientError


TABLE_NAME = os.getenv(
    "PLANNER_TABLE_NAME",
    "AIPlannerItems"
)

REGION_NAME = os.getenv(
    "AWS_REGION",
    "ap-south-1"
)


def get_dynamodb_resource():
    """
    Create a connection to Amazon DynamoDB.
    """
    return boto3.resource(
        "dynamodb",
        region_name=REGION_NAME
    )


def create_table():
    """
    Create the planner DynamoDB table if it does not already exist.
    """

    dynamodb = get_dynamodb_resource()

    try:
        table = dynamodb.create_table(
            TableName=TABLE_NAME,

            KeySchema=[
                {
                    "AttributeName": "item_id",
                    "KeyType": "HASH"
                }
            ],

            AttributeDefinitions=[
                {
                    "AttributeName": "item_id",
                    "AttributeType": "S"
                }
            ],

            BillingMode="PAY_PER_REQUEST"
        )

        print(
            f"Creating DynamoDB table: {TABLE_NAME}"
        )

        table.wait_until_exists()

        print(
            f"Table '{TABLE_NAME}' is ready."
        )

        return table

    except ClientError as error:

        if error.response["Error"]["Code"] == (
            "ResourceInUseException"
        ):
            print(
                f"Table '{TABLE_NAME}' already exists."
            )

            return dynamodb.Table(TABLE_NAME)

        raise


def save_item(item):
    """
    Save one PlannerItem into DynamoDB.
    """

    dynamodb = get_dynamodb_resource()

    table = dynamodb.Table(TABLE_NAME)

    item_id = str(uuid.uuid4())

    record = {
        "item_id": item_id,

        "type": item.type.value,

        "title": item.title,

        "date_text": (
            item.date_text
            if item.date_text is not None
            else ""
        ),

        "resolved_date": (
            item.resolved_date
            if item.resolved_date is not None
            else ""
        ),

        "days_remaining": (
            item.days_remaining
            if item.days_remaining is not None
            else -1
        ),

        "priority": (
            item.priority
            if item.priority is not None
            else ""
        ),

        "time_text": (
            item.time_text
            if item.time_text is not None
            else ""
        ),

        "context": (
            item.context
            if item.context is not None
            else ""
        ),

        "created_at": datetime.now(
            timezone.utc
        ).isoformat()
    }

    table.put_item(
        Item=record
    )

    return item_id


def get_all_items():
    """
    Retrieve all planner items.
    """

    dynamodb = get_dynamodb_resource()

    table = dynamodb.Table(TABLE_NAME)

    response = table.scan()

    return response.get(
        "Items",
        []
    )


def delete_item(item_id):
    """
    Delete one planner item by ID.
    """

    dynamodb = get_dynamodb_resource()

    table = dynamodb.Table(TABLE_NAME)

    table.delete_item(
        Key={
            "item_id": item_id
        }
    )


if __name__ == "__main__":

    print("=" * 60)
    print("              DYNAMODB STORAGE TEST")
    print("=" * 60)

    print(
        f"\nTable name: {TABLE_NAME}"
    )

    print(
        f"AWS region: {REGION_NAME}"
    )

    try:

        table = create_table()

        print(
            "\nDynamoDB connection successful."
        )

        print(
            f"Table status: {table.table_status}"
        )

        print(
            "\nStorage layer is ready."
        )

    except Exception as error:

        print(
            "\nDYNAMODB ERROR"
        )

        print(
            f"{type(error).__name__}: {error}"
        )