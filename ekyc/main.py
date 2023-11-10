from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse
import boto3
import uuid
import os

app = FastAPI()

# Configuration for AWS
REGION = "ap-northeast-1"
BUCKET = "s3tokyooo"
# Make sure your AWS credentials are properly configured in the environment variables or AWS credentials file

# AWS session and client
session = boto3.Session(region_name=REGION)
s3_client = session.client("s3", region_name=REGION)
rekognition_client = session.client("rekognition", region_name=REGION)


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
