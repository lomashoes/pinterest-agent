# 📌 LomaShooes Pinterest Agent

Agente de marketing automatizado para **[@lomashoes](https://pinterest.com/lomashoes)** que:

- 🛍️ **Extrae productos** del catálogo Shopify de [lomas-shoes.com](https://lomas-shoes.com) automáticamente
- 🤖 **Genera copy SEO** con Claude AI en 5 idiomas (ES / EN / FR / IT / PT)
- 📌 **Publica Pins** en Pinterest con imagen, título optimizado, descripción y 20 hashtags
- 🗂️ **Crea y gestiona 12 tableros** (idioma × estilo) automáticamente
- ⏰ **3 publicaciones diarias** a las 09:00, 13:30 y 21:00 hora España
- ♻️ **Rota el catálogo** sin repetir productos hasta agotarlo

---

## 🗂️ Estructura de tableros (creados automáticamente)

| Tablero | Idioma | Estilo |
|---------|--------|--------|
| Sandalias de Novia Elegantes \| Loma Shoes | 🇪🇸 ES | Elegante |
| Zapatos Novia Playa \| Loma Shoes | 🇪🇸 ES | Playa |
| Sandalias Novia Boho Chic \| Loma Shoes | 🇪🇸 ES | Boho |
| Elegant Wedding Sandals \| Loma Shoes | 🇬🇧 EN | Elegant |
| Beach Wedding Shoes \| Loma Shoes | 🇬🇧 EN | Beach |
| Boho Bridal Sandals \| Loma Shoes | 🇬🇧 EN | Boho |
| Sandales Mariée Élégantes \| Loma Shoes | 🇫🇷 FR | Élégant |
| Chaussures Mariage Plage \| Loma Shoes | 🇫🇷 FR | Plage |
| Sandali Sposa Eleganti \| Loma Shoes | 🇮🇹 IT | Elegante |
| Scarpe Sposa Spiaggia \| Loma Shoes | 🇮🇹 IT | Spiaggia |
| Sandálias Noiva Elegantes \| Loma Shoes | 🇵🇹 PT | Elegante |
| Sapatos Casamento Praia \| Loma Shoes | 🇵🇹 PT | Praia |

---

## ⏰ Franja horaria de publicación

| Hora (España) | Idioma |
|---------------|--------|
| 09:00 | 🇪🇸 Español |
| 13:30 | 🇬🇧 Inglés |
| 21:00 | 🔄 Rota: Italiano → Francés → Portugués → Italiano… |

---

## 🚀 Instalación y configuración

### 1. Clonar el repositorio

```bash
git clone https://github.com/lomashoes/pinterest-agent.git
cd lomashoes-pinterest-agent
```

### 2. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 3. Configurar credenciales

```bash
cp .env.example .env
# Edita .env con tus credenciales reales
```

#### 🔑 Cómo obtener cada credencial

**Pinterest Access Token:**
1. Ve a [developers.pinterest.com](https://developers.pinterest.com)
2. `My Apps` → selecciona tu app (o crea una nueva)
3. `Authentication` → `Generate access token`
4. Permisos necesarios: `boards:read`, `boards:write`, `pins:read`, `pins:write`

**Shopify Admin API Token:**
1. En tu admin Shopify → `Apps` → `Develop apps`
2. `Create an app` → nombre: "Pinterest Agent"
3. `Configure Admin API scopes` → activa: `read_products`
4. `Install app` → copia el **Admin API access token**

**Anthropic API Key:**
1. Ve a [console.anthropic.com](https://console.anthropic.com)
2. `API Keys` → `Create Key`

### 4. Primer paso: crear los tableros

```bash
python main.py --setup
```

Esto creará los 12 tableros automáticamente en tu cuenta de Pinterest.

### 5. Test (sin publicar)

```bash
python main.py --test
```

### 6. Publicación manual

```bash
# Publicar en español ahora mismo
python main.py --lang es

# Publicar en inglés
python main.py --lang en
```

---

## ⚙️ Automatización con GitHub Actions (GRATUITO)

### 1. Subir el proyecto a GitHub

```bash
git init
git add .
git commit -m "🚀 LomaShooes Pinterest Agent — inicial"
git remote add origin https://github.com/TU_USUARIO/pinterest-agent.git
git push -u origin main
```

### 2. Configurar GitHub Secrets

Ve a tu repositorio → `Settings` → `Secrets and variables` → `Actions` → `New repository secret`

Añade estos 4 secrets:

| Secret | Valor |
|--------|-------|
| `PINTEREST_ACCESS_TOKEN` | Tu token de Pinterest |
| `SHOPIFY_STORE_URL` | `lomas-shoes.myshopify.com` |
| `SHOPIFY_ACCESS_TOKEN` | Tu token de Shopify Admin API |
| `ANTHROPIC_API_KEY` | Tu API key de Anthropic |

### 3. Activar el workflow

Ve a `Actions` → `📌 LomaShooes Pinterest Agent` → `Enable workflow`

¡Listo! El agente publicará automáticamente a las 09:00, 13:30 y 21:00 hora España todos los días.

---

## 🕹️ Ejecución manual desde GitHub

1. `Actions` → `📌 LomaShooes Pinterest Agent` → `Run workflow`
2. Selecciona el modo:
   - `auto` — detecta el slot horario automáticamente
   - `test` — dry run sin publicar
   - `setup` — solo crear tableros
   - `lang_es / lang_en / lang_fr / lang_it / lang_pt` — fuerza idioma

---

## 📁 Estructura del proyecto

```
lomashoes-pinterest-agent/
├── .github/
│   └── workflows/
│       └── pinterest_agent.yml   ← Automatización GitHub Actions
├── agent/
│   ├── config.py                 ← Configuración central + 12 tableros
│   ├── shopify_client.py         ← Conexión Shopify API
│   ├── pinterest_client.py       ← Conexión Pinterest API v5
│   ├── seo_generator.py          ← Generación SEO con Claude AI
│   ├── board_manager.py          ← Gestión automática de tableros
│   └── state_manager.py          ← Estado entre ejecuciones
├── main.py                       ← Orquestador principal
├── state.json                    ← Estado persistente (no borrar)
├── requirements.txt
├── .env.example
├── .gitignore
└── README.md
```

---

## 📊 Ver estadísticas

```bash
python main.py --stats
```

Muestra: total de pins publicados, productos publicados en el ciclo actual y última ejecución.

---

## 🔧 Personalización

Edita `agent/config.py` para:
- Cambiar los nombres o descripciones de los tableros
- Añadir/eliminar idiomas
- Modificar las franjas horarias
- Cambiar el estilo de copy (variable `BRAND_NAME`, `PRODUCT_TYPE`)

---

## 📋 Requisitos

- Python 3.12+
- Cuenta de Pinterest Business con acceso a API v5
- Tienda Shopify con API Admin habilitada
- API key de Anthropic (Claude)

---

*Desarrollado para [Loma Shoes](https://lomas-shoes.com) 🥿*
