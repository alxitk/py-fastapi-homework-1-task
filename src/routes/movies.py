from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
import math

from database import get_db, MovieModel
from schemas.movies import MovieListResponseSchema, MovieDetailResponseSchema

router = APIRouter()


def get_pagination_params(
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=20),
):
    return {"page": page, "per_page": per_page}


@router.get("/movies/", response_model=MovieListResponseSchema)
async def read_movies(
        db: AsyncSession = Depends(get_db),
        pagination: dict = Depends(get_pagination_params),
):

    page = pagination["page"]
    per_page = pagination["per_page"]
    start = (page - 1) * per_page

    result = await db.execute(
        select(MovieModel).offset(start).limit(per_page)
    )
    movies = result.scalars().all()
    movie_list = [MovieDetailResponseSchema.model_validate
                  (movie, from_attributes=True) for movie in movies]

    if not movies:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No movies found."
        )

    count_result = await db.execute(select(func.count(MovieModel.id)))
    total_items = count_result.scalar()
    total_pages = math.ceil(total_items / per_page)

    base_url = "/theater/movies"
    prev_page = f"{base_url}?page={page-1}&per_page={per_page}" \
        if page > 1 else None
    next_page = f"{base_url}?page={page+1}&per_page={per_page}" \
        if page < total_pages else None
    return {
        "movies": movie_list,
        "prev_page": prev_page,
        "next_page": next_page,
        "total_pages": total_pages,
        "total_items": total_items,
    }


@router.get("/movies/{movie_id}/", response_model=MovieDetailResponseSchema)
async def get_movie(movie_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(MovieModel).where(MovieModel.id == movie_id)
    )
    movie = result.scalar_one_or_none()
    if not movie:
        raise HTTPException(
            status_code=404, detail="Movie with the given ID was not found."
        )
    return movie
