from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.sql import func
from app.models.reviews import Review as ReviewModel
from app.models.products import Product as ProductModel


async def update_product_rating(db: AsyncSession, product_id: int) -> None:
    """
    Пересчитывает средний рейтинг продукта на основе всех активных отзывов.
    """
    result = await db.execute(
        select(func.avg(ReviewModel.grade)).where(
            ReviewModel.product_id == product_id,
            ReviewModel.is_active == True
        )
    )
    avg_rating = result.scalar()
    new_rating = round(avg_rating, 2) if avg_rating is not None else 0.0

    product = await db.get(ProductModel, product_id)
    if product:
        product.rating = new_rating
        await db.commit()
