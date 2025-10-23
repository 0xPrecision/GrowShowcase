from decimal import Decimal, ROUND_HALF_UP
from typing import List, Optional, Tuple
from uuid import uuid4

from database.models import Cart, Order, OrderItem, Product, User, Review


# -------- USERS --------


async def get_or_create_user_profile(user_id: int) -> Optional[User]:
    """
    Возвращает профиль по Telegram ID или создаёт новый.
    """
    user = await User.get_or_none(id=user_id)
    if not user:
        user = await User.create(id=user_id)
    return user


# -------- REVIEWS --------


async def create_review(file_id: str, file_unique_id: str):
    # Проверяем, есть ли уже отзыв с таким уникальным файлом
    existing = await Review.get_or_none(file_unique_id=file_unique_id)

    if existing:
        # Файл уже есть — обновим file_id на новый (если Telegram его сменил)
        existing.file_id = file_id
        await existing.save()
        return existing

    # Если нет — создаём новый отзыв
    return await Review.create(file_id=file_id, file_unique_id=file_unique_id)


async def get_all_reviews():
    return await Review.all().count()


async def get_review_by_index(idx: int) -> Optional[Review]:
    rows = await Review.all().offset(idx).limit(1)
    return rows[0] if rows else None


# -------- PRODUCTS --------


async def create_product(
    name: str,
    description: str,
    price: Decimal,
    photo: str = None,
    is_active: bool = True,
) -> Product:
    """
    Creates a new product.
    :param name: Product name.
    :param description: Product description.
    :param price: Price.
    :param photo: Photo file ID.
    :param is_active: Whether the product is active.
    :return: Product object.
    """
    return await Product.create(
        name=name,
        description=description,
        price=price,
        photo=photo,
        is_active=is_active,
    )


async def update_product(product_id: int, **fields) -> int:
    """
    Обновляет поля продукта по id.
    ВНИМАНИЕ: поля должны существовать в модели Product.
    """
    # выкидываем любые неожиданные ключи, чтобы не уронить апдейт
    allowed = {"name", "description", "price", "photo", "is_active", "sku"}
    clean = {k: v for k, v in fields.items() if k in allowed}
    if not clean:
        return 0
    return await Product.filter(id=product_id).update(**clean)


async def get_all_products() -> List[Product]:
    """
    Returns the list of all products.
    :return: List of Product objects.
    """
    return await Product.filter(is_active=True).all()


async def get_product_by_id(product_id: int) -> Optional[Product]:
    """
    Returns a product by its ID.
    :param product_id: Product ID.
    :return: Product object or None.
    """
    return await Product.get_or_none(id=product_id)


async def get_products_page(
    page: int = 1, page_size: int = 10
) -> Tuple[List[Product], bool, bool]:
    total = await Product.filter(is_active=True).count()  # ← без .all()
    total_pages = (total + page_size - 1) // page_size
    page = max(1, page)
    skip = (page - 1) * page_size
    products = (
        await Product.filter(is_active=True)
        .order_by("-id")
        .offset(skip)
        .limit(page_size)
    )
    has_prev = page > 1
    has_next = page < total_pages
    return products, has_next, has_prev


# -------- CART --------


async def add_to_cart(user_id: int, product_id: int, quantity: int) -> Cart:
    """
    Adds a product to the user_kb's cart or increases the quantity if it already exists.
    :param user_id: User ID.
    :param product_id: Product ID.
    :param quantity: Quantity.
    :return: Cart object (cart item).
    """
    user = await get_or_create_user_profile(user_id)
    product = await Product.get(id=product_id)
    cart_item = await Cart.get_or_none(user=user, product=product)
    if cart_item:
        cart_item.quantity += quantity
        await cart_item.save()
    else:
        cart_item = await Cart.create(user=user, product=product, quantity=quantity)
    return cart_item


async def get_cart(user_id: int) -> List[Cart]:
    """
    Returns the user_kb's cart (list of Cart items).
    :param user_id: User ID.
    :return: List of Cart.
    """
    user = await get_or_create_user_profile(user_id)
    return await Cart.filter(user=user).prefetch_related("product").all()


async def remove_from_cart(user_id: int, product_id: int) -> None:
    """
    Удаляет позицию из корзины.
    """
    user = await get_or_create_user_profile(user_id)
    await Cart.filter(user=user, product_id=product_id).delete()


async def clear_cart(user_id: int) -> None:
    """
    Clears the user_kb's cart.
    :param user_id: User ID.
    :return: None
    """
    user = await get_or_create_user_profile(user_id)
    await Cart.filter(user=user).delete()


# -------- ORDERS --------


def _to_cents(x) -> int:
    if isinstance(x, Decimal):
        v = x
    else:
        v = Decimal(str(x))
    return int((v * 100).quantize(Decimal("1"), rounding=ROUND_HALF_UP))


async def create_order(
    user_id: int,
    client_name: Optional[str],
    payment_method: str,
    comment: str = "-",
    currency: str = "USD",
    order_uid: Optional[str] = None,
    name: Optional[str] = None,
) -> Optional[Order]:
    user = await get_or_create_user_profile(user_id)

    cart_items = await Cart.filter(user=user).prefetch_related("product")
    if not cart_items:
        return None

    items_count = 0
    total_cents = 0
    snapshot = []
    for it in cart_items:
        product = it.product
        title = getattr(product, "name", None) or getattr(product, "title", "Item")
        qty = int(getattr(it, "quantity", 1))
        unit_price = getattr(product, "price", 0)
        unit_cents = _to_cents(unit_price)

        if qty <= 0 or unit_cents <= 0:
            continue

        items_count += qty
        total_cents += unit_cents * qty

        snapshot.append(
            {
                "title": title,
                "product_id": getattr(product, "id", None),
                "unit_amount_cents": unit_cents,
                "quantity": qty,
                "meta": {"sku": getattr(product, "sku", None)},  # ← sku в meta
            }
        )

    if not snapshot:
        return None

    currency = (currency or "USD").upper()
    order_uid = order_uid or uuid4().hex[:16]
    name = name or (f"Cart ({items_count} items)" if items_count > 1 else "Order")

    order = await Order.create(
        user=user,
        client_name=client_name,
        name=name,
        amount_cents=total_cents,
        currency=currency,
        status="pending",
        provider=payment_method.lower(),
        order_uid=order_uid,
        payment_method=payment_method,
        comment=comment,
        meta={
            "items_count": items_count,
            "cart_hash": uuid4().hex[:12],
            "source": "telegram",
            "schema_version": 1,
        },
    )

    for snap in snapshot:
        await OrderItem.create(
            order=order,
            title=snap["title"],
            product_id=snap["product_id"],
            unit_amount_cents=snap["unit_amount_cents"],
            quantity=snap["quantity"],
            meta=snap["meta"],  # здесь лежит sku
        )

    await clear_cart(user_id)
    return order


async def get_orders(user_id: int | None = None) -> List[Order]:
    """
    Возвращает список заказов. Для конкретного пользователя — его заказы,
    иначе — все, отсортированные по дате.
    """
    qs = Order.all().order_by("-created_at")
    if user_id:
        qs = qs.filter(user_id=user_id)
    return await qs.prefetch_related("items", "user")


async def get_order_items(order: Order) -> List[OrderItem]:
    """
    Возвращает позиции заказа.
    """
    return await OrderItem.filter(order=order).all()


async def get_order_by_id(order_id: int) -> Optional[Order]:
    """
    Возвращает заказ по id.
    """
    order = await Order.get_or_none(id=order_id)
    if order:
        await order.fetch_related("user", "items")
    return order


async def get_orders_page(
    page: int = 1, page_size: int = 10
) -> Tuple[List[Order], bool, bool]:
    """
    Пагинация заказов по дате убыв.
    """
    total = await Order.all().count()
    total_pages = (total + page_size - 1) // page_size
    page = max(1, page)
    skip = (page - 1) * page_size

    orders = (
        await Order.all()
        .order_by("-created_at")
        .offset(skip)
        .limit(page_size)
        .prefetch_related("items", "user")
    )

    has_prev = page > 1
    has_next = page < total_pages
    return orders, has_next, has_prev
