"""Crawler classes."""

from congress_crawler import CongressCrawler
from senate_crawler import SenateCrawler
import asyncio


async def main() -> None:
    senate_task = asyncio.create_task(SenateCrawler().run())
    congress_task = asyncio.create_task(CongressCrawler().run())
    await senate_task
    await congress_task


if __name__ == "__main__":
    asyncio.run(main())
