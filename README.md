# Reddit AI Content Manager

A self-hosted application that uses Azure OpenAI to generate content and publishes it to Reddit communities with intelligent scheduling.

## Architecture

```
┌──────────────────────────────────────────────────┐
│                  React Dashboard                  │
│  (Content creation, approval, scheduling, stats)  │
└──────────────┬───────────────────────────────────┘
               │ REST API
┌──────────────▼───────────────────────────────────┐
│              FastAPI Backend                       │
│  ┌─────────┐ ┌──────────┐ ┌───────────────────┐  │
│  │  Auth   │ │ Azure AI │ │ Reddit OAuth API  │  │
│  │ Module  │ │ Pipeline │ │    Integration    │  │
│  └─────────┘ └──────────┘ └───────────────────┘  │
│  ┌─────────────────┐ ┌───────────────────────┐   │
│  │ SQLite Database  │ │  APScheduler Queue    │   │
│  └─────────────────┘ └───────────────────────┘   │
└──────────────────────────────────────────────────┘
```

## Quick Start

### 1. Prerequisites
- Python 3.10+
- Node.js 18+
- A Reddit account + registered app (script type)
- An Azure OpenAI resource with a deployed model

### 2. Backend Setup

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your credentials
python main.py
```

### 3. Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

### 4. Reddit App Registration
1. Go to https://www.reddit.com/prefs/apps
2. Click "create another app..."
3. Select "web app"
4. Set redirect URI to: `http://localhost:8000/api/auth/reddit/callback`
5. Note your client_id and client_secret

### 5. Azure OpenAI Setup
1. Create an Azure OpenAI resource in Azure Portal
2. Deploy your model (e.g., gpt-5-mini)
3. Copy the endpoint URL, API key, and deployment name to .env

## Environment Variables

See `backend/.env.example` for all required configuration.
