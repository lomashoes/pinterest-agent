"""
main.py — LomaShooes Pinterest Agent 🥿
Orquestador principal: conecta Shopify → Claude AI → Pinterest
Ejecuta la publicación según la franja horaria España correspondiente.

Uso:
  python main.py              → publicación automática según hora actual
  python main.py --setup      → solo crear/verificar tableros
  python main.py --test       → ejecuta sin publicar (dry run)
  python main.py --stats      → muestra estadísticas
"""

import argparse
import logging
import sys
import random
from datetime import datetime
from zoneinfo import ZoneInfo

from agent.config import (
    PINTEREST_ACCESS_TOKEN,
    SHOPIFY_STORE_URL,
    SHOPIFY_ACCESS_TOKEN,
    ANTHROPIC_API_KEY,
    TIMEZONE,
    POSTING_SCHEDULE,
    ROTATE_LANGS,
    TIME_TOLERANCE_MIN,
)
from agent.shopify_client   import ShopifyClient
from agent.pinterest_client import PinterestClient
from agent.seo_generator    import SEOGenerator
from agent.board_manager    import BoardManager
from agent.state_manager    import StateManager

# ─────────────────────────────────────────────
#  LOGGING
# ─────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-7s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("lomashoes_agent.log", encoding="utf-8"),
    ],
)
logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────
#  VALIDACIÓN DE CREDENCIALES
# ─────────────────────────────────────────────
def validate_credentials():
    missing = []
    if not PINTEREST_ACCESS_TOKEN: missing.append("PINTEREST_ACCESS_TOKEN")
    if not SHOPIFY_STORE_URL:       missing.append("SHOPIFY_STORE_URL")
    if not SHOPIFY_ACCESS_TOKEN:    missing.append("SHOPIFY_ACCESS_TOKEN")
    if not ANTHROPIC_API_KEY:       missing.append("ANTHROPIC_API_KEY")
    if missing:
        logger.error(f"❌ Faltan credenciales: {', '.join(missing)}")
        logger.error("   Configura las variables en .env o en GitHub Secrets")
        sys.exit(1)
    logger.info("✅ Credenciales verificadas")


# ─────────────────────────────────────────────
#  DETERMINAR QUÉ SLOT CORRESPONDE AHORA
# ─────────────────────────────────────────────
def get_current_slot() -> dict | None:
    """
    Comprueba si la hora actual (zona España) coincide con alguna
    franja programada (con tolerancia de ±TIME_TOLERANCE_MIN minutos).
    """
    now_spain = datetime.now(ZoneInfo(TIMEZONE))
    now_total = now_spain.hour * 60 + now_spain.minute

    for slot in POSTING_SCHEDULE:
        h, m      = slot["time"]
        slot_total = h * 60 + m
        if abs(now_total - slot_total) <= TIME_TOLERANCE_MIN:
            return slot

    logger.info(
        f"⏰ Hora España: {now_spain.strftime('%H:%M')} — "
        f"No hay slot programado en este momento (tolerancia ±{TIME_TOLERANCE_MIN} min)"
    )
    return None


# ─────────────────────────────────────────────
#  PUBLICACIÓN DE UN PIN
# ─────────────────────────────────────────────
def publish_pin(
    lang:       str,
    products:   list[dict],
    board_map:  dict,
    state:      StateManager,
    pinterest:  PinterestClient,
    seo:        SEOGenerator,
    board_mgr:  BoardManager,
    dry_run:    bool = False,
):
    # 1. Producto no publicado aún
    candidates = state.get_unpublished(products)
    if not candidates:
        logger.warning("⚠️  No hay productos disponibles para publicar")
        return

    product = random.choice(candidates)
    logger.info(f"📦 Producto seleccionado: «{product['title']}» (id={product['id']})")

    # 2. Seleccionar tablero según idioma
    board_id, board_cfg = board_mgr.get_board_for_lang(board_map, lang)
    if not board_id:
        logger.error(f"❌ No se encontró tablero para lang={lang}")
        return

    logger.info(f"📌 Tablero destino: «{board_cfg['name']}»")

    # 3. Generar contenido SEO con Claude
    logger.info(f"🤖 Generando SEO con Claude AI [{lang}]…")
    seo_content = seo.generate(
        product=product,
        lang=lang,
        board_style=board_cfg["style"],
    )

    # 4. Combinar hashtags del tablero + generados por IA
    all_hashtags = list(dict.fromkeys(
        board_cfg.get("hashtags", []) + seo_content["hashtags"]
    ))[:20]

    logger.info(f"📝 Título: {seo_content['title']}")
    logger.info(f"🏷️  Hashtags ({len(all_hashtags)}): {' '.join(all_hashtags[:5])}…")

    if dry_run:
        logger.info("🔍 DRY RUN — Pin NO publicado en Pinterest")
        logger.info(f"   Descripción preview: {seo_content['description'][:120]}…")
        return

    # 5. Publicar en Pinterest
    pinterest.wait_between_requests(1.5)
    pin = pinterest.create_pin(
        board_id=board_id,
        image_url=product["image_url"],
        title=seo_content["title"],
        description=seo_content["description"],
        link=product["product_url"],
        hashtags=all_hashtags,
    )

    if pin:
        state.mark_published(
            product_id=product["id"],
            lang=lang,
            pin_id=str(pin.get("id", "")),
            title=seo_content["title"],
        )
        logger.info(f"🎉 ¡Pin publicado con éxito! pin_id={pin.get('id')}")
    else:
        logger.error("❌ Fallo al publicar el pin en Pinterest")


# ─────────────────────────────────────────────
#  SETUP DE TABLEROS
# ─────────────────────────────────────────────
def setup_boards(pinterest: PinterestClient) -> dict:
    logger.info("🗂️  Iniciando setup de tableros Pinterest para @lomashoes…")
    board_mgr = BoardManager(pinterest)
    board_map = board_mgr.ensure_all_boards()
    logger.info(f"✅ Setup completo — {len(board_map)} tableros configurados")
    return board_map


# ─────────────────────────────────────────────
#  MAIN
# ─────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(description="LomaShooes Pinterest Agent")
    parser.add_argument("--setup",   action="store_true", help="Solo crear/verificar tableros")
    parser.add_argument("--test",    action="store_true", help="Dry run — no publica en Pinterest")
    parser.add_argument("--stats",   action="store_true", help="Mostrar estadísticas")
    parser.add_argument("--lang",    type=str,            help="Forzar idioma (es/en/fr/it/pt)")
    args = parser.parse_args()

    validate_credentials()

    # Clientes
    pinterest = PinterestClient(PINTEREST_ACCESS_TOKEN)
    shopify   = ShopifyClient(SHOPIFY_STORE_URL, SHOPIFY_ACCESS_TOKEN)
    seo       = SEOGenerator(ANTHROPIC_API_KEY)
    state     = StateManager()
    board_mgr = BoardManager(pinterest)

    # ── Estadísticas ──
    if args.stats:
        logger.info(f"📊 {state.summary()}")
        return

    # ── Solo setup de tableros ──
    if args.setup:
        setup_boards(pinterest)
        return

    # ── Determinar idioma según slot horario ──
    if args.lang:
        lang = args.lang
        logger.info(f"⚙️  Idioma forzado por argumento: {lang}")
    else:
        slot = get_current_slot()
        if not slot and not args.test:
            logger.info("🚫 Fuera de franja horaria — saliendo sin publicar")
            return

        if slot:
            lang_raw = slot["lang"]
        else:
            lang_raw = "es"  # fallback para test

        # Resolver el idioma rotativo
        if lang_raw == "rotate":
            lang = state.get_and_advance_rotate_lang(ROTATE_LANGS)
        else:
            lang = lang_raw

    logger.info(f"🌍 Idioma seleccionado: {lang}")

    # ── Obtener productos de Shopify ──
    logger.info("🛍️  Obteniendo catálogo de Shopify…")
    products = shopify.get_pin_ready_products()
    if not products:
        logger.error("❌ No se obtuvieron productos de Shopify — abortando")
        return
    logger.info(f"✅ {len(products)} productos disponibles en catálogo")

    # ── Verificar / crear tableros ──
    board_map = board_mgr.ensure_all_boards()

    # ── Publicar pin ──
    now_spain = datetime.now(ZoneInfo(TIMEZONE))
    logger.info(
        f"🕐 Hora España: {now_spain.strftime('%H:%M')} | "
        f"Modo: {'DRY RUN' if args.test else 'PRODUCCIÓN'}"
    )

    publish_pin(
        lang=lang,
        products=products,
        board_map=board_map,
        state=state,
        pinterest=pinterest,
        seo=seo,
        board_mgr=board_mgr,
        dry_run=args.test,
    )

    logger.info(f"━━━ Fin ejecución | {state.summary()} ━━━")


if __name__ == "__main__":
    main()
