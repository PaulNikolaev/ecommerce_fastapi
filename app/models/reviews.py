from sqlalchemy import Integer, String, Boolean, ForeignKey, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Review(Base):
    __tablename__ = "reviews"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"), nullable=False)
    comment: Mapped[str | None] = mapped_column(String, nullable=True)
    comment_date: Mapped[DateTime] = mapped_column(DateTime, default=func.now())
    grade: Mapped[int] = mapped_column(Integer, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # Отношения
    user = relationship("User", back_populates="reviews")
    product = relationship("Product", back_populates="reviews")
