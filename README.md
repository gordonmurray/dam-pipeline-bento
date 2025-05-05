# dam-pipeline

A decoupled, async processing pipeline for digital asset management using FastAPI, RabbitMQ, Cloudflare R2, and PyTorch models for image analysis.

## Overview

This project consists of two components:

- **Producer (FastAPI)**: Accepts image uploads, stores them in Cloudflare R2, and queues metadata to RabbitMQ.
- **Worker (Python)**: Consumes messages from the queue, downloads the image from R2, generates a BLIP-based image caption, vectorizes it using CLIP, and appends metadata to a Parquet file on R2.

## Technologies

- Python 3.11 & FastAPI
- RabbitMQ (via CloudAMQP)
- Cloudflare R2 (S3-compatible storage)
- CLIP (image vectorization)
- BLIP (image captioning)
- Parquet via pandas/pyarrow

## Architecture

[Client] → [FastAPI Producer] → [RabbitMQ] → [Worker] → [R2: assets + metadata + vectors]

## Environment Variables (secrets)

Set these using `fly secrets set` for both apps:

```
fly secrets set \
  R2_ENDPOINT="https://00000.r2.cloudflarestorage.com" \
  R2_ACCESS_KEY_ID="00000" \
  R2_SECRET_ACCESS_KEY="00000" \
  R2_BUCKET="my-bucket" \
  AMQP_URL="amqps://00000@seal.lmq.cloudamqp.com/"
```

## Deployment

This project is intended to be deployed to Fly.io. Each component has its own Dockerfile.

### Producer

```
fly apps create dam-producer
fly -a dam-producer deploy
```

### Worker

```
fly apps create dam-worker
fly -a dam-worker deploy
```


## Test Upload

```bash
curl -X POST https://dam-producer.fly.dev/upload \
  -F "file=@/path/to/image.jpg"
```

## Output

* assets/{uuid}.jpg — original uploaded file
* vectors/{uuid}.json — CLIP embedding
* metadata/assets.parquet — appended metadata for each file

An example of the resulting meta data:

```
{
  "id": "b227facd-7e87-4988-9a64-6f728123f79c",
  "filename": "image.jpg",
  "r2_key": "assets/b227facd-7e87-4988-9a64-6f728123f79c.jpg",
  "vector_key": "vectors/b227facd-7e87-4988-9a64-6f728123f79c.json",
  "mime_type": "image/jpeg",
  "caption": "a golf ball on the tee at the golf course"
}
```