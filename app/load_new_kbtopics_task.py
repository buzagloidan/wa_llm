import asyncio
import logging
import httpx
import logfire

from pydantic_settings import BaseSettings, SettingsConfigDict


class CheckStatusSettings(BaseSettings):
    base_url: str = "http://localhost:8080"
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        arbitrary_types_allowed=True,
        case_sensitive=False,
        extra="ignore",
    )


async def main():
    logger = logging.getLogger(__name__)

    settings = CheckStatusSettings()

    logging.basicConfig(
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        level=logging.INFO,
    )
    logfire.configure()
    logfire.instrument_pydantic_ai()
    logfire.instrument_httpx(capture_all=True)
    logfire.instrument_system_metrics()

    logger.info("Starting daily topics loading task at 19:00 Israel time (16:00 UTC)")
    
    try:
        # Create an async HTTP client and call the topics loading endpoint
        async with httpx.AsyncClient(timeout=600.0) as client:
            logger.info(f"Calling topics loading endpoint: {settings.base_url}/load_new_kbtopics")
            response = await client.post(
                f"{settings.base_url}/load_new_kbtopics",
            )
            response.raise_for_status()
            logger.info(f"Daily topics loading task completed successfully: {response.status_code}")

    except httpx.HTTPError as exc:
        logger.error(f"Daily topics loading task failed - HTTP error: {exc}")
        raise
    except Exception as exc:
        logger.error(f"Daily topics loading task failed - Unexpected error: {exc}")
        raise


if __name__ == "__main__":
    asyncio.run(main())
