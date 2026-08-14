"""
State Manager — Gestiona el estado del agente entre ejecuciones
Evita repetir productos y lleva el turno de idiomas rotativos.
Guarda el estado en state.json (commiteado en GitHub para persistir).
"""

import json
import logging
from datetime import datetime, timezone
from pathlib import Path

logger = logging.getLogger(__name__)

STATE_FILE = Path("state.json")

DEFAULT_STATE = {
    "published_product_ids": [],   # IDs de productos ya publicados
    "rotate_lang_index":     0,    # turno actual de it/fr/pt
    "total_pins_published":  0,
    "last_run_utc":          None,
    "log": []                      # últimas 50 publicaciones
}


class StateManager:
    def __init__(self):
        self.state = self._load()

    # ──────────────────────────────────────────
    def _load(self) -> dict:
        if STATE_FILE.exists():
            try:
                data = json.loads(STATE_FILE.read_text())
                # Asegurar claves nuevas si el archivo es antiguo
                for k, v in DEFAULT_STATE.items():
                    data.setdefault(k, v)
                return data
            except Exception as e:
                logger.warning(f"No se pudo leer state.json: {e} — usando estado vacío")
        return DEFAULT_STATE.copy()

    def _save(self):
        try:
            # Guardar solo los últimos 200 IDs publicados (evitar crecer indefinidamente)
            self.state["published_product_ids"] = self.state["published_product_ids"][-200:]
            # Guardar solo los últimos 50 logs
            self.state["log"] = self.state["log"][-50:]
            STATE_FILE.write_text(json.dumps(self.state, indent=2, ensure_ascii=False))
        except Exception as e:
            logger.error(f"No se pudo guardar state.json: {e}")

    # ──────────────────────────────────────────
    #  Productos
    # ──────────────────────────────────────────

    def mark_published(self, product_id: str, lang: str, pin_id: str, title: str):
        self.state["published_product_ids"].append(product_id)
        self.state["total_pins_published"] += 1
        self.state["last_run_utc"] = datetime.now(timezone.utc).isoformat()
        self.state["log"].append({
            "ts":         self.state["last_run_utc"],
            "product_id": product_id,
            "title":      title[:60],
            "lang":       lang,
            "pin_id":     pin_id,
        })
        self._save()
        logger.info(
            f"  💾 Estado guardado — total pins: {self.state['total_pins_published']}"
        )

    def is_published(self, product_id: str) -> bool:
        return product_id in self.state["published_product_ids"]

    def get_unpublished(self, products: list[dict]) -> list[dict]:
        """Filtra productos que aún no han sido publicados."""
        unpublished = [p for p in products if not self.is_published(p["id"])]

        # Si ya publicamos todos, reiniciar el ciclo (catálogo agotado)
        if not unpublished:
            logger.info("🔄 Catálogo completo publicado — reiniciando ciclo")
            self.state["published_product_ids"] = []
            self._save()
            unpublished = products

        return unpublished

    # ──────────────────────────────────────────
    #  Rotación de idiomas (it / fr / pt)
    # ──────────────────────────────────────────

    def get_and_advance_rotate_lang(self, rotate_langs: list[str]) -> str:
        idx  = self.state["rotate_lang_index"] % len(rotate_langs)
        lang = rotate_langs[idx]
        self.state["rotate_lang_index"] = (idx + 1) % len(rotate_langs)
        self._save()
        logger.info(f"  🔄 Idioma rotativo seleccionado: {lang} (índice {idx})")
        return lang

    # ──────────────────────────────────────────
    #  Stats rápidas
    # ──────────────────────────────────────────

    def summary(self) -> str:
        return (
            f"Total pins publicados: {self.state['total_pins_published']} | "
            f"Publicados en ciclo actual: {len(self.state['published_product_ids'])} | "
            f"Última ejecución: {self.state.get('last_run_utc', 'nunca')}"
        )
