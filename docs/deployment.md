# Axiom Design Engine - Deployment Guide

## Quick Start (Docker Compose)

### Prerequisites
- Docker 24.0+
- Docker Compose v2+
- NVIDIA GPU with drivers (optional, for AI generation)
- NVIDIA Container Toolkit (optional, for GPU support)

### Local Development

1. **Clone and setup:**
   ```bash
   git clone https://github.com/your-org/axiom-engine.git
   cd axiom-engine
   ./scripts/dev-setup.sh
   ```

2. **Access services:**
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - API Docs: http://localhost:8000/docs
   - Adminer (DB): http://localhost:8080
   - Redis Commander: http://localhost:8081

3. **View logs:**
   ```bash
   docker compose logs -f backend
   docker compose logs -f worker-gpu
   ```

4. **Stop services:**
   ```bash
   docker compose down
   ```

### Production Deployment (Docker Compose)

1. **Configure environment:**
   ```bash
   cp .env.production.example .env
   # Edit .env with production values
   ```

2. **Generate secure secrets:**
   ```bash
   # JWT Secret
   openssl rand -hex 32
   
   # Worker API Key
   openssl rand -hex 32
   
   # Database password
   openssl rand -base64 24
   ```

3. **Deploy:**
   ```bash
   docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d
   ```

4. **Enable GPU workers:**
   ```bash
   docker compose -f docker-compose.yml -f docker-compose.prod.yml --profile gpu up -d
   ```

5. **Enable monitoring:**
   ```bash
   docker compose -f docker-compose.yml -f docker-compose.prod.yml --profile monitoring up -d
   ```

---

## Kubernetes Deployment

### Prerequisites
- Kubernetes 1.28+
- kubectl configured
- kustomize (or kubectl with kustomize support)
- NVIDIA GPU Operator (for GPU nodes)
- Ingress controller (nginx-ingress recommended)
- cert-manager (for TLS certificates)

### Cluster Preparation

1. **Install NVIDIA GPU Operator (if using GPUs):**
   ```bash
   helm repo add nvidia https://helm.ngc.nvidia.com/nvidia
   helm install --wait --generate-name \
     -n gpu-operator --create-namespace \
     nvidia/gpu-operator
   ```

2. **Label GPU nodes:**
   ```bash
   kubectl label nodes <gpu-node-name> gpu=true
   ```

3. **Install cert-manager:**
   ```bash
   kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.13.0/cert-manager.yaml
   ```

### Deployment Steps

1. **Build and push images:**
   ```bash
   ./scripts/build-docker.sh -r your-registry.com/axiom -t v1.0.0 -p all
   ```

2. **Configure secrets:**
   ```bash
   # Create secrets.env in k8s/overlays/production/
   cat > k8s/overlays/production/secrets.env << EOF
   POSTGRES_USER=axiom_prod
   POSTGRES_PASSWORD=$(openssl rand -base64 24)
   JWT_SECRET=$(openssl rand -hex 32)
   WORKER_API_KEY=$(openssl rand -hex 32)
   REDIS_PASSWORD=$(openssl rand -base64 16)
   EOF
   ```

3. **Update image references:**
   Edit `k8s/overlays/production/kustomization.yaml` with your registry.

4. **Deploy to staging:**
   ```bash
   ./scripts/deploy-k8s.sh staging
   ```

5. **Deploy to production:**
   ```bash
   ./scripts/deploy-k8s.sh production
   ```

6. **Verify deployment:**
   ```bash
   kubectl -n ai-platform get pods
   kubectl -n ai-platform get services
   kubectl -n ai-platform get ingress
   ```

### GPU Worker Scaling

For GPU workers, use manual scaling or KEDA:

```bash
# Scale GPU workers manually
kubectl -n ai-platform scale deployment axiom-worker-gpu --replicas=2
```

---

## Configuration Reference

### Environment Variables

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `DATABASE_URL` | PostgreSQL connection string | Yes | - |
| `REDIS_URL` | Redis connection string | Yes | - |
| `JWT_SECRET` | Secret for JWT signing | Yes | - |
| `STORAGE_BACKEND` | `local` or `s3` | No | `local` |
| `STORAGE_PATH` | Path for local storage | No | `/data/axiom-storage` |
| `COMFYUI_ENDPOINT` | ComfyUI server URL | Yes | `http://localhost:8188` |
| `WORKER_API_KEY` | Internal API authentication | Yes | - |

### Storage Configuration

**Local Storage:**
```env
STORAGE_BACKEND=local
STORAGE_PATH=/data/axiom-storage
```

**S3 Storage:**
```env
STORAGE_BACKEND=s3
S3_ENDPOINT_URL=https://s3.amazonaws.com
S3_ACCESS_KEY=your-key
S3_SECRET_KEY=your-secret
S3_BUCKET_NAME=axiom-assets
S3_REGION=us-east-1
```

### GPU Requirements

- NVIDIA GPU with 12GB+ VRAM recommended
- CUDA 12.1 compatible drivers
- nvidia-container-toolkit installed

Verify GPU access:
```bash
docker run --rm --gpus all nvidia/cuda:12.1.0-base-ubuntu22.04 nvidia-smi
```

---

## Health Checks

### Docker Compose
```bash
./scripts/health-check.sh
```

### Kubernetes
```bash
kubectl -n ai-platform get pods
kubectl -n ai-platform describe pod <pod-name>
kubectl -n ai-platform logs <pod-name>
```

### Endpoints
- Backend health: `GET /api/v1/health`
- Backend ready: `GET /api/v1/ready`
- ComfyUI status: `GET /system_stats`

---

## Monitoring

### Prometheus Metrics

Metrics available at `/metrics`:
- `axiom_jobs_total` - Total jobs by type and status
- `axiom_job_execution_time_seconds` - Job execution histogram
- `axiom_gpu_memory_usage_bytes` - GPU memory usage
- `http_requests_total` - HTTP request count

### Grafana Dashboards

Access Grafana at http://localhost:3001 (default: admin/admin)

Pre-configured dashboards:
- Axiom Engine Overview
- GPU Utilization
- Job Queue Status

---

## Troubleshooting

### Common Issues

**Container won't start:**
```bash
docker compose logs <service>
docker inspect <container-id>
```

**GPU not detected:**
```bash
# Check NVIDIA drivers
nvidia-smi

# Check container toolkit
docker run --rm --gpus all nvidia/cuda:12.1.0-base-ubuntu22.04 nvidia-smi
```

**Database connection failed:**
```bash
# Check PostgreSQL
docker exec axiom-db pg_isready -U axiom

# Check connection string
docker exec axiom-backend env | grep DATABASE_URL
```

**Redis connection failed:**
```bash
docker exec axiom-redis redis-cli ping
```

### Logs

```bash
# All services
docker compose logs -f

# Specific service
docker compose logs -f backend

# Kubernetes
kubectl -n ai-platform logs -f deployment/axiom-backend
```

---

## Security Checklist

- [ ] Change all default passwords
- [ ] Generate strong JWT secret (32+ bytes)
- [ ] Enable HTTPS/TLS in production
- [ ] Configure network policies
- [ ] Use secrets manager for sensitive data
- [ ] Enable rate limiting
- [ ] Review CORS configuration
- [ ] Set up backup for PostgreSQL
