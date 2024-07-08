from bs4 import BeautifulSoup
import json
import logging
import pandas as pd
import requests
import os

logging.basicConfig(format="%(asctime)s %(levelname)s:%(message)s",
                    level=logging.INFO)


def get_html(url):
    """Fetch HTML content from a given URL."""
    return requests.get(url).text


class SenateCrawler:
    """Senate class."""

    def __init__(self):
        """Place Senate-related variables."""
        self.base_url = "https://www25.senado.leg.br/"
        self.search_url = self.base_url + "web/senadores/em-exercicio/-/e/por-nome"
        self.senate = []

    def get_senate(self):
        """Fetch Senatepeople's data and append them into the Senate list."""
        soup = BeautifulSoup(get_html(self.search_url), "html.parser")
        trs = soup.find("table").find("tbody").find_all("tr")
        for tr in trs:
            cells = tr.find_all("td")
            senateperson = {
                "name": cells[0].get_text(),
                "party": cells[1].get_text(),
                "email": cells[5].get_text(),
            }

            if senateperson["email"]:
                self.senate.append(senateperson)

    async def run(self):
        """Start the Senate crawler."""
        try:
            self.get_senate()
        except Exception:
            logging.exception("global failure")
            requests.post(
                os.environ.get("SLACK_WEBHOOK_URL"),
                json.dumps({
                    "channel": "#notifications",
                    "icon_emoji": ":fire:",
                    "text":
                    ":warning: Brazilian senate crawler <https://github.com/7onn/politicians-contacts/actions|failed>! :fire:",
                    "username": "politicians-contacts",
                }),
                headers={"Content-Type": "application/json"},
            )
        finally:
            if len(self.senate) > 0:
                df = pd.DataFrame(self.senate)
                df.to_csv("senate.csv")
                logging.info("Senate crawler exited 0")
            else:
                logging.info("Senate crawler exited 1")
