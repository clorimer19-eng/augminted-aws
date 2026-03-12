#!/bin/bash

# Configuration
export PATH=$PATH:/Users/chrislorimer/Downloads/google-cloud-sdk/bin
# Load .env
if [ -f .env ]; then
  export $(cat .env | xargs)
fi

PROJECT_ID="augminted"
REGION="us-central1"
SERVICE_NAME="augminted-v1"
REPO_NAME="augminted-repo"

# Enable APIs
echo "Enabling APIs..."
gcloud services enable artifactregistry.googleapis.com run.googleapis.com cloudbuild.googleapis.com

# Create Artifact Registry Repo (if not exists)
echo "Creating Artifact Registry..."
gcloud artifacts repositories create $REPO_NAME \
    --repository-format=docker \
    --location=$REGION \
    --description="Augminted Docker Repo" || true

# Build and Push
echo "Building and Pushing Container..."
gcloud builds submit --tag $REGION-docker.pkg.dev/$PROJECT_ID/$REPO_NAME/$SERVICE_NAME .

# Deploy to Cloud Run
echo "Deploying to Cloud Run..."
gcloud run deploy $SERVICE_NAME \
    --image $REGION-docker.pkg.dev/$PROJECT_ID/$REPO_NAME/$SERVICE_NAME \
    --platform managed \
    --region $REGION \
    --allow-unauthenticated \
    --memory 4Gi \
    --cpu 2 \
    --timeout 3600 \
    --set-env-vars TRIPO_API_KEY=$TRIPO_API_KEY

echo "Deployment Complete!"
echo "Service URL:"
gcloud run services describe $SERVICE_NAME --platform managed --region $REGION --format 'value(status.url)'
