from tortoise import BaseDBAsyncClient

RUN_IN_TRANSACTION = True


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


MODELS_STATE = (
    "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"
    "nP0u5rbTQ39Po/dZRSaw=="
)
