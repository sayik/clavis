import boto3
from botocore.exceptions import ClientError
from botocore.config import Config
import os
from dotenv import load_dotenv

load_dotenv()


# size and proper naming needed
def create_presigned_url(
    file_name: str,
    method: str,
    expiration: int = 3600,
) -> str | None:
    # Generate a presigned URL for the S3 object
    object_name = f"note_files/{file_name}"
    s3_client = boto3.client(
        "s3",
        region_name=os.getenv("AWS_REGION"),
        aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
        aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
    )
    if method == "GET":
        try:
            response = s3_client.generate_presigned_url(
                "get_object",
                Params={
                    "Bucket": os.getenv("AWS_BUCKET_NAME"),
                    "Key": object_name,
                },
                ExpiresIn=expiration,
            )
        except ClientError as e:
            return None
    elif method == "PUT":
        try:
            response = s3_client.generate_presigned_url(
                "put_object",
                Params={
                    "Bucket": os.getenv("AWS_BUCKET_NAME"),
                    "Key": object_name,
                },
                ExpiresIn=expiration,
            )
        except ClientError as e:
            return None

    print(response)
    return response


if __name__ == "__main__":
    create_presigned_url(
        object_name="note_files/bdrack.png",
        bucket_name="fastapinotes",
        method="PUT",
    )
