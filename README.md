# Apex Residences Premium Chatbot

A sophisticated, AI-powered concierge chatbot for luxury home management services. This application demonstrates advanced retrieval-augmented generation (RAG), multi-source data integration, and conversational AI orchestration.

## Features

- **Dual-Source AI Orchestration**: Seamlessly combines company knowledge base with real-time web search
- **Retrieval-Augmented Generation (RAG)**: Vector-based document retrieval using FAISS and OpenAI embeddings
- **Multi-Turn Conversations**: Context-aware dialogue with conversation history management
- **Web Search Integration**: Real-time internet searches via Tavily API
- **Dual Interfaces**: Both CLI (terminal) and Web browser interfaces
- **Error Resilience**: Automatic retry logic with exponential backoff for API calls
- **Luxury Design**: Premium gold-and-dark theme with polished UI/UX

## Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│                   User Interface                         │
│  ┌──────────────────┐          ┌──────────────────┐    │
│  │   Web Interface  │          │   CLI Interface  │    │
│  │   (Flask + JS)   │          │   (Rich)         │    │
│  └────────┬─────────┘          └────────┬─────────┘    │
└───────────┼──────────────────────────────┼──────────────┘
            │                              │
            └──────────────┬───────────────┘
                          │
        ┌─────────────────┴─────────────────┐
        │   Premium Chatbot Orchestrator     │
        │   (Query Routing & Integration)    │
        └────────┬────────────────┬──────────┘
                 │                │
      ┌──────────┴─┐      ┌───────┴────────┐
      │             │      │                │
    ┌─┴──┐     ┌───┴──┐ ┌─┴──┐          ┌──┴──┐
    │RAG │     │ Web  │ │    │          │ API │
    │Engine    │Search│ │    │          │Call │
    │   │      │      │ │    │          │     │
    └─┬──┘     └─┬────┘ └─┬──┘          └──┬──┘
      │          │        │                 │
   ┌──┴──────┐ ┌─┴──┐  ┌──┴──────┐  ┌──────┴────┐
   │Company  │ │Tavily│ │Claude   │  │Conversation
   │Knowledge│ │API   │ │API  3   │  │History
   │(FAISS)  │ │      │ │Haiku    │  │Management
   └─────────┘ └──────┘ └─────────┘  └───────────┘
```

## Prerequisites

- Python 3.8+
- Required API Keys:
  - `ANTHROPIC_API_KEY` - Claude API (required)
  - `TAVILY_API_KEY` - For web search (optional, graceful degradation if unavailable)
- For RAG Embeddings (choose one):
  - `OPENAI_API_KEY` - OpenAI API for embeddings (optional, recommended for best quality)
  - OR use free HuggingFace embeddings (automatically installed, no API key needed)

**Note**: All required dependencies are in `requirements.txt`, including:
- `sentence-transformers` - For HuggingFace embeddings
- `faiss-cpu` - For vector store (semantic search)
- Both will be installed automatically with `pip install -r requirements.txt`

## Installation

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/DigitalEstateManager.git
cd DigitalEstateManager
```

### 2. Create Virtual Environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables

Create a `.env` file in the project root:

```env
# Required
ANTHROPIC_API_KEY=sk-ant-...

# Optional: Web search
TAVILY_API_KEY=tvly-...

# Optional: High-quality embeddings (RAG will use HuggingFace if not provided)
OPENAI_API_KEY=sk-...
```

Alternatively, set these as system environment variables.

**Embeddings Configuration**:
- If `OPENAI_API_KEY` is set → uses OpenAI embeddings (high quality)
- If not set → automatically uses free HuggingFace embeddings (all-MiniLM-L6-v2)
- No additional configuration needed

## Usage

### Web Interface (Recommended)

```bash
python app.py --web --port 5000
```

Open your browser to `http://localhost:5000`

### CLI Interface (Terminal)

```bash
python app.py --cli
```

### Interactive Menu

```bash
python app.py
```

Displays a menu to choose between CLI and Web interfaces.

## Project Structure

```
DigitalEstateManager/
├── app.py                      # Main entry point
├── requirements.txt            # Python dependencies
├── company_info.md            # Company knowledge base
├── README.md                  # This file
│
├── chatbot/                   # Core chatbot module
│   ├── __init__.py
│   ├── premium_chatbot.py     # Main orchestrator (RAG + Web + LLM)
│   ├── rag_engine.py          # Retrieval-Augmented Generation
│   ├── web_search_engine.py   # Web search via Tavily
│   ├── api.py                 # Flask REST API
│   └── cli.py                 # Terminal interface
│
└── static/                    # Web interface assets
    ├── index.html             # Main page
    ├── script.js              # Frontend logic
    └── style.css              # Luxury styling
```

## API Endpoints

### Health Check

```http
GET /api/health
```

Response:
```json
{
  "status": "healthy",
  "service": "Apex Residences Chatbot",
  "version": "1.0.0"
}
```

### Chat Endpoint

```http
POST /api/chat
Content-Type: application/json

{
  "message": "What services does Apex Residences offer?",
  "include_source": true
}
```

Response:
```json
{
  "response": "Apex Residences offers...",
  "source": "company",
  "timestamp": "2024-04-02T10:30:45.123456",
  "context_used": {
    "company_knowledge": true,
    "web_search": false
  }
}
```

### Conversation History

**Get History:**
```http
GET /api/history
```

**Clear History:**
```http
DELETE /api/history
```

## How It Works

### Query Processing Pipeline

1. **Query Received**: User sends message to chatbot

2. **Query Classification**: System determines if query is about company (RAG) or general knowledge (web)

3. **Context Retrieval**:
   - For company queries: Uses RAG engine to retrieve relevant documents from vector store
   - For general queries: Performs web search via Tavily API

4. **Context Synthesis**: Retrieved context is formatted and included in Claude prompt

5. **Response Generation**: Claude generates response grounded in retrieved context

6. **History Management**: Conversation is stored with context-aware limiting

### RAG Engine

The RAG engine processes company knowledge documents with intelligent embeddings provider selection:

1. Loads `company_info.md` file
2. Splits content into semantic chunks (~500 chars with 100-char overlap)
3. Creates vector embeddings using best available provider:
   - **Primary**: OpenAI's `text-embedding-3-small` (if `OPENAI_API_KEY` set)
   - **Fallback**: Free HuggingFace `all-MiniLM-L6-v2` (no API key needed)
4. Stores embeddings in FAISS (Facebook AI Similarity Search) vector store
5. On query: Performs similarity search to retrieve top-3 most relevant chunks

**Embeddings Provider Strategy**:
- Automatically detects available API keys
- No configuration needed - just set `OPENAI_API_KEY` if available
- Falls back to free HuggingFace option automatically
- Both options provide good quality embeddings for document retrieval

### Error Handling

- **API Failures**: Automatic retry with exponential backoff (up to 3 attempts)
- **Missing Services**: Graceful degradation (e.g., chatbot works without web search)
- **Network Issues**: Timeout handling (30-second default)
- **Rate Limiting**: Respects API rate limits with retry delays

### Conversation Management

- Maintains last 5 exchanges (configurable)
- Context-aware trim for token efficiency
- Preserves conversation history across sessions (API-level)
- Supports history clearing via API

## Configuration Options

### Premium Chatbot

```python
chatbot = PremiumChatbot(
    tavily_api_key="your-key",      # Optional, graceful degradation
    max_history=5,                   # Conversation history size
    knowledge_file="company_info.md", # Knowledge base file
    api_timeout=30,                  # API timeout in seconds
    max_retries=3                    # Retry attempts
)
```

### RAG Engine

```python
rag = RAGEngine(
    knowledge_file="company_info.md",  # Path to knowledge base
    timeout=30                         # API timeout in seconds
)
```

**Embeddings Configuration**:
- Automatically selects best available provider
- If `OPENAI_API_KEY` env var is set → uses OpenAI embeddings
- Otherwise → uses free HuggingFace embeddings (sentence-transformers)
- No additional parameters needed

### Web Search

```python
search = WebSearchEngine(
    api_key="your-tavily-key"
)
```

## Performance Characteristics

- **Response Time**: 2-5 seconds (including API calls)
- **Context Window**: Haiku model (200K token limit)
- **Retrieved Context**: Top 3 most relevant documents
- **Web Results**: Up to 5 search results per query
- **Conversation History**: 5 exchanges (10 messages)

## Best Practices

1. **Company Questions**: Include keywords like "service", "pricing", "team" for RAG routing
2. **Web Questions**: Ask general knowledge questions, news, or facts
3. **Prompt Engineering**: System prompt emphasizes grounding in company knowledge
4. **Context Length**: Conversations trim older messages to manage token usage
5. **Error Recovery**: All API failures have retry logic; no hard failures

## Troubleshooting

### "ANTHROPIC_API_KEY not found"
- Ensure `.env` file exists in project root
- Check environment variables: `echo $ANTHROPIC_API_KEY`

### "RAG Engine initialization failed"
- Ensure `company_info.md` exists in project root
- Install sentence-transformers for HuggingFace embeddings: `pip install sentence-transformers`
- Or set `OPENAI_API_KEY` for OpenAI embeddings
- Check logs for specific error details

### Web search returns no results
- Check `TAVILY_API_KEY` is valid
- Chatbot will gracefully fall back to company knowledge only

### Slow responses
- Check network connectivity
- Verify API keys have appropriate rate limits
- Consider reducing `max_history` to lower token usage
- First embeddings initialization may be slow while downloading HuggingFace model

## 📚 Complete Documentation

This project includes comprehensive documentation for different use cases:

### [API Documentation](API_DOCUMENTATION.md)
Complete REST API reference including:
- All 6 endpoints with detailed examples
- Request/response formats and status codes
- Error handling guide
- Example clients (Python, JavaScript)
- CORS configuration
- Rate limiting recommendations
- Performance considerations

**Quick Links:**
- `POST /api/chat` - Send message to chatbot
- `GET /api/health` - Health check
- `GET /api/status` - Circuit breaker and feature status
- `GET /api/tools` - List available tools
- `GET /api/history` - Get conversation history
- `DELETE /api/history` - Clear conversation

### [Deployment Guide](DEPLOYMENT_GUIDE.md)
Complete deployment instructions for all environments:
- **Development**: Local setup with virtual environment
- **Staging**: Docker and Docker Compose setup
- **Production**:
  - AWS EC2 with Nginx reverse proxy
  - Kubernetes deployment
  - Heroku deployment
- Environment configuration and secrets management
- Database setup (SQLite, PostgreSQL)
- SSL/TLS certificate setup (Let's Encrypt)
- Systemd service configuration
- Monitoring and logging setup
- Security best practices
- Backup and rollback procedures

### [Troubleshooting Guide](TROUBLESHOOTING.md)
Comprehensive troubleshooting for all common issues:
- Quick diagnostics and status checks
- Installation & setup problems (20+ scenarios)
- API and chat issues (8+ scenarios)
- Database problems (3+ scenarios)
- Performance optimization
- Web interface issues
- Circuit breaker debugging
- Deployment troubleshooting
- Common error messages explained
- Performance optimization tips

### Quick Reference

| Topic | Location |
|-------|----------|
| **API Usage** | [API_DOCUMENTATION.md](API_DOCUMENTATION.md#api-usage-examples) |
| **Deployment** | [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) |
| **Troubleshooting** | [TROUBLESHOOTING.md](TROUBLESHOOTING.md) |
| **Docker Setup** | [DEPLOYMENT_GUIDE.md#docker-container-setup](DEPLOYMENT_GUIDE.md#docker-container-setup) |
| **Production Checklist** | [DEPLOYMENT_GUIDE.md#security-considerations](DEPLOYMENT_GUIDE.md#security-considerations) |
| **Error Messages** | [TROUBLESHOOTING.md#common-error-messages](TROUBLESHOOTING.md#common-error-messages) |

## Development

### Running Tests

```bash
python -m pytest test_routing.py -v
```

### Debugging

Enable debug logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Code Style

- Follows PEP 8
- Type hints for all function signatures
- Comprehensive docstrings
- Descriptive variable names

## Recent Improvements

✨ **Version 1.2.0** (Current)
- **Integrated Property Tools**: 6 tools for property search, vendor management, and maintenance scheduling
- **Conversation Persistence**: Full database integration with SQLAlchemy for conversation history and analytics
- **Circuit Breaker Pattern**: Service resilience with automatic recovery mechanisms
- **Comprehensive Documentation**: 
  - Complete API documentation with examples
  - Detailed deployment guides for all platforms (AWS, Docker, Kubernetes, Heroku)
  - Extensive troubleshooting guide covering 30+ scenarios
- **System Status Endpoint**: Real-time visibility into circuit breaker states and feature availability
- **Intent Classification**: Automatic query categorization for analytics

✨ **Version 1.1.1**
- Fixed embeddings provider configuration (removed invalid GitHub Models endpoint)
- Implemented intelligent embeddings fallback chain: OpenAI → HuggingFace
- Added automatic provider detection with graceful degradation
- No API key required for HuggingFace embeddings (free alternative)

✨ **Version 1.1.0**
- Integrated RAG retrieval into response generation
- Added web search context synthesis
- Implemented API call retry logic with exponential backoff
- Enhanced conversation context management with token-aware history
- Added detailed error handling and logging
- Improved system prompts for better context grounding

## Future Enhancements

- [ ] Multi-language support
- [ ] Document memory persistence
- [ ] Response streaming
- [ ] User authentication
- [ ] Analytics dashboard
- [ ] Custom embedding models
- [ ] Function calling for calendar/booking
- [ ] Voice interface support

## License

Proprietary - Apex Residences Premium Services

## Support

For issues or questions, contact: `hello@apexresidences.com`

---

**Last Updated**: April 2, 2026  
**Version**: 1.2.0  
**Status**: Production Ready ✅

## Documentation Status

- ✅ [README.md](README.md) - Project overview and quick start
- ✅ [API_DOCUMENTATION.md](API_DOCUMENTATION.md) - Complete API reference 
- ✅ [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) - Deployment instructions
- ✅ [TROUBLESHOOTING.md](TROUBLESHOOTING.md) - Troubleshooting guide
- ✅ [ASSESSMENT_RUBRIC_RESULTS.md](ASSESSMENT_RUBRIC_RESULTS.md) - Rubric evaluation
- ✅ [IMPLEMENTATION_SUMMARY.md](IMPLEMENTATION_SUMMARY.md) - Recent implementations
