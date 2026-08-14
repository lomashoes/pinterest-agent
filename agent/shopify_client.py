"""
Shopify Client — Obtiene productos del catálogo de lomas-shoes.com
Usa la Admin REST API de Shopify (sin coste adicional).
"""

import requests
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class ShopifyClient:
    def __init__(self, store_url: str, access_token: str):
        self.base_url = f"https://{store_url}/admin/api/2024-01"
        self.headers  = {
            "X-Shopify-Access-Token": access_token,
            "Content-Type": "application/json",
        }

    # ──────────────────────────────────────────
    def get_all_products(self, limit: int = 250) -> list[dict]:
        """Devuelve todos los productos activos del catálogo."""
        products, page_info = [], None

        while True:
            params: dict = {"limit": limit, "status": "active"}
            if page_info:
                params["page_info"] = page_info

            try:
                r = requests.get(
                    f"{self.base_url}/products.json",
                    headers=self.headers,
                    params=params,
                    timeout=15,
                )
                r.raise_for_status()
            except requests.RequestException as e:
                logger.error(f"Shopify API error: {e}")
                break

            data = r.json().get("products", [])
            products.extend(data)
            logger.info(f"  ↳ Shopify: {len(data)} productos obtenidos (total: {len(products)})")

            # Paginación basada en Link header
            link_header = r.headers.get("Link", "")
            if 'rel="next"' in link_header:
                import re
                match = re.search(r'page_info=([^&>]+).*rel="next"', link_header)
                page_info = match.group(1) if match else None
                if not page_info:
                    break
            else:
                break

        return products

    # ──────────────────────────────────────────
    def extract_pin_data(self, product: dict) -> Optional[dict]:
        """
        Extrae de un producto Shopify los datos necesarios para crear un Pin:
        - image_url : primera imagen de alta resolución
        - title     : nombre del producto
        - price     : precio formateado
        - product_url: enlace directo al producto
        - tags      : tags de Shopify (útiles para SEO)
        """
        images = product.get("images", [])
        if not images:
            logger.debug(f"  Producto sin imagen: {product.get('title')} — omitido")
            return None

        # Imagen de máxima resolución (Shopify admite parámetros de tamaño)
        raw_src: str = images[0]["src"]
        # Forzar máximo tamaño disponible
        image_url = raw_src.split("?")[0]  # limpia parámetros previos

        variants    = product.get("variants", [{}])
        price_raw   = variants[0].get("price", "0.00") if variants else "0.00"
        price       = f"{float(price_raw):.2f} €"

        handle      = product.get("handle", "")
        product_url = f"https://lomas-shoes.com/products/{handle}"

        return {
            "id":          str(product["id"]),
            "title":       product.get("title", ""),
            "description": product.get("body_html", "").replace("<br>", "\n")
                                                       .replace("</p>", "\n")
                                                       .replace("<[^>]+>", ""),
            "price":       price,
            "image_url":   image_url,
            "product_url": product_url,
            "tags":        [t.strip() for t in product.get("tags", "").split(",") if t.strip()],
            "vendor":      product.get("vendor", ""),
        }

    # ──────────────────────────────────────────
    def get_pin_ready_products(self) -> list[dict]:
        """Devuelve lista de productos listos para publicar como Pins."""
        raw  = self.get_all_products()
        pins = [self.extract_pin_data(p) for p in raw]
        pins = [p for p in pins if p is not None]
        logger.info(f"Shopify: {len(pins)} productos listos para Pinterest")
        return pins
