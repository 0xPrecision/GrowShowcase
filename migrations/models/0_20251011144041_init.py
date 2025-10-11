from tortoise import BaseDBAsyncClient

RUN_IN_TRANSACTION = True


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
CREATE TABLE IF NOT EXISTS "reviews" (
    "id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    "file_id" VARCHAR(255) NOT NULL UNIQUE,
    "file_unique_id" VARCHAR(255) NOT NULL,
    "added_by" BIGINT,
    "created_at" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS "idx_reviews_file_un_f9d627" ON "reviews" ("file_unique_id");
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


MODELS_STATE = (
    "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"
    "UtRDTQ=="
)
