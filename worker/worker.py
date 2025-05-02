import boto3, os, json, asyncio
import aio_pika
from io import BytesIO
import pandas as pd
from PIL import Image
import torch
from transformers import CLIPProcessor, CLIPModel, BlipProcessor, BlipForConditionalGeneration

R2_BUCKET = os.getenv("R2_BUCKET")
R2_ENDPOINT = os.getenv("R2_ENDPOINT")
R2_KEY = os.getenv("R2_ACCESS_KEY_ID")
R2_SECRET = os.getenv("R2_SECRET_ACCESS_KEY")
AMQP_URL = os.getenv("AMQP_URL")
METADATA_KEY = "metadata/assets.parquet"
VECTOR_DIR = "vectors"

s3 = boto3.client(
    "s3",
    endpoint_url=R2_ENDPOINT,
    aws_access_key_id=R2_KEY,
    aws_secret_access_key=R2_SECRET,
)

clip_model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32")
clip_processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")

blip_processor = BlipProcessor.from_pretrained("Salesforce/blip-image-captioning-base")
blip_model = BlipForConditionalGeneration.from_pretrained("Salesforce/blip-image-captioning-base")

async def handle(msg: aio_pika.IncomingMessage):
    async with msg.process():
        payload = json.loads(msg.body)
        print(f"Processing: {payload['id']}")

        # Download image from R2
        obj = s3.get_object(Bucket=R2_BUCKET, Key=payload["r2_key"])
        img = Image.open(BytesIO(obj["Body"].read())).convert("RGB")

        # Generate vector with CLIP
        inputs = clip_processor(images=img, return_tensors="pt")
        with torch.no_grad():
            embeddings = clip_model.get_image_features(**inputs)
        vector = embeddings[0].tolist()

        # Generate caption with BLIP
        blip_inputs = blip_processor(images=img, return_tensors="pt")
        with torch.no_grad():
            caption_ids = blip_model.generate(**blip_inputs)
        caption = blip_processor.decode(caption_ids[0], skip_special_tokens=True)

        # Save vector to R2
        vector_key = f"{VECTOR_DIR}/{payload['id']}.json"
        s3.put_object(
            Bucket=R2_BUCKET,
            Key=vector_key,
            Body=json.dumps(vector).encode("utf-8"),
            ContentType="application/json",
        )

        # Update metadata with caption
        meta = pd.DataFrame([{
            "id": payload["id"],
            "filename": payload["filename"],
            "r2_key": payload["r2_key"],
            "vector_key": vector_key,
            "mime_type": payload["mime_type"],
            "caption": caption
        }])

        try:
            existing = s3.get_object(Bucket=R2_BUCKET, Key=METADATA_KEY)
            existing_df = pd.read_parquet(BytesIO(existing["Body"].read()))
            combined = pd.concat([existing_df, meta], ignore_index=True)
        except s3.exceptions.NoSuchKey:
            combined = meta

        buf = BytesIO()
        combined.to_parquet(buf, engine="pyarrow", index=False)
        buf.seek(0)

        s3.put_object(
            Bucket=R2_BUCKET,
            Key=METADATA_KEY,
            Body=buf.getvalue(),
            ContentType="application/octet-stream"
        )

async def main():
    print("Boot: connecting to AMQP...")
    connection = await aio_pika.connect_robust(AMQP_URL)
    print("Connected. Getting channel...")
    channel = await connection.channel()
    print("Channel ready. Declaring queue...")
    queue = await channel.declare_queue("uploads", durable=True)
    print("Queue declared. Waiting for messages...")
    await queue.consume(handle)
    print("Worker is consuming...")
    await asyncio.Event().wait()

if __name__ == "__main__":
    asyncio.run(main())
