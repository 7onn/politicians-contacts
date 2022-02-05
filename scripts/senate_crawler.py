from bs4 import BeautifulSoup
import logging
import pandas as pd
import csv
import re
import requests

from urllib.parse import urljoin

logging.basicConfig(format="%(asctime)s %(levelname)s:%(message)s", level=logging.INFO)


def get_html(url):
    return requests.get(url).text


class SenateCrawler:
    def __init__(self):
        self.base_url = "https://www25.senado.leg.br/"
        self.search_url = self.base_url + "web/senadores/em-exercicio/-/e/por-nome"
        self.senate = []

    def get_senate(self, url):
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

    def run(self):
        try:
            self.get_senate(self.search_url)
        except Exception:
            logging.exception("global failure")
        finally:
            df = pd.DataFrame(self.senate)
            df.to_csv("senate.csv")
            logging.info("Senate crawler exited")
