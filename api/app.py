from fastapi import FastAPI, UploadFile, File
import boto3
import uuid
import json

app = FastAPI()

sqs = boto3.client("sqs", region_name="ap-southeast-1")
s3 = boto3.client("s3", region_name="ap-southeast-1")

QUEUE_URL = "https://sqs.ap-southeast-1.amazonaws.com/544885083148/augminted-jobs"
BUCKET_NAME = "augminted-pipeline-prod"

@app.get("/")
def root():
    return {"ok": True, "service": "augminted-api"}

@app.post("/generate-model")
async def generate_model(image: UploadFile = File(...)):

    job_id = f"job-{uuid.uuid4().hex[:8]}"
    input_path = f"uploads/{job_id}/main.jpg"

    file_bytes = await image.read()

    s3.put_object(
        Bucket=BUCKET_NAME,
        Key=input_path,
        Body=file_bytes,
        ContentType=image.content_type or "image/jpeg"
    )

    body = {
        "job_id": job_id,
        "input_path": input_path
    }

    sqs.send_message(
        QueueUrl=QUEUE_URL,
        MessageBody=json.dumps(body)
    )

    return {
        "job_id": job_id,
        "upload_path": input_path,
        "status_url": f"/status/{job_id}"
    }

@app.get("/status/{job_id}")
def get_status(job_id: str):
    key = f"status/{job_id}.json"

    try:
        response = s3.get_object(Bucket=BUCKET_NAME, Key=key)
        content = response["Body"].read().decode("utf-8")
        return json.loads(content)

    except s3.exceptions.NoSuchKey:
        return {"job_id": job_id, "status": "not_found"}

    except Exception as e:
        return {
            "job_id": job_id,
            "status": "error",
            "detail": str(e)
        }
