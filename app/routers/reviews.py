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


@router.get("/", response_model=list[ReviewSchema])
async def get_all_reviews(db: AsyncSession = Depends(get_async_db)):
    """
    Возвращает список всех активных отзывов
    """
    result = await db.scalars(
        select(ReviewModel).where(ReviewModel.is_active == True).order_by(ReviewModel.comment_date.desc())
    )
    return result.all()


@router.get("/{product_id}/reviews/", response_model=list[ReviewSchema])
async def get_reviews_for_product(product_id: int, db: AsyncSession = Depends(get_async_db)):
    """
    Возвращает список активных отзывов для указанного товара.
    """
    # Проверка существования и активности товара
    product = await db.get(ProductModel, product_id)
    if not product or not product.is_active:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Товар не найден или не активен."
        )

    # Получение активных отзывов
    result = await db.scalars(
        select(ReviewModel)
        .where(
            ReviewModel.product_id == product_id,
            ReviewModel.is_active == True
        )
        .order_by(ReviewModel.comment_date.desc())
    )
    return result.all()


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

    # Проверка существования и активности товара
    product = await db.get(ProductModel, product_id)
    if not product or not product.is_active:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Товар не найден или не активен."
        )

    # Проверка: не оставлял ли пользователь уже активный отзыв на этот товар?
    existing_review = await db.scalar(
        select(ReviewModel).where(
            and_(
                ReviewModel.product_id == product_id,
                ReviewModel.user_id == user_id,
                ReviewModel.is_active == True
            )
        )
    )

    if existing_review:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Вы уже оставили активный отзыв на этот товар. Обновите или удалите его, чтобы создать новый."
        )

    # Создание отзыва.
    db_review = ReviewModel(
        **review_data.model_dump(),
        user_id=user_id
    )

    db.add(db_review)
    await db.commit()
    await db.refresh(db_review)

    # Пересчёт рейтинга товара
    await update_product_rating(db, product_id)

    return db_review
