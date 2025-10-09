from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        CREATE TABLE IF NOT EXISTS "product" (
    "id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    "name" VARCHAR(128) NOT NULL,
    "description" TEXT,
    "price" VARCHAR(40) NOT NULL,
    "is_active" INT NOT NULL DEFAULT 1,
    "photo" VARCHAR(256),
    "created_at" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
) /* Product model. */;
CREATE TABLE IF NOT EXISTS "user" (
    "id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    "username" VARCHAR(64),
    "full_name" VARCHAR(128) NOT NULL,
    "phone" VARCHAR(20),
    "address" VARCHAR(128) NOT NULL,
    "created_at" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "is_active" INT NOT NULL DEFAULT 1
) /* User model. */;
CREATE TABLE IF NOT EXISTS "cart" (
    "id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    "quantity" INT NOT NULL,
    "product_id" INT NOT NULL REFERENCES "product" ("id") ON DELETE CASCADE,
    "user_id" BIGINT NOT NULL REFERENCES "user" ("id") ON DELETE CASCADE
) /* Cart item. */;
CREATE TABLE IF NOT EXISTS "order" (
    "updated_at" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    "name" VARCHAR(128),
    "created_at" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "status" VARCHAR(32) NOT NULL DEFAULT 'In progress',
    "total_price" VARCHAR(40) NOT NULL DEFAULT 0,
    "payment_method" VARCHAR(64),
    "comment" TEXT,
    "user_id" BIGINT NOT NULL REFERENCES "user" ("id") ON DELETE CASCADE
) /* Order model. */;
CREATE TABLE IF NOT EXISTS "orderitem" (
    "id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    "quantity" INT NOT NULL,
    "price_at_order" VARCHAR(40) NOT NULL,
    "order_id" INT NOT NULL REFERENCES "order" ("id") ON DELETE CASCADE,
    "product_id" INT NOT NULL REFERENCES "product" ("id") ON DELETE CASCADE
) /* Order item (product within an order). */;
CREATE TABLE IF NOT EXISTS "userlocale" (
    "locale" VARCHAR(8) NOT NULL,
    "user_id" BIGINT NOT NULL PRIMARY KEY REFERENCES "user" ("id") ON DELETE RESTRICT
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
