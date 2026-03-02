# Quick Start Guide - 5 Minutes to Running Pipeline

## Prerequisites
- Docker Desktop installed and running
- 8GB RAM available
- 10GB free disk space

## Step 1: Clone & Setup (1 minute)

```bash
git clone https://github.com/yourusername/data-pipeline-kafka.git
cd data-pipeline-kafka
cp .env.example .env
```

## Step 2: Start Everything (2 minutes)

```bash
# Make script executable (Mac/Linux)
chmod +x scripts/quick-start.sh

# Start all services
bash scripts/quick-start.sh start

# Wait for services to start (2-3 minutes)
```

**Windows users:**
```bash
docker-compose up -d
```

## Step 3: Access Services (30 seconds)

Open in your browser:

| Service | URL | Purpose |
|---------|-----|---------|
| **Kibana** | http://localhost:5601 | View logs & metrics |
| **Kafka UI** | http://localhost:8080 | Monitor Kafka topics |
| **Grafana** | http://localhost:3001 | System dashboards |
| **Elasticsearch** | http://localhost:9200 | Search API |

## Step 4: View Data (1 minute)

### In Kibana:
1. Go to http://localhost:5601
2. Click **"Explore on my own"**
3. Click **"Discover"** in left menu
4. Click **"Create data view"**
5. Enter index pattern: `pipeline-logs-*`
6. Select time field: `@timestamp`
7. Click **"Save data view to Kibana"**
8. **Start exploring your real-time logs!** 🎉

## Quick Commands

```bash
# View logs
docker-compose logs -f

# View specific service
docker-compose logs -f kafka

# Check status
docker-compose ps

# Stop everything
docker-compose down

# Restart
docker-compose restart
```

## Verify It's Working

```bash
# Check Elasticsearch has data
curl http://localhost:9200/pipeline-logs-*/_count

# Expected output: {"count": 1000+, ...}

# List Kafka topics
docker-compose exec kafka kafka-topics --list --bootstrap-server localhost:9092

# Expected output:
# application-logs
# system-metrics
# business-events
```

## What's Happening?

```
Data Flow:
┌─────────────────────────────────────────────────┐
│                                                 │
│  Producers          Kafka          Consumers    │
│  ┌─────────┐      ┌─────┐       ┌──────────┐  │
│  │  Logs   │─────▶│Topic│──────▶│Elasticsearch││
│  │ Metrics │      └─────┘       └──────────┘  │
│  └─────────┘         │                │        │
│                      │                ▼        │
│                      │           ┌────────┐    │
│                      │           │ Kibana │    │
│                      │           └────────┘    │
│                      │                         │
└─────────────────────────────────────────────────┘
```

**Producers** generate sample logs and metrics → 
**Kafka** streams them in real-time → 
**Consumers** index to Elasticsearch → 
**Kibana** visualizes everything!

## Troubleshooting

### "Port already in use"
```bash
# Stop conflicting services or change ports in docker-compose.yml
docker-compose down
```

### "Out of memory"
```bash
# Increase Docker memory:
# Docker Desktop → Settings → Resources → Memory: 8GB
```

### "Kafka won't start"
```bash
# Wait longer (it takes 30-60 seconds)
docker-compose logs kafka

# Or restart
docker-compose restart kafka
sleep 30
```

### "No data in Kibana"
```bash
# Check producers are running
docker-compose ps log-producer

# Restart if needed
docker-compose restart log-producer metrics-producer

# Wait 10 seconds and refresh Kibana
```

## Next Steps

1. **Create Custom Dashboards**
   - Go to Kibana → Dashboard → Create
   - Add visualizations for errors, response times, etc.

2. **Explore Kafka UI**
   - http://localhost:8080
   - See real-time message flow
   - Monitor consumer lag

3. **Check Grafana**
   - http://localhost:3001
   - Login: admin / admin123
   - View system metrics

4. **Read Full Documentation**
   - [SETUP.md](SETUP.md) - Detailed setup guide
   - [README.md](README.md) - Architecture & features

## Common Questions

**Q: How do I stop everything?**
```bash
docker-compose down
```

**Q: How do I remove all data?**
```bash
docker-compose down -v
```

**Q: How do I add my own logs?**
Edit `kafka/producers/log-producer.py` and modify the `generate_log_entry()` function.

**Q: Is this production-ready?**
For learning: Yes! For production: Add authentication, monitoring, backup, and see [SETUP.md](SETUP.md) for deployment guides.

**Q: How much does this cost?**
$0 locally. See [SETUP.md](SETUP.md) for free cloud deployment options.

## Support

- 📧 Issues: [GitHub Issues](https://github.com/yourusername/data-pipeline-kafka/issues)
- 📖 Docs: [Full Documentation](README.md)
- 💬 Help: [Discord Community](https://discord.gg/your-invite)

---

**That's it! You now have a production-grade data pipeline running locally!** 🚀

Try filtering logs in Kibana:
- `level: ERROR` - See all errors
- `response_time_ms > 1000` - Slow requests
- `service: api-gateway` - Specific service logs

**Happy monitoring!** ⭐ Star the repo if this helped you!