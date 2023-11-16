from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse
from dotenv import load_dotenv

import boto3
import uuid
import os
from database import create_mysql_connection

load_dotenv()

app = FastAPI()

REGION = os.getenv("AWS_REGION")
BUCKET = os.getenv("AWS_BUCKET")

session = boto3.Session(
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
    region_name=REGION,
)
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
        connection = create_mysql_connection()

        if file.content_type not in ["image/jpeg", "image/png"]:
            raise HTTPException(status_code=400, detail="Invalid file type")

        file_name = str(uuid.uuid4())
        file_extension = os.path.splitext(file.filename)[1]
        s3_object_name = f"{file_name}{file_extension}"

        upload_file_to_s3(file.file, BUCKET, s3_object_name)

        response = rekognition_client.detect_faces(
            Image={"S3Object": {"Bucket": BUCKET, "Name": s3_object_name}},
            Attributes=["ALL"],
        )
        if response["FaceDetails"]:
            face_detail = response["FaceDetails"][0]
            if face_detail["Confidence"] > 90:
                facing = "unknown"
                if face_detail["Pose"]["Yaw"] < -45:
                    facing = "left"
                elif face_detail["Pose"]["Yaw"] > 45:
                    facing = "right"

                gender = face_detail["Gender"]["Value"]
                gender_confidence = face_detail["Gender"]["Confidence"]
                age_range = f"{face_detail['AgeRange']['Low']}-{face_detail['AgeRange']['High']}"
                print('\033[91m'+'face_detail["Pose"]["Yaw"]: ' + '\033[92m', face_detail["Pose"]["Yaw"])
                return {
                    "message": "Human detected",
                    "facing": facing,
                    "gender": gender,
                    "gender_confidence": gender_confidence,
                    "age_range": age_range
                }
            else:
                return {"message": "Human face not detected with high confidence"}
        return {"message": "Human face not detected"}
    except Exception as e:
        return JSONResponse(status_code=500, content={"message": str(e)})
    finally:
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
