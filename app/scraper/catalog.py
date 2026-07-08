import re
from typing import Iterator, List, Optional, TypedDict

from bs4 import BeautifulSoup

from app.scraper.client import BASE_URL, FilmwebClient
from app.scraper.utils import parse_score

GENRE_ID_RE = re.compile(r"/genre/(\d+)")

ITEMS_PER_PAGE = 50


class GenreDict(TypedDict):
    id: int
    name: str


class MovieCatalogEntry(TypedDict):
    id: int
    title: str
    original_title: Optional[str]
    year: int
    url: str
    poster_url: Optional[str]
    user_score: Optional[float]
    user_count: Optional[int]
    genres: List[GenreDict]


def parse_ranking_page(html: str, fallback_year: int) -> List[MovieCatalogEntry]:
    """Parse one page of https://www.filmweb.pl/ranking/film/{year} into movie records."""
    soup = BeautifulSoup(html, "lxml")
    entries: List[MovieCatalogEntry] = []

    for container in soup.select("div.rankingType[data-id]"):
        if container.get("data-entity-name") != "film":
            continue

        movie_id = int(container["data-id"])

        title_link = container.select_one("h2.rankingType__title a")
        if title_link is None:
            continue
        title = title_link.get_text(strip=True)
        detail_path = title_link["href"]

        # The page path (fallback_year) is the source of truth for a movie's
        # year - it's how filmweb itself categorizes the ranking. The
        # schema.org datePublished on the card can differ slightly (e.g. a
        # film's original vs. Polish premiere date) and must not override it.
        year = fallback_year
        original_title = None
        original_title_p = container.select_one("p.rankingType__originalTitle")
        if original_title_p is not None:
            year_span = original_title_p.select_one("span.rankingType__year")
            if year_span is not None:
                full_text = original_title_p.get_text(" ", strip=True)
                year_text = year_span.get_text(strip=True)
                if year_text and full_text.endswith(year_text):
                    full_text = full_text[: -len(year_text)].strip()
                original_title = full_text or None

        rate_value = container.select_one("span.rankingType__rate--value")
        user_score = parse_score(rate_value.get_text() if rate_value else None)

        rate_count = container.select_one("span.rankingType__rate--count")
        user_count = None
        if rate_count is not None and rate_count.get("content", "").isdigit():
            user_count = int(rate_count["content"])

        poster_url = None
        ribbon = container.select_one("div.ribbon")
        if ribbon is not None and ribbon.get("data-image"):
            poster_url = ribbon["data-image"]

        genres: List[GenreDict] = []
        for genre_link in container.select("div.rankingType__genres a.rankingGerne"):
            match = GENRE_ID_RE.search(genre_link.get("href", ""))
            if not match:
                continue
            genres.append({"id": int(match.group(1)), "name": genre_link.get_text(strip=True)})

        entries.append(
            {
                "id": movie_id,
                "title": title,
                "original_title": original_title,
                "year": year,
                "url": "{}{}".format(BASE_URL, detail_path),
                "poster_url": poster_url,
                "user_score": user_score,
                "user_count": user_count,
                "genres": genres,
            }
        )

    return entries


def iterate_year(
    client: FilmwebClient,
    year: int,
    max_pages: Optional[int] = None,
    force_refresh: bool = False,
) -> Iterator[MovieCatalogEntry]:
    """Yield every movie found in the /ranking/film/{year} listing, across all pages."""
    page = 1
    while True:
        path = "/ranking/film/{}".format(year) if page == 1 else "/ranking/film/{}?page={}".format(year, page)
        html = client.get_html(path, force_refresh=force_refresh)
        entries = parse_ranking_page(html, fallback_year=year)
        if not entries:
            return
        for entry in entries:
            yield entry
        if max_pages is not None and page >= max_pages:
            return
        page += 1
