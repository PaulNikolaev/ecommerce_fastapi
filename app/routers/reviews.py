from fastapi import APIRouter, Depends, HTTPException, status, Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from app.models.reviews import Review as ReviewModel
from app.models.products import Product as ProductModel
from app.models.users import User as UserModel

from app.schemas import Review as ReviewSchema, ReviewCreate
from app.db_depends import get_async_db
from app.auth import get_current_admin, get_current_buyer
from app.utils.rating import update_product_rating

router = APIRouter(
    prefix="/reviews",
    tags=["reviews"],
)


@router.post("/", response_model=ReviewSchema, status_code=status.HTTP_201_CREATED)
async def create_review(
        review_data: ReviewCreate,
        db: AsyncSession = Depends(get_async_db),
        current_user: UserModel = Depends(get_current_buyer)
):
    """
    Создаёт новый отзыв (оценка 1-5). Автоматически пересчитывает рейтинг продукта.
    Доступ: buyer.
    """
    product_id = review_data.product_id
    user_id = current_user.id

    # 1. Проверка существования и активности товара (404 Not Found)
    product = await db.get(ProductModel, product_id)
    if not product or not product.is_active:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Товар не найден или не активен."
        )

    # 2. Создание отзыва. Валидация grade (1-5) происходит в Pydantic.
    db_review = ReviewModel(
        **review_data.model_dump(),
        user_id=user_id
    )

    db.add(db_review)
    await db.commit()
    await db.refresh(db_review)

    # 3. Пересчёт рейтинга товара
    await update_product_rating(db, product_id)

    return db_review