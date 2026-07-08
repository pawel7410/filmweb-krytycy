import datetime as dt

from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String, Table
from sqlalchemy.orm import relationship

from app.db import Base

movie_genre = Table(
    "movie_genre",
    Base.metadata,
    Column("movie_id", ForeignKey("movies.id"), primary_key=True),
    Column("genre_id", ForeignKey("genres.id"), primary_key=True),
)


class Genre(Base):
    __tablename__ = "genres"

    id = Column(Integer, primary_key=True)  # filmweb genre id
    name = Column(String, unique=True, nullable=False)

    movies = relationship("Movie", secondary=movie_genre, back_populates="genres")


class Movie(Base):
    __tablename__ = "movies"

    id = Column(Integer, primary_key=True)  # filmweb film id
    title = Column(String, nullable=False)
    original_title = Column(String, nullable=True)
    year = Column(Integer, nullable=False, index=True)
    url = Column(String, nullable=False)
    poster_url = Column(String, nullable=True)

    user_score = Column(Float, nullable=True)
    user_count = Column(Integer, nullable=True)

    critics_score = Column(Float, nullable=True)
    critics_count = Column(Integer, nullable=True)
    critics_scraped_at = Column(DateTime, nullable=True)

    scraped_at = Column(DateTime, default=dt.datetime.utcnow, nullable=False)

    genres = relationship("Genre", secondary=movie_genre, back_populates="movies")
