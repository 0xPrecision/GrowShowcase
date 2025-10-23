from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        CREATE TABLE IF NOT EXISTS "products" (
    "id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    "name" VARCHAR(128) NOT NULL,
    "description" TEXT,
    "price" VARCHAR(40) NOT NULL,
    "sku" VARCHAR(64),
    "is_active" INT NOT NULL DEFAULT 1,
    "photo" VARCHAR(512),
    "created_at" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
) /* Storefront product (catalog item). */;
CREATE INDEX IF NOT EXISTS "idx_products_sku_df1bf0" ON "products" ("sku");
CREATE INDEX IF NOT EXISTS "idx_products_is_acti_b94558" ON "products" ("is_active", "created_at");
CREATE TABLE IF NOT EXISTS "reviews" (
    "id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    "file_id" VARCHAR(255) NOT NULL UNIQUE,
    "file_unique_id" VARCHAR(255) NOT NULL,
    "added_by" BIGINT,
    "created_at" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS "idx_reviews_file_un_f9d627" ON "reviews" ("file_unique_id");
CREATE TABLE IF NOT EXISTS "users" (
    "id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    "username" VARCHAR(64),
    "full_name" VARCHAR(128),
    "phone" VARCHAR(20),
    "address" VARCHAR(256),
    "created_at" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "is_active" INT NOT NULL DEFAULT 1
) /* Telegram user. PK = telegram_id (BigInt). */;
CREATE INDEX IF NOT EXISTS "idx_users_usernam_266d85" ON "users" ("username");
CREATE INDEX IF NOT EXISTS "idx_users_is_acti_fe165a" ON "users" ("is_active", "created_at");
CREATE TABLE IF NOT EXISTS "cart" (
    "id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    "quantity" INT NOT NULL DEFAULT 1,
    "product_id" INT NOT NULL REFERENCES "products" ("id") ON DELETE RESTRICT,
    "user_id" BIGINT NOT NULL REFERENCES "users" ("id") ON DELETE CASCADE,
    CONSTRAINT "uid_cart_user_id_d2f7dd" UNIQUE ("user_id", "product_id")
) /* User's cart item. One row per (user, product). */;
CREATE INDEX IF NOT EXISTS "idx_cart_user_id_5e18ab" ON "cart" ("user_id");
CREATE TABLE IF NOT EXISTS "orders" (
    "id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    "client_name" VARCHAR(128),
    "name" VARCHAR(128),
    "amount_cents" INT NOT NULL DEFAULT 0,
    "currency" VARCHAR(8) NOT NULL DEFAULT 'USD',
    "status" VARCHAR(32) NOT NULL DEFAULT 'pending',
    "created_at" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "provider" VARCHAR(32),
    "order_uid" VARCHAR(64) UNIQUE,
    "txid" VARCHAR(128),
    "stripe_session_id" VARCHAR(128),
    "stripe_payment_intent" VARCHAR(128),
    "stripe_customer" VARCHAR(128),
    "payment_method" VARCHAR(64),
    "comment" TEXT,
    "meta" JSON,
    "user_id" BIGINT NOT NULL REFERENCES "users" ("id") ON DELETE RESTRICT
) /* Customer order. Single-payment workflow. */;
CREATE INDEX IF NOT EXISTS "idx_orders_user_id_705a43" ON "orders" ("user_id", "created_at");
CREATE INDEX IF NOT EXISTS "idx_orders_status_c63842" ON "orders" ("status", "created_at");
CREATE INDEX IF NOT EXISTS "idx_orders_provide_d31ce3" ON "orders" ("provider", "created_at");
CREATE TABLE IF NOT EXISTS "order_items" (
    "id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    "title" VARCHAR(256) NOT NULL,
    "unit_amount_cents" INT NOT NULL,
    "quantity" INT NOT NULL DEFAULT 1,
    "meta" JSON,
    "order_id" INT NOT NULL REFERENCES "orders" ("id") ON DELETE CASCADE,
    "product_id" INT REFERENCES "products" ("id") ON DELETE SET NULL
) /* Order position snapshot + FK to live Product. */;
CREATE INDEX IF NOT EXISTS "idx_order_items_order_i_3cb419" ON "order_items" ("order_id");
CREATE TABLE IF NOT EXISTS "user_locales" (
    "locale" VARCHAR(8) NOT NULL,
    "user_id" BIGINT NOT NULL PRIMARY KEY REFERENCES "users" ("id") ON DELETE RESTRICT
) /* One-to-one to User. PK = user_id. */;
CREATE TABLE IF NOT EXISTS "aerich" (
    "id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    "version" VARCHAR(255) NOT NULL,
    "app" VARCHAR(100) NOT NULL,
    "content" JSON NOT NULL
);"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        """
