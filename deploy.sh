#!/usr/bin/env bash
set -euo pipefail

# ── Configuration ──
PROJECT_ID="ai-monopoly-487405"
REGION="us-central1"
BACKEND_SERVICE="monopoly-backend"
FRONTEND_SERVICE="monopoly-frontend"
SECRET_NAME="google-api-key"

echo "=== Monopoly AI Agents — GCP Cloud Run Deployment ==="
echo "Project:  $PROJECT_ID"
echo "Region:   $REGION"
echo ""

gcloud config set project "$PROJECT_ID"

# ── 1. Enable required APIs ──
echo ">>> Enabling required APIs..."
gcloud services enable \
  run.googleapis.com \
  cloudbuild.googleapis.com \
  secretmanager.googleapis.com \
  artifactregistry.googleapis.com \
  --quiet

# ── 2. Set up Secret Manager ──
echo ">>> Setting up Secret Manager secret: $SECRET_NAME"
if ! gcloud secrets describe "$SECRET_NAME" --quiet 2>/dev/null; then
  # Prompt for the key if creating for the first time
  read -rp "Enter your GOOGLE_API_KEY: " GOOGLE_API_KEY
  echo -n "$GOOGLE_API_KEY" | gcloud secrets create "$SECRET_NAME" --data-file=- --quiet
  echo "    Secret created."
else
  echo "    Secret already exists. To update: gcloud secrets versions add $SECRET_NAME --data-file=-"
fi

# Grant Cloud Run access to the secret
PROJECT_NUMBER=$(gcloud projects describe "$PROJECT_ID" --format='value(projectNumber)')
COMPUTE_SA="${PROJECT_NUMBER}-compute@developer.gserviceaccount.com"
gcloud secrets add-iam-policy-binding "$SECRET_NAME" \
  --member="serviceAccount:${COMPUTE_SA}" \
  --role="roles/secretmanager.secretAccessor" \
  --quiet > /dev/null 2>&1 || true

# ── 3. Deploy Backend ──
echo ""
echo ">>> Building & deploying backend..."
gcloud run deploy "$BACKEND_SERVICE" \
  --source backend/ \
  --region "$REGION" \
  --platform managed \
  --allow-unauthenticated \
  --port 8080 \
  --memory 512Mi \
  --timeout 300 \
  --set-secrets="GOOGLE_API_KEY=${SECRET_NAME}:latest" \
  --quiet

BACKEND_URL=$(gcloud run services describe "$BACKEND_SERVICE" \
  --region "$REGION" --format='value(status.url)')
echo "    Backend deployed: $BACKEND_URL"

# ── 4. Deploy Frontend ──
echo ""
echo ">>> Building & deploying frontend..."

# WebSocket URL: replace https:// with wss://
WS_URL="${BACKEND_URL/https:\/\//wss:\/\/}"

gcloud run deploy "$FRONTEND_SERVICE" \
  --source frontend/ \
  --region "$REGION" \
  --platform managed \
  --allow-unauthenticated \
  --port 3000 \
  --memory 512Mi \
  --set-env-vars="HOSTNAME=0.0.0.0" \
  --set-build-env-vars="NEXT_PUBLIC_API_URL=${BACKEND_URL}/api,NEXT_PUBLIC_WS_URL=${WS_URL}" \
  --quiet

FRONTEND_URL=$(gcloud run services describe "$FRONTEND_SERVICE" \
  --region "$REGION" --format='value(status.url)')
echo "    Frontend deployed: $FRONTEND_URL"

# ── 5. Update Backend CORS with Frontend URL ──
echo ""
echo ">>> Updating backend CORS to allow frontend origin..."
gcloud run services update "$BACKEND_SERVICE" \
  --region "$REGION" \
  --set-env-vars="CORS_ORIGINS=${FRONTEND_URL}" \
  --quiet

# ── Done ──
echo ""
echo "=== Deployment Complete ==="
echo "Frontend: $FRONTEND_URL"
echo "Backend:  $BACKEND_URL"
echo "API Docs: $BACKEND_URL/docs"
echo ""
echo "To view logs:"
echo "  gcloud run logs read $BACKEND_SERVICE --region $REGION --project $PROJECT_ID"
echo "  gcloud run logs read $FRONTEND_SERVICE --region $REGION --project $PROJECT_ID"
