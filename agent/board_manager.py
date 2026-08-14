"""
Board Manager — Crea y mapea automáticamente los 12 tableros de LomaShooes
Combinación idioma × estilo para máxima cobertura SEO
"""

import json
import logging
from pathlib import Path

from agent.config import BOARDS_CONFIG
from agent.pinterest_client import PinterestClient

logger = logging.getLogger(__name__)

BOARDS_CACHE_FILE = Path("boards_cache.json")


class BoardManager:
    """
    Gestiona los tableros de Pinterest para @lomashoes.
    - Comprueba si existen en la cuenta
    - Los crea si no existen
    - Cachea los IDs para no llamar a la API innecesariamente
    """

    def __init__(self, pinterest: PinterestClient):
        self.pinterest = pinterest
        self._cache: dict = self._load_cache()

    # ──────────────────────────────────────────
    def ensure_all_boards(self) -> dict:
        """
        Garantiza que los 12 tableros existen en Pinterest.
        Retorna un dict {board_key: board_id}
        """
        logger.info("🗂️  Verificando / creando tableros de Pinterest…")
        existing = {b["name"]: b for b in self.pinterest.get_all_boards()}

        board_map = {}
        for cfg in BOARDS_CONFIG:
            key  = cfg["key"]
            name = cfg["name"]

            # Usar caché si ya tenemos el ID
            if key in self._cache:
                board_map[key] = self._cache[key]
                logger.info(f"  ✔ Tablero «{name}» ya cacheado (id={self._cache[key]})")
                continue

            # Comprobar si ya existe en Pinterest
            if name in existing:
                board_id = existing[name]["id"]
                logger.info(f"  ✔ Tablero «{name}» ya existe (id={board_id})")
            else:
                # Crear el tablero
                self.pinterest.wait_between_requests(1.2)
                board = self.pinterest.create_board(
                    name=name,
                    description=cfg["description"],
                    privacy="PUBLIC",
                )
                if board is None:
                    logger.error(f"  ❌ No se pudo crear el tablero «{name}» — omitido")
                    continue
                board_id = board["id"]

            board_map[key] = board_id
            self._cache[key] = board_id

        self._save_cache(self._cache)
        logger.info(f"✅ {len(board_map)}/12 tableros disponibles")
        return board_map

    # ──────────────────────────────────────────
    def get_board_for_lang(self, board_map: dict, lang: str) -> tuple[str, dict] | tuple[None, None]:
        """
        Selecciona aleatoriamente uno de los tableros del idioma dado.
        Retorna (board_id, board_config)
        """
        import random
        from agent.config import BOARDS_CONFIG

        candidates = [
            (cfg["key"], board_map[cfg["key"]])
            for cfg in BOARDS_CONFIG
            if cfg["lang"] == lang and cfg["key"] in board_map
        ]

        if not candidates:
            logger.warning(f"No hay tableros disponibles para lang={lang}")
            return None, None

        key, board_id = random.choice(candidates)
        cfg = next(c for c in BOARDS_CONFIG if c["key"] == key)
        return board_id, cfg

    # ──────────────────────────────────────────
    #  Caché en disco
    # ──────────────────────────────────────────
    def _load_cache(self) -> dict:
        if BOARDS_CACHE_FILE.exists():
            try:
                return json.loads(BOARDS_CACHE_FILE.read_text())
            except Exception:
                pass
        return {}

    def _save_cache(self, data: dict):
        try:
            BOARDS_CACHE_FILE.write_text(json.dumps(data, indent=2))
        except Exception as e:
            logger.warning(f"No se pudo guardar caché de tableros: {e}")
