# QnA Agent API

A production-ready question-answering agent API built with FastAPI, LiteLLM, and OpenAI function calling.

## Features

- **Chat Management**: Create, list, update, and delete chat sessions
- **AI-Powered Responses**: Uses OpenAI function calling via LiteLLM
- **Knowledge Base**: File-based knowledge retrieval with search capabilities
- **Real-time Updates**: Server-Sent Events (SSE) for live notifications
- **LLM Observability**: Langfuse integration for tracing and monitoring
- **Production Ready**: Docker, Kubernetes, Terraform for Hetzner Cloud

## Tech Stack

| Component | Technology |
|-----------|------------|
| Framework | FastAPI |
| Python | 3.14+ |
| LLM Client | LiteLLM |
| LLM Provider | OpenRouter |
| Database (Dev) | SQLite + aiosqlite |
| Database (Prod) | PostgreSQL + PgBouncer |
| ORM | SQLAlchemy 2.0 + Alembic |
| Observability | Langfuse |
| Logging | Loguru |
| Reverse Proxy | Traefik v3.6.4 |
| IaC | Terraform |
| Cloud | Hetzner Cloud |

## Quick Start

### Prerequisites

- Python 3.14+
- [uv](https://docs.astral.sh/uv/) package manager
- OpenRouter API key (get one at https://openrouter.ai/)
- Optional: Langfuse account for LLM observability

### Installation

```bash
# Clone the repository
git clone https://github.com/evrone/evrone-qna-agent.git
cd evrone-qna-agent

# Copy environment file and configure
cp .env.example .env.local
# Edit .env.local with your API keys

# Install dependencies and run
make dev
make local
```

### Environment Variables

```env
# Required
LITELLM_API_KEY=sk-or-v1-your-key
DATABASE_URL=sqlite+aiosqlite:///./data/qna.db

# Optional - Langfuse observability
LANGFUSE_PUBLIC_KEY=pk-lf-xxx
LANGFUSE_SECRET_KEY=sk-lf-xxx
```

## API Endpoints

### Chat Sessions

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/chats` | Create a new chat |
| GET | `/api/v1/chats` | List all chats (paginated) |
| GET | `/api/v1/chats/{id}` | Get chat details |
| PATCH | `/api/v1/chats/{id}` | Update chat |
| DELETE | `/api/v1/chats/{id}` | Delete chat |

### Messages

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/chats/{id}/messages` | Get message history |
| POST | `/api/v1/chats/{id}/messages` | Send message, get AI response |

### Events (SSE)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/chats/{id}/events` | Subscribe to real-time updates |

### Health

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Basic health check |
| GET | `/health/live` | Liveness probe |
| GET | `/health/ready` | Readiness probe |

## Usage Example

```bash
# Create a chat
curl -X POST http://localhost:8000/api/v1/chats \
  -H "Content-Type: application/json" \
  -d '{"title": "My Chat"}'

# Send a message (replace {chat_id} with actual ID)
curl -X POST http://localhost:8000/api/v1/chats/{chat_id}/messages \
  -H "Content-Type: application/json" \
  -d '{"content": "What documents are in the knowledge base?"}'
```

## Development

### Available Commands

```bash
make help      # Show all commands
make dev       # Install dependencies
make local     # Run development server
make test      # Run tests
make lint      # Run linting
make format    # Format code
make migrate   # Run database migrations
```

### CI/CD

GitHub Actions workflows for automated quality checks and deployment.

**Setup pre-commit hooks:**
```bash
uv sync
pre-commit install
```

**GitHub Secrets required for deployment:**
- `K3S_SERVER_IP` - Server IP address
- `K3S_SERVER_SSH_KEY` - SSH private key (PEM format)

**Workflows:**
| Workflow | Trigger | Description |
|----------|---------|-------------|
| PR Checks | PR / push to main | Format, lint, type check, security, tests |
| Build Validation | Dockerfile changes | Docker build verification |
| Deploy | Manual | SSH deploy to k3s server |

### Project Structure

```
evrone-qna-agent/
├── src/qna_agent/           # Application source
│   ├── chats/               # Chat domain
│   ├── messages/            # Messages domain
│   ├── agent/               # LLM agent domain
│   ├── knowledge/           # Knowledge base domain
│   ├── events/              # SSE events domain
│   ├── health/              # Health checks
│   ├── main.py              # FastAPI app
│   ├── config.py            # Settings
│   └── database.py          # Database setup
├── tests/                   # Test suite
├── knowledge/               # Knowledge base files
├── terraform/               # Infrastructure as code
├── alembic/                 # Database migrations
├── Dockerfile               # Container build
├── docker-compose.yml       # Local development
└── docker-compose.prod.yml  # Production setup
```

## Production Deployment

### Docker Compose (Single Server)

```bash
# Copy and configure production environment
cp .env.prod.example .env.prod
# Edit .env.prod with production values

# Deploy
make prod
```

### Kubernetes (Hetzner Cloud)

Full infrastructure deployment on Hetzner Cloud with k3s, PostgreSQL, PgBouncer, and Traefik.

#### Prerequisites

- [Terraform](https://www.terraform.io/downloads) >= 1.0
- [Docker](https://docs.docker.com/get-docker/)
- [kubectl](https://kubernetes.io/docs/tasks/tools/)
- [Helm](https://helm.sh/docs/intro/install/)
- SSH key at `~/.ssh/id_rsa.pub`
- Hetzner Cloud API token

#### Required Environment Variables

```bash
export HCLOUD_TOKEN="your-hetzner-api-token"
export DB_PASSWORD="your-secure-database-password"
export LITELLM_API_KEY="your-openrouter-api-key"

# Optional
export DOMAIN="your-domain.com"
export ACME_EMAIL="admin@your-domain.com"
export LANGFUSE_PUBLIC_KEY="pk-lf-xxx"
export LANGFUSE_SECRET_KEY="sk-lf-xxx"
```

#### Deploy Infrastructure

```bash
# One-command deployment (recommended)
make infra-apply
```

This script will:
1. Validate prerequisites and environment variables
2. Auto-detect your IP for firewall rules
3. Create Hetzner Cloud resources (server, network, firewall)
4. Wait for k3s to be ready
5. Install Traefik ingress controller
6. Build and push Docker image to k3s
7. Deploy Kubernetes resources (PostgreSQL, PgBouncer, QnA Agent)
8. Run health checks

#### Manual Deployment (Step by Step)

If you need more control or the setup script fails:

```bash
# 1. Initialize Terraform
make infra-init

# 2. Create Hetzner infrastructure only
TF_VAR_hcloud_token="$HCLOUD_TOKEN" \
TF_VAR_db_password="$DB_PASSWORD" \
TF_VAR_litellm_api_key="$LITELLM_API_KEY" \
TF_VAR_admin_ips='["YOUR_IP/32"]' \
terraform -chdir=terraform apply -target=module.hetzner -auto-approve

# 3. Get server IP
SERVER_IP=$(terraform -chdir=terraform output -raw server_ip)

# 4. Wait for k3s and install Traefik
ssh -o StrictHostKeyChecking=no root@$SERVER_IP "kubectl get nodes"
ssh root@$SERVER_IP "export KUBECONFIG=/etc/rancher/k3s/k3s.yaml && \
  helm repo add traefik https://traefik.github.io/charts && \
  helm repo update && \
  helm install traefik traefik/traefik --namespace kube-system \
    --set image.tag=v3.6.4 --wait"

# 5. Configure local kubeconfig
scp root@$SERVER_IP:/etc/rancher/k3s/k3s.yaml ~/.kube/config
sed -i.bak "s/127.0.0.1/$SERVER_IP/g" ~/.kube/config

# 6. Build and push Docker image
docker build -t qna-agent:latest .
docker save qna-agent:latest | gzip > /tmp/qna-agent.tar.gz
scp /tmp/qna-agent.tar.gz root@$SERVER_IP:/tmp/
ssh root@$SERVER_IP "k3s ctr images import /tmp/qna-agent.tar.gz"

# 7. Deploy Kubernetes resources
TF_VAR_hcloud_token="$HCLOUD_TOKEN" \
TF_VAR_db_password="$DB_PASSWORD" \
TF_VAR_litellm_api_key="$LITELLM_API_KEY" \
TF_VAR_admin_ips='["YOUR_IP/32"]' \
terraform -chdir=terraform apply -auto-approve
```

#### Verify Deployment

```bash
# Check all pods are running
kubectl get pods -n qna-agent

# Expected output:
# NAME                         READY   STATUS    RESTARTS   AGE
# postgres-0                   1/1     Running   0          2m
# pgbouncer-xxx                1/1     Running   0          2m
# pgbouncer-xxx                1/1     Running   0          2m
# qna-agent-xxx                1/1     Running   0          1m
# qna-agent-xxx                1/1     Running   0          1m

# Health checks
curl http://$SERVER_IP/health/live
curl http://$SERVER_IP/health/ready
```

#### Update Application

```bash
# Deploy new version without recreating infrastructure
make k8s-deploy
```

#### Useful Commands

```bash
make k8s-status   # Check cluster status
make k8s-logs     # View application logs
make k8s-restart  # Restart deployment
```

#### Destroy Infrastructure

```bash
# With confirmation prompt
make infra-destroy

# Skip confirmation
make infra-destroy-force
```

## Architecture

### Domain-Driven Design

The application follows a domain-driven structure inspired by Netflix Dispatch:

- **Chats**: Chat session lifecycle management
- **Messages**: Message storage and retrieval
- **Agent**: LLM interaction with tool calling
- **Knowledge**: File-based knowledge base operations
- **Events**: SSE pub/sub for real-time updates
- **Health**: Kubernetes probes

### Exception Handling

Uses "OOPS over What-if" approach:
- Domain-specific exception classes
- FastAPI exception handlers at app level
- No defensive coding - let type system and exceptions handle errors

### LLM Observability

Langfuse integration provides:
- Request tracing per chat/session
- Token usage and cost tracking
- Latency monitoring
- Debug logging for tool calls

## Documentation

- [stack.md](stack.md) - Technology decisions and justifications
- [OpenAPI Docs](http://localhost:8000/docs) - Interactive API documentation

## License

MIT
