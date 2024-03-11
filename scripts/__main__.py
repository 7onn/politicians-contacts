"""Crawler classes."""

from congress_crawler import CongressCrawler
from senate_crawler import SenateCrawler


if __name__ == "__main__":
    SenateCrawler().run()
    CongressCrawler().run()
