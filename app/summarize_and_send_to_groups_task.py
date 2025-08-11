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

    logger.info("Starting daily summary task at 20:00 Israel time (17:00 UTC)")
    
    try:
        # Create an async HTTP client and call the summary endpoint
        async with httpx.AsyncClient(timeout=600.0) as client:
            logger.info(f"Calling summarize endpoint: {settings.base_url}/summarize_and_send_to_groups")
            response = await client.post(
                f"{settings.base_url}/summarize_and_send_to_groups",
            )
            response.raise_for_status()
            logger.info(f"Daily summary task completed successfully: {response.status_code}")

    except httpx.HTTPError as exc:
        logger.error(f"Daily summary task failed - HTTP error: {exc}")
        raise
    except Exception as exc:
        logger.error(f"Daily summary task failed - Unexpected error: {exc}")
        raise


if __name__ == "__main__":
    asyncio.run(main())
