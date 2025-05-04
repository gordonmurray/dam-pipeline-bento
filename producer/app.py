from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
import boto3, uuid, os
import aio_pika

app = FastAPI()

R2_BUCKET = os.getenv("R2_BUCKET")
R2_ENDPOINT = os.getenv("R2_ENDPOINT")
R2_KEY = os.getenv("R2_ACCESS_KEY_ID")
R2_SECRET = os.getenv("R2_SECRET_ACCESS_KEY")
AMQP_URL = os.getenv("AMQP_URL")

s3 = boto3.client(
    "s3",
    endpoint_url=R2_ENDPOINT,
    aws_access_key_id=R2_KEY,
    aws_secret_access_key=R2_SECRET,
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/upload")
async def upload(file: UploadFile = File(...)):
    file_bytes = await file.read()
    file_id = str(uuid.uuid4())
    ext = os.path.splitext(file.filename)[-1]
    r2_key = f"assets/{file_id}{ext}"

    # Upload to R2
    s3.put_object(
        Bucket=R2_BUCKET,
        Key=r2_key,
        Body=file_bytes,
        ContentType=file.content_type,
    )

    # Push message to RabbitMQ
    connection = await aio_pika.connect_robust(AMQP_URL)
    channel = await connection.channel()
    await channel.default_exchange.publish(
        aio_pika.Message(
            body=(
                f'{{"id":"{file_id}","filename":"{file.filename}","r2_key":"{r2_key}","mime_type":"{file.content_type}"}}'
            ).encode()
        ),
        routing_key="uploads"
    )

    await connection.close()
    return {"message": "Queued for processing", "id": file_id}
