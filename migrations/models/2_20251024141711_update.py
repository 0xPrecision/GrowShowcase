from tortoise import BaseDBAsyncClient

RUN_IN_TRANSACTION = True


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


MODELS_STATE = (
    "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"
)
