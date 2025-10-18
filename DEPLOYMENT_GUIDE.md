# VidyaVani IVR Learning System - Production Deployment Guide

## Overview

This guide covers deploying VidyaVani to production environments including Render.com, Railway.app, and Docker-based platforms.

## Pre-Deployment Checklist

### 1. Environment Variables

Ensure all required environment variables are set:

**Required:**
- `SECRET_KEY` - Flask secret key (auto-generated on Render/Railway)
- `EXOTEL_ACCOUNT_SID` - Exotel account SID
- `EXOTEL_API_KEY` - Exotel API key
- `EXOTEL_API_TOKEN` - Exotel API token
- `EXOTEL_PHONE_NUMBER` - Exotel phone number
- `EXOTEL_APP_ID` - Exotel application ID
- `OPENAI_API_KEY` - OpenAI API key
- `GOOGLE_CLOUD_PROJECT` - Google Cloud project ID
- `GOOGLE_APPLICATION_CREDENTIALS_JSON` - Google Cloud service account JSON (as string)

**Optional:**
- `FLASK_ENV=production`
- `DEPLOYMENT_PLATFORM` - render, railway, docker, or local
- `REDIS_URL` - Redis connection URL (for caching)
- `ADMIN_RESTART_KEY` - Admin key for system restart
- `MAX_CONCURRENT_CALLS=5`
- `RESPONSE_TIMEOUT=8`
- `AUTO_BACKUP_ENABLED=true`
- `BACKUP_RETENTION_DAYS=7`

### 2. Content Preparation

Ensure NCERT content is processed:
```bash
python scripts/add_ncert_pdf.py
```

## Deployment Options

### Option 1: Render.com Deployment

1. **Connect Repository**
   - Connect your GitHub repository to Render
   - Render will automatically detect the `render.yaml` configuration

2. **Environment Variables**
   - Set required environment variables in Render dashboard
   - Use the "Generate Value" option for `SECRET_KEY`

3. **Deploy**
   ```bash
   git push origin main
   ```
   - Render will automatically build and deploy
   - Health checks will verify deployment success

4. **Post-Deployment**
   - Access production dashboard at `https://your-app.onrender.com/production-dashboard`
   - Monitor logs in Render dashboard

### Option 2: Railway.app Deployment

1. **Connect Repository**
   - Connect your GitHub repository to Railway
   - Railway will detect the `railway.json` configuration

2. **Environment Variables**
   - Set required environment variables in Railway dashboard
   - Railway auto-generates `SECRET_KEY`

3. **Deploy**
   ```bash
   railway up
   ```
   - Or push to connected GitHub repository

4. **Custom Domain (Optional)**
   ```bash
   railway domain
   ```

### Option 3: Docker Deployment

1. **Build Image**
   ```bash
   docker build -t vidyavani-ivr .
   ```

2. **Run with Docker Compose**
   ```bash
   # Copy environment file
   cp .env.example .env
   # Edit .env with your API keys
   
   # Start services
   docker-compose up -d
   ```

3. **Manual Docker Run**
   ```bash
   docker run -d \
     --name vidyavani-ivr \
     -p 5000:5000 \
     --env-file .env \
     -v $(pwd)/data:/app/data \
     -v $(pwd)/logs:/app/logs \
     vidyavani-ivr
   ```

### Option 4: Manual Server Deployment

1. **Server Setup**
   ```bash
   # Install Python 3.9+
   sudo apt update
   sudo apt install python3.9 python3.9-venv python3.9-dev
   
   # Clone repository
   git clone <your-repo-url>
   cd vidyavani-ivr-system
   
   # Create virtual environment
   python3.9 -m venv venv
   source venv/bin/activate
   
   # Install dependencies
   pip install -r requirements.txt
   ```

2. **Environment Configuration**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

3. **Production Setup**
   ```bash
   python scripts/setup_production.py
   ```

4. **Start with Gunicorn**
   ```bash
   gunicorn --bind 0.0.0.0:5000 \
            --workers 2 \
            --timeout 120 \
            --max-requests 1000 \
            --max-requests-jitter 100 \
            --preload \
            app:app
   ```

5. **Process Management (Optional)**
   ```bash
   # Install supervisor
   sudo apt install supervisor
   
   # Create supervisor config
   sudo nano /etc/supervisor/conf.d/vidyavani.conf
   ```

   ```ini
   [program:vidyavani]
   command=/path/to/venv/bin/gunicorn --bind 0.0.0.0:5000 --workers 2 --timeout 120 app:app
   directory=/path/to/vidyavani-ivr-system
   user=www-data
   autostart=true
   autorestart=true
   redirect_stderr=true
   stdout_logfile=/var/log/vidyavani.log
   ```

## Production Configuration

### Health Monitoring

The system includes comprehensive health monitoring:

- **Health Check Endpoint**: `/health`
- **Detailed Health**: `/health/detailed`
- **Health History**: `/health/history`
- **Production Dashboard**: `/production-dashboard`

### Automatic Backups

Backups are automatically created every 6 hours (configurable):

- **FAISS vector database**
- **Cached responses**
- **System configuration**

Backup endpoints:
- `POST /api/backup/create` - Create manual backup
- `GET /api/backup/list` - List available backups
- `POST /api/backup/restore` - Restore from backup

### Load Balancing

The system includes built-in load balancing:

- **Concurrent request limiting**
- **Rate limiting per phone number**
- **Circuit breaker for fault tolerance**
- **Request queuing and prioritization**

### Performance Monitoring

Real-time performance monitoring includes:

- **Response time tracking**
- **API usage and costs**
- **Cache performance**
- **System resource usage**
- **Error tracking and alerting**

## Monitoring and Maintenance

### 1. Health Checks

Monitor system health:
```bash
curl https://your-app.com/health
```

### 2. Performance Dashboard

Access the production dashboard:
```
https://your-app.com/production-dashboard
```

### 3. Log Monitoring

Production logs are structured JSON:
```bash
# View application logs
tail -f logs/app.log

# View error logs
tail -f logs/error.log

# View performance logs
tail -f logs/performance.log
```

### 4. Backup Management

Create manual backup:
```bash
curl -X POST https://your-app.com/api/backup/create \
  -H "Content-Type: application/json" \
  -d '{"backup_type": "full"}'
```

### 5. System Restart

Emergency system restart (requires admin key):
```bash
curl -X POST https://your-app.com/health/restart \
  -H "X-Admin-Key: your-admin-key"
```

## Troubleshooting

### Common Issues

1. **High Response Times**
   - Check `/api/performance/dashboard`
   - Monitor API usage limits
   - Verify FAISS index is loaded

2. **Memory Issues**
   - Check system resources in dashboard
   - Consider increasing worker memory limits
   - Review backup retention settings

3. **API Rate Limits**
   - Monitor API usage in dashboard
   - Implement request caching
   - Consider upgrading API plans

4. **FAISS Index Issues**
   - Restore from backup: `POST /api/backup/restore`
   - Regenerate index: `python scripts/add_ncert_pdf.py`

### Emergency Procedures

1. **System Overload**
   - Reduce `MAX_CONCURRENT_CALLS`
   - Enable circuit breaker
   - Scale up resources

2. **Data Corruption**
   - Restore from latest backup
   - Regenerate FAISS index
   - Clear cache and restart

3. **API Failures**
   - Check API key validity
   - Monitor rate limits
   - Switch to backup responses

## Security Considerations

### 1. Environment Variables

- Never commit API keys to version control
- Use platform-specific secret management
- Rotate keys regularly

### 2. Network Security

- Enable HTTPS in production
- Use secure headers
- Implement rate limiting

### 3. Data Privacy

- Phone numbers are hashed in logs
- Voice recordings are not stored
- Session data is automatically cleaned

### 4. Access Control

- Protect admin endpoints
- Use strong admin keys
- Monitor access logs

## Performance Optimization

### 1. Caching Strategy

- Enable Redis for production
- Pre-cache common responses
- Implement audio caching

### 2. Resource Management

- Monitor memory usage
- Optimize worker count
- Use connection pooling

### 3. API Optimization

- Batch API requests where possible
- Use streaming for large responses
- Implement request deduplication

## Scaling Considerations

### Horizontal Scaling

For high traffic, consider:

1. **Load Balancer**
   - Use external load balancer (nginx, HAProxy)
   - Distribute across multiple instances
   - Implement session affinity

2. **Database Scaling**
   - Use Redis cluster for caching
   - Replicate FAISS index across instances
   - Implement distributed session storage

3. **CDN Integration**
   - Cache audio responses
   - Distribute static assets
   - Reduce latency for global users

### Vertical Scaling

For better performance:

1. **Increase Resources**
   - More CPU cores for parallel processing
   - More RAM for FAISS index caching
   - Faster storage for audio processing

2. **Optimize Configuration**
   - Tune Gunicorn worker count
   - Adjust timeout values
   - Optimize cache sizes

## Support and Maintenance

### Regular Maintenance Tasks

1. **Weekly**
   - Review performance metrics
   - Check backup integrity
   - Monitor API usage

2. **Monthly**
   - Update dependencies
   - Review error logs
   - Optimize cache settings

3. **Quarterly**
   - Security audit
   - Performance optimization
   - Capacity planning

### Getting Help

- Check production dashboard for system status
- Review structured logs for error details
- Use backup/restore for data recovery
- Monitor health endpoints for system issues

## Conclusion

This deployment guide provides comprehensive instructions for deploying VidyaVani to production. The system includes built-in monitoring, backup, and recovery capabilities to ensure reliable operation in production environments.

For additional support or questions, refer to the system logs and monitoring dashboards for detailed diagnostic information.