# Troubleshooting Guide

This guide helps diagnose and resolve common issues with the Apex Residences Chatbot.

---

## Quick Diagnostics

### Check System Status
```bash
# Check health endpoint
curl http://localhost:5000/api/health

# Check detailed status
curl http://localhost:5000/api/status
```

### View Application Logs
```bash
# Development
# Logs appear in terminal where app was started

# Systemd service
sudo journalctl -u apex-chatbot -f

# Docker container
docker logs -f apex-chatbot

# Docker Compose
docker-compose logs -f chatbot
```

---

## Installation & Setup Issues

### Issue: ModuleNotFoundError: No module named 'anthropic'

**Cause**: Python dependencies not installed

**Solution**:
```bash
# Activate virtual environment
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Verify installation
python -c "import anthropic; print(anthropic.__version__)"
```

---

### Issue: ANTHROPIC_API_KEY not found

**Cause**: Environment variable not set

**Solution**:
```bash
# Option 1: Set in .env file
echo "ANTHROPIC_API_KEY=sk-ant-..." >> .env

# Option 2: Set as environment variable
export ANTHROPIC_API_KEY=sk-ant-...

# Option 3: Export permanently (Linux/Mac)
echo "export ANTHROPIC_API_KEY=sk-ant-..." >> ~/.bashrc
source ~/.bashrc

# Verify
echo $ANTHROPIC_API_KEY
```

---

### Issue: Port 5000 already in use

**Cause**: Another application using port 5000

**Solution**:
```bash
# Option 1: Use different port
python app.py --web --port 8000

# Option 2: Kill process using port 5000
# macOS/Linux
lsof -ti :5000 | xargs kill -9

# Windows
netstat -ano | findstr :5000
taskkill /PID <PID> /F

# Option 3: Configure port in environment
export PORT=8000
python app.py --web
```

---

### Issue: FileNotFoundError: company_info.md not found

**Cause**: Knowledge base file missing

**Solution**:
```bash
# Verify file exists
ls -la company_info.md

# If missing, restore from git
git checkout company_info.md

# If in wrong directory
cd /path/to/DigitalEstateManager
python app.py --web
```

---

## API & Chat Issues

### Issue: 500 Error on /api/chat

**Cause**: Multiple possibilities, check logs

**Solution**:
```bash
# 1. Check logs for error details
sudo journalctl -u apex-chatbot -f

# 2. Verify API keys are valid
python -c "
from anthropic import Anthropic
client = Anthropic(api_key='your-key')
msg = client.messages.create(
    model='claude-3-haiku-20240307',
    max_tokens=10,
    messages=[{'role': 'user', 'content': 'Hi'}]
)
print('API is working')
"

# 3. Check message length
# Max 5000 characters

# 4. Check for rate limiting
# API key might be rate limited
```

---

### Issue: API returns "Chatbot not initialized"

**Cause**: Chatbot failed to initialize on startup

**Solution**:
```bash
# Check detailed error
tail -100 /var/log/apex-chatbot.log

# Verify all API keys are set
python -c "
import os
from dotenv import load_dotenv
load_dotenv()
print('ANTHROPIC_API_KEY:', 'SET' if os.getenv('ANTHROPIC_API_KEY') else 'MISSING')
print('TAVILY_API_KEY:', 'SET' if os.getenv('TAVILY_API_KEY') else 'MISSING')
print('OPENAI_API_KEY:', 'SET' if os.getenv('OPENAI_API_KEY') else 'MISSING')
"

# Restart application
sudo systemctl restart apex-chatbot
```

---

### Issue: Chatbot returns "Unable to process your request"

**Cause**: LLM API call failed after retries

**Solution**:
```bash
# 1. Check circuit breaker status
curl http://localhost:5000/api/status | grep -A 10 anthropic

# 2. If circuit is OPEN, wait for recovery timeout
# Default: 60 seconds

# 3. Check API quota
# Visit Anthropic dashboard to verify credit

# 4. Check API key validity
# Check if key format is correct: sk-ant-...

# 5. Check network connectivity
ping api.anthropic.com
curl -I https://api.anthropic.com

# 6. Temporarily increase timeout
export API_TIMEOUT=60
systemctl restart apex-chatbot
```

---

### Issue: Web search not working

**Cause**: Tavily API key not set or invalid

**Solution**:
```bash
# Check if TAVILY_API_KEY is set
echo $TAVILY_API_KEY

# If not set, add to .env
echo "TAVILY_API_KEY=tvly-..." >> .env

# Verify API key format
# Should start with 'tvly-'

# Check circuit breaker status
curl http://localhost:5000/api/status | grep -A 10 tavily

# Test web search manually
python -c "
from tavily import TavilyClient
client = TavilyClient(api_key='your-key')
results = client.search('test query', max_results=5)
print('Web search is working')
"
```

---

### Issue: Responses are always from web search, never RAG

**Cause**: Query not recognized as company question

**Solution**:
```bash
# Check company keywords
# Try quoting company name or service names exactly:
# "What is Apex Residences?" instead of "Tell me about the company"

# Manually check query classification
python -c "
from chatbot.premium_chatbot import PremiumChatbot
chatbot = PremiumChatbot()
query = 'What services do you offer?'
is_company = chatbot._is_company_question(query)
print(f'Is company question: {is_company}')
"

# If still not working, update company keywords in premium_chatbot.py
```

---

### Issue: RAG not retrieving relevant information

**Cause**: Embeddings or vector store issue

**Solution**:
```bash
# 1. Check if RAG engine initialized correctly
python -c "
from chatbot.rag_engine import RAGEngine
engine = RAGEngine()
print('RAG initialized successfully')
"

# 2. Verify knowledge base file
head -20 company_info.md

# 3. Check embeddings being used
python -c "
from chatbot.rag_engine import RAGEngine
engine = RAGEngine()
print(f'Embeddings model: {engine.embeddings}')
"

# 4. If using OpenAI embeddings, verify API key
export OPENAI_API_KEY=sk-...
python app.py --web

# 5. Force rebuild of FAISS index
rm -f .faiss_index
python app.py --web  # Will rebuild

# 6. Test RAG directly
python -c "
from chatbot.rag_engine import RAGEngine
engine = RAGEngine()
context, scores = engine.retrieve_context('pricing', top_k=3)
print('Results:', context)
print('Scores:', scores)
"
```

---

## Database Issues

### Issue: "database is locked" error

**Cause**: SQLite file locked by another process

**Solution**:
```bash
# Check which process is using database
lsof | grep apex_chatbot.db

# Kill the process
kill -9 <PID>

# Or use WAL (Write-Ahead Logging) mode for SQLite
python -c "
import sqlite3
conn = sqlite3.connect('apex_chatbot.db')
conn.execute('PRAGMA journal_mode=WAL')
conn.close()
"
```

---

### Issue: Database connection failed

**Cause**: Invalid DATABASE_URL or PostgreSQL not running

**Solution**:
```bash
# 1. Verify DATABASE_URL format
echo $DATABASE_URL

# PostgreSQL: postgresql://user:password@localhost:5432/database
# SQLite: sqlite:///apex_chatbot.db

# 2. Check PostgreSQL is running
sudo systemctl status postgresql

# 3. Test database connection
python -c "
from sqlalchemy import create_engine
engine = create_engine('postgresql://user:password@localhost/apex_chatbot')
connection = engine.connect()
print('Database connection successful')
connection.close()
"

# 4. Check database credentials
psql -h localhost -U apex_user -d apex_chatbot

# 5. If PostgreSQL not running
sudo systemctl start postgresql
```

---

### Issue: Conversation history not persisting

**Cause**: Database not enabled or not configured correctly

**Solution**:
```bash
# Check if persistence is enabled
curl http://localhost:5000/api/status | grep persistence_enabled

# If false, enable in code or environment
export ENABLE_PERSISTENCE=true

# Verify DATABASE_URL
echo $DATABASE_URL

# Check database connection
python -c "
from chatbot.database import DatabaseManager
db = DatabaseManager()
print('Database connection successful')
"

# Check if messages are being saved
sqlite3 apex_chatbot.db 'SELECT COUNT(*) FROM messages;'
```

---

## Performance Issues

### Issue: Slow response times (>5 seconds)

**Cause**: Multiple possible causes

**Solution**:
```bash
# 1. Check what source is being used
# Company queries (RAG) should be 200-500ms
# Web search queries should be 500-2000ms
# Tool queries should be 100-300ms

# 2. Check circuit breaker status
curl http://localhost:5000/api/status

# 3. Check network connectivity
ping api.anthropic.com
ping tavily.com

# 4. Check system resources
top -n 1 | head -20
df -h
free -h

# 5. If RAG is slow, check vector store size
wc -c apex_chatbot.db

# 6. Increase API timeout temporarily
export API_TIMEOUT=60
```

---

### Issue: Memory usage growing (memory leak)

**Cause**: In-memory history or vector store growing

**Solution**:
```bash
# 1. Limit conversation history
export MAX_HISTORY=3

# 2. Enable conversation persistence
export ENABLE_PERSISTENCE=true

# 3. Clear conversation history periodically
curl -X DELETE http://localhost:5000/api/history

# 4. Monitor memory over time
watch -n 5 'free -h'

# 5. Check if FAISS index is growing
du -sh apex_chatbot.db

# 6. Restart application periodically (daily)
# Add cron job:
# 0 2 * * * systemctl restart apex-chatbot
```

---

### Issue: High CPU usage

**Cause**: Embeddings computation or vector search

**Solution**:
```bash
# 1. Check which process is using CPU
top -p $(pidof python)

# 2. Disable expensive operations
# - Use HuggingFace embeddings instead of OpenAI
# - Reduce conversation history
# - Reduce RAG top_k parameter

# 3. Check if in development mode
# Disable debug mode in production:
export FLASK_ENV=production

# 4. Profile application
python -m cProfile -s cumulative app.py

# 5. Switch to async processing for long operations
```

---

## Web Interface Issues

### Issue: Web pages not loading (blank page, 404)

**Cause**: Static files not found or Flask not serving them

**Solution**:
```bash
# 1. Verify static files exist
ls -la static/
ls -la static/index.html
ls -la static/script.js
ls -la static/style.css

# 2. Restart Flask application
sudo systemctl restart apex-chatbot

# 3. Clear browser cache
# Ctrl+Shift+Delete in most browsers

# 4. Check Nginx configuration if using proxy
sudo nginx -t

# 5. Check file permissions
sudo chown -R www-data:www-data /opt/apex-chatbot/static
```

---

### Issue: Styles not applied, font broken (unstyled page)

**Cause**: CSS file not loading

**Solution**:
```bash
# 1. Check CSS file exists and is readable
ls -la static/style.css
file static/style.css

# 2. Verify Content-Type header
curl -I http://localhost:5000/static/style.css
# Should be: Content-Type: text/css

# 3. Clear browser cache
# Hard refresh: Ctrl+Shift+R (Windows) or Cmd+Shift+R (Mac)

# 4. Check Nginx cache settings
# In nginx config, ensure:
# expires 1d;  # or other appropriate value
```

---

### Issue: "Cannot send message" or send button not responding

**Cause**: JavaScript error or API not responding

**Solution**:
```bash
# 1. Open browser console (F12)
# Look for JavaScript errors

# 2. Check network tab
# Verify POST /api/chat requests are being made

# 3. Check if /api/chat is responding
curl -X POST http://localhost:5000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "test"}'

# 4. Check CORS configuration
# If API and frontend on different domains, setup CORS

# 5. Check message content
# Verify message is not empty and under 5000 chars

# 6. Check browser console for errors
# Look for fetch() errors or CORS errors
```

---

## Circuit Breaker Issues

### Issue: Circuit breaker stuck OPEN

**Cause**: Service consistently failing

**Solution**:
```bash
# 1. Check circuit breaker status
curl http://localhost:5000/api/status

# 2. Wait for recovery timeout
# Anthropic: 60 seconds
# Tavily: 30 seconds

# 3. Check why service is failing
# - API key invalid?
# - Rate limited?
# - Service down?

# 4. Manually reset circuit breaker
python -c "
from chatbot.premium_chatbot import PremiumChatbot
chatbot = PremiumChatbot()
chatbot.anthropic_breaker.reset()
chatbot.tavily_breaker.reset()
print('Circuit breakers reset')
"

# 5. Restart application
sudo systemctl restart apex-chatbot
```

---

## Deployment Issues

### Issue: Application won't start after deployment

**Cause**: Code errors or configuration issues

**Solution**:
```bash
# 1. Check syntax errors
python -m py_compile chatbot/premium_chatbot.py
python -m py_compile chatbot/api.py

# 2. Run in foreground to see errors
python app.py --web

# 3. Check recent changes
git log --oneline -5
git diff HEAD~1

# 4. Rollback to previous version
git revert HEAD
git push origin main

# 5. Check environment variables
env | grep ANTHROPIC_API_KEY
env | grep TAVILY_API_KEY
```

---

### Issue: Docker container exits immediately

**Cause**: Application crashes on startup

**Solution**:
```bash
# 1. Check container logs
docker logs apex-chatbot

# 2. Run interactively to see errors
docker run -it -e ANTHROPIC_API_KEY=sk-ant-... apex-residences-chatbot

# 3. Verify Dockerfile is correct
# Check CMD instruction

# 4. Build with verbose output
docker build --no-cache -t apex:debug .

# 5. Test dependencies in container
docker run -it apex:debug python -c "import anthropic; print('OK')"
```

---

### Issue: Nginx returns 502 Bad Gateway

**Cause**: Flask application not accessible

**Solution**:
```bash
# 1. Verify Flask is running
ps aux | grep python
# Should see: python app.py --web

# 2. Check Flask port
netstat -tlnp | grep 5000

# 3. Check Nginx configuration
cat /etc/nginx/sites-enabled/apex-chatbot
# Verify upstream port matches Flask port

# 4. Test Nginx proxy locally
curl http://127.0.0.1:5000/api/health

# 5. Restart Flask
sudo systemctl restart apex-chatbot

# 6. Restart Nginx
sudo systemctl restart nginx

# 7. Check Nginx error log
sudo tail -50 /var/log/nginx/error.log
```

---

## Common Error Messages

### "circuit breaker is OPEN"

**Meaning**: Service has failed repeatedly and is temporarily unavailable

**Action**:
- Wait for recovery timeout (60s for Claude, 30s for Tavily)
- Check service status: `curl /api/status`
- Verify API key and rate limits
- Check network connectivity

---

### "Failed to initialize RAG Engine"

**Meaning**: Vector store or embeddings initialization failed

**Action**:
- Check `company_info.md` exists
- Verify OPENAI_API_KEY is valid (if using OpenAI)
- Try with HuggingFace embeddings (default)
- Check disk space for FAISS index

---

### "No embeddings provider available"

**Meaning**: Both OpenAI and HuggingFace embeddings failed

**Action**:
- Install sentence-transformers: `pip install sentence-transformers`
- Check internet connection for model download
- Verify no disk space issues
- Fallback: Use static knowledge base without RAG

---

## Getting Help

### Check These Resources First
1. [API_DOCUMENTATION.md](API_DOCUMENTATION.md) - API reference
2. [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) - Deployment help
3. Application logs (most helpful resource)
4. `/api/status` endpoint for system health

### Enable Debug Logging
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Report Issues
When reporting, include:
1. Full error message
2. Stack trace from logs
3. Python version and OS
4. Recent configuration changes
5. Steps to reproduce

### Useful Commands for Debugging
```bash
# Test API connectivity
curl -X POST http://localhost:5000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "hello"}'

# Check all logs
journalctl -u apex-chatbot -S "24 hours ago"

# Monitor in real-time
watch -n 1 'curl -s http://localhost:5000/api/status | jq .'

# Database query
sqlite3 apex_chatbot.db "SELECT COUNT(*) FROM messages;"

# Python version check
python --version

# Dependency versions
pip list | grep -E "(anthropic|langchain|flask)" 
```

---

## Performance Optimization Tips

1. **Use HuggingFace embeddings** in production (no API calls)
2. **Enable conversation persistence** to reduce in-memory storage
3. **Limit MAX_HISTORY** to 3-5 exchanges
4. **Use PostgreSQL** instead of SQLite for production
5. **Enable Gzip compression** in Nginx
6. **Setup caching** for RAG queries
7. **Monitor circuit breaker** status regularly
8. **Update dependencies** monthly for security and performance

