from typing import List, Optional

from pydantic import BaseModel, ConfigDict


class GenreOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str


class MovieOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    original_title: Optional[str]
    year: int
    url: str
    poster_url: Optional[str]
    user_score: Optional[float]
    user_count: Optional[int]
    critics_score: Optional[float]
    critics_count: Optional[int]
    genres: List[GenreOut]


class MoviesPage(BaseModel):
    total: int
    page: int
    page_size: int
    results: List[MovieOut]
