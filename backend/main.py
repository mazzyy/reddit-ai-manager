"""
Reddit AI Content Manager — FastAPI Backend
============================================
All API routes for auth, content generation, subreddit management,
post approval, and scheduled publishing.
"""

import os
import json
import secrets
import logging
from datetime import datetime, timedelta
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Depends, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()

from database import (
    init_db, save_reddit_token, get_reddit_token,
    create_post, get_posts, get_post, update_post, delete_post,
    save_subreddits, get_saved_subreddits, mark_subreddit_joined,
    get_jobs_for_post, get_pending_jobs,
)
from azure_ai import generate_content, refine_content, test_connection
from reddit_api import (
    build_auth_url, exchange_code_for_token, get_reddit_identity,
    search_subreddits, subscribe_to_subreddit, unsubscribe_from_subreddit,
    get_my_subreddits,
)
from scheduler import schedule_post_publishing, start_scheduler, shutdown_scheduler

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("main")

# ── Simple session store (for single-user local app) ──
sessions: dict[str, dict] = {}

APP_USERNAME = os.getenv("APP_USERNAME", "admin")
APP_PASSWORD = os.getenv("APP_PASSWORD", "admin")
APP_SECRET = os.getenv("APP_SECRET_KEY", secrets.token_hex(32))


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    start_scheduler()
    logger.info("🚀 Reddit AI Manager is running")
    yield
    shutdown_scheduler()


app = FastAPI(
    title="Reddit AI Content Manager",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ═══════════════════════════════════════════════════
#  AUTH — Local session + Reddit OAuth
# ═══════════════════════════════════════════════════

def get_session(request: Request) -> dict:
    sid = request.cookies.get("session_id")
    if sid and sid in sessions:
        return sessions[sid]
    raise HTTPException(status_code=401, detail="Not authenticated")


class LoginRequest(BaseModel):
    username: str
    password: str


@app.post("/api/auth/login")
async def login(body: LoginRequest, response: Response):
    if body.username == APP_USERNAME and body.password == APP_PASSWORD:
        sid = secrets.token_hex(32)
        sessions[sid] = {"user": body.username, "logged_in_at": datetime.utcnow().isoformat()}
        response.set_cookie("session_id", sid, httponly=True, samesite="lax", max_age=86400)
        return {"status": "ok", "message": "Logged in"}
    raise HTTPException(status_code=401, detail="Invalid credentials")


@app.post("/api/auth/logout")
async def logout(request: Request, response: Response):
    sid = request.cookies.get("session_id")
    if sid and sid in sessions:
        del sessions[sid]
    response.delete_cookie("session_id")
    return {"status": "ok"}


@app.get("/api/auth/me")
async def auth_me(session: dict = Depends(get_session)):
    token = await get_reddit_token()
    return {
        "user": session["user"],
        "reddit_connected": token is not None,
        "reddit_username": token.get("reddit_username") if token else None,
    }


# ── Reddit OAuth flow ──

@app.get("/api/auth/reddit/start")
async def reddit_auth_start(session: dict = Depends(get_session)):
    state = secrets.token_hex(16)
    sessions[session["user"] + "_oauth_state"] = state
    url = build_auth_url(state=state)
    return {"auth_url": url}


@app.get("/api/auth/reddit/callback")
async def reddit_auth_callback(code: str, state: str):
    try:
        token_data = await exchange_code_for_token(code)
        # Fetch Reddit username
        identity = await get_reddit_identity(token_data["access_token"])
        token_data["reddit_username"] = identity.get("name", "unknown")
        await save_reddit_token(token_data)
        # Redirect back to dashboard
        return RedirectResponse(url="http://localhost:5173/?reddit=connected")
    except Exception as e:
        logger.error(f"Reddit OAuth error: {e}")
        return RedirectResponse(url=f"http://localhost:5173/?reddit=error&msg={str(e)}")


@app.get("/api/auth/reddit/status")
async def reddit_status(session: dict = Depends(get_session)):
    token = await get_reddit_token()
    if token:
        return {
            "connected": True,
            "username": token.get("reddit_username"),
            "scope": token.get("scope"),
        }
    return {"connected": False}


# ═══════════════════════════════════════════════════
#  AZURE AI — Content Generation
# ═══════════════════════════════════════════════════

class GenerateRequest(BaseModel):
    idea: str
    target_subreddits: list[str] = []
    content_type: str = "reddit_post"
    extra_context: str = ""


@app.post("/api/ai/generate")
async def ai_generate(body: GenerateRequest, session: dict = Depends(get_session)):
    try:
        result = generate_content(
            idea=body.idea,
            target_subreddits=body.target_subreddits,
            content_type=body.content_type,
            extra_context=body.extra_context,
        )
        # Save as a pending post
        post_id = await create_post({
            "title": result.get("title", "Untitled"),
            "body": result.get("body", ""),
            "status": "pending",
            "target_subreddits": body.target_subreddits,
            "tags": body.target_subreddits,
            "original_idea": body.idea,
            "ai_model": os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-5-mini"),
        })
        return {"post_id": post_id, **result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI generation failed: {str(e)}")


class RefineRequest(BaseModel):
    post_id: int
    feedback: str


@app.post("/api/ai/refine")
async def ai_refine(body: RefineRequest, session: dict = Depends(get_session)):
    post = await get_post(body.post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    try:
        result = refine_content(post["title"], post["body"], body.feedback)
        await update_post(body.post_id, {
            "title": result.get("title", post["title"]),
            "body": result.get("body", post["body"]),
        })
        return {"post_id": body.post_id, **result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Refinement failed: {str(e)}")


@app.get("/api/ai/test")
async def ai_test(session: dict = Depends(get_session)):
    return test_connection()


# ═══════════════════════════════════════════════════
#  POSTS — CRUD + Approval Workflow
# ═══════════════════════════════════════════════════

class PostUpdate(BaseModel):
    title: str | None = None
    body: str | None = None
    status: str | None = None
    target_subreddits: list[str] | None = None


@app.get("/api/posts")
async def list_posts(status: str | None = None, session: dict = Depends(get_session)):
    posts = await get_posts(status)
    return {"posts": posts}


@app.get("/api/posts/{post_id}")
async def read_post(post_id: int, session: dict = Depends(get_session)):
    post = await get_post(post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    jobs = await get_jobs_for_post(post_id)
    return {**post, "jobs": jobs}


@app.patch("/api/posts/{post_id}")
async def edit_post(post_id: int, body: PostUpdate, session: dict = Depends(get_session)):
    post = await get_post(post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    updates = body.model_dump(exclude_none=True)
    await update_post(post_id, updates)
    return {"status": "updated", "post_id": post_id}


@app.delete("/api/posts/{post_id}")
async def remove_post(post_id: int, session: dict = Depends(get_session)):
    await delete_post(post_id)
    return {"status": "deleted"}


@app.post("/api/posts/{post_id}/approve")
async def approve_post(post_id: int, session: dict = Depends(get_session)):
    """Approve a post and schedule it for publishing."""
    post = await get_post(post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    subreddits = json.loads(post["target_subreddits"]) if isinstance(post["target_subreddits"], str) else post["target_subreddits"]
    if not subreddits:
        raise HTTPException(status_code=400, detail="No target subreddits set")

    await update_post(post_id, {"status": "approved"})
    scheduled = await schedule_post_publishing(post_id, subreddits)
    return {"status": "approved_and_scheduled", "jobs": scheduled}


# ═══════════════════════════════════════════════════
#  SUBREDDITS — Discovery & Management
# ═══════════════════════════════════════════════════

@app.get("/api/subreddits/search")
async def search_subs(q: str, session: dict = Depends(get_session)):
    token = await get_reddit_token()
    if not token:
        raise HTTPException(status_code=400, detail="Reddit not connected")
    results = await search_subreddits(token["access_token"], q)
    await save_subreddits(results)
    return {"subreddits": results}


@app.get("/api/subreddits/saved")
async def list_saved_subs(session: dict = Depends(get_session)):
    return {"subreddits": await get_saved_subreddits()}


@app.get("/api/subreddits/mine")
async def my_subs(session: dict = Depends(get_session)):
    token = await get_reddit_token()
    if not token:
        raise HTTPException(status_code=400, detail="Reddit not connected")
    subs = await get_my_subreddits(token["access_token"])
    return {"subreddits": subs}


@app.post("/api/subreddits/{name}/join")
async def join_sub(name: str, session: dict = Depends(get_session)):
    token = await get_reddit_token()
    if not token:
        raise HTTPException(status_code=400, detail="Reddit not connected")
    ok = await subscribe_to_subreddit(token["access_token"], name)
    if ok:
        await mark_subreddit_joined(name, True)
    return {"joined": ok, "subreddit": name}


@app.post("/api/subreddits/{name}/leave")
async def leave_sub(name: str, session: dict = Depends(get_session)):
    token = await get_reddit_token()
    if not token:
        raise HTTPException(status_code=400, detail="Reddit not connected")
    ok = await unsubscribe_from_subreddit(token["access_token"], name)
    if ok:
        await mark_subreddit_joined(name, False)
    return {"left": ok, "subreddit": name}


# ═══════════════════════════════════════════════════
#  SCHEDULER — Job Status
# ═══════════════════════════════════════════════════

@app.get("/api/jobs/pending")
async def pending_jobs(session: dict = Depends(get_session)):
    return {"jobs": await get_pending_jobs()}


# ═══════════════════════════════════════════════════
#  HEALTH
# ═══════════════════════════════════════════════════

@app.get("/api/health")
async def health():
    return {"status": "ok", "version": "1.0.0", "time": datetime.utcnow().isoformat()}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
