# ── Monopoly AI Agents — GCP Cloud Run Makefile ──

PROJECT_ID   := ai-monopoly-487405
REGION       := us-central1
BACKEND_SVC  := monopoly-backend
FRONTEND_SVC := monopoly-frontend
SECRET_NAME  := google-api-key

GCLOUD := gcloud --project $(PROJECT_ID)

# Resolve backend URL (used by frontend build and CORS update)
BACKEND_URL = $(shell $(GCLOUD) run services describe $(BACKEND_SVC) --region $(REGION) --format='value(status.url)' 2>/dev/null)
FRONTEND_URL = $(shell $(GCLOUD) run services describe $(FRONTEND_SVC) --region $(REGION) --format='value(status.url)' 2>/dev/null)

.PHONY: help deploy deploy-backend deploy-frontend setup-secret cors logs-backend logs-frontend status urls destroy

help: ## Show available commands
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'

# ── Full deployment ──

deploy: deploy-backend deploy-frontend cors ## Deploy everything (backend → frontend → CORS)
	@echo ""
	@echo "=== Deployment Complete ==="
	@echo "Frontend: $(FRONTEND_URL)"
	@echo "Backend:  $(BACKEND_URL)"
	@echo "API Docs: $(BACKEND_URL)/docs"

# ── Individual targets ──

setup-secret: ## Create GOOGLE_API_KEY in Secret Manager
	@if ! $(GCLOUD) secrets describe $(SECRET_NAME) --quiet 2>/dev/null; then \
		read -rp "Enter your GOOGLE_API_KEY: " key && \
		echo -n "$$key" | $(GCLOUD) secrets create $(SECRET_NAME) --data-file=- --quiet && \
		echo "Secret created."; \
	else \
		echo "Secret '$(SECRET_NAME)' already exists."; \
	fi
	@PROJECT_NUMBER=$$($(GCLOUD) projects describe $(PROJECT_ID) --format='value(projectNumber)') && \
	$(GCLOUD) secrets add-iam-policy-binding $(SECRET_NAME) \
		--member="serviceAccount:$${PROJECT_NUMBER}-compute@developer.gserviceaccount.com" \
		--role="roles/secretmanager.secretAccessor" \
		--quiet > /dev/null 2>&1 || true

deploy-backend: setup-secret ## Build & deploy backend to Cloud Run
	@echo ">>> Deploying backend..."
	$(GCLOUD) run deploy $(BACKEND_SVC) \
		--source backend/ \
		--region $(REGION) \
		--platform managed \
		--allow-unauthenticated \
		--port 8080 \
		--memory 512Mi \
		--timeout 300 \
		--set-secrets="GOOGLE_API_KEY=$(SECRET_NAME):latest" \
		--quiet
	@echo "Backend: $(BACKEND_URL)"

deploy-frontend: ## Build & deploy frontend to Cloud Run (requires backend to be deployed first)
	@if [ -z "$(BACKEND_URL)" ]; then echo "ERROR: Backend not deployed yet. Run 'make deploy-backend' first." && exit 1; fi
	@echo ">>> Deploying frontend..."
	$(GCLOUD) run deploy $(FRONTEND_SVC) \
		--source frontend/ \
		--region $(REGION) \
		--platform managed \
		--allow-unauthenticated \
		--port 3000 \
		--memory 512Mi \
		--set-env-vars="HOSTNAME=0.0.0.0" \
		--set-build-env-vars="NEXT_PUBLIC_API_URL=$(BACKEND_URL)/api,NEXT_PUBLIC_WS_URL=$(subst https://,wss://,$(BACKEND_URL))" \
		--quiet
	@echo "Frontend: $(FRONTEND_URL)"

cors: ## Update backend CORS with the frontend URL
	@if [ -z "$(FRONTEND_URL)" ]; then echo "ERROR: Frontend not deployed yet." && exit 1; fi
	@echo ">>> Updating backend CORS..."
	$(GCLOUD) run services update $(BACKEND_SVC) \
		--region $(REGION) \
		--set-env-vars="CORS_ORIGINS=$(FRONTEND_URL)" \
		--quiet
	@echo "CORS updated to allow $(FRONTEND_URL)"

# ── Operations ──

logs-backend: ## Tail backend logs
	$(GCLOUD) run logs read $(BACKEND_SVC) --region $(REGION) --limit 50

logs-frontend: ## Tail frontend logs
	$(GCLOUD) run logs read $(FRONTEND_SVC) --region $(REGION) --limit 50

status: ## Show Cloud Run service status
	@echo "=== Backend ==="
	@$(GCLOUD) run services describe $(BACKEND_SVC) --region $(REGION) --format='table(status.url, status.conditions.type, status.conditions.status)' 2>/dev/null || echo "  Not deployed"
	@echo ""
	@echo "=== Frontend ==="
	@$(GCLOUD) run services describe $(FRONTEND_SVC) --region $(REGION) --format='table(status.url, status.conditions.type, status.conditions.status)' 2>/dev/null || echo "  Not deployed"

urls: ## Print service URLs
	@echo "Frontend: $(FRONTEND_URL)"
	@echo "Backend:  $(BACKEND_URL)"
	@echo "API Docs: $(BACKEND_URL)/docs"

destroy: ## Delete both Cloud Run services (requires confirmation)
	@read -rp "Delete both services? [y/N] " confirm && [ "$$confirm" = "y" ] || exit 1
	$(GCLOUD) run services delete $(BACKEND_SVC) --region $(REGION) --quiet || true
	$(GCLOUD) run services delete $(FRONTEND_SVC) --region $(REGION) --quiet || true
	@echo "Services deleted."
