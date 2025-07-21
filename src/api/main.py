from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, RedirectResponse
import logging
from datetime import datetime
from pathlib import Path

from .database import Database
from .schemas import (
    SubscribeRequest, 
    UpdatePreferencesRequest, 
    UnsubscribeRequest,
    StatusResponse,
    SubscribeResponse
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Aurora Alert API",
    description="Real-time aurora notifications based on location and preferences",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

db = Database()

# Mount static files for frontend
frontend_path = Path(__file__).parent.parent.parent / "frontend"
if frontend_path.exists():
    app.mount("/static", StaticFiles(directory=str(frontend_path)), name="static")


def get_database():
    return db


@app.post("/subscribe", response_model=SubscribeResponse)
async def subscribe(request: SubscribeRequest, database: Database = Depends(get_database)):
    """Subscribe to aurora notifications."""
    try:
        # Check if user already exists
        existing_user = database.get_user_by_token(request.token)
        if existing_user:
            return SubscribeResponse(
                success=False,
                message="User already subscribed with this token"
            )
        
        # Add new user
        user = database.add_user(
            lat=request.lat,
            lon=request.lon,
            radius_km=request.radius_km,
            threshold=request.threshold,
            fcm_token=request.token
        )
        
        if user:
            logger.info(f"New user subscribed: {user.id} at {user.lat},{user.lon}")
            return SubscribeResponse(
                success=True,
                message="Successfully subscribed to aurora notifications",
                user_id=user.id
            )
        else:
            return SubscribeResponse(
                success=False,
                message="Failed to create subscription"
            )
            
    except Exception as e:
        logger.error(f"Error in subscribe endpoint: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.patch("/prefs")
async def update_preferences(request: UpdatePreferencesRequest, 
                           token: str, database: Database = Depends(get_database)):
    """Update user preferences."""
    try:
        # Check if user exists
        user = database.get_user_by_token(token)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Update preferences
        success = database.update_user_preferences(
            fcm_token=token,
            radius_km=request.radius_km,
            threshold=request.threshold
        )
        
        if success:
            logger.info(f"Updated preferences for user {user.id}")
            return {"success": True, "message": "Preferences updated successfully"}
        else:
            raise HTTPException(status_code=400, detail="Failed to update preferences")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in update_preferences endpoint: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.delete("/unsubscribe")
async def unsubscribe(request: UnsubscribeRequest, database: Database = Depends(get_database)):
    """Unsubscribe from aurora notifications."""
    try:
        # Check if user exists
        user = database.get_user_by_token(request.token)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Deactivate user
        success = database.deactivate_user(request.token)
        
        if success:
            logger.info(f"User {user.id} unsubscribed")
            return {"success": True, "message": "Successfully unsubscribed"}
        else:
            raise HTTPException(status_code=400, detail="Failed to unsubscribe")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in unsubscribe endpoint: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.get("/status", response_model=StatusResponse)
async def get_status(database: Database = Depends(get_database)):
    """Get API health status."""
    try:
        active_users = len(database.get_active_users())
        
        return StatusResponse(
            status="healthy",
            message=f"Aurora Alert API is running. Last checked: {datetime.utcnow().isoformat()}",
            active_users=active_users
        )
        
    except Exception as e:
        logger.error(f"Error in status endpoint: {e}")
        return StatusResponse(
            status="error",
            message=f"Service error: {str(e)}"
        )


@app.get("/app")
async def serve_frontend():
    """Serve the frontend application."""
    frontend_path = Path(__file__).parent.parent.parent / "frontend" / "index.html"
    if frontend_path.exists():
        return FileResponse(str(frontend_path))
    else:
        raise HTTPException(status_code=404, detail="Frontend not found")

@app.get("/{filename}")
async def serve_static_file(filename: str):
    """Serve static files from frontend directory."""
    frontend_path = Path(__file__).parent.parent.parent / "frontend" / filename
    if frontend_path.exists() and frontend_path.is_file():
        return FileResponse(str(frontend_path))
    else:
        # If file not found, serve the main app (for SPA routing)
        return await serve_frontend()


@app.get("/")
async def root():
    """Redirect to frontend app."""
    return RedirectResponse(url="/app")


@app.get("/api")
async def api_info():
    """API information endpoint."""
    return {
        "message": "Aurora Alert API",
        "version": "1.0.0",
        "frontend": "GET /app",
        "endpoints": {
            "subscribe": "POST /subscribe",
            "update_prefs": "PATCH /prefs?token=<fcm_token>",
            "unsubscribe": "DELETE /unsubscribe",
            "status": "GET /status"
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("src.api.main:app", host="0.0.0.0", port=8000, reload=True)