import os
import boto3
from botocore.exceptions import ClientError
from botocore.client import Config

SPACES_ENDPOINT = os.getenv("SPACES_ENDPOINT")
SPACES_REGION = os.getenv("SPACES_REGION")
SPACES_ACCESS_KEY = os.getenv("SPACES_ACCESS_KEY")
SPACES_SECRET_KEY = os.getenv("SPACES_SECRET_KEY")
SPACES_BUCKET = os.getenv("SPACES_BUCKET")

# Clean endpoint if the bucket name is wrongly included in the endpoint URL
# e.g., https://aurumfx-images.sgp1.digitaloceanspaces.com -> https://sgp1.digitaloceanspaces.com
clean_endpoint = SPACES_ENDPOINT
if SPACES_BUCKET and f"{SPACES_BUCKET}." in clean_endpoint:
    clean_endpoint = clean_endpoint.replace(f"{SPACES_BUCKET}.", "")

s3_client = boto3.client(
    "s3",
    endpoint_url=clean_endpoint,
    region_name=SPACES_REGION,
    aws_access_key_id=SPACES_ACCESS_KEY,
    aws_secret_access_key=SPACES_SECRET_KEY,
)

def upload_business_image(file_obj, filename: str, content_type: str) -> str:
    key = f"businesses/{filename}"
    try:
        s3_client.upload_fileobj(
            file_obj,
            SPACES_BUCKET,
            key,
            ExtraArgs={
                "ACL": "public-read",
                "ContentType": content_type
            }
        )
        
        # Construct the final public URL
        if SPACES_BUCKET in SPACES_ENDPOINT:
            return f"{SPACES_ENDPOINT}/{key}"
        else:
            scheme, domain = SPACES_ENDPOINT.split("://")
            return f"{scheme}://{SPACES_BUCKET}.{domain}/{key}"
            
    except Exception as e:
        raise Exception(f"Failed to upload image: {str(e)}")

def upload_staff_image(file_obj, filename: str, content_type: str) -> str:
    key = f"staff_kyc/{filename}"
    try:
        s3_client.upload_fileobj(
            file_obj,
            SPACES_BUCKET,
            key,
            ExtraArgs={
                "ACL": "public-read",
                "ContentType": content_type
            }
        )
        
        # Construct the final public URL
        if SPACES_BUCKET in SPACES_ENDPOINT:
            return f"{SPACES_ENDPOINT}/{key}"
        else:
            scheme, domain = SPACES_ENDPOINT.split("://")
            return f"{scheme}://{SPACES_BUCKET}.{domain}/{key}"
            
    except Exception as e:
        raise Exception(f"Failed to upload image: {str(e)}")

def delete_business_image(image_url: str):
    if not image_url:
        return
        
    try:
        # Extract the key dynamically (everything after /businesses/)
        key_index = image_url.find("/businesses/")
        if key_index != -1:
            key = image_url[key_index + 1:]
            s3_client.delete_object(Bucket=SPACES_BUCKET, Key=key)
    except Exception as e:
        print(f"Failed to delete image from spaces: {str(e)}")
