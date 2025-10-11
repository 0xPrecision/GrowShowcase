from aiogram import Router

from .admin_common import router as admin_common_router
from .add_product import router as add_product_router
from .admin_access import router as access_router
from .admin_catalog import router as catalog_router
from .admin_help import router as help_router
from .admin_orders import router as orders_router
from .admin_stats import router as stats_router
from .delete_product import router as delete_product_router
from .edit_product import router as edit_product_router
from .search_order import router as search_order_router
from .search_product import router as search_product_router
from .add_review import router as review_router

router = Router()
router.include_router(admin_common_router)
router.include_router(access_router)
router.include_router(orders_router)
router.include_router(search_order_router)
router.include_router(catalog_router)
router.include_router(search_product_router)
router.include_router(add_product_router)
router.include_router(edit_product_router)
router.include_router(delete_product_router)
router.include_router(stats_router)
router.include_router(help_router)
router.include_router(review_router)
