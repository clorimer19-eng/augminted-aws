# Augminted Cloud Deployment Guide

## Prerequisites
1.  **Google Cloud Project**: `augminted` (Billing Enabled).
2.  **Google Cloud CLI**: Installed and authenticated (`gcloud auth login`).
3.  **Tripo API Key**: You need your key ready.

## 1. Setup Environment
Open your terminal and run:
```bash
export PROJECT_ID="augminted"
export REGION="us-central1"
export TRIPO_API_KEY="your-tripo-key-here"
```

## 2. Deploy
Run the deployment script:
```bash
chmod +x deploy.sh
./deploy.sh
```
This will:
1.  Enable necessary Google Cloud APIs.
2.  Create a Docker repository in Artifact Registry.
3.  Build the Docker image (Python + Blender) and push it.
4.  Deploy the service to Cloud Run (Gen 2).

## 3. Usage
Once deployed, you can trigger a job via HTTP POST:

**Endpoint:** `https://<your-service-url>/run_job`

**Payload:**
```json
{
  "job_id": "test_job_01",
  "category": "table",
  "input_url": "gs://your-input-bucket/table.jpg",
  "output_bucket": "your-output-bucket"
}
```

## 4. Architecture
*   **Compute**: Cloud Run (Serverless Container).
*   **Storage**: Google Cloud Storage (Inputs/Outputs).
*   **Queue**: (Optional) Use Cloud Tasks to trigger the `/run_job` endpoint for async processing.
