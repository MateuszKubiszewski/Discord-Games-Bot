import os
import boto3

ACCESS_KEY_ID = os.environ["ACCESS_KEY_ID"]
ACCESS_TOKEN = os.environ["ACCESS_TOKEN"]
S3_BUCKET_NAME = os.environ["S3_BUCKET_NAME"]
SECRET_ACCESS_KEY = os.environ["SECRET_ACCESS_KEY"]

s3 = boto3.resource('s3', region_name='eu-central-1', aws_access_key_id=ACCESS_KEY_ID, aws_secret_access_key='SECRET_ACCESS_KEY')

def write(filename: String, content: String):
    return s3.Object(S3_BUCKET_NAME, filename).put(Body=content)

def read(filename: String):
    return s3.Object(S3_BUCKET_NAME, filename).get()