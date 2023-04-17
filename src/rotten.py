import random
import re
from string import ascii_lowercase

import aswan
import datazimmer as dz
import requests
from bs4 import BeautifulSoup

source = dz.SourceUrl("https://www.rottentomatoes.com")

HEADERS = {
    "Accept": "*/*",
    "Connection": "keep-alive",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/68.0.3440.84 Safari/537.36",
    "Accept-Encoding": "gzip, deflate, br",
    "Accept-Language": "en-US;q=0.5,en;q=0.3",
    "Cache-Control": "max-age=0",
    "DNT": "1",
    "Upgrade-Insecure-Requests": "1",
}


class LetterHandler(aswan.RequestSoupHandler):
    url_root = source

    def parse(self, soup: "BeautifulSoup"):
        ul = soup.find("ul", class_="critics__list")
        _as = ul.find_all("a", href=re.compile("/critics/*"))
        api_links = [f"/napi{a['href']}/movies" for a in _as]
        self.register_links_to_handler(api_links, CriticHandler)
        next_page = soup.find("critics-pagination-nav").get("endcursor")
        self.register_url_with_params({"after": next_page})
        return ul.encode("utf-8")


class LegacyLetterHandler(LetterHandler):
    process_indefinitely = True


class CriticHandler(aswan.RequestJsonHandler):
    def parse(self, obj: dict):
        ec = obj.get("pageInfo", {}).get("endCursor")
        if ec:
            self.register_url_with_params({"after": ec})
        return obj

    def handle_driver(self, session: "requests.Session"):
        session.headers = HEADERS

    def get_sleep_time(self):
        return random.randint(2, 10)


class RottenProject(dz.DzAswan):
    cron = "0 6 * * 1"
    name = "rotten-tomatoes"
    starters = {
        LetterHandler: [f"{source}/critics/authors?letter={l}" for l in ascii_lowercase]
        + [f"{source}/critics/sources?letter={l}" for l in ["#", *ascii_lowercase]],
        LegacyLetterHandler: [
            f"{source}/critics/legacy_authors?letter={l}" for l in ascii_lowercase
        ],
    }

    def prepare_run(self):
        self.project.max_cpu_use = 2


# @dz.register
def proc():
    pass
