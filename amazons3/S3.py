import os
import boto3

# heroku run
ACCESS_KEY_ID = os.environ["ACCESS_KEY_ID"]
S3_BUCKET_NAME = os.environ["S3_BUCKET_NAME"]
SECRET_ACCESS_KEY = os.environ["SECRET_ACCESS_KEY"]

# # local run
# from dotenv import load_dotenv
# load_dotenv()
# ACCESS_KEY_ID = os.getenv("ACCESS_KEY_ID")
# S3_BUCKET_NAME = os.getenv("S3_BUCKET_NAME")
# SECRET_ACCESS_KEY = os.getenv("SECRET_ACCESS_KEY")

s3 = boto3.resource('s3', region_name='eu-central-1', aws_access_key_id=ACCESS_KEY_ID, aws_secret_access_key=SECRET_ACCESS_KEY)

def write(filename: str, content: str):
    return s3.Object(S3_BUCKET_NAME, filename).put(Body=content)

def read(filename: str):
    return s3.Object(S3_BUCKET_NAME, filename).get()