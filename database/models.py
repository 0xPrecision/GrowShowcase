from decimal import Decimal
from constants import ORDER_STATUSES
from tortoise import fields
from tortoise.models import Model


# -----------------------------
# User & Locale
# -----------------------------


class User(Model):
    """
    Telegram user. PK = telegram_id (BigInt).
    """

    id = fields.BigIntField(pk=True)  # Telegram user id
    username = fields.CharField(max_length=64, null=True, index=True)
    full_name = fields.CharField(max_length=128, null=True)
    phone = fields.CharField(max_length=20, null=True)
    address = fields.CharField(max_length=256, null=True)

    created_at = fields.DatetimeField(auto_now_add=True)
    is_active = fields.BooleanField(default=True)

    class Meta:
        table = "users"
        indexes = (("is_active", "created_at"),)


class UserLocale(Model):
    """
    One-to-one to User. PK = user_id.
    """

    user: fields.OneToOneRelation[User] = fields.OneToOneField(
        "models.User",
        pk=True,
        related_name="locale_pref",
        on_delete=fields.RESTRICT,
    )
    locale = fields.CharField(max_length=8)

    class Meta:
        table = "user_locales"


# -----------------------------
# Catalog
# -----------------------------


class Product(Model):
    """
    Storefront product (catalog item).
    """

    id = fields.IntField(pk=True)
    name = fields.CharField(max_length=128)
    description = fields.TextField(null=True)
    price = fields.DecimalField(max_digits=10, decimal_places=2)  # каталогная цена
    sku = fields.CharField(max_length=64, null=True, index=True)
    is_active = fields.BooleanField(default=True)
    photo = fields.CharField(max_length=512, null=True, default=None)

    created_at = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = "products"
        indexes = (("is_active", "created_at"),)

    @property
    def status_key(self) -> str:
        return "product.status.active" if self.is_active else "product.status.archived"

    def status_label(self, t) -> str:
        return t(self.status_key)


# -----------------------------
# Orders
# -----------------------------


class Order(Model):
    """
    Customer order. Single-payment workflow.
    """

    id = fields.IntField(pk=True)
    user = fields.ForeignKeyField(
        "models.User", related_name="orders", on_delete=fields.RESTRICT
    )

    # For admin notifications and receipts
    client_name = fields.CharField(max_length=128, null=True)
    name = fields.CharField(
        max_length=128, null=True
    )  # e.g. "Cart (3 items)" / "Order #ABCD1234"

    # Money (source of truth)
    amount_cents = fields.IntField(default=0)
    currency = fields.CharField(max_length=8, default="USD")

    status = fields.CharField(max_length=32, choices=ORDER_STATUSES, default="pending")
    created_at = fields.DatetimeField(auto_now_add=True)

    # Provider and external references
    provider = fields.CharField(max_length=32, null=True)  # 'stripe' | 'cryptomus'
    order_uid = fields.CharField(max_length=64, unique=True, null=True)
    txid = fields.CharField(max_length=128, null=True)

    # Stripe-only fields for reconciliation
    stripe_session_id = fields.CharField(max_length=128, null=True)
    stripe_payment_intent = fields.CharField(max_length=128, null=True)
    stripe_customer = fields.CharField(max_length=128, null=True)

    # Aux
    payment_method = fields.CharField(max_length=64, null=True)
    comment = fields.TextField(null=True)
    meta = fields.JSONField(null=True)
    notified_paid = fields.BooleanField(default=False, null=True)
    notified_cancel = fields.BooleanField(default=False, null=True)

    class Meta:
        table = "orders"
        indexes = (
            ("user_id", "created_at"),
            ("status", "created_at"),
            ("provider", "created_at"),
        )

    async def normalize(self):
        if self.currency:
            self.currency = self.currency.upper()
        if self.status and self.status not in dict(ORDER_STATUSES):
            self.status = "pending"

    async def save(self, *args, **kwargs):
        await self.normalize()
        return await super().save(*args, **kwargs)

    @property
    def total_cents(self) -> int:
        return int(self.amount_cents or 0)

    @property
    def total_price(self) -> Decimal:
        return (Decimal(self.total_cents) / Decimal(100)).quantize(Decimal("0.01"))


class OrderItem(Model):
    """
    Order position snapshot + FK to live Product.
    """

    id = fields.IntField(pk=True)
    order = fields.ForeignKeyField(
        "models.Order", related_name="items", on_delete=fields.CASCADE
    )

    # Live link to catalog (optional)
    product = fields.ForeignKeyField(
        "models.Product",
        related_name="order_items",
        null=True,
        on_delete=fields.SET_NULL,
    )

    # Snapshot for the receipt
    title = fields.CharField(max_length=256)
    unit_amount_cents = fields.IntField()
    quantity = fields.IntField(default=1)

    meta = fields.JSONField(null=True)

    class Meta:
        table = "order_items"
        indexes = (("order_id",),)

    @property
    def total_cents(self) -> int:
        return int(self.unit_amount_cents) * int(self.quantity)


# -----------------------------
# Cart
# -----------------------------


class Cart(Model):
    """
    User's cart item. One row per (user, product).
    """

    id = fields.IntField(pk=True)
    user = fields.ForeignKeyField(
        "models.User", related_name="cart", on_delete=fields.CASCADE
    )
    product = fields.ForeignKeyField(
        "models.Product", related_name="+", on_delete=fields.RESTRICT
    )
    quantity = fields.IntField(default=1)

    class Meta:
        table = "cart"
        unique_together = (("user_id", "product_id"),)
        indexes = (("user_id",),)

    async def save(self, *args, **kwargs):
        # не даём хранить нули/отрицательное
        if not self.quantity or self.quantity < 1:
            self.quantity = 1
        return await super().save(*args, **kwargs)


# -----------------------------
# Reviews
# -----------------------------


class Review(Model):
    id = fields.IntField(pk=True)
    file_id = fields.CharField(max_length=255, unique=True)
    file_unique_id = fields.CharField(max_length=255, index=True)
    added_by = fields.BigIntField(null=True)  # telegram user id
    created_at = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = "reviews"
        ordering = ["-created_at"]
