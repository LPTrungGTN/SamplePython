from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse
import boto3
import uuid
import os
from dotenv import load_dotenv
import mysql.connector
from mysql.connector import Error

load_dotenv()

app = FastAPI()

# Configuration for AWS
REGION = os.getenv("AWS_REGION")
BUCKET = os.getenv("AWS_BUCKET")
# Make sure your AWS credentials are properly configured in the environment variables or AWS credentials file

# AWS session and client
session = boto3.Session(
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
    region_name=REGION,
)
s3_client = session.client("s3", region_name=REGION)
rekognition_client = session.client("rekognition", region_name=REGION)

# Configuration for MySQL Database
MYSQL_HOST = "attendance_db"
MYSQL_DATABASE = "attendance"
MYSQL_USER = "root"
MYSQL_PASSWORD = "root_password1"


def create_mysql_connection():
    try:
        connection = mysql.connector.connect(
            host=MYSQL_HOST,
            database=MYSQL_DATABASE,
            user=MYSQL_USER,
            password=MYSQL_PASSWORD,
        )
        if connection.is_connected():
            return connection
    except Error as e:
        print("Error while connecting to MySQL", e)
        return None


def upload_file_to_s3(file, bucket, object_name):
    s3_client.upload_fileobj(file, bucket, object_name)
    return object_name


def delete_file_from_s3(bucket, object_name):
    try:
        response = s3_client.delete_object(Bucket=bucket, Key=object_name)
        return response
    except Exception as e:
        raise e


@app.post("/detect_faces/")
async def detect_faces(file: UploadFile = File(...)):
    s3_object_name = None
    try:
        connection = create_mysql_connection()
        if connection:
            print("Connection to MySQL DB successful")
            connection.close()

        # Validate file type
        if file.content_type not in ["image/jpeg", "image/png"]:
            raise HTTPException(status_code=400, detail="Invalid file type")

        # Generate a unique file name
        file_name = str(uuid.uuid4())
        file_extension = os.path.splitext(file.filename)[1]
        s3_object_name = f"{file_name}{file_extension}"

        # Upload file to S3
        upload_file_to_s3(file.file, BUCKET, s3_object_name)

        # Use boto3 to connect to AWS Rekognition with the image from S3
        response = rekognition_client.detect_faces(
            Image={"S3Object": {"Bucket": BUCKET, "Name": s3_object_name}},
            Attributes=["ALL"],
        )
        # Process response and check if human
        if response["FaceDetails"]:
            face_detail = response["FaceDetails"][0]
            if face_detail["Confidence"] > 90:
                facing = "unknown"
                if face_detail["Pose"]["Yaw"] < -45:
                    facing = "left"
                elif face_detail["Pose"]["Yaw"] > 45:
                    facing = "right"

                # Return result without adding to the database
                return {"message": "Human detected", "facing": facing}
            else:
                return {"message": "Human face not detected with high confidence"}
        return {"message": "Human face not detected"}
    except Exception as e:
        return JSONResponse(status_code=500, content={"message": str(e)})
    finally:
        # Delete the file from S3 if it was uploaded
        if s3_object_name:
            try:
                delete_file_from_s3(BUCKET, s3_object_name)
            except Exception as delete_error:
                return JSONResponse(
                    status_code=500,
                    content={
                        "An error occurred while trying to delete the file: ": str(
                            delete_error
                        )
                    },
                )
