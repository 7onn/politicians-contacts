"""HTML parser."""

from bs4 import BeautifulSoup

from datetime import timedelta, datetime

import json
import logging
import pandas as pd
import re
import requests
import os
import asyncio
from urllib.parse import urljoin

logging.basicConfig(format="%(asctime)s %(levelname)s:%(message)s", level=logging.INFO)


def get_html(url):
    """Fetch HTML content from a given URL."""
    return requests.get(url).text


class CongressCrawler:
    """Congress class."""

    def __init__(self):
        """Place Congress-related variables."""
        self.base_url = "https://www.camara.leg.br/"
        self.congress = []
        self.search_url = (
            self.base_url + "deputados/quem-sao/resultado?search=&partido=&uf=&sexo="
        )

    async def run(self):
        """Start the Congress crawler."""
        try:
            legislature = self.get_current_legislature()
            total = self.get_total_congress(legislature)
            if int(total) < 1:
                logging.error(
                    "The latest legislature"
                    "'s quorum for the Congress have not been informed yet"
                )

            pages = round(int(total) / 25) + 1
            tasks = []
            for i in range(1, pages):
                tasks.append(
                    asyncio.create_task(
                        self.get_congress_by_page(
                            self.search_url
                            + "&legislatura="
                            + legislature
                            + "&pagina="
                            + str(i)
                        )
                    )
                )
            await asyncio.gather(*tasks)

        except Exception:
            logging.exception("global failure")
            requests.post(
                os.environ.get("SLACK_WEBHOOK_URL"),
                json.dumps(
                    {
                        "channel": "#notifications",
                        "icon_emoji": ":fire:",
                        "text": ":warning: Brazilian congress crawler <https://github.com/7onn/politicians-contacts/actions|failed>! :fire:",
                        "username": "politicians-contacts",
                    }
                ),
                headers={"Content-Type": "application/json"},
            )

        finally:
            if len(self.congress) > 0:
                df = pd.DataFrame(self.congress)
                df.to_csv("congress.csv")
                logging.info("Congress crawler exited 0")
            else:
                logging.error("Congress crawler exited 1")

    def get_current_legislature(self):
        """Get the current legislature number."""

        date = datetime.now()
        date -= timedelta(days=31)
        return str((date.year - 1795) // 4)

    def get_total_congress(self, legislature):
        """Fetch the amount of active Congresspeople."""
        soup = BeautifulSoup(
            get_html(self.search_url + "&legislatura=" + legislature),
            "html.parser",
        )
        pfound = soup.find(text=re.compile(r"\d+\sencontrados"))
        if not pfound:
            return 0

        total = re.findall(r"\d{3,}", pfound)[0]
        return total

    async def get_congress_by_page(self, url):
        """Fetch Congressperson's data from their page."""
        logging.info(f"page: {url}")
        soup = BeautifulSoup(get_html(url), "html.parser")
        tasks = []
        for link in soup.find_all(href=re.compile(r"/deputados/\d.*")):
            tasks.append(
                asyncio.create_task(
                    self.get_congress_person_data(
                        urljoin(self.base_url, link.get("href"))
                    )
                )
            )

        await asyncio.gather(*tasks)

    async def get_congress_person_data(self, url):
        """
        Fetch Congresspeople's data.

        And then append them into Congress list.
        """

        congressperson = self.get_congress_person_data_from_page(url)
        if congressperson:
            self.congress.append(congressperson)
            logging.info(
                f"congressperson: {url} - "
                f' email: {congressperson["email"]} -'
                f' party: {congressperson["party"]}'
            )

    def get_congress_person_data_from_page(self, url):
        try:
            soup = BeautifulSoup(get_html(url), "html.parser")
            name = soup.find(id="nomedeputado").contents[0]
            party_state = soup.find(class_="informacoes-deputado__inline").contents[1]
            party = re.findall(r".+?(?=\s-)", party_state)[0]
            email = soup.find(class_="email").contents[0]

            congressperson = {
                "name": name,
                "party": party,
                "email": email,
            }

            return congressperson
        except Exception:
            logging.exception(f"failed at {url}")
            return
