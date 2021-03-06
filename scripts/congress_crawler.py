from bs4 import BeautifulSoup
import logging
import pandas as pd
import re
import requests

from urllib.parse import urljoin

logging.basicConfig(format="%(asctime)s %(levelname)s:%(message)s", level=logging.INFO)


def get_html(url):
    return requests.get(url).text


class CongressCrawler:
    def __init__(self):
        self.base_url = "https://www.camara.leg.br/"
        self.congress = []
        self.search_url = (
            self.base_url + "deputados/quem-sao/resultado?search=&partido=&uf=&sexo="
        )

    def get_congressperson_data(self, url):
        try:
            soup = BeautifulSoup(get_html(url), "html.parser")
            name = soup.find(id="nomedeputado").contents[0]
            party_state = soup.find(class_="foto-deputado__partido-estado").contents[0]
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

    def get_congressperson_href(self, soup):
        for link in soup.find_all(href=re.compile(r"/deputados/\d.*")):
            yield urljoin(self.base_url, link.get("href"))

    def get_congress_by_page(self, url):
        logging.info(f"page: {url}")
        soup = BeautifulSoup(get_html(url), "html.parser")
        for congressperson_url in self.get_congressperson_href(soup):
            congressperson = self.get_congressperson_data(congressperson_url)
            if congressperson:
                self.congress.append(congressperson)
                logging.info(
                    f'congressperson: {congressperson_url} - email: {congressperson["email"]} - party: {congressperson["party"]}'
                )

    def get_total_congress(self, legislature):
        soup = BeautifulSoup(
            get_html(self.search_url + "&legislatura=" + legislature),
            "html.parser",
        )
        pfound = soup.find(text=re.compile(r"\d+\sencontrados"))
        total = re.findall(r"\d{3,}", pfound)[0]
        return total

    def get_current_legislature(self):
        soup = BeautifulSoup(get_html(self.base_url), "html.parser")

        found = soup.find(text=re.compile(r"\d.*\sLegislatura"))
        legislature = re.findall(r"\d\d", found)[0]
        return legislature

    def run(self):
        try:
            legislature = self.get_current_legislature()
            total = self.get_total_congress(legislature)
            pages = round(int(total) / 25) + 1
            for i in range(1, pages):
                self.get_congress_by_page(
                    self.search_url
                    + "&legislatura="
                    + legislature
                    + "&pagina="
                    + str(i)
                )
        except Exception:
            logging.exception("global failure")
        finally:
            df = pd.DataFrame(self.congress)
            df.to_csv("congress.csv")
            logging.info("Congress crawler exited")
