from aiogram import Router

from .user_cart import router as cart_router
from .user_orders import router as order_router
from .user_catalog import router as catalog_router
from .user_checkout import router as checkout_router
from .user_common import router as common_router
from .user_help import router as help_router
from .user_menu import router as menu_router
from .user_profile import router as profile_router

router = Router()
router.include_router(common_router)
router.include_router(catalog_router)
router.include_router(cart_router)
router.include_router(order_router)
router.include_router(checkout_router)
router.include_router(profile_router)
router.include_router(help_router)
router.include_router(menu_router)
