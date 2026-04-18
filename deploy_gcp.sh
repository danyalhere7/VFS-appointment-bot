#!/bin/bash
# =============================================================================
#  VFS Global Appointment Bot — GCP Cloud Run Deployment Script
#
#  This script deploys the Dockerized bot to Google Cloud Platform as a 
#  serverless Cloud Run Job, scheduled to run via Google Cloud Scheduler.
#  
#  Prerequisites:
#  1. GCP Project created and billing enabled (Free Tier covered)
#  2. Google Cloud CLI (gcloud) installed and authenticated
#  3. Docker installed
# =============================================================================

# Exit immediately if a command exits with a non-zero status
set -e

# --- Configuration variables (Change these to your GCP project details) ---
PROJECT_ID="your-gcp-project-id"
REGION="us-central1"
SERVICE_NAME="vfs-appointment-bot"
IMAGE_URL="gcr.io/${PROJECT_ID}/${SERVICE_NAME}:latest"
JOB_NAME="vfs-bot-job"
SCHEDULER_JOB_NAME="vfs-bot-scheduler"

echo "🚀 Starting GCP Deployment for $SERVICE_NAME..."

# 1. Set GCP Project
gcloud config set project "$PROJECT_ID"
echo "✅ Project set to $PROJECT_ID"

# 2. Enable necessary Google Cloud APIs
echo "Enabling necessary APIs (Cloud Run, Cloud Scheduler, Cloud Build, Artifact Registry)..."
gcloud services enable \
    run.googleapis.com \
    cloudscheduler.googleapis.com \
    cloudbuild.googleapis.com \
    artifactregistry.googleapis.com
echo "✅ APIs enabled."

# 3. Build and push Docker image to Google Container Registry (GCR)
# (You can also use Artifact Registry if preferred)
echo "🐳 Building Docker image..."
# Use Cloud Build for the build step (or docker build locally)
gcloud builds submit --tag "$IMAGE_URL"
echo "✅ Image built and pushed to $IMAGE_URL"

# 4. Deploy as a Cloud Run Job (Serverless, scales to 0, cost-effective)
echo "☁️ Deploying Cloud Run Job..."
gcloud run jobs create "$JOB_NAME" \
    --image "$IMAGE_URL" \
    --region "$REGION" \
    --max-retries 1 \
    --task-timeout 10m \
    --set-env-vars="HEADLESS=true" \
    --set-secrets="VFS_EMAIL=VFS_EMAIL:latest,VFS_PASSWORD=VFS_PASSWORD:latest,EMAIL_SENDER=EMAIL_SENDER:latest,EMAIL_PASSWORD=EMAIL_PASSWORD:latest,EMAIL_RECEIVER=EMAIL_RECEIVER:latest"
# Assumes secrets are pre-created in Google Secret Manager. Adjust if using plain env vars.
echo "✅ Cloud Run Job $JOB_NAME created."

# 5. Create Cloud Scheduler trigger to run the job every 10 minutes
echo "⏱️ Creating Cloud Scheduler task..."
# Ensure App Engine default service account exists or specify a service account
gcloud scheduler jobs create http "$SCHEDULER_JOB_NAME" \
    --location "$REGION" \
    --schedule "*/10 * * * *" \
    --uri "https://${REGION}-run.googleapis.com/apis/run.googleapis.com/v1/namespaces/${PROJECT_ID}/jobs/${JOB_NAME}:run" \
    --http-method POST \
    --oauth-service-account-email "$(gcloud projects describe $PROJECT_ID --format=\"value(projectNumber)\")-compute@developer.gserviceaccount.com"
echo "✅ Cloud Scheduler job $SCHEDULER_JOB_NAME created."

echo "🎉 Deployment complete! The bot will now run every 10 minutes on GCP."
echo "View logs at: https://console.cloud.google.com/run/jobs/details/${REGION}/${JOB_NAME}/logs?project=${PROJECT_ID}"
