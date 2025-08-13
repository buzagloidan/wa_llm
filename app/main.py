import asyncio
from contextlib import asynccontextmanager
from warnings import warn

from fastapi import FastAPI
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlmodel.ext.asyncio.session import AsyncSession
import logging
import logfire

import logging

# Add early logging to debug imports
early_logger = logging.getLogger("main")
early_logger.setLevel(logging.INFO)

try:
    from api import load_new_kbtopics_api, status, webhook, database_admin, dashboard, dashboard_html
    early_logger.info("Successfully imported all API modules")
except ImportError as e:
    early_logger.error(f"Failed to import API modules: {e}")
    raise
import models  # noqa
from config import Settings
from whatsapp import WhatsAppClient
from voyageai.client_async import AsyncClient

try:
    settings = Settings()  # pyright: ignore [reportCallIssue]
    early_logger.info("Settings loaded successfully")
except Exception as e:
    early_logger.error(f"Failed to load settings: {e}")
    early_logger.error("Check that all required environment variables are set in Railway")
    raise


@asynccontextmanager
async def lifespan(app: FastAPI):
    global settings
    # Create and configure logger
    logging.basicConfig(
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        level=settings.log_level,
    )

    app.state.settings = settings

    app.state.whatsapp = WhatsAppClient(
        settings.whatsapp_host,
        settings.whatsapp_basic_auth_user,
        settings.whatsapp_basic_auth_password,
    )

    if settings.db_uri.startswith("postgresql://"):
        warn("use 'postgresql+asyncpg://' instead of 'postgresql://' in db_uri")
    engine = create_async_engine(
        settings.db_uri,
        pool_size=20,
        max_overflow=40,
        pool_timeout=30,
        pool_pre_ping=True,
        pool_recycle=600,
        future=True,
    )
    logfire.instrument_sqlalchemy(engine)
    async_session = async_sessionmaker(
        engine, expire_on_commit=False, class_=AsyncSession
    )


    app.state.db_engine = engine
    app.state.async_session = async_session
    app.state.embedding_client = AsyncClient(
        api_key=settings.voyage_api_key, max_retries=settings.voyage_max_retries
    )
    try:
        yield
    finally:
        await engine.dispose()


# Initialize FastAPI app
app = FastAPI(title="Webhook API", lifespan=lifespan)

logfire.configure()
logfire.instrument_pydantic_ai()
logfire.instrument_fastapi(app)
logfire.instrument_httpx(capture_all=True)
logfire.instrument_system_metrics()


logging.info("Registering API routes...")

logging.info(f"Webhook router has {len(webhook.router.routes)} routes")
app.include_router(webhook.router)

logging.info(f"Status router has {len(status.router.routes)} routes") 
app.include_router(status.router)

logging.info(f"Load topics router has {len(load_new_kbtopics_api.router.routes)} routes")
app.include_router(load_new_kbtopics_api.router)

logging.info(f"Database admin router has {len(database_admin.router.routes)} routes")
for route in database_admin.router.routes:
    logging.info(f"  Database admin route: {route.path} ({route.methods if hasattr(route, 'methods') else 'N/A'})")
app.include_router(database_admin.router)

logging.info(f"Dashboard router has {len(dashboard.router.routes)} routes")
app.include_router(dashboard.router)

logging.info(f"Dashboard HTML router has {len(dashboard_html.router.routes)} routes")
app.include_router(dashboard_html.router)

logging.info("All API routes registered successfully")

# Add simple root endpoint for debugging
@app.get("/")
async def root():
    """Simple root endpoint to verify app is running."""
    return {
        "message": "Jeen.ai Company Representative Bot is running",
        "status": "healthy",
        "version": "2.0",
        "transformation": "WhatsApp Group Bot -> Jeen.ai Company Representative"
    }

@app.get("/debug-test")
async def debug_test():
    """Debug endpoint to test connectivity."""
    return {"status": "success", "message": "Debug endpoint is working"}

if __name__ == "__main__":
    import uvicorn

    print(f"Running on {settings.host}:{settings.port}")

    uvicorn.run("main:app", host=settings.host, port=settings.port, reload=True)
