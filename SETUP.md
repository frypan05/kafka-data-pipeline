# Setup Guide - Data Pipeline with Kafka & ELK Stack

This guide will walk you through setting up the complete data pipeline on your local machine and deploying to production using free-tier services.

---

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Local Development Setup](#local-development-setup)
3. [Verifying Installation](#verifying-installation)
4. [Production Deployment](#production-deployment)
5. [Troubleshooting](#troubleshooting)
6. [Next Steps](#next-steps)

---

## Prerequisites

### Required Software

- **Docker** (20.10+) - [Install Docker](https://docs.docker.com/get-docker/)
- **Docker Compose** (2.0+) - Usually included with Docker Desktop
- **Git** - [Install Git](https://git-scm.com/downloads)
- **Python 3.11+** (for local development) - [Install Python](https://www.python.org/downloads/)
- **Node.js 18+** (for API Gateway) - [Install Node.js](https://nodejs.org/)

### Recommended Tools

- **Visual Studio Code** with Docker extension
- **Postman** or **Insomnia** for API testing
- **Terminal** or **Git Bash** (Windows)

### System Requirements

- **RAM**: 8GB minimum (16GB recommended)
- **Disk Space**: 20GB free space
- **CPU**: 4 cores minimum
- **OS**: Windows 10/11, macOS 10.15+, or Linux (Ubuntu 20.04+)

---

## Local Development Setup

### Step 1: Clone the Repository

```bash
# Clone the repository
git clone https://github.com/yourusername/data-pipeline-kafka.git
cd data-pipeline-kafka

# Or if you're starting fresh
mkdir data-pipeline-kafka
cd data-pipeline-kafka
```

### Step 2: Environment Configuration

```bash
# Copy the example environment file
cp .env.example .env

# Edit the .env file with your preferred editor
# For Windows:
notepad .env

# For Mac/Linux:
nano .env
# or
vim .env
```

**Important Environment Variables to Configure:**

```env
# Kafka Configuration
KAFKA_BROKERS=localhost:9092

# Elasticsearch Configuration
ELASTICSEARCH_URL=http://localhost:9200

# Database (PostgreSQL)
DATABASE_URL=postgresql://pipeline_user:pipeline_pass@localhost:5432/pipeline_metadata

# Redis
REDIS_URL=redis://localhost:6379

# API Gateway
PORT=3000

# Monitoring
GRAFANA_ADMIN_PASSWORD=admin123
```

### Step 3: Make Scripts Executable (Mac/Linux)

```bash
chmod +x scripts/quick-start.sh
chmod +x scripts/*.sh
```

### Step 4: Start the Pipeline

#### Option A: Using Quick Start Script (Recommended)

```bash
# Start all services
bash scripts/quick-start.sh start

# The script will:
# 1. Run pre-flight checks
# 2. Set up the environment
# 3. Start all Docker containers
# 4. Verify service health
# 5. Display access information
```

#### Option B: Manual Docker Compose

```bash
# Start infrastructure services first
docker-compose up -d zookeeper kafka

# Wait for Kafka to be ready (30-60 seconds)
sleep 30

# Start ELK Stack
docker-compose up -d elasticsearch
sleep 30
docker-compose up -d logstash kibana

# Start supporting services
docker-compose up -d postgres redis kafka-ui

# Start data pipeline
docker-compose up -d log-producer metrics-producer elasticsearch-consumer

# Start monitoring
docker-compose up -d prometheus grafana
```

### Step 5: Verify Services are Running

```bash
# Check all containers
docker-compose ps

# Check specific service logs
docker-compose logs -f kafka
docker-compose logs -f elasticsearch
docker-compose logs -f kibana

# Check service health
bash scripts/quick-start.sh status
```

---

## Verifying Installation

### 1. Check Elasticsearch

```bash
# Health check
curl http://localhost:9200/_cluster/health?pretty

# Expected output:
# {
#   "cluster_name" : "es-docker-cluster",
#   "status" : "yellow" or "green",
#   "number_of_nodes" : 1,
#   ...
# }

# List indices
curl http://localhost:9200/_cat/indices?v
```

### 2. Check Kafka

```bash
# List Kafka topics
docker-compose exec kafka kafka-topics --list --bootstrap-server localhost:9092

# Expected topics:
# application-logs
# system-metrics
# business-events

# Check topic details
docker-compose exec kafka kafka-topics --describe --topic application-logs --bootstrap-server localhost:9092
```

### 3. Access Kibana

1. Open browser: `http://localhost:5601`
2. Click **"Explore on my own"**
3. Go to **Management** → **Stack Management** → **Index Management**
4. You should see indices like:
   - `pipeline-logs-2024.01.15`
   - `pipeline-metrics-2024.01.15`

### 4. Create Data Views in Kibana

1. Go to **Management** → **Stack Management** → **Data Views**
2. Click **"Create data view"**
3. For Logs:
   - Name: `Application Logs`
   - Index pattern: `pipeline-logs-*`
   - Time field: `@timestamp`
   - Click **"Save data view to Kibana"**
4. Repeat for Metrics:
   - Name: `System Metrics`
   - Index pattern: `pipeline-metrics-*`
   - Time field: `@timestamp`

### 5. Explore Data in Discover

1. Go to **Discover** (left sidebar)
2. Select your data view (Application Logs)
3. You should see real-time logs flowing in!
4. Try filtering:
   - `level: ERROR`
   - `service: api-gateway`
   - `response_time_ms > 1000`

### 6. Check Kafka UI

1. Open browser: `http://localhost:8080`
2. You should see:
   - Kafka cluster information
   - Topics list
   - Messages flowing through topics
   - Consumer groups

### 7. Check Grafana

1. Open browser: `http://localhost:3001`
2. Login:
   - Username: `admin`
   - Password: `admin123`
3. You should see pre-configured dashboards (if available)

---

## Production Deployment

### Option 1: Deploy on GCP Free Tier

#### Step 1: Set up GCP Account

1. Sign up for [Google Cloud Platform](https://cloud.google.com/free)
2. Free tier includes:
   - 1 e2-micro VM instance
   - 30GB standard persistent disk
   - 1GB network egress per month

#### Step 2: Create GCP VM

```bash
# Install gcloud CLI
# https://cloud.google.com/sdk/docs/install

# Authenticate
gcloud auth login

# Set project
gcloud config set project YOUR_PROJECT_ID

# Create VM instance
gcloud compute instances create kafka-elk-vm \
  --zone=us-central1-a \
  --machine-type=e2-medium \
  --image-family=ubuntu-2204-lts \
  --image-project=ubuntu-os-cloud \
  --boot-disk-size=30GB \
  --tags=http-server,https-server

# SSH into the instance
gcloud compute ssh kafka-elk-vm --zone=us-central1-a
```

#### Step 3: Install Docker on GCP VM

```bash
# Update system
sudo apt-get update
sudo apt-get upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Add user to docker group
sudo usermod -aG docker $USER
newgrp docker
```

#### Step 4: Deploy Application

```bash
# Clone repository
git clone https://github.com/yourusername/data-pipeline-kafka.git
cd data-pipeline-kafka

# Set up environment
cp .env.example .env
nano .env  # Edit with production values

# Start services
docker-compose -f docker-compose.prod.yml up -d

# Check status
docker-compose ps
```

#### Step 5: Configure Firewall

```bash
# Open required ports
gcloud compute firewall-rules create allow-kafka \
  --allow=tcp:9092 \
  --target-tags=http-server

gcloud compute firewall-rules create allow-kibana \
  --allow=tcp:5601 \
  --target-tags=http-server

gcloud compute firewall-rules create allow-elasticsearch \
  --allow=tcp:9200 \
  --target-tags=http-server
```

### Option 2: Deploy on Render (Backend Services)

#### Step 1: Create Render Account

1. Sign up at [Render.com](https://render.com)
2. Connect your GitHub repository

#### Step 2: Deploy Kafka Consumer Service

1. Go to Render Dashboard
2. Click **"New +"** → **"Background Worker"**
3. Configure:
   - Name: `elasticsearch-consumer`
   - Build Command: `pip install -r kafka/consumers/requirements.txt`
   - Start Command: `python kafka/consumers/elasticsearch-consumer.py`
   - Environment Variables: Add from `.env` file

#### Step 3: Deploy API Gateway

1. Click **"New +"** → **"Web Service"**
2. Configure:
   - Name: `api-gateway`
   - Build Command: `cd services/api-gateway && npm install`
   - Start Command: `cd services/api-gateway && npm start`
   - Environment Variables: Add from `.env` file

### Option 3: Deploy Frontend on Vercel

#### Step 1: Create Vercel Account

1. Sign up at [Vercel.com](https://vercel.com)
2. Install Vercel CLI:

```bash
npm install -g vercel
```

#### Step 2: Deploy Frontend

```bash
cd frontend/dashboard

# Login to Vercel
vercel login

# Deploy
vercel --prod

# Set environment variables
vercel env add VITE_API_URL
# Enter your API Gateway URL from Render
```

### Option 4: Use Supabase for PostgreSQL

#### Step 1: Create Supabase Project

1. Sign up at [Supabase.com](https://supabase.com)
2. Create new project
3. Note down:
   - Project URL
   - Service Role Key
   - Database URL

#### Step 2: Update Environment Variables

```env
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_KEY=your-service-role-key
DATABASE_URL=postgresql://postgres:[YOUR-PASSWORD]@db.your-project.supabase.co:5432/postgres
```

### Option 5: Use Upstash for Kafka (Alternative)

#### Step 1: Create Upstash Account

1. Sign up at [Upstash.com](https://upstash.com)
2. Create a Kafka cluster (free tier available)

#### Step 2: Update Configuration

```env
UPSTASH_KAFKA_REST_URL=https://your-cluster.upstash.io
UPSTASH_KAFKA_REST_USERNAME=your-username
UPSTASH_KAFKA_REST_PASSWORD=your-password
```

---

## Troubleshooting

### Issue: Docker Containers Won't Start

**Solution:**

```bash
# Check Docker daemon is running
docker info

# Check logs
docker-compose logs

# Remove old containers and volumes
docker-compose down -v

# Rebuild and restart
docker-compose up -d --build
```

### Issue: Elasticsearch Out of Memory

**Solution:**

```bash
# Increase Docker memory allocation
# Docker Desktop → Settings → Resources → Memory: 4GB+

# Or adjust heap size in docker-compose.yml
environment:
  - "ES_JAVA_OPTS=-Xms512m -Xmx512m"
```

### Issue: Kafka Connection Refused

**Solution:**

```bash
# Check if Kafka is running
docker-compose ps kafka

# Check Kafka logs
docker-compose logs kafka

# Restart Kafka
docker-compose restart kafka

# Wait for Kafka to be ready (30-60 seconds)
sleep 30
```

### Issue: Kibana Not Loading

**Solution:**

```bash
# Check if Elasticsearch is running
curl http://localhost:9200/_cluster/health

# Restart Kibana
docker-compose restart kibana

# Clear browser cache and try again
```

### Issue: No Data in Kibana

**Solution:**

```bash
# Check if producers are running
docker-compose ps log-producer metrics-producer

# Check producer logs
docker-compose logs log-producer

# Check if data is in Elasticsearch
curl http://localhost:9200/pipeline-logs-*/_count

# Restart producers
docker-compose restart log-producer metrics-producer

# Check consumer logs
docker-compose logs elasticsearch-consumer
```

### Issue: Port Already in Use

**Solution:**

```bash
# Find what's using the port (example: port 5601)
# Windows:
netstat -ano | findstr :5601

# Mac/Linux:
lsof -i :5601

# Kill the process or change port in docker-compose.yml
ports:
  - "5602:5601"  # Change external port
```

### Issue: Performance is Slow

**Solution:**

1. **Increase Docker Resources:**
   - Memory: 8GB+
   - CPUs: 4+
   - Disk: SSD recommended

2. **Reduce Producer Frequency:**
   ```env
   LOG_PRODUCER_INTERVAL_MS=5000  # Increase from 1000
   METRICS_PRODUCER_INTERVAL_MS=10000  # Increase from 5000
   ```

3. **Adjust Batch Sizes:**
   ```env
   PRODUCER_BATCH_SIZE=32768  # Increase from 16384
   CONSUMER_MAX_POLL_RECORDS=1000  # Increase from 500
   ```

---

## Next Steps

### 1. Create Custom Dashboards

1. Open Kibana: `http://localhost:5601`
2. Go to **Dashboard** → **Create dashboard**
3. Add visualizations:
   - Error rate over time
   - Response time percentiles
   - Top 10 slow services
   - CPU/Memory usage charts

### 2. Set Up Alerting

Create alert rules for:
- High error rate (>5%)
- Slow response time (p95 > 1000ms)
- High CPU usage (>80%)
- High memory usage (>85%)

### 3. Add Custom Data Sources

Modify producers to send your application's actual data:

```python
# In kafka/producers/log-producer.py
# Replace generate_log_entry() with your logging logic
```

### 4. Implement Authentication

Add security layers:
- API Gateway authentication
- Elasticsearch security (X-Pack)
- Kibana access control
- Network security groups

### 5. Scale the System

- Add more Kafka brokers
- Scale consumers horizontally
- Use Kafka partitions for parallelism
- Implement data retention policies

### 6. Monitor Costs

Set up cost monitoring:
- GCP billing alerts
- Resource utilization tracking
- Auto-scaling policies
- Data retention policies

---

## Useful Commands

### Docker Commands

```bash
# View all containers
docker-compose ps

# View logs for all services
docker-compose logs -f

# View logs for specific service
docker-compose logs -f kafka

# Restart a service
docker-compose restart kafka

# Stop all services
docker-compose down

# Stop and remove volumes
docker-compose down -v

# Rebuild containers
docker-compose up -d --build

# Scale a service
docker-compose up -d --scale log-producer=3
```

### Kafka Commands

```bash
# List topics
docker-compose exec kafka kafka-topics --list --bootstrap-server localhost:9092

# Create topic
docker-compose exec kafka kafka-topics --create --topic test-topic --partitions 3 --replication-factor 1 --bootstrap-server localhost:9092

# Describe topic
docker-compose exec kafka kafka-topics --describe --topic application-logs --bootstrap-server localhost:9092

# Consume messages
docker-compose exec kafka kafka-console-consumer --bootstrap-server localhost:9092 --topic application-logs --from-beginning

# Produce messages
docker-compose exec kafka kafka-console-producer --bootstrap-server localhost:9092 --topic application-logs

# Check consumer group
docker-compose exec kafka kafka-consumer-groups --bootstrap-server localhost:9092 --describe --group elasticsearch-consumers
```

### Elasticsearch Commands

```bash
# Cluster health
curl http://localhost:9200/_cluster/health?pretty

# List indices
curl http://localhost:9200/_cat/indices?v

# Get index stats
curl http://localhost:9200/pipeline-logs-*/_stats?pretty

# Count documents
curl http://localhost:9200/pipeline-logs-*/_count?pretty

# Search documents
curl -X GET "http://localhost:9200/pipeline-logs-*/_search?pretty" -H 'Content-Type: application/json' -d'
{
  "query": {
    "match": {
      "level": "ERROR"
    }
  }
}
'

# Delete old indices
curl -X DELETE "http://localhost:9200/pipeline-logs-2024.01.01"
```

---

## Support

- **GitHub Issues**: [Report bugs](https://github.com/yourusername/data-pipeline-kafka/issues)
- **Documentation**: [Full docs](https://github.com/yourusername/data-pipeline-kafka/docs)
- **Discord**: [Join community](https://discord.gg/your-invite)

---

**Happy Monitoring!** 🚀

If you found this helpful, please ⭐ the repository!