from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE "orders" ADD "notified_paid" INT DEFAULT 0;
        ALTER TABLE "orders" ADD "notified_cancel" INT DEFAULT 0;
        ALTER TABLE "orders" DROP COLUMN "notified_user";"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE "orders" ADD "notified_user" INT DEFAULT 0;
        ALTER TABLE "orders" DROP COLUMN "notified_paid";
        ALTER TABLE "orders" DROP COLUMN "notified_cancel";"""
