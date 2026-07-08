from typing import Optional, TypedDict

from bs4 import BeautifulSoup

from app.scraper.client import FilmwebClient
from app.scraper.utils import parse_score


class CriticsRating(TypedDict):
    critics_score: Optional[float]
    critics_count: Optional[int]


def parse_critics_rating(html: str) -> CriticsRating:
    """Parse the aggregated critics score off a /film/{slug}-{year}-{id} page.

    Filmweb shows this in a `a.filmRating--filmCritic` block, separate from
    the user rating (`a.filmRating--filmRate`). Films with no critic reviews
    yet simply don't have this block.
    """
    soup = BeautifulSoup(html, "lxml")
    container = soup.select_one("a.filmRating--filmCritic")
    if container is None:
        return {"critics_score": None, "critics_count": None}

    score_el = container.select_one(".filmRating__rateValue")
    score = parse_score(score_el.get_text() if score_el else None)

    count_el = container.select_one(".filmRating__count")
    count = None
    if count_el is not None:
        raw_count = count_el.get("data-rating-count", "")
        if raw_count.isdigit():
            count = int(raw_count)

    return {"critics_score": score, "critics_count": count}


def fetch_critics_rating(
    client: FilmwebClient, film_url: str, force_refresh: bool = False
) -> CriticsRating:
    """film_url is the full https://www.filmweb.pl/film/... URL stored on Movie.url."""
    path = film_url.split("filmweb.pl", 1)[1] if "filmweb.pl" in film_url else film_url
    html = client.get_html(path, force_refresh=force_refresh)
    return parse_critics_rating(html)
