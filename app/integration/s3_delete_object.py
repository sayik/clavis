import os
import boto3

from botocore.exceptions import ClientError
from dotenv import load_dotenv

load_dotenv()

s3 = boto3.client("s3")

BUCKET_NAME = os.getenv("AWS_BUCKET_NAME")


def delete_objects(items: list[str]) -> dict:
    try:
        response = s3.delete_objects(
            Bucket=BUCKET_NAME,
            Delete={"Objects": [{"Key": f"note_files/{item}"} for item in items]},
        )

        deleted = [obj["Key"] for obj in response.get("Deleted", [])]

        failed = [
            {"file": obj["Key"], "error": obj["Message"]}
            for obj in response.get("Errors", [])
        ]

        return {"deleted": deleted, "failed": failed}

    except ClientError as e:
        print(f"S3 delete error: {e}")

        return {"error": str(e)}
