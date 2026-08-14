"""
Pinterest Client — API v5
Crea tableros y publica Pins para @lomashoes
"""

import requests
import logging
import time

logger = logging.getLogger(__name__)

PINTEREST_API = "https://api-sandbox.pinterest.com/v5"


class PinterestClient:
    def __init__(self, access_token: str):
        self.headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        }

    # ──────────────────────────────────────────
    #  BOARDS
    # ──────────────────────────────────────────

    def get_all_boards(self) -> list[dict]:
        """Devuelve todos los tableros de la cuenta."""
        boards, bookmark = [], None

        while True:
            params = {"page_size": 100}
            if bookmark:
                params["bookmark"] = bookmark

            try:
                r = requests.get(
                    f"{PINTEREST_API}/boards",
                    headers=self.headers,
                    params=params,
                    timeout=15,
                )
                r.raise_for_status()
            except requests.RequestException as e:
                logger.error(f"Pinterest get_boards error: {e}")
                break

            data     = r.json()
            boards  += data.get("items", [])
            bookmark = data.get("bookmark")
            if not bookmark:
                break

        logger.info(f"Pinterest: {len(boards)} tableros encontrados en la cuenta")
        return boards

    def create_board(self, name: str, description: str, privacy: str = "PUBLIC") -> dict | None:
        """Crea un tablero nuevo. Retorna el objeto board creado."""
        payload = {
            "name":        name,
            "description": description,
            "privacy":     privacy,
        }

        try:
            r = requests.post(
                f"{PINTEREST_API}/boards",
                headers=self.headers,
                json=payload,
                timeout=15,
            )
            r.raise_for_status()
            board = r.json()
            logger.info(f"  ✅ Tablero creado: «{name}» (id={board['id']})")
            return board
        except requests.HTTPError as e:
            # 409 = ya existe, buscarlo
            if r.status_code == 409:
                logger.warning(f"  ⚠️  Tablero «{name}» ya existe — buscando id…")
                return self._find_board_by_name(name)
            logger.error(f"  ❌ Error creando tablero «{name}»: {e} — {r.text}")
            return None
        except requests.RequestException as e:
            logger.error(f"  ❌ Error creando tablero «{name}»: {e}")
            return None

    def _find_board_by_name(self, name: str) -> dict | None:
        boards = self.get_all_boards()
        for b in boards:
            if b.get("name", "").strip().lower() == name.strip().lower():
                return b
        return None

    # ──────────────────────────────────────────
    #  PINS
    # ──────────────────────────────────────────

    def create_pin(
        self,
        board_id:    str,
        image_url:   str,
        title:       str,
        description: str,
        link:        str,
        hashtags:    list[str],
    ) -> dict | None:
        """
        Publica un Pin en el tablero indicado.
        Combina descripción + hashtags en el campo 'description' de Pinterest.
        """
        # Pinterest max: title 100 chars, description 500 chars
        full_description = description.strip()
        if hashtags:
            tags_str = " ".join(hashtags[:20])
            # Asegurar que no excede 500 chars
            if len(full_description) + len(tags_str) + 2 <= 500:
                full_description += f"\n\n{tags_str}"
            else:
                # Truncar descripción para que quepan los hashtags
                max_desc = 500 - len(tags_str) - 3
                full_description = full_description[:max_desc].rstrip() + f"\n\n{tags_str}"

        payload = {
            "board_id": board_id,
            "title":    title[:100],
            "description": full_description[:500],
            "link":     link,
            "media_source": {
                "source_type": "image_url",
                "url":         image_url,
            },
        }

        try:
            r = requests.post(
                f"{PINTEREST_API}/pins",
                headers=self.headers,
                json=payload,
                timeout=30,
            )
            r.raise_for_status()
            pin = r.json()
            logger.info(f"  📌 Pin publicado: «{title[:50]}…» → board {board_id} (pin_id={pin.get('id')})")
            return pin
        except requests.HTTPError as e:
            logger.error(f"  ❌ Error publicando pin «{title[:40]}»: {e} — {r.text}")
            return None
        except requests.RequestException as e:
            logger.error(f"  ❌ Error publicando pin: {e}")
            return None

    # ──────────────────────────────────────────
    #  RATE LIMIT helper
    # ──────────────────────────────────────────
    @staticmethod
    def wait_between_requests(seconds: float = 1.0):
        """Pequeña pausa para respetar rate limits de Pinterest API."""
        time.sleep(seconds)
