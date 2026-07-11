# Deployment Guide

This guide covers deploying the Speech-to-Text application to various production environments.

## Table of Contents

1. [Streamlit Cloud](#streamlit-cloud)
2. [Docker (Local/Self-Hosted)](#docker-localself-hosted)
3. [AWS](#aws)
4. [Heroku](#heroku)
5. [Environment Configuration](#environment-configuration)
6. [Monitoring & Maintenance](#monitoring--maintenance)

---

## Streamlit Cloud

### Easiest Deployment Option

Streamlit Cloud is the quickest way to deploy a Streamlit app.

### Prerequisites

- GitHub account with repository
- OpenAI API key
- Streamlit account

### Steps

1. **Push code to GitHub**
   ```bash
   git push origin main
   ```

2. **Go to Streamlit Cloud** (https://streamlit.io/cloud)
   - Click "New app"
   - Select repository: `Speech-to-text`
   - Select branch: `main`
   - Select main file path: `app.py`

3. **Configure Secrets**
   - Click "Settings" → "Secrets"
   - Add your OpenAI API key:
   ```
   OPENAI_API_KEY = "sk-your-api-key-here"
   ```

4. **Deploy**
   - Click "Deploy"
   - App will be live at: `https://[your-username]-speech-to-text.streamlit.app`

### Limits

- Free tier: 1 app
- Shared resources (may be slower during peak hours)
- Public by default (can restrict to specific users)

### Cost

- **Free tier**: ✓ Included
- **Pro tier**: $10/month for priority resources

---

## Docker (Local/Self-Hosted)

### Requirements

- Docker and Docker Compose installed
- Linux/macOS/Windows with Docker support
- Sufficient disk space (~2GB)

### Build and Run

1. **Build Docker image**
   ```bash
   docker build -t speech-to-text:latest .
   ```

2. **Run container**
   ```bash
   docker run -p 8501:8501 \
     -e OPENAI_API_KEY="sk-your-api-key" \
     speech-to-text:latest
   ```

3. **Access application**
   - Open `http://localhost:8501`

### Using Docker Compose

1. **Create `.env` file**
   ```bash
   cp .env.example .env
   # Edit .env and add your OPENAI_API_KEY
   ```

2. **Start services**
   ```bash
   docker-compose up -d
   ```

3. **View logs**
   ```bash
   docker-compose logs -f app
   ```

4. **Stop services**
   ```bash
   docker-compose down
   ```

### Production Configuration

For production deployments:

1. **Use environment-specific compose file**
   ```bash
   docker-compose -f docker-compose.prod.yml up -d
   ```

2. **Enable HTTPS**
   - Use reverse proxy (Nginx)
   - Let's Encrypt for SSL certificates

3. **Resource limits**
   ```yaml
   deploy:
     resources:
       limits:
         cpus: '2'
         memory: 2G
       reservations:
         cpus: '1'
         memory: 1G
   ```

---

## AWS

### Option 1: AWS App Runner (Recommended)

Simplest AWS deployment.

1. **Create ECR Repository**
   ```bash
   aws ecr create-repository --repository-name speech-to-text
   ```

2. **Build and push image**
   ```bash
   aws ecr get-login-password --region us-east-1 | \
     docker login --username AWS --password-stdin <account-id>.dkr.ecr.us-east-1.amazonaws.com
   
   docker build -t speech-to-text:latest .
   docker tag speech-to-text:latest \
     <account-id>.dkr.ecr.us-east-1.amazonaws.com/speech-to-text:latest
   docker push <account-id>.dkr.ecr.us-east-1.amazonaws.com/speech-to-text:latest
   ```

3. **Create App Runner Service**
   - AWS Console → App Runner
   - Source: ECR
   - Port: 8501
   - Configure environment variables

4. **Set environment variables**
   - `OPENAI_API_KEY`: Your API key
   - `STREAMLIT_SERVER_HEADLESS`: true
   - `STREAMLIT_SERVER_PORT`: 8501

### Option 2: AWS ECS (EC2)

For more control and scaling:

1. **Create ECS cluster**
2. **Create task definition** with Docker image
3. **Configure service** for auto-scaling
4. **Set up load balancer** for traffic distribution

### Estimated Costs

- **App Runner**: $0.065/hour + data transfer
- **ECS (t3.micro)**: ~$8/month + data transfer

---

## Heroku

### Deprecated (as of November 2022)

Heroku has ended free tier support. Use alternatives instead.

---

## Environment Configuration

### Required Variables

```bash
# .env or environment variables
OPENAI_API_KEY=sk-your-api-key-here
```

### Optional Variables

```bash
# Streamlit configuration
STREAMLIT_SERVER_PORT=8501
STREAMLIT_SERVER_HEADLESS=true
STREAMLIT_SERVER_RUN_ON_SAVE=false

# Application configuration
CHUNK_LENGTH_SEC=600
LOG_LEVEL=INFO
```

### Secrets Management

**Option 1: Environment Variables**
```bash
export OPENAI_API_KEY="sk-..."
streamlit run app.py
```

**Option 2: .streamlit/secrets.toml**
```toml
openai_api_key = "sk-..."
```

**Option 3: Docker Secrets (Swarm)**
```bash
docker secret create openai_key openai_api_key.txt
docker service create --secret openai_key speech-to-text:latest
```

---

## Monitoring & Maintenance

### Health Checks

```bash
# Test endpoint
curl http://localhost:8501/_stcore/health
```

### Logging

For Docker deployments:

```bash
# View logs
docker logs <container-id>

# Follow logs
docker logs -f <container-id>

# Logs from compose
docker-compose logs -f app
```

### Performance Monitoring

Monitor these metrics:

- **Response time**: < 30s per minute of audio
- **Memory usage**: < 2GB
- **CPU usage**: < 2 cores
- **Concurrent users**: Limited by resources

### Updating Deployment

1. **Update code**
   ```bash
   git commit -am "Update feature"
   git push origin main
   ```

2. **For Streamlit Cloud**: Auto-deploys on push

3. **For Docker deployments**:
   ```bash
   docker pull speech-to-text:latest
   docker-compose up -d
   ```

### Database Backup (if using storage)

```bash
# Backup transcripts
tar -czf transcripts_backup.tar.gz data/transcripts/

# Upload to S3
aws s3 cp transcripts_backup.tar.gz s3://my-bucket/backups/
```

### Security Checklist

- [ ] API key stored in secrets (not in code)
- [ ] HTTPS enabled for production
- [ ] Rate limiting configured
- [ ] Access logs enabled
- [ ] Regular dependency updates
- [ ] Container image scanning enabled
- [ ] Firewall rules configured
- [ ] Backup strategy implemented

---

## Troubleshooting

### Port already in use

```bash
# Find process using port
lsof -i :8501

# Kill process
kill -9 <pid>

# Or use different port
streamlit run app.py --server.port 8502
```

### API key not recognized

```bash
# Verify key is set
echo $OPENAI_API_KEY

# Check in app
streamlit run app.py --logger.level=debug
```

### Memory issues

Increase Docker memory allocation:
```bash
docker run -m 4g speech-to-text:latest
```

### High latency

- Check network connection
- Increase chunk size
- Use closer region (for cloud deployments)
- Scale up resources

---

## Cost Optimization

### OpenAI Whisper Pricing

As of 2024:
- `whisper-1`: $0.02 per minute of audio

Example costs for 1 hour of audio:
- Cost: $0.02 × 60 = $1.20

### Infrastructure Costs

| Service | Free Tier | Paid |
|---------|-----------|------|
| Streamlit Cloud | Yes | $10/month |
| AWS App Runner | No | ~$0.065/hour |
| Docker (self-hosted) | Yes | $0/month + server |
| Heroku | No (discontinued) | - |

### Cost Reduction Tips

1. **Increase chunk length** (more efficient, slightly less accurate)
2. **Cache results** (don't re-transcribe)
3. **Use lower cost tier** for less important transcripts
4. **Scale down during off-peak hours**

---

## Next Steps

1. Choose deployment platform
2. Configure environment variables
3. Test in staging environment
4. Deploy to production
5. Monitor performance
6. Plan maintenance schedule

For questions or issues, check [DEVELOPMENT.md](DEVELOPMENT.md) or [API.md](API.md).
