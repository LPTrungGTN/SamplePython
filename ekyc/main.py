from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse
from dotenv import load_dotenv

import boto3
import uuid
import os
from database import create_mysql_connection
from repository.card_repository import insert_card_record

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


@app.post("/detect_faces/left")
async def detect_faces(
    file: UploadFile = File(...), card_type: str = None, profile_id: int = None
):
    s3_object_name: str = ""
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
                if -45 <= face_detail["Pose"]["Yaw"] < -30:
                    facing = "left"
                    gender = face_detail["Gender"]["Value"]
                    gender_confidence = face_detail["Gender"]["Confidence"]
                    age_range = f"{face_detail['AgeRange']['Low']}-{face_detail['AgeRange']['High']}"
                    print(
                        "\033[91m" + 'face_detail["Pose"]["Yaw"]: ' + "\033[92m",
                        face_detail["Pose"]["Yaw"],
                    )
                    insert_card_record(
                        connection, profile_id, card_type, s3_object_name
                    )
                    return {
                        "message": "Human detected",
                        "facing": facing,
                        "gender": gender,
                        "gender_confidence": gender_confidence,
                        "age_range": age_range,
                    }
                else:
                    return {"message": "You need to turn left to be detected correctly"}
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


@app.post("/compare_faces")
async def compare_faces(
    source_file: UploadFile = File(...),
    target_file: UploadFile = File(...),
    similarity_threshold: float = 90,
):
    source_s3_object_name = None
    target_s3_object_name = None
    try:
        for file in [source_file, target_file]:
            if file.content_type not in ["image/jpeg", "image/png"]:
                raise HTTPException(status_code=400, detail="Invalid file type")

        source_file_name = str(uuid.uuid4())
        source_file_extension = os.path.splitext(source_file.filename)[1]
        source_s3_object_name = f"{source_file_name}{source_file_extension}"
        upload_file_to_s3(source_file.file, BUCKET, source_s3_object_name)

        target_file_name = str(uuid.uuid4())
        target_file_extension = os.path.splitext(target_file.filename)[1]
        target_s3_object_name = f"{target_file_name}{target_file_extension}"
        upload_file_to_s3(target_file.file, BUCKET, target_s3_object_name)

        response = rekognition_client.compare_faces(
            SimilarityThreshold=similarity_threshold,
            SourceImage={"S3Object": {"Bucket": BUCKET, "Name": source_s3_object_name}},
            TargetImage={"S3Object": {"Bucket": BUCKET, "Name": target_s3_object_name}},
        )

        return response
    except Exception as e:
        return JSONResponse(status_code=500, content={"message": str(e)})
    finally:
        for s3_object_name in [source_s3_object_name, target_s3_object_name]:
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
