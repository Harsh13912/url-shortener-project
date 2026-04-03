"""
URL Shortener Backend - FastAPI
High-scale read system with Redis caching and PostgreSQL persistence
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks, Request
from fastapi.responses import RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, HttpUrl
from contextlib import asynccontextmanager
import asyncpg
import redis.asyncio as redis
import secrets
import string
from datetime import datetime, timedelta
from typing import Optional
import os
from dotenv import load_dotenv

load_dotenv()

# Configuration
DATABASE_URL = os.getenv("DATABASE_URL")
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
BASE62_CHARS = string.ascii_letters + string.digits
SHORT_CODE_LENGTH = 5
LINK_EXPIRY_DAYS = 5
CACHE_TTL = 60 * 60 * 24 * 5  # 5 days in seconds

# Global connections
db_pool: Optional[asyncpg.Pool] = None
redis_client: Optional[redis.Redis] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage database and Redis connections lifecycle"""
    global db_pool, redis_client
    
    # Startup
    db_pool = await asyncpg.create_pool(DATABASE_URL, min_size=5, max_size=20)
    redis_client = await redis.from_url(REDIS_URL, encoding="utf-8", decode_responses=True)

    yield
    
    # Shutdown
    await db_pool.close()
    await redis_client.close()


app = FastAPI(
    title="URL Shortener API",
    description="High-scale URL shortener with Redis caching",
    version="1.0.0",
    lifespan=lifespan
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Pydantic Models
class URLCreate(BaseModel):
    long_url: HttpUrl


class URLResponse(BaseModel):
    short_code: str
    short_url: str
    long_url: str
    created_at: datetime
    expires_at: datetime


class AnalyticsResponse(BaseModel):
    short_code: str
    long_url: str
    clicks: int
    created_at: datetime
    expires_at: datetime


# Helper Functions
def generate_short_code(length: int = SHORT_CODE_LENGTH) -> str:
    """Generate a cryptographically secure random Base62 string"""
    return ''.join(secrets.choice(BASE62_CHARS) for _ in range(length))


async def check_collision(short_code: str) -> bool:
    """Check if short_code already exists in database"""
    query = "SELECT 1 FROM urls WHERE short_code = $1"
    result = await db_pool.fetchval(query, short_code)
    return result is not None


async def sync_clicks_to_db(short_code: str):
    """Background task: Sync click counts from Redis to PostgreSQL"""
    try:
        click_key = f"clicks:{short_code}"
        clicks = await redis_client.get(click_key)
        
        if clicks:
            # Update database with current click count
            query = """
                UPDATE urls 
                SET click_count = COALESCE(click_count, 0) + $1 
                WHERE short_code = $2
            """
            await db_pool.execute(query, int(clicks), short_code)
            
            # Reset Redis counter after sync
            await redis_client.delete(click_key)
    except Exception as e:
        print(f"Error syncing clicks for {short_code}: {e}")


# API Endpoints
@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "URL Shortener API",
        "version": "1.0.0"
    }


@app.post("/shorten", response_model=URLResponse, status_code=201)
async def shorten_url(url_data: URLCreate, request: Request):
    """
    Create a shortened URL
    
    Write Path:
    1. Generate random Base62 code
    2. Check for collisions in PostgreSQL
    3. Save to database
    4. Cache in Redis
    5. Return shortened URL
    """
    long_url = str(url_data.long_url)
    
    # Generate unique short code
    max_attempts = 5
    short_code = None
    
    for _ in range(max_attempts):
        candidate = generate_short_code()
        if not await check_collision(candidate):
            short_code = candidate
            break
    
    if not short_code:
        # Fallback to 6 characters if 5-char collision rate is high
        short_code = generate_short_code(length=6)
    
    # Calculate expiry
    created_at = datetime.utcnow()
    expires_at = created_at + timedelta(days=LINK_EXPIRY_DAYS)
    
    # Save to PostgreSQL
    query = """
        INSERT INTO urls (short_code, long_url, created_at, expires_at, click_count)
        VALUES ($1, $2, $3, $4, 0)
        RETURNING id
    """
    
    try:
        await db_pool.execute(query, short_code, long_url, created_at, expires_at)
    except asyncpg.exceptions.UniqueViolationError:
        raise HTTPException(status_code=500, detail="Failed to generate unique short code")
    
    # Cache in Redis
    cache_key = f"url:{short_code}"
    await redis_client.setex(cache_key, CACHE_TTL, long_url)
    
    # Build short URL
    base_url = str(request.base_url).rstrip('/')
    short_url = f"{base_url}/{short_code}"
    
    return URLResponse(
        short_code=short_code,
        short_url=short_url,
        long_url=long_url,
        created_at=created_at,
        expires_at=expires_at
    )


@app.get("/{short_code}")
async def redirect_url(short_code: str, background_tasks: BackgroundTasks):
    """
    Redirect to original URL (HIGH-SCALE READ PATH)
    
    Read Path:
    1. Check Redis cache first (Cache Hit: <1ms redirect)
    2. If miss, query PostgreSQL
    3. Cache result in Redis
    4. Increment click counter in Redis (non-blocking)
    5. Redirect user
    """
    
    # Try Redis cache first (FAST PATH)
    cache_key = f"url:{short_code}"
    long_url = await redis_client.get(cache_key)
    
    if long_url:
        # Cache Hit - Instant redirect
        click_key = f"clicks:{short_code}"
        await redis_client.incr(click_key)
        
        # Schedule background sync every 10 clicks
        clicks = await redis_client.get(click_key)
        if clicks and int(clicks) % 10 == 0:
            background_tasks.add_task(sync_clicks_to_db, short_code)
        
        return RedirectResponse(url=long_url, status_code=307)
    
    # Cache Miss - Query PostgreSQL
    query = """
        SELECT long_url, expires_at 
        FROM urls 
        WHERE short_code = $1
    """
    row = await db_pool.fetchrow(query, short_code)
    
    if not row:
        raise HTTPException(status_code=404, detail="Short URL not found")
    
    long_url = row['long_url']
    expires_at = row['expires_at']
    
    # Check if link has expired
    if datetime.utcnow() > expires_at:
        raise HTTPException(status_code=410, detail="This link has expired")
    
    # Cache for future requests
    await redis_client.setex(cache_key, CACHE_TTL, long_url)
    
    # Increment click counter
    click_key = f"clicks:{short_code}"
    await redis_client.incr(click_key)
    background_tasks.add_task(sync_clicks_to_db, short_code)
    
    return RedirectResponse(url=long_url, status_code=307)


@app.get("/analytics/{short_code}", response_model=AnalyticsResponse)
async def get_analytics(short_code: str):
    """
    Get analytics for a shortened URL
    
    Returns:
    - Click count (from Redis + PostgreSQL)
    - Creation and expiry timestamps
    """
    query = """
        SELECT long_url, created_at, expires_at, COALESCE(click_count, 0) as db_clicks
        FROM urls
        WHERE short_code = $1
    """
    row = await db_pool.fetchrow(query, short_code)
    
    if not row:
        raise HTTPException(status_code=404, detail="Short URL not found")
    
    # Get current clicks from Redis
    click_key = f"clicks:{short_code}"
    redis_clicks = await redis_client.get(click_key)
    redis_clicks = int(redis_clicks) if redis_clicks else 0
    
    total_clicks = row['db_clicks'] + redis_clicks
    
    return AnalyticsResponse(
        short_code=short_code,
        long_url=row['long_url'],
        clicks=total_clicks,
        created_at=row['created_at'],
        expires_at=row['expires_at']
    )


@app.delete("/delete/{short_code}")
async def delete_url(short_code: str):
    """Delete a shortened URL (also removes from cache)"""
    
    # Delete from PostgreSQL
    query = "DELETE FROM urls WHERE short_code = $1 RETURNING id"
    result = await db_pool.fetchval(query, short_code)
    
    if not result:
        raise HTTPException(status_code=404, detail="Short URL not found")
    
    # Delete from Redis cache
    cache_key = f"url:{short_code}"
    click_key = f"clicks:{short_code}"
    await redis_client.delete(cache_key, click_key)
    
    return {"message": "URL deleted successfully", "short_code": short_code}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
