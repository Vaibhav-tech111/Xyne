# Xyne
The Most Advanced AI Coder.
xyne-backend

The Most Advanced AI Coder.

xyne-backend is a modular, highly scalable FastAPI service that routes user prompts to the best AI model, performs real-time search, generates images, and keeps your environment in perfect health. 

---

Table of Contents

- Features  
- Tech Stack  
- Project Structure  
- Getting Started  
  - Prerequisites  
  - Installation  
  - Configuration  
  - Running Locally  
- API Endpoints  
- Environment Health Checks  
- Deployment on Vercel  
- Contributing  
- License  

---

Features

- dynamic model selection based on prompt keywords  
- real-time DuckDuckGo search integration  
- natural text generation via Pollinations AI  
- on-the-fly image creation with Pollinations image API  
- centralized configuration with Pydantic and python-dotenv  
- Redis support for caching or session management  
- strict environment validation and health checks at startup  
- versioned REST API with FastAPI and automatic OpenAPI docs  

---

Tech Stack

- Python 3.10+  
- FastAPI for high-performance web services  
- Uvicorn as ASGI server  
- Pydantic v2 for settings and data validation  
- python-dotenv for environment variable loading  
- Redis (via redis-py) for caching or ephemeral state  
- requests for HTTP integrations  
- google-generativeai, groq, huggingface-hub for model APIs  
- DuckDuckGo Instant Answer API for search  
- Pollinations for text and image generation  

---

Project Structure

`
xyne-backend/
├── main.py                      # FastAPI application entrypoint
├── requirements.txt             # Python dependencies
├── .env.example                 # Environment variable template
├── vercel.json                  # Vercel deployment settings
├── brain_rules.json             # Keyword → model mapping rules
├── core/
│   ├── init.py
│   ├── config.py                # Centralized settings loader
│   └── env_health.py            # Environment validation & logging
├── services/
│   ├── init.py
│   ├── gemini_service.py        # Google Gemini integration
│   ├── groq_service.py          # Groq AI integration
│   ├── hf_service.py            # HuggingFace integration
│   ├── pollinations_service.py  # Pollinations text & image APIs
│   ├── ddg_service.py           # DuckDuckGo search integration
│   └── brain_service.py         # Prompt → model routing logic
└── routers/
    ├── init.py
    └── search.py                # /v1/search endpoint
`

---

Getting Started

Prerequisites

- Python 3.10 or higher  
- Redis server (optional, for caching or sessions)  
- Vercel account (for deployment)  

Installation

1. clone the repo  
   `bash
   git clone https://github.com/your-org/xyne-backend.git
   cd xyne-backend
   `
2. install dependencies  
   `bash
   pip install -r requirements.txt
   `

Configuration

1. copy the example file  
   `bash
   cp .env.example .env
   `
2. open .env and fill in your API keys and any overrides  
   - GEMINIAPIKEY, GROQAPIKEY, HFAPIKEY must be set  
   - adjust POLLINATIONSTEXTURL, POLLINATIONSIMAGEURL if needed  
   - set REDISURL, SESSIONTTL_SECONDS for caching  
   - modify HOST, PORT, ENV, CORSALLOWORIGINS as required  

Running Locally

`bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
`

Visit http://localhost:8000/docs to explore the interactive API documentation.

---

API Endpoints

/v1/search

Perform a real-time search via DuckDuckGo.

- method: GET  
- query parameters:  
  - q (string, required) — search term  
  - limit (integer, default=5) — maximum results (1–20)  
  - safe (boolean, default=true) — safe search toggle  
  - region (string, optional) — ISO region code  

Response model: array of objects  
`json
[
  {
    "title": "Example result title",
    "snippet": "Short description or abstract.",
    "url": "https://example.com/page"
  },
  ...
]
`

---

Environment Health Checks

On startup, core/env_health.py runs a full report:

- verifies presence of required vars (Gemini, Groq, HF keys)  
- validates optional URLs (Pollinations, Redis)  
- ensures integers (port, timeouts) are within valid ranges  
- logs a redacted, structured snapshot  
- in production mode, fails fast if any critical checks fail  

---

Deployment on Vercel

1. push your code to GitHub  
2. configure Vercel project with vercel.json as shown  
3. add environment variables in Vercel dashboard, matching your .env names  
4. Vercel will automatically build and serve main.py with @vercel/python  

Your app will be available at https://<your-vercel-app>.vercel.app

---

Contributing

1. fork the repository  
2. create a feature branch (git checkout -b feature/XYZ)  
3. commit your changes (git commit -m "Add XYZ")  
4. push to your fork (git push origin feature/XYZ)  
5. open a pull request  

Please follow the existing code style and add tests for new functionality.

---

License

This project is licensed under the MIT License.  
See LICENSE for details.
