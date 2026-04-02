"""
FastAPI Application definition and routes
"""
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

logger = logging.getLogger(__name__)


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title="Digital Estate Manager API",
        description="REST API for the Digital Estate Manager agent",
        version="1.0.0"
    )
    
    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Include routes (will be added)
    # app.include_router(chat_router)
    # app.include_router(history_router)
    # app.include_router(health_router)
    
    @app.get("/health")
    async def health_check():
        """Health check endpoint."""
        return {"status": "ok", "message": "Digital Estate Manager API is running"}
    
    logger.info("FastAPI app created successfully")
    return app


if __name__ == "__main__":
    import uvicorn
    app = create_app()
    uvicorn.run(app, host="0.0.0.0", port=8000)
