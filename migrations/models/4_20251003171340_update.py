from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE "product" ADD "description" TEXT;
        ALTER TABLE "product" DROP COLUMN "description_key";"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE "product" ADD "description_key" VARCHAR(128);
        ALTER TABLE "product" DROP COLUMN "description";"""
