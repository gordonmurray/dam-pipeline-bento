# dam-pipeline-bento

A decoupled, async processing pipeline for digital asset management using FastAPI, RabbitMQ, Cloudflare R2, and BentoML + CLIP for image vectorization.

## Overview

This project consists of two components:

- **Producer (FastAPI)**: Accepts image uploads, stores them in Cloudflare R2, and queues metadata to RabbitMQ.
- **Worker (Python)**: Consumes messages from the queue, downloads the image from R2, vectorizes it using CLIP via BentoML, and appends metadata to a Parquet file on R2.

## Technologies

- Python 3.11
- FastAPI
- RabbitMQ (via CloudAMQP)
- Cloudflare R2 (S3-compatible storage)
- BentoML + CLIP (image vectorization)
- Parquet via pandas/pyarrow

## Architecture

[Client] → [FastAPI Producer] → [RabbitMQ] → [Worker] → [R2: assets + metadata + vectors]


## Environment Variables (secrets)

Set these using `fly secrets set` for both apps:

- `R2_ENDPOINT`: Cloudflare R2 endpoint URL
- `R2_ACCESS_KEY_ID`: Access key ID for R2
- `R2_SECRET_ACCESS_KEY`: Secret key for R2
- `R2_BUCKET`: Bucket name used for storing assets and metadata
- `AMQP_URL`: Full RabbitMQ URL (e.g. from CloudAMQP)

## Deployment

This project is intended to be deployed to [Fly.io](https://fly.io). Each component has its own `Dockerfile`.

### Producer

```
fly -a dam-producer deploy
```


### Worker


## Test Upload

```bash
curl -X POST https://dam-producer.fly.dev/upload \
  -F "file=@/path/to/image.jpg"
```

## Output

* assets/{uuid}.jpg — original uploaded file
* vectors/{uuid}.json — CLIP embedding
* metadata/assets.parquet — appended metadata for each file

