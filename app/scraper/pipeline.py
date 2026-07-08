import datetime as dt
import logging
from typing import Optional, Tuple

from app.db import SessionLocal, init_db
from app.models import Genre, Movie
from app.scraper.catalog import MovieCatalogEntry, iterate_year
from app.scraper.client import FilmwebClient
from app.scraper.detail import fetch_critics_rating

logger = logging.getLogger(__name__)


def _get_or_create_genre(session, genre_cache: dict, genre_id: int, name: str) -> Genre:
    # genre_cache avoids creating duplicate pending Genre objects for the same
    # id within one uncommitted transaction, which session.get() alone won't
    # catch (it only reliably finds already-flushed rows).
    genre = genre_cache.get(genre_id)
    if genre is not None:
        return genre

    genre = session.get(Genre, genre_id)
    if genre is None:
        genre = Genre(id=genre_id, name=name)
        session.add(genre)
    genre_cache[genre_id] = genre
    return genre


def _upsert_movie(session, entry: MovieCatalogEntry, genre_cache: dict) -> Movie:
    movie = session.get(Movie, entry["id"])
    if movie is None:
        movie = Movie(id=entry["id"])
        session.add(movie)

    movie.title = entry["title"]
    movie.original_title = entry["original_title"]
    movie.year = entry["year"]
    movie.url = entry["url"]
    movie.poster_url = entry["poster_url"]
    movie.user_score = entry["user_score"]
    movie.user_count = entry["user_count"]
    movie.scraped_at = dt.datetime.utcnow()

    movie.genres = [
        _get_or_create_genre(session, genre_cache, g["id"], g["name"]) for g in entry["genres"]
    ]

    return movie


def scrape_catalog(
    year: int,
    client: Optional[FilmwebClient] = None,
    force_refresh: bool = False,
    max_pages: Optional[int] = None,
) -> int:
    """Populate/refresh basic movie info (title, genres, user score) for a given year."""
    own_client = client is None
    client = client or FilmwebClient()
    session = SessionLocal()
    genre_cache: dict = {}
    count = 0
    try:
        for entry in iterate_year(client, year, max_pages=max_pages, force_refresh=force_refresh):
            _upsert_movie(session, entry, genre_cache)
            count += 1
            if count % 20 == 0:
                session.commit()
                logger.info("Catalog: %d movies scraped so far for %d", count, year)
        session.commit()
    finally:
        session.close()
        if own_client:
            client.close()
    return count


def enrich_critics_scores(
    year: Optional[int] = None,
    client: Optional[FilmwebClient] = None,
    force_refresh: bool = False,
) -> int:
    """Fetch the aggregated critics score for movies already stored by scrape_catalog.

    By default only movies not yet enriched (critics_scraped_at is NULL) are
    fetched, so re-running this is cheap. Pass force_refresh=True to re-fetch
    everyone (e.g. to pick up new critic reviews for older years).
    """
    own_client = client is None
    client = client or FilmwebClient()
    session = SessionLocal()
    count = 0
    try:
        query = session.query(Movie)
        if year is not None:
            query = query.filter(Movie.year == year)
        if not force_refresh:
            query = query.filter(Movie.critics_scraped_at.is_(None))

        movies = query.all()
        for movie in movies:
            rating = fetch_critics_rating(client, movie.url, force_refresh=force_refresh)
            movie.critics_score = rating["critics_score"]
            movie.critics_count = rating["critics_count"]
            movie.critics_scraped_at = dt.datetime.utcnow()
            count += 1
            if count % 20 == 0:
                session.commit()
                logger.info("Critics enrichment: %d/%d movies done", count, len(movies))
        session.commit()
    finally:
        session.close()
        if own_client:
            client.close()
    return count


def scrape_year(
    year: int, force_refresh: bool = False, max_pages: Optional[int] = None
) -> Tuple[int, int]:
    """Run the full two-phase pipeline for a single year: catalog then critics detail."""
    init_db()
    with FilmwebClient() as client:
        n_catalog = scrape_catalog(
            year, client=client, force_refresh=force_refresh, max_pages=max_pages
        )
        logger.info("Catalog phase done: %d movies for %d", n_catalog, year)
        n_details = enrich_critics_scores(year=year, client=client, force_refresh=force_refresh)
        logger.info("Critics phase done: %d movies enriched", n_details)
    return n_catalog, n_details
