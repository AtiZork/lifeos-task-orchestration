# GCP Deployment Guide

This guide provides step-by-step instructions for deploying the LifeOS Task Orchestration Service to Google Cloud Platform (GCP).

## Prerequisites

Before starting, ensure you have:

1. **GCP Account** with billing enabled
2. **gcloud CLI** installed and configured ([Install Guide](https://cloud.google.com/sdk/docs/install))
3. **Docker** installed locally ([Install Guide](https://docs.docker.com/get-docker/))
4. **A GCP Project** created in the Google Cloud Console

## Quick Deployment

### 1. Set Environment Variables

```bash
export PROJECT_ID="your-gcp-project-id"
export REGION="us-central1"
export SERVICE_NAME="lifeos-task-orchestration"
```

### 2. Authenticate with GCP

```bash
# Login to GCP
gcloud auth login

# Set the active project
gcloud config set project $PROJECT_ID
```

### 3. Enable Required APIs

```bash
gcloud services enable \
  run.googleapis.com \
  cloudbuild.googleapis.com \
  containerregistry.googleapis.com \
  logging.googleapis.com \
  monitoring.googleapis.com
```

### 4. Build and Deploy

```bash
# Build the container image
gcloud builds submit --tag gcr.io/$PROJECT_ID/$SERVICE_NAME

# Deploy to Cloud Run
gcloud run deploy $SERVICE_NAME \
  --image gcr.io/$PROJECT_ID/$SERVICE_NAME \
  --platform managed \
  --region $REGION \
  --allow-unauthenticated \
  --min-instances 0 \
  --max-instances 10 \
  --cpu 1 \
  --memory 512Mi \
  --timeout 300 \
  --concurrency 80 \
  --set-env-vars="ENVIRONMENT=production,LOG_LEVEL=INFO"
```

### 5. Get Service URL

```bash
gcloud run services describe $SERVICE_NAME \
  --region $REGION \
  --format 'value(status.url)'
```

### 6. Test Deployment

```bash
# Save service URL
SERVICE_URL=$(gcloud run services describe $SERVICE_NAME \
  --region $REGION \
  --format 'value(status.url)')

# Test health endpoint
curl $SERVICE_URL/api/v1/health

# Test task creation
curl -X POST $SERVICE_URL/api/v1/tasks \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Test deployment task",
    "description": "Verify Cloud Run deployment is working",
    "priority": "high"
  }'
```

## Production Deployment Checklist

### Security

- [ ] Enable authentication (Cloud Identity, Firebase Auth, or API keys)
- [ ] Use Secret Manager for sensitive configuration
- [ ] Restrict Cloud Run ingress to internal traffic only (if applicable)
- [ ] Set up VPC Service Controls for added security

### Observability

- [ ] Configure Cloud Logging filters
- [ ] Set up log-based metrics
- [ ] Create Cloud Monitoring dashboards
- [ ] Configure alerting policies

### Performance

- [ ] Enable Cloud CDN for static assets (if any)
- [ ] Configure Cloud Run min instances based on traffic patterns
- [ ] Set appropriate CPU and memory allocation
- [ ] Enable HTTP/2 for better performance

### Cost Optimization

- [ ] Set max instances to prevent runaway costs
- [ ] Use min instances = 0 for dev/staging environments
- [ ] Configure request timeout appropriately
- [ ] Monitor and optimize cold start times

## Advanced Configuration

### Using Cloud Firestore for Persistence

```bash
# Enable Firestore API
gcloud services enable firestore.googleapis.com

# Create Firestore database
gcloud firestore databases create \
  --location=$REGION \
  --type=firestore-native

# Update Cloud Run with Firestore config
gcloud run services update $SERVICE_NAME \
  --region $REGION \
  --set-env-vars="USE_FIRESTORE=true,FIRESTORE_PROJECT=$PROJECT_ID"
```

### Using Cloud Pub/Sub for Async Processing

```bash
# Create Pub/Sub topic
gcloud pubsub topics create workflow-execution-tasks

# Create subscription
gcloud pubsub subscriptions create workflow-execution-sub \
  --topic workflow-execution-tasks

# Update Cloud Run
gcloud run services update $SERVICE_NAME \
  --region $REGION \
  --set-env-vars="USE_PUBSUB=true,PUBSUB_TOPIC=workflow-execution-tasks"
```

### CI/CD with Cloud Build

1. **Connect your GitHub repository** to Cloud Build
2. **Create a trigger** in the Cloud Build console
3. **Cloud Build will automatically**:
   - Build the Docker image on every push
   - Deploy to Cloud Run
   - Run tests before deployment

See `cloudbuild.yaml` in the repository for the build configuration.

## Monitoring and Logging

### View Logs

```bash
# Real-time logs
gcloud logging tail "resource.type=cloud_run_revision AND resource.labels.service_name=$SERVICE_NAME"

# Recent logs
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=$SERVICE_NAME" \
  --limit 50 \
  --format json
```

### Create Log-Based Metrics

```bash
# Task creation metric
gcloud logging metrics create task_creation_count \
  --description="Count of task creation requests" \
  --log-filter='resource.type="cloud_run_revision" AND jsonPayload.message=~"Task created"'

# Workflow execution metric
gcloud logging metrics create workflow_execution_count \
  --description="Count of workflow executions" \
  --log-filter='resource.type="cloud_run_revision" AND jsonPayload.message=~"Workflow execution"'
```

### Set Up Alerts

```bash
# Create an alert policy for high error rates
gcloud alpha monitoring policies create \
  --notification-channels=YOUR_CHANNEL_ID \
  --display-name="High Error Rate Alert" \
  --condition-threshold-value=10 \
  --condition-threshold-duration=60s \
  --condition-display-name="Error rate > 10/min"
```

## Troubleshooting

### Common Issues

**Issue**: Service fails to start
- Check logs: `gcloud logging read ...`
- Verify environment variables are set correctly
- Ensure Docker image was built successfully

**Issue**: Slow cold starts
- Increase memory allocation (more memory = faster CPU)
- Set min instances to 1 for production
- Optimize Docker image size

**Issue**: Request timeouts
- Increase timeout in Cloud Run configuration
- Check agent timeout settings
- Optimize workflow execution times

### Health Checks

Cloud Run automatically performs health checks on your service. The service provides:

- `/api/v1/health` - Basic health check
- `/api/v1/ready` - Readiness check

## Scaling Configuration

### Auto-scaling

Cloud Run automatically scales based on:
- Incoming request volume
- CPU utilization
- Memory usage
- Concurrency settings

### Recommended Settings

| Environment | Min Instances | Max Instances | Concurrency | Memory |
|-------------|---------------|---------------|-------------|--------|
| Development | 0             | 3             | 80          | 512Mi  |
| Staging     | 0             | 5             | 80          | 512Mi  |
| Production  | 1             | 10            | 100         | 1Gi    |

## Cost Estimation

Cloud Run pricing is based on:
- Request volume
- CPU and memory allocation
- Execution time

**Example** (us-central1):
- 1M requests/month
- Average 200ms execution time
- 512MB memory, 1 vCPU
- **Cost**: ~$5-10/month

Use the [GCP Pricing Calculator](https://cloud.google.com/products/calculator) for accurate estimates.

## Cleanup

To remove all resources:

```bash
# Delete Cloud Run service
gcloud run services delete $SERVICE_NAME --region $REGION

# Delete container images
gcloud container images delete gcr.io/$PROJECT_ID/$SERVICE_NAME --quiet

# Delete Pub/Sub resources (if created)
gcloud pubsub subscriptions delete workflow-execution-sub
gcloud pubsub topics delete workflow-execution-tasks

# Delete Firestore database (if created)
gcloud firestore databases delete --database="(default)"
```

## Next Steps

- Set up custom domain with Cloud Run
- Implement authentication with Cloud Identity
- Add Cloud Armor for DDoS protection
- Configure Cloud CDN for better performance
- Set up multi-region deployment
- Implement blue-green deployments

## Support

For issues related to:
- **Cloud Run**: [GCP Documentation](https://cloud.google.com/run/docs)
- **This service**: See README.md for architecture and API documentation
