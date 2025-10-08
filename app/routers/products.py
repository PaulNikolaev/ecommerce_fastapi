from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, update
from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.products import Product as ProductModel
from app.models.categories import Category as CategoryModel
from app.schemas import Product as ProductSchema, ProductCreate
from app.db_depends import get_db
from app.db_depends import get_async_db

router = APIRouter(
    prefix="/products",
    tags=["products"],
)


@router.get("/", response_model=list[ProductSchema])
async def get_all_products(db: AsyncSession = Depends(get_async_db)):
    """
    Возвращает список всех товаров.
    """
    result = await db.scalars(
        select(ProductModel).join(CategoryModel).where(ProductModel.is_active == True,
                                                       CategoryModel.is_active == True,
                                                       ProductModel.stock > 0))

    return result.all()


@router.post("/", response_model=ProductSchema, status_code=status.HTTP_201_CREATED)
async def create_product(product: ProductCreate, db: AsyncSession = Depends(get_async_db)):
    """
    Создаёт новый товар.
    """
    category_result = await db.scalars(select(CategoryModel).where(CategoryModel.id == product.category_id,
                                                      CategoryModel.is_active == True))
    category = category_result.first()
    if not category:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Категория не найдена или не активна")
    db_product = ProductModel(**product.model_dump())
    db.add(db_product)
    await db.commit()
    await db.refresh(db_product)
    return db_product


@router.get("/category/{category_id}", response_model=list[ProductSchema])
async def get_products_by_category(category_id: int, db: AsyncSession = Depends(get_async_db)):
    """
    Возвращает список активных товаров в указанной категории по её ID.
    """
    # Проверяем, существует ли активная категория
    category_result = await db.scalars(
        select(CategoryModel).where(CategoryModel.id == category_id,
                                    CategoryModel.is_active == True))
    category = category_result.first()
    if not category:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="Category not found or inactive")

    # Получаем активные товары в категории
    products_result = await db.scalars(
        select(ProductModel).where(ProductModel.category_id == category_id,
                                   ProductModel.is_active == True))
    return products_result.all()


@router.get("/{product_id}", response_model=ProductSchema)
async def get_product(product_id: int, db: Session = Depends(get_db)):
    """
    Возвращает детальную информацию о товаре по его ID.
    """
    product = db.scalars(
        select(ProductModel).where(ProductModel.id == product_id,
                                   ProductModel.is_active == True)
    ).first()
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Продукт не найден или не активен")

    category = db.scalars(
        select(CategoryModel).where(CategoryModel.id == product.category_id,
                                    CategoryModel.is_active == True)
    ).first()
    if not category:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Категория не найдена или не активна")
    return product


@router.put("/{product_id}", response_model=ProductSchema)
async def update_product(product_id: int, product: ProductCreate, db: Session = Depends(get_db)):
    """
    Обновляет товар по его ID.
    """
    db_product = db.scalars(
        select(ProductModel).where(ProductModel.id == product_id, ProductModel.is_active == True)
    ).first()
    if not db_product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")

    # Проверяем, существует ли активная категория
    category = db.scalars(
        select(CategoryModel).where(CategoryModel.id == product.category_id,
                                    CategoryModel.is_active == True)
    ).first()
    if not category:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Category not found or inactive")

    # Обновляем товар
    db.execute(
        update(ProductModel).where(ProductModel.id == product_id).values(**product.model_dump())
    )
    db.commit()
    db.refresh(db_product)
    return db_product


@router.delete("/{product_id}")
async def delete_product(product_id: int, db: Session = Depends(get_db)):
    """
    Удаляет товар по его ID (логическое удаление).
    """
    # Проверяем, существует ли активный товар
    product = db.scalars(
        select(ProductModel).where(ProductModel.id == product_id, ProductModel.is_active == True)
    ).first()
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="Product not found or inactive")


    # Изменяем объект устанавив is_active=False и сохраняем
    product.is_active = False
    db.commit()

    return {"status": "Успех", "message": "Продукт отмечен как неактивная"}
