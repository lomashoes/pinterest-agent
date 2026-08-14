"""
SEO Generator — Genera títulos, descripciones y hashtags con Claude AI
Optimizados para Pinterest y búsqueda orgánica de zapatos de novia.
"""

import anthropic
import logging
import re

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────
#  PROMPTS POR IDIOMA
# ─────────────────────────────────────────────
LANG_PROMPTS = {
    "es": {
        "system": (
            "Eres un experto en marketing de moda nupcial y SEO para Pinterest. "
            "Escribes en español de España con un tono elegante, romántico y con llamada a la acción. "
            "Conoces perfectamente el sector nupcial: novias, bodas en España y tendencias 2025. "
            "Tus textos posicionan en Google y generan clics en Pinterest."
        ),
        "style_note": "Mezcla lo emocional (el gran día, el momento único) con lo práctico (comodidad, precio, envío).",
    },
    "en": {
        "system": (
            "You are an expert in bridal fashion marketing and Pinterest SEO. "
            "You write in English (global audience) with an elegant, romantic yet conversion-focused tone. "
            "You know the bridal industry: brides, weddings, 2025 trends. "
            "Your texts rank on Google and drive clicks on Pinterest."
        ),
        "style_note": "Mix emotional appeal (the big day, dream wedding) with practical value (comfort, price, shipping).",
    },
    "fr": {
        "system": (
            "Tu es un expert en marketing de mode nuptiale et SEO Pinterest. "
            "Tu écris en français avec un ton élégant, romantique et orienté conversion. "
            "Tu maîtrises le secteur nuptial : mariées, mariages, tendances 2025. "
            "Tes textes se positionnent sur Google et génèrent des clics sur Pinterest."
        ),
        "style_note": "Mêle l'aspect émotionnel (le grand jour, le mariage de rêve) au côté pratique.",
    },
    "it": {
        "system": (
            "Sei un esperto di marketing per la moda nuziale e SEO per Pinterest. "
            "Scrivi in italiano con un tono elegante, romantico e orientato alla conversione. "
            "Conosci il settore nuziale: spose, matrimoni, tendenze 2025. "
            "I tuoi testi si posizionano su Google e generano clic su Pinterest."
        ),
        "style_note": "Unisci l'aspetto emotivo (il grande giorno, il matrimonio da sogno) al valore pratico.",
    },
    "pt": {
        "system": (
            "Você é um especialista em marketing de moda nupcial e SEO para Pinterest. "
            "Você escreve em português (Portugal e Brasil) com um tom elegante, romântico e focado em conversão. "
            "Você conhece o setor nupcial: noivas, casamentos, tendências 2025. "
            "Seus textos se posicionam no Google e geram cliques no Pinterest."
        ),
        "style_note": "Misture apelo emocional (o grande dia, casamento dos sonhos) com valor prático.",
    },
}

LANG_LABELS = {"es": "español", "en": "English", "fr": "français", "it": "italiano", "pt": "português"}


class SEOGenerator:
    def __init__(self, api_key: str):
        self.client = anthropic.Anthropic(api_key=api_key)

    # ──────────────────────────────────────────
    def generate(
        self,
        product: dict,
        lang: str,
        board_style: str,
    ) -> dict:
        """
        Genera: title, description, hashtags para un Pin en el idioma indicado.
        Devuelve dict con keys: title, description, hashtags (list[str])
        """
        cfg        = LANG_PROMPTS.get(lang, LANG_PROMPTS["en"])
        lang_label = LANG_LABELS.get(lang, lang)

        prompt = f"""
Datos del producto:
- Nombre: {product['title']}
- Precio: {product['price']}
- URL: {product['product_url']}
- Descripción original: {product['description'][:300] if product['description'] else 'sandalia nupcial artesanal'}
- Tags Shopify: {', '.join(product['tags'][:8]) if product['tags'] else 'novia, sandalia, boda'}
- Estilo del tablero: {board_style}
- Marca: Loma Shoes | lomas-shoes.com

Genera en {lang_label}:

1. TÍTULO DEL PIN (máx 100 caracteres):
   - Incluye keyword principal al inicio
   - Menciona "Loma Shoes" o "lomashoes"
   - Añade año 2025 si encaja naturalmente
   - Debe generar curiosidad y clics

2. DESCRIPCIÓN DEL PIN (150-200 palabras):
   - Párrafo 1: evoca la emoción del día de la boda (2-3 frases)
   - Párrafo 2: características del producto (comodidad, materiales, estilo)
   - Párrafo 3: llamada a la acción clara con la URL {product['product_url']}
   - {cfg['style_note']}
   - NO uses emojis excesivos (máximo 2-3 en toda la descripción)

3. HASHTAGS (exactamente 20):
   - 5 hashtags de alto volumen (bodas, novia, wedding...)
   - 8 hashtags de nicho medio (zapatos novia playa, bridal sandals 2025...)
   - 4 hashtags de marca (lomashoes, lomashoescom...)
   - 3 hashtags de estilo ({board_style})
   - Sin el símbolo #, solo las palabras

Responde ÚNICAMENTE en este formato JSON exacto (sin markdown, sin explicaciones):
{{
  "title": "...",
  "description": "...",
  "hashtags": ["tag1", "tag2", ...]
}}
"""
        try:
            message = self.client.messages.create(
                model="claude-sonnet-4-5",
                max_tokens=1024,
                system=cfg["system"],
                messages=[{"role": "user", "content": prompt}],
            )
            raw = message.content[0].text.strip()

            # Limpiar posibles bloques de código
            raw = re.sub(r"```json|```", "", raw).strip()

            import json
            data = json.loads(raw)

            # Validación básica
            title       = str(data.get("title", product["title"]))[:100]
            description = str(data.get("description", ""))[:800]
            hashtags    = [f"#{h.lstrip('#')}" for h in data.get("hashtags", [])[:20]]

            logger.info(f"  ✅ SEO generado [{lang}]: {title[:50]}...")
            return {
                "title":       title,
                "description": description,
                "hashtags":    hashtags,
            }

        except Exception as e:
            logger.error(f"SEO generation error [{lang}]: {e}")
            # Fallback básico
            return {
                "title":       f"{product['title']} | Loma Shoes",
                "description": (
                    f"Descubre {product['title']} en Loma Shoes. "
                    f"Precio: {product['price']}. Visita {product['product_url']}"
                ),
                "hashtags": ["#lomashoes", "#zapatosnovia", "#weddingsandals", "#noviashooes"],
            }
