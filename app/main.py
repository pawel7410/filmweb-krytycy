from pathlib import Path
from typing import List, Optional

from fastapi import FastAPI, Query
from fastapi.staticfiles import StaticFiles
from sqlalchemy import distinct

from app.db import SessionLocal, init_db
from app.models import Genre, Movie
from app.schemas import GenreOut, MovieOut, MoviesPage

STATIC_DIR = Path(__file__).resolve().parent.parent / "static"

# Movies without a critics score, or with a critics score below this, are
# treated as not ranked and excluded everywhere in the API.
MIN_CRITICS_SCORE = 5.0

app = FastAPI(title="Filmweb Critics Ranking")


def _eligible_movies(session):
    return session.query(Movie).filter(
        Movie.critics_score.isnot(None), Movie.critics_score >= MIN_CRITICS_SCORE
    )


@app.on_event("startup")
def on_startup() -> None:
    init_db()


@app.get("/api/movies", response_model=MoviesPage)
def list_movies(
    year: Optional[int] = None,
    genre: Optional[str] = None,
    min_critics_votes: int = Query(0, ge=0),
    sort: str = Query("critics_score", pattern="^(critics_score|user_score)$"),
    order: str = Query("desc", pattern="^(asc|desc)$"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
) -> MoviesPage:
    session = SessionLocal()
    try:
        query = _eligible_movies(session)
        if year is not None:
            query = query.filter(Movie.year == year)
        if genre:
            query = query.filter(Movie.genres.any(Genre.name == genre))
        if min_critics_votes:
            query = query.filter(Movie.critics_count >= min_critics_votes)

        total = query.count()

        sort_column = Movie.critics_score if sort == "critics_score" else Movie.user_score
        sort_column = sort_column.desc() if order == "desc" else sort_column.asc()
        query = query.order_by(sort_column)

        movies = query.offset((page - 1) * page_size).limit(page_size).all()
        return MoviesPage(
            total=total,
            page=page,
            page_size=page_size,
            results=[MovieOut.model_validate(m) for m in movies],
        )
    finally:
        session.close()


@app.get("/api/genres", response_model=List[GenreOut])
def list_genres() -> List[Genre]:
    session = SessionLocal()
    try:
        eligible_ids = _eligible_movies(session).with_entities(Movie.id).subquery()
        return (
            session.query(Genre)
            .join(Genre.movies)
            .filter(Movie.id.in_(eligible_ids))
            .distinct()
            .order_by(Genre.name)
            .all()
        )
    finally:
        session.close()


@app.get("/api/years", response_model=List[int])
def list_years() -> List[int]:
    session = SessionLocal()
    try:
        rows = (
            _eligible_movies(session)
            .with_entities(distinct(Movie.year))
            .order_by(Movie.year.desc())
            .all()
        )
        return [row[0] for row in rows]
    finally:
        session.close()


app.mount("/", StaticFiles(directory=str(STATIC_DIR), html=True), name="static")
