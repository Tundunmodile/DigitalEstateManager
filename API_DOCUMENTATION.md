# API Documentation

## Overview

The Apex Residences Chatbot provides a RESTful API for chat interactions, conversation management, system status monitoring, and tool discovery. The API is built with Flask and supports JSON request/response format.

**Base URL**: `http://localhost:5000/api`

**Default Port**: 5000 (configurable)

---

## Authentication

Currently, the API does not require authentication. In production, implement:
- API key authentication via headers
- OAuth 2.0 for multi-user scenarios
- JWT tokens for session management

---

## Response Format

### Success Response
```json
{
  "response": "Chatbot response text",
  "source": "company|web|tools|error",
  "timestamp": "2026-04-02T14:30:45.123456",
  "context_used": {
    "company_knowledge": true,
    "web_search": false,
    "tools": false
  }
}
```

### Error Response
```json
{
  "error": "Description of the error"
}
```

---

## Endpoints

### 1. Chat Endpoint

**POST** `/api/chat`

Send a message and receive a chatbot response.

#### Request Body
```json
{
  "message": "What services do you offer?",
  "include_source": true
}
```

**Parameters:**
- `message` (string, required): User's question or message (max 5000 characters)
- `include_source` (boolean, optional): Include source attribution in response (default: true)

#### Response
```json
{
  "response": "Apex Residences offers comprehensive home management services...",
  "source": "company",
  "timestamp": "2026-04-02T14:30:45.123456",
  "context_used": {
    "company_knowledge": true,
    "web_search": false,
    "tools": false
  }
}
```

#### Status Codes
- `200 OK` - Successfully processed
- `400 Bad Request` - Missing or invalid message
- `500 Internal Server Error` - Server error

#### Example Request (cURL)
```bash
curl -X POST http://localhost:5000/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Tell me about your pricing tiers",
    "include_source": true
  }'
```

#### Example Request (Python)
```python
import requests

url = "http://localhost:5000/api/chat"
payload = {
    "message": "What is your team's background?",
    "include_source": True
}

response = requests.post(url, json=payload)
data = response.json()
print(data["response"])
print(f"Source: {data['source']}")
```

#### Example Request (JavaScript/Node.js)
```javascript
const message = "How much does the Premium tier cost?";

fetch('/api/chat', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    message: message,
    include_source: true
  })
})
.then(response => response.json())
.then(data => {
  console.log("Response:", data.response);
  console.log("Source:", data.source);
});
```

---

### 2. Conversation History Endpoint

**GET** `/api/history`

Retrieve the current conversation history.

#### Response
```json
{
  "history": [
    {
      "role": "user",
      "content": "What services do you offer?"
    },
    {
      "role": "assistant",
      "content": "Apex Residences provides comprehensive home management services..."
    }
  ]
}
```

#### Status Codes
- `200 OK` - Successfully retrieved
- `500 Internal Server Error` - Server error

#### Example Request
```bash
curl http://localhost:5000/api/history
```

---

### 3. Clear History Endpoint

**DELETE** `/api/history`

Clear the conversation history for current session.

#### Response
```json
{
  "message": "History cleared"
}
```

#### Status Codes
- `200 OK` - Successfully cleared
- `500 Internal Server Error` - Server error

#### Example Request
```bash
curl -X DELETE http://localhost:5000/api/history
```

---

### 4. Health Check Endpoint

**GET** `/api/health`

Check if the service is running and healthy.

#### Response
```json
{
  "status": "healthy",
  "service": "Apex Residences Chatbot",
  "version": "1.0.0"
}
```

#### Status Codes
- `200 OK` - Service is healthy

#### Example Request
```bash
curl http://localhost:5000/api/health
```

---

### 5. System Status Endpoint

**GET** `/api/status`

Get detailed system status including circuit breaker states and feature availability.

#### Response
```json
{
  "service": "Apex Residences Chatbot",
  "status": "healthy",
  "conversation_id": "abc123def456",
  "persistence_enabled": true,
  "tools_enabled": true,
  "circuit_breakers": {
    "anthropic_api": {
      "name": "anthropic_api",
      "state": "closed",
      "failures": 0,
      "successes": 42,
      "last_failure": null,
      "time_until_retry": 0
    },
    "tavily_api": {
      "name": "tavily_api",
      "state": "closed",
      "failures": 0,
      "successes": 8,
      "last_failure": null,
      "time_until_retry": 0
    }
  }
}
```

**Circuit Breaker States:**
- `closed` - Service operating normally
- `open` - Service unavailable, rejecting requests
- `half-open` - Testing if service recovered

#### Status Codes
- `200 OK` - Status retrieved successfully
- `500 Internal Server Error` - Server error

#### Example Request
```bash
curl http://localhost:5000/api/status
```

---

### 6. Tools Endpoint

**GET** `/api/tools`

List all available tools that the chatbot can use.

#### Response
```json
{
  "tools": [
    {
      "name": "search_properties",
      "description": "Search for properties by address or type. Returns matching properties."
    },
    {
      "name": "get_property_details",
      "description": "Get detailed information about a specific property including features and maintenance status."
    },
    {
      "name": "get_maintenance_history",
      "description": "Get maintenance history for a property."
    },
    {
      "name": "search_vendors",
      "description": "Search for trusted vendors by category (e.g., HVAC, Plumbing, Electrical)."
    },
    {
      "name": "get_vendor_details",
      "description": "Get detailed information about a specific vendor."
    },
    {
      "name": "schedule_maintenance",
      "description": "Schedule maintenance for a property with a trusted vendor."
    },
    {
      "name": "get_scheduled_maintenance",
      "description": "Get upcoming scheduled maintenance for a property."
    }
  ],
  "count": 7
}
```

#### Status Codes
- `200 OK` - Tools retrieved
- `500 Internal Server Error` - Server error

#### Example Request
```bash
curl http://localhost:5000/api/tools
```

---

## Response Source Attribution

The `source` field indicates where the response content originated:

| Source | Meaning |
|--------|---------|
| `company` | Information from company knowledge base (company_info.md) |
| `web` | Information from web search (Tavily API) |
| `tools` | Information from executed tools (property database, vendor database) |
| `error` | Error occurred; fallback message provided |

---

## Error Handling

### Common Error Responses

**Missing Required Parameter**
```json
{
  "error": "Missing 'message' in request body"
}
```
Status: 400

**Message Too Long**
```json
{
  "error": "Message too long (max 5000 characters)"
}
```
Status: 400

**Empty Message**
```json
{
  "error": "Message cannot be empty"
}
```
Status: 400

**API Not Available**
```json
{
  "error": "Chatbot not initialized"
}
```
Status: 500

---

## Rate Limiting

Currently, no rate limiting is implemented. For production deployment, consider:
- Request-per-second limits (e.g., 10 req/sec per IP)
- Burst limits (e.g., 100 requests per minute)
- User-level quotas for authenticated users

---

## Pagination

Not applicable for current endpoints. Future endpoints may support:
- `limit`: Number of results (default: 50)
- `offset`: Starting position (default: 0)

---

## Query Parameters

### Chat Endpoint Parameters
- `include_source` (boolean): Whether to include source information

Example:
```
POST /api/chat?include_source=false
```

---

## Content Types

- **Request**: `application/json`
- **Response**: `application/json`

---

## CORS

CORS is enabled for local development:
- Origin: `*` (all origins allowed in development)
- For production, restrict to specific domains

---

## Performance Considerations

### Response Time
- Company knowledge queries: 200-500ms (RAG retrieval)
- Web search queries: 500-2000ms (API latency)
- Tool execution: 100-300ms (database queries)
- Total: 300-2500ms depending on query type

### Timeout Configuration
- Default API timeout: 30 seconds
- Web search timeout: 10 seconds
- Configure via environment or code

### Conversation History Limits
- In-memory history: Last 5 exchanges (configurable)
- Database history: Unlimited
- Message size: Max 5000 characters per message

---

## API Usage Examples

### Example 1: Company Information Query
```bash
curl -X POST http://localhost:5000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "What is the Premium tier pricing?"}'
```

### Example 2: Web Search Query
```bash
curl -X POST http://localhost:5000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "What is the current weather in New York?"}'
```

### Example 3: Property Search Tool
```bash
curl -X POST http://localhost:5000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Search for properties on Park Avenue"}'
```

### Example 4: Vendor Search Tool
```bash
curl -X POST http://localhost:5000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Find HVAC vendors"}'
```

### Example 5: Multi-turn Conversation
```bash
# Message 1
curl -X POST http://localhost:5000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "What is your concierge service?"}'

# Message 2 (context maintained)
curl -X POST http://localhost:5000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Is it available 24/7?"}'

# Message 3 (still maintains conversation context)
curl -X POST http://localhost:5000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "How do I contact them?"}'
```

---

## SDK / Client Library Examples

### Python Client
```python
import requests
import json

class ApexResidencesClient:
    def __init__(self, base_url="http://localhost:5000"):
        self.base_url = base_url
    
    def chat(self, message, include_source=True):
        """Send a message and get response."""
        url = f"{self.base_url}/api/chat"
        response = requests.post(url, json={
            "message": message,
            "include_source": include_source
        })
        return response.json()
    
    def get_history(self):
        """Get conversation history."""
        url = f"{self.base_url}/api/history"
        response = requests.get(url)
        return response.json()
    
    def clear_history(self):
        """Clear conversation."""
        url = f"{self.base_url}/api/history"
        response = requests.delete(url)
        return response.json()
    
    def health(self):
        """Check if service is healthy."""
        url = f"{self.base_url}/api/health"
        response = requests.get(url)
        return response.json()

# Usage
client = ApexResidencesClient()
response = client.chat("What services do you offer?")
print(response["response"])
```

### JavaScript Client
```javascript
class ApexResidencesClient {
  constructor(baseUrl = "http://localhost:5000") {
    this.baseUrl = baseUrl;
  }

  async chat(message, includeSource = true) {
    const response = await fetch(`${this.baseUrl}/api/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message, include_source: includeSource })
    });
    return response.json();
  }

  async getHistory() {
    const response = await fetch(`${this.baseUrl}/api/history`);
    return response.json();
  }

  async clearHistory() {
    const response = await fetch(`${this.baseUrl}/api/history`, {
      method: 'DELETE'
    });
    return response.json();
  }
}

// Usage
const client = new ApexResidencesClient();
const result = await client.chat("Tell me about your team");
console.log(result.response);
```

---

## Versioning

Current API version: 1.0.0

### Future Versions
- v1.1: Tool-use integration for Claude
- v2.0: Multi-user authentication
- v2.1: Advanced analytics endpoints

---

## Backward Compatibility

API changes follow semantic versioning:
- **Patch (1.0.x)**: Bug fixes, no breaking changes
- **Minor (1.x)**: New features, backward compatible
- **Major (2.0)**: Breaking changes

---

## Deprecation Policy

Deprecated endpoints will:
1. Be marked with warning in response headers
2. Continue functioning for 6 months
3. Be removed in next major version
4. Have migration guide provided

---

## Support & Issues

For API issues:
1. Check [Troubleshooting Guide](TROUBLESHOOTING.md)
2. Review error responses carefully
3. Check status endpoint: `/api/status`
4. Review logs for detailed error information
5. Submit issue with endpoint, request, and error

