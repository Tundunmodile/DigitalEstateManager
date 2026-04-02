# Documentation Quick Reference

##  Quick Start

**Installation & Running** (5 minutes):
```bash
git clone <repo>
cd DigitalEstateManager
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
echo "ANTHROPIC_API_KEY=sk-ant-..." > .env
python app.py --web
```

Open: http://localhost:5000

---

## 📖 Documentation Map

### For Different Audiences

#### I want to... | Go to...
|---|---|
| Use the chatbot | Quick Start above + [README.md](README.md#usage) |
| Integrate with my app | [API_DOCUMENTATION.md](API_DOCUMENTATION.md) |
| Deploy to production | [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) |
| Fix an issue | [TROUBLESHOOTING.md](TROUBLESHOOTING.md) |
| Check API endpoints | [API_DOCUMENTATION.md#endpoints](API_DOCUMENTATION.md#endpoints) |
| Deploy with Docker | [DEPLOYMENT_GUIDE.md#docker-container-setup](DEPLOYMENT_GUIDE.md#docker-container-setup) |
| Deploy on AWS | [DEPLOYMENT_GUIDE.md#aws-ec2-deployment](DEPLOYMENT_GUIDE.md#aws-ec2-deployment) |
| Deploy on Kubernetes | [DEPLOYMENT_GUIDE.md#kubernetes-deployment](DEPLOYMENT_GUIDE.md#kubernetes-deployment) |
| Setup with Nginx | [DEPLOYMENT_GUIDE.md#setup-nginx-reverse-proxy](DEPLOYMENT_GUIDE.md#setup-nginx-reverse-proxy) |
| Configure SSL | [DEPLOYMENT_GUIDE.md#setup-ssl-certificate-lets-encrypt](DEPLOYMENT_GUIDE.md#setup-ssl-certificate-lets-encrypt) |
| Understand error messages | [TROUBLESHOOTING.md#common-error-messages](TROUBLESHOOTING.md#common-error-messages) |
| Check API health | `curl http://localhost:5000/api/health` |
| See available tools | `curl http://localhost:5000/api/tools` |
| Monitor system status | `curl http://localhost:5000/api/status` |

---

## 🔧 Common Tasks

### Send a Chat Message
```bash
curl -X POST http://localhost:5000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "What services do you offer?"}'
```
📖 See: [API_DOCUMENTATION.md#chat-endpoint](API_DOCUMENTATION.md#chat-endpoint)

### Get Conversation History
```bash
curl http://localhost:5000/api/history
```
📖 See: [API_DOCUMENTATION.md#conversation-history-endpoint](API_DOCUMENTATION.md#conversation-history-endpoint)

### Get System Status
```bash
curl http://localhost:5000/api/status
```
📖 See: [API_DOCUMENTATION.md#system-status-endpoint](API_DOCUMENTATION.md#system-status-endpoint)

### Clear Conversation
```bash
curl -X DELETE http://localhost:5000/api/history
```

### Deploy with Docker
```bash
docker build -t apex-chatbot .
docker run -p 5000:5000 \
  -e ANTHROPIC_API_KEY=sk-ant-... \
  apex-chatbot
```
📖 See: [DEPLOYMENT_GUIDE.md#docker-container-setup](DEPLOYMENT_GUIDE.md#docker-container-setup)

### Deploy with Docker Compose
```bash
docker-compose up -d
```
📖 See: [DEPLOYMENT_GUIDE.md#docker-compose-setup](DEPLOYMENT_GUIDE.md#docker-compose-setup)

---

##  Troubleshooting Quick Links

| Issue | Solution |
|-------|----------|
| "ANTHROPIC_API_KEY not found" | [Link](TROUBLESHOOTING.md#issue-anthropic_api_key-not-found) |
| Port 5000 already in use | [Link](TROUBLESHOOTING.md#issue-port-5000-already-in-use) |
| "Chatbot not initialized" | [Link](TROUBLESHOOTING.md#issue-api-returns-chatbot-not-initialized) |
| Web search not working | [Link](TROUBLESHOOTING.md#issue-web-search-not-working) |
| Slow responses | [Link](TROUBLESHOOTING.md#issue-slow-response-times--5-seconds) |
| Circuit breaker stuck OPEN | [Link](TROUBLESHOOTING.md#issue-circuit-breaker-stuck-open) |
| Docker container exits | [Link](TROUBLESHOOTING.md#issue-docker-container-exits-immediately) |
| Nginx 502 Bad Gateway | [Link](TROUBLESHOOTING.md#issue-nginx-returns-502-bad-gateway) |

---

## 📊 API Endpoints at a Glance

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/chat` | POST | Send message to chatbot |
| `/api/health` | GET | Health check |
| `/api/status` | GET | System status & circuit breakers |
| `/api/history` | GET | Get conversation history |
| `/api/history` | DELETE | Clear conversation |
| `/api/tools` | GET | List available tools |

📖 Full documentation: [API_DOCUMENTATION.md](API_DOCUMENTATION.md)

---

## 🚀 Deployment Platforms

| Platform | Guide | Difficulty |
|----------|-------|-----------|
| Local Development | [README.md](README.md#usage) | ⭐ Easy |
| Docker | [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md#docker-container-setup) | ⭐ Easy |
| Docker Compose | [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md#docker-compose-setup) | ⭐ Easy |
| AWS EC2 | [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md#aws-ec2-deployment) | ⭐⭐ Medium |
| Kubernetes | [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md#kubernetes-deployment) | ⭐⭐⭐ Advanced |
| Heroku | [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md#heroku-deployment) | ⭐ Easy |

---

## ⚙️ Configuration Reference

### Environment Variables
```bash
# Required
ANTHROPIC_API_KEY=sk-ant-...

# Optional
TAVILY_API_KEY=tvly-...
OPENAI_API_KEY=sk-...
FLASK_ENV=production
DATABASE_URL=postgresql://...
PORT=5000
```

📖 See: [DEPLOYMENT_GUIDE.md#environment-variables](DEPLOYMENT_GUIDE.md#environment-variables)

### Python Configuration
```python
PremiumChatbot(
    tavily_api_key="...",       # Optional
    max_history=5,              # Conversation history size
    knowledge_file="company_info.md",
    api_timeout=30,             # Seconds
    max_retries=3
)
```

📖 See: [README.md#configuration-options](README.md#configuration-options)

---

## 📈 Features Overview

### Data Sources
- 🏢 **Company Knowledge (RAG)** - Semantic search over company_info.md
- 🌐 **Web Search** - Real-time internet search via Tavily
- 🔧 **Tools** - Property search, vendor lookup, maintenance scheduling
- 📊 **Analytics** - Query intent tracking and conversation analytics

### AI Capabilities
- 🤖 **Claude 3 Haiku** - Fast, capable LLM (200K context window)
- 🧠 **Intelligent Routing** - Determines best data source for each query
- 💬 **Multi-turn Context** - Maintains conversation history (configurable)
- 🔄 **Automatic Retries** - Exponential backoff with circuit breaker protection

### Interfaces
- 🌐 **Web Interface** - Luxury design with gold/dark theme
- 📱 **REST API** - Full-featured API with 6 endpoints
- 💻 **CLI Interface** - Rich terminal UI
- 📊 **Status Dashboard** - Circuit breaker and feature status

### Reliability
- 🔌 **Circuit Breaker** - Protects against cascading failures
- 💾 **Conversation Persistence** - Database storage with analytics
- ⚡ **Graceful Degradation** - Works without optional services
- 📝 **Comprehensive Logging** - Debug information for all operations

---

## 🆘 Getting Help

1. **Quick Questions**: Check [README.md](README.md)
2. **API Usage**: See [API_DOCUMENTATION.md](API_DOCUMENTATION.md)
3. **Having Issues**: Go to [TROUBLESHOOTING.md](TROUBLESHOOTING.md)
4. **Deployment Help**: Read [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)
5. **Still Stuck**: Check [TROUBLESHOOTING.md#getting-help](TROUBLESHOOTING.md#getting-help)

---

## 📚 Full Documentation Files

| File | Purpose | Size |
|------|---------|------|
| [README.md](README.md) | Overview, quick start, features | ~5 KB |
| [API_DOCUMENTATION.md](API_DOCUMENTATION.md) | Complete API reference | ~30 KB |
| [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) | Deployment for all platforms | ~35 KB |
| [TROUBLESHOOTING.md](TROUBLESHOOTING.md) | Problem solving guide | ~40 KB |
| [ASSESSMENT_RUBRIC_RESULTS.md](ASSESSMENT_RUBRIC_RESULTS.md) | Rubric evaluation | ~15 KB |
| [IMPLEMENTATION_SUMMARY.md](IMPLEMENTATION_SUMMARY.md) | Recent changes | ~10 KB |

**Total**: ~135 KB of comprehensive documentation

---

## 🎯 By Use Case

### 👨‍💻 Developer
1. Read: [README.md](README.md)
2. Try: [Quick Start](#-quick-start) above
3. Explore: [API_DOCUMENTATION.md](API_DOCUMENTATION.md)
4. Integrate: Build with provided API examples

### 🔧 DevOps Engineer
1. Read: [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) for your platform
2. Configure: Environment variables and secrets
3. Monitor: Use `/api/status` endpoint
4. Troubleshoot: [TROUBLESHOOTING.md](TROUBLESHOOTING.md)

### 👨‍💼 Operations/Manager
1. Understand: [README.md#how-it-works](README.md#how-it-works)
2. Monitor: Use `/api/status` for health
3. Scale: See [DEPLOYMENT_GUIDE.md#performance-tuning](DEPLOYMENT_GUIDE.md#performance-tuning)
4. Troubleshoot: [TROUBLESHOOTING.md](TROUBLESHOOTING.md)

### 🚀 Product Manager
1. Overview: [README.md#features](README.md#features)
2. Capabilities: [README.md#tools-endpoint](README.md#api-endpoints)
3. Roadmap: [README.md#future-enhancements](README.md#future-enhancements)

---

## ✅ Pre-Deployment Checklist

- [ ] All API keys configured
- [ ] Database validated (if using PostgreSQL)
- [ ] SSL certificate obtained (production)
- [ ] Environment variables set
- [ ] Nginx config tested: `sudo nginx -t`
- [ ] Systemd service created: `sudo systemctl status apex-chatbot`
- [ ] Backup strategy in place
- [ ] Monitoring setup complete
- [ ] Rollback plan documented
- [ ] Team trained on troubleshooting

📖 See: [DEPLOYMENT_GUIDE.md#maintenance--updates](DEPLOYMENT_GUIDE.md#maintenance--updates)

---

**Last Updated**: April 2, 2026  
**Documentation Version**: 1.2.0
