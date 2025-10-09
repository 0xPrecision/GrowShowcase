import logging

logging.basicConfig(
    level=logging.INFO,  # ставишь DEBUG, если хочешь видеть всё подряд
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)

logger = logging.getLogger(__name__)
