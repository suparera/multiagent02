# glmpython

FastAPI proxy server that calls the z.ai GLM-5.1 model via the Anthropic-compatible API endpoint, exposing an OpenAI-compatible `/v1/chat/completions` interface.

## Setup

1. Install dependencies:

```bash
uv sync
```

2. Set your API key in `.env`:

```
GLM_API_KEY=your-api-key-here
```

Get an API key from [z.ai](https://z.ai).

## Usage

Start the server:

```bash
python main.py
```

The server runs on `http://0.0.0.0:8000`.

### Send a request

```bash
curl http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "glm-5.1",
    "messages": [{"role": "user", "content": "Hello!"}],
    "stream": false
  }'
```

### Streaming

```bash
curl http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "glm-5.1",
    "messages": [{"role": "user", "content": "Hello!"}],
    "stream": true
  }'
```

## Features

- OpenAI-compatible request/response format
- Streaming (SSE) support
- Tool calling (function calling) support
- Response caching with 5-minute TTL
- Automatic retry with exponential backoff on 429 errors
- Tool call loop guard (max 20 rounds)
- Old tool context trimming to reduce token cost
