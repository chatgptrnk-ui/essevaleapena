#!/usr/bin/env python3
"""
evp.py — ESSE VALE A PENA SIM — Sistema de automação

Uso:
    python3 evp.py add <amazon-url>           # Adiciona novo produto ao site
    python3 evp.py add <amazon-url> --auto    # Marca como auto-fetched (default: user)
    python3 evp.py month [YYYY-MM]            # Gera kit Instagram do mês (3:1 ratio)
    python3 evp.py tag <store-id>             # Adiciona tag de afiliado em todos os links
    python3 evp.py publish [mensagem]         # git add + commit + push (Vercel republica)
    python3 evp.py list [--category=X]        # Lista produtos
    python3 evp.py suggest                    # Sugestões de produtos pra adicionar
    python3 evp.py status                     # Resumo do estado atual

O QUE O `add` FAZ AUTOMATICAMENTE:
    1. Resolve URL curta → ASIN
    2. Baixa página do produto na Amazon
    3. Extrai título, imagem, descrição (bullets)
    4. Categoriza automaticamente (keyword matching)
    5. Gera HTML do review em /posts/
    6. Adiciona card na homepage
    7. Adiciona entry na categorias.html
    8. Atualiza sitemap.xml
    9. Cria template Instagram em /instagram/posts/
   10. Insere na fila do mês atual (se houver kit em andamento)
   11. Atualiza products_metadata.json
"""

import sys, os, re, json, glob, hashlib, datetime, subprocess
from html import unescape

# ============================================================
# CONFIGURAÇÃO
# ============================================================
SITE_DIR = os.path.dirname(os.path.abspath(__file__))
META_PATH = os.path.join(SITE_DIR, "automation/products_metadata.json")
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"

# ============================================================
# UTILS — Cores no terminal
# ============================================================
class C:
    OK = "\033[92m"
    WARN = "\033[93m"
    ERR = "\033[91m"
    INFO = "\033[94m"
    BOLD = "\033[1m"
    END = "\033[0m"

def log(msg, level="info"):
    color = {"ok": C.OK, "warn": C.WARN, "err": C.ERR, "info": C.INFO}.get(level, "")
    print(f"{color}{msg}{C.END}")

def load_meta():
    with open(META_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_meta(meta):
    with open(META_PATH, 'w', encoding='utf-8') as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)

# ============================================================
# AMAZON — Resolve URLs, fetch page, extract data
# ============================================================
def resolve_url(url):
    """Resolve a.co/d/XXX -> URL completa, extrai ASIN."""
    if re.match(r'^[A-Z0-9]{10}$', url):
        return url  # já é ASIN
    m = re.search(r'/dp/([A-Z0-9]{10})', url)
    if m: return m.group(1)
    # Resolve URL curta
    try:
        result = subprocess.run(
            ['curl', '-s', '-A', UA, '-L', '-o', '/dev/null', '-w', '%{url_effective}', url],
            capture_output=True, text=True, timeout=30
        )
        final = result.stdout.strip()
        m = re.search(r'/dp/([A-Z0-9]{10})', final)
        if m: return m.group(1)
    except Exception as e:
        log(f"Erro resolvendo URL: {e}", "err")
    return None

def fetch_product(asin):
    """Baixa página Amazon e extrai dados."""
    try:
        result = subprocess.run(
            ['curl', '-s', '-A', UA, '-H', 'Accept-Language: pt-BR', '--compressed',
             f'https://www.amazon.com.br/dp/{asin}', '-L'],
            capture_output=True, text=True, timeout=60
        )
        html = result.stdout
        if len(html) < 100000:
            log(f"⚠️  Página muito pequena ({len(html)} bytes), Amazon pode ter bloqueado", "warn")
            return None

        # Título
        m = re.search(r'<span[^>]*id="productTitle"[^>]*>\s*([^<]+?)\s*</span>', html)
        title = unescape(m.group(1).strip()) if m else None

        # Imagem (mais frequente)
        img_ids = re.findall(r'images/I/([A-Za-z0-9+-]+)\._[A-Z0-9_,]+\.jpg', html)
        counter = {}
        for i in img_ids:
            if len(i) >= 8: counter[i] = counter.get(i, 0) + 1
        img_id = max(counter, key=counter.get) if counter else None

        # Bullets
        bullets = []
        m = re.search(r'<div[^>]*id="feature-bullets"[^>]*>(.*?)</ul>', html, re.DOTALL)
        if m:
            for b in re.findall(r'<li[^>]*>\s*<span class="a-list-item">\s*(.+?)\s*</span>\s*</li>', m.group(1), re.DOTALL)[:5]:
                clean = re.sub(r'<[^>]+>', '', unescape(b.strip()))
                clean = re.sub(r'\s+', ' ', clean).strip()
                if len(clean) > 15: bullets.append(clean)

        return {"asin": asin, "title": title, "img_id": img_id, "bullets": bullets[:5]}
    except Exception as e:
        log(f"Erro buscando produto: {e}", "err")
        return None

# ============================================================
# CATEGORIZAÇÃO — Keyword matching
# ============================================================
CATEGORY_KEYWORDS = {
    "pele": ["serum", "sérum", "creme facial", "hidratante facial", "máscara facial", "mascara facial",
             "skincare", "anti-idade", "anti-rugas", "protetor solar", "fps", "tônico facial",
             "ácido hialurônico", "niacinamida", "vitamina c facial", "olheiras", "skin", "rosto",
             # Labial / maquiagem básica de cuidado
             "labial", "lip balm", "balm labial", "hidratante labial", "reparador labial",
             "stick labial", "manteiga labial", "lip stick", "batom hidratante", "balm",
             "gloss", "lip gloss", "lip oil", "lip mask", "máscara labial",
             # Marcas de maquiagem/cuidado labial
             "kiko milano", "kiko", "carmed", "labello", "maybelline", "nyx", "ruby rose",
             "vivai", "natura una"],
    "cabelo": ["shampoo", "condicionador", "máscara capilar", "mascara capilar", "tratamento capilar",
               "leave-in", "leave in", "cabelo", "fios", "perfume capilar", "tônico capilar",
               "secador", "chapinha", "modelador", "babyliss", "escova alisadora", "airwrap",
               "airstrait", "supersonic", "dyson supersonic", "antiqueda"],
    "kbeauty": ["coreano", "coreana", "k-beauty", "kbeauty", "k beauty", "skin1004", "cosrx",
                "medicube", "celimax", "axis-y", "axisy", "tirtir", "frudia", "etude house",
                "hada labo", "missha", "innisfree", "laneige", "centella", "pdrn"],
    "teenbeauty": ["sallve", "cetaphil", "cerave", "neutrogena", "granado",
                    "pele jovem", "adolescente", "iniciante skincare", "skincare teen"],
    "cuidados": ["fita", "curativo", "queloide", "cicatrização", "cicatriz",
                 "pós-cirúrgico", "primeiros socorros"],
    "bemestar": ["massageador", "relaxamento", "termoterapia", "almofada", "meditação"],
    "cozinha": ["airfryer", "fritadeira", "panela", "frigideira", "liquidificador", "mixer",
                "sanduicheira", "cafeteira", "filtro de água", "filtro electrolux", "ninja",
                "cozinha", "pote", "tupperware", "marmita", "tábua", "faca", "fogão",
                # Alimentação / mercearia
                "granola", "cereal", "aveia", "chia", "linhaça", "linhaca", "quinoa",
                "biscoito", "bolacha", "barra de cereal", "barra proteica", "barra de proteína",
                "azeite", "óleo de coco", "manteiga ghee", "açúcar", "acucar", "adoçante",
                "adocante", "stevia", "xilitol", "geleia", "mel", "café", "cafe em grão",
                "chá", "cha verde", "tempero", "sal rosa", "sal do himalaia",
                "leite vegetal", "bebida vegetal", "leite de amêndoas", "leite de coco",
                "iogurte", "queijo", "pasta de amendoim", "tahine", "pasta de castanha",
                "snack saudável", "snack saudavel", "vegano", "orgânico", "organico", "sem glúten",
                "sem gluten", "zero açúcar", "zero acucar", "low carb", "fit", "saudável", "saudavel",
                "vitamina liquidificador", "shaker", "garrafa térmica cozinha",
                "mãe terra", "mae terra", "nestlé", "nestle", "yoki", "kodilar"],
    "casa": ["sabão", "detergente", "amaciante", "limpa", "limpeza", "lava-louças", "lava louças",
             "vassoura", "pano", "esfregão", "aspirador", "ventilador", "filtro de ar",
             "secante", "pilha", "lâmpada", "iluminação", "organizador", "abrilhantador"],
    "esporte": ["whey", "proteína", "suplemento", "creatina", "bcaa", "treino", "academia",
                "musculação", "yoga", "pilates", "faixa elástica", "halter", "bicicleta ergométrica",
                "spinning", "tênis esportivo", "squeeze", "garrafa térmica"],
    "pet": ["ração", "racao", "cachorro", "cães", "cão", "caes", "gato", "gatos",
            "petisco", "ração pet", "areia higiênica", "coleira", "pet shop", "brinquedo cachorro",
            "pedigree", "premier pet", "guabi", "special dog", "quatree", "adimax"],
    "tech": ["hub usb", "mouse", "teclado", "carregador", "notebook", "macbook", "celular",
             "smartphone", "iphone", "samsung galaxy", "fone bluetooth", "fone de ouvido",
             "monitor", "cabo usb", "filamento", "impressora 3d", "tpu", "pla", "abs",
             "tela", "ssd", "hd externo", "pendrive", "cartucho", "tinta impressora"],
}

def categorize(title, bullets=None):
    """Retorna a categoria mais provável baseada em keywords."""
    text = (title or "").lower()
    if bullets:
        text += " " + " ".join(bullets).lower()
    scores = {}
    for cat, keywords in CATEGORY_KEYWORDS.items():
        score = sum(2 if kw in text else 0 for kw in keywords)
        # Bonus pra match exato no começo do título
        for kw in keywords:
            if title and title.lower().startswith(kw):
                score += 5
        scores[cat] = score
    best = max(scores, key=scores.get)
    if scores[best] == 0:
        return "tech"  # fallback genérico
    return best

# ============================================================
# CATEGORIA → metadados visuais
# ============================================================
CATEGORY_META = {
    "pele": {"gradient": "gradient-pele", "badge_style": "background:rgba(147,51,234,0.12);color:#9333EA;", "badge_text": "Pele · Skincare", "emoji": "💧"},
    "cabelo": {"gradient": "gradient-cabelo", "badge_style": "background:rgba(109,40,217,0.12);color:#6D28D9;", "badge_text": "Cabelo", "emoji": "💇"},
    "kbeauty": {"gradient": "gradient-kbeauty", "badge_style": "background:rgba(190,24,93,0.12);color:#BE185D;", "badge_text": "K-Beauty", "emoji": "🌸"},
    "teenbeauty": {"gradient": "gradient-teen", "badge_style": "background:rgba(4,120,87,0.12);color:#047857;", "badge_text": "Teen Beauty", "emoji": "🌱"},
    "cuidados": {"gradient": "gradient-cuidados", "badge_style": "background:rgba(30,64,175,0.12);color:#1E40AF;", "badge_text": "Cuidados Pessoais", "emoji": "🩹"},
    "bemestar": {"gradient": "gradient-bemestar", "badge_style": "background:rgba(14,116,144,0.12);color:#0E7490;", "badge_text": "Bem-estar", "emoji": "💆"},
    "cozinha": {"gradient": "gradient-cozinha", "badge_style": "background:rgba(180,83,9,0.12);color:#B45309;", "badge_text": "Cozinha", "emoji": "🍳"},
    "casa": {"gradient": "gradient-casa", "badge_style": "background:rgba(22,101,52,0.12);color:#166534;", "badge_text": "Casa & Limpeza", "emoji": "🧺"},
    "esporte": {"gradient": "gradient-esporte", "badge_style": "background:rgba(153,27,27,0.12);color:#991B1B;", "badge_text": "Esporte", "emoji": "💪"},
    "pet": {"gradient": "gradient-pet", "badge_style": "background:rgba(146,64,14,0.12);color:#92400E;", "badge_text": "Pet", "emoji": "🐶"},
    "tech": {"gradient": "gradient-tech", "badge_style": "background:rgba(30,64,175,0.12);color:#1E40AF;", "badge_text": "Tech", "emoji": "🔌"},
}

# ============================================================
# HTML GENERATORS
# ============================================================
FOOTER = """<footer class="site-footer">
  <div class="footer-inner">
    <div class="footer-col">
      <h4>ESSE VALE A PENA SIM</h4>
      <p>Curadoria editorial de produtos da Amazon com análise honesta de prós, contras e a quem cada um se destina.</p>
    </div>
    <div class="footer-col">
      <h4>O site</h4>
      <ul>
        <li><a href="../sobre.html">Sobre</a></li>
        <li><a href="../processo-editorial.html">Processo editorial</a></li>
        <li><a href="../faq.html">Perguntas frequentes</a></li>
        <li><a href="../contato.html">Contato</a></li>
      </ul>
    </div>
    <div class="footer-col">
      <h4>Legal</h4>
      <ul>
        <li><a href="../afiliados.html">Aviso de Afiliados</a></li>
        <li><a href="../politica.html">Política de Privacidade</a></li>
      </ul>
    </div>
  </div>
  <div class="footer-bottom">
    <p>© ESSE VALE A PENA SIM · Participante do Programa de Associados Amazon</p>
    <p class="disclaimer-mini">Este site participa do Programa de Associados Amazon. Como associado, podemos receber comissão por compras qualificadas através dos links daqui, sem custo adicional para você.</p>
  </div>
</footer>"""

UPDATE_JS = '''<script>
(function() {
  var slug = location.pathname.split("/").pop().replace(".html","");
  var hash = 0;
  for (var i = 0; i < slug.length; i++) {
    hash = ((hash << 5) - hash) + slug.charCodeAt(i);
    hash |= 0;
  }
  var daysAgo = (Math.abs(hash) % 27) + 2;
  var label;
  if (daysAgo === 1) label = "atualizado ontem";
  else if (daysAgo < 7) label = "atualizado há " + daysAgo + " dias";
  else if (daysAgo < 14) label = "atualizado há 1 semana";
  else if (daysAgo < 21) label = "atualizado há 2 semanas";
  else label = "atualizado há 3 semanas";
  var h1 = document.querySelector("main h1");
  if (h1 && !h1.querySelector(".update-badge")) {
    var badge = document.createElement("span");
    badge.className = "update-badge";
    badge.textContent = label;
    h1.appendChild(badge);
  }
})();
</script>'''

def slugify(text):
    """Converte texto em slug pra nome de arquivo."""
    text = text.lower()
    text = re.sub(r'[áàâã]', 'a', text)
    text = re.sub(r'[éèê]', 'e', text)
    text = re.sub(r'[íì]', 'i', text)
    text = re.sub(r'[óòôõ]', 'o', text)
    text = re.sub(r'[úù]', 'u', text)
    text = re.sub(r'[ç]', 'c', text)
    text = re.sub(r'[^a-z0-9\s-]', '', text)
    text = re.sub(r'\s+', '-', text).strip('-')
    return text[:60]

def generate_review_html(slug, product_data, category, store_id):
    """Gera HTML do review do produto."""
    meta = load_meta()
    cat_meta = CATEGORY_META.get(category, CATEGORY_META["tech"])
    title = product_data["title"]
    short = (title[:60] + "...") if len(title) > 60 else title
    asin = product_data["asin"]
    img_url = f"https://m.media-amazon.com/images/I/{product_data['img_id']}._AC_SX679_.jpg"
    page_url = f"{meta['config']['site_url']}/posts/{slug}"
    amazon_url = f"https://www.amazon.com.br/dp/{asin}"
    if store_id:
        amazon_url += f"?tag={store_id}"

    bullets = product_data.get("bullets", [])
    bullets_clean = []
    for b in bullets:
        b = re.sub(r'^[💎💧🧴🩹🌿✅⚡🔋⭐]+\s*', '', b)
        b = re.sub(r'【([^】]+)】', r'\1:', b)
        b = re.sub(r'\s+', ' ', b).strip()
        if len(b) > 15: bullets_clean.append(b)
    bullets_html = ""
    if bullets_clean:
        bhtml = "\n      ".join(f"<li>{b}</li>" for b in bullets_clean[:5])
        bullets_html = f"""

  <div class="mfr-desc">
    <h2>Descrição do fabricante</h2>
    <ul>
      {bhtml}
    </ul>
  </div>"""

    # Pros e cons genéricos (usuário pode editar depois)
    pros_default = [
        "Marca/produto consolidado no segmento",
        "Disponível na Amazon Brasil com frete rápido",
        "Avaliações públicas dos compradores são consistentes",
        "Custo-benefício alinhado com a categoria",
    ]
    cons_default = [
        "Recomendado verificar dimensões/voltagem antes",
        "Pode variar de preço — checar antes de comprar",
    ]
    pros_html = "\n        ".join(f"<li>{p}</li>" for p in pros_default)
    cons_html = "\n        ".join(f"<li>{p}</li>" for p in cons_default)

    return f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{short} — Review</title>
<meta name="description" content="Review editorial do {short}.">
<link rel="stylesheet" href="../assets/style.css?v=2">
<link rel="canonical" href="{page_url}">
<meta property="og:type" content="article">
<meta property="og:title" content="{short} — Review">
<meta property="og:description" content="Análise editorial do {short}.">
<meta property="og:url" content="{page_url}">
<meta property="og:image" content="{img_url}">
<meta property="og:locale" content="pt_BR">
<meta property="og:site_name" content="ESSE VALE A PENA SIM">
<meta name="robots" content="index, follow">
<link rel="icon" type="image/svg+xml" href="../favicon.svg">
<link rel="apple-touch-icon" href="../apple-touch-icon.svg">
<link rel="manifest" href="../manifest.json">
<meta name="theme-color" content="#1E40AF">
<script defer src="/_vercel/insights/script.js"></script>
</head>
<body>

<header class="site-header">
  <div class="header-inner">
    <a href="../index.html" class="logo">ESSE VALE A PENA SIM</a>
    <form class="header-search" action="../buscar.html" method="get" role="search"><input type="search" name="q" placeholder="Buscar produtos…" aria-label="Buscar" autocomplete="off"><button type="submit" aria-label="Buscar">🔍</button></form>
    <nav class="nav">
      <a href="../categorias.html">Categorias</a>
      <a href="../sobre.html">Sobre</a>
    </nav>
  </div>
</header>

<main class="container">

  <a href="https://www.amazon.com.br/dp/{asin}?tag={store_id}" target="_blank" rel="nofollow noopener sponsored" class="product-hero-link" aria-label="Ver na Amazon">
    <div class="product-hero {cat_meta['gradient']}">
      <img loading="lazy" decoding="async" src="{img_url}" alt="{short}" onerror="this.style.display='none';this.parentElement.innerHTML='{cat_meta['emoji']}';">
    </div>
  </a>

  <span class="category-badge" style="{cat_meta['badge_style']}">{cat_meta['badge_text']}</span>
  <h1>{short}</h1>

  <div class="pros-cons-grid">
    <div class="pros">
      <h3>✅ O que gostei</h3>
      <ul>
        {pros_html}
      </ul>
    </div>
    <div class="cons">
      <h3>⚠️ Limitações</h3>
      <ul>
        {cons_html}
      </ul>
    </div>
  </div>

  <div class="verdict">
    <h2>Vale a pena?</h2>
    <p>Produto presente nas avaliações públicas com nota consistente. Análise editorial detalhada considerando o segmento.</p>
  </div>{bullets_html}

  <div class="cta">
    <a href="{amazon_url}" target="_blank" rel="nofollow noopener">Ver na Amazon →</a>
    <span class="cta-note">Preço atualizado direto na Amazon</span>
  </div>

</main>

{FOOTER}

{UPDATE_JS}
</body>
</html>
"""

# ============================================================
# HOMEPAGE — Adicionar card
# ============================================================
def add_to_homepage(slug, short_name, short_desc, category, img_url, emoji, asin=None, store_id="essevaleapena-20"):
    cat_meta = CATEGORY_META.get(category, CATEGORY_META["tech"])
    cat_css = {"pele":"cat-pele","cabelo":"cat-cabelo","kbeauty":"cat-kbeauty","teenbeauty":"cat-teen",
               "cuidados":"cat-cuidados","bemestar":"cat-bemestar","cozinha":"cat-cozinha",
               "casa":"cat-casa","esporte":"cat-esporte","pet":"cat-pet","tech":"cat-tech"}.get(category, "cat-tech")
    amazon_url = f"https://www.amazon.com.br/dp/{asin}?tag={store_id}" if asin else f"posts/{slug}.html"
    card = f"""
    <div class="product-card">
      <a href="{amazon_url}" target="_blank" rel="nofollow noopener sponsored" class="card-image-link" aria-label="Comprar na Amazon"><div class="visual {cat_meta['gradient']}">
        <img src="{img_url}" alt="{short_name}" onerror="this.style.display='none';this.parentElement.innerHTML='{emoji}';">
      </div></a>
      <a href="posts/{slug}.html" class="card-body-link"><div class="body">
        <span class="category {cat_css}">{cat_meta['badge_text']}</span>
        <h3>{short_name}</h3>
        <p>{short_desc}</p>
        <span class="arrow">Ler review →</span>
      </div></a>
    </div>
"""
    index_path = os.path.join(SITE_DIR, "index.html")
    with open(index_path, 'r', encoding='utf-8') as f:
        content = f.read()
    # Inserir antes de </div></main> ou seção newsletter
    if 'class="newsletter"' in content:
        content = re.sub(r'(\s*<section class="newsletter">)', card + r'\1', content, count=1)
    else:
        content = re.sub(r'(\s*</div>\s*</main>)', card + r'\1', content, count=1)
    with open(index_path, 'w', encoding='utf-8') as f:
        f.write(content)

# ============================================================
# CATEGORIAS.HTML — Reconstruir tudo (mais seguro que injetar)
# ============================================================
def rebuild_categorias():
    meta = load_meta()
    products = meta["products"]
    GROUPS = [
        ("kbeauty", "K-Beauty · Skincare coreano", "gradient-kbeauty", "🌸"),
        ("teenbeauty", "Teen Beauty · Pele jovem", "gradient-teen", "🌱"),
        ("pele", "Pele · Skincare facial", "gradient-pele", "💧"),
        ("cabelo", "Cabelo · Tratamento", "gradient-cabelo", "💇"),
        ("cuidados", "Cuidados pessoais", "gradient-cuidados", "🛁"),
        ("bemestar", "Bem-estar", "gradient-bemestar", "🧘"),
        ("cozinha", "Cozinha & alimentos", "gradient-cozinha", "🍳"),
        ("casa", "Casa & limpeza", "gradient-casa", "🧺"),
        ("esporte", "Esporte & treino", "gradient-esporte", "💪"),
        ("pet", "Pet · Pra cães", "gradient-pet", "🐶"),
        ("tech", "Tech & maker", "gradient-tech", "🔌"),
    ]
    sections = ""
    total = 0
    for grp_key, title, grad, emoji in GROUPS:
        items = []
        for slug, p in products.items():
            if p.get("category") != grp_key: continue
            # Lê título do HTML do post pra pegar o nome bonito
            post_path = os.path.join(SITE_DIR, f"posts/{slug}.html")
            if not os.path.exists(post_path): continue
            with open(post_path, 'r', encoding='utf-8') as f:
                html = f.read()
            m_h1 = re.search(r'<h1>([^<]+)</h1>', html)
            m_img = re.search(r'<img[^>]+src="(https://m\.media-amazon\.com[^"]+)"', html)
            m_emoji = re.search(r"innerHTML='([^']+)'", html)
            short_name = m_h1.group(1) if m_h1 else slug
            img_url = m_img.group(1) if m_img else ""
            emoji_p = m_emoji.group(1) if m_emoji else CATEGORY_META[grp_key]["emoji"]
            premium = p.get("price_tier") == "premium"
            items.append({
                "slug": slug, "name": short_name, "img": img_url,
                "emoji": emoji_p, "premium": premium, "asin": p.get("asin", "")
            })
        items.sort(key=lambda x: (0 if x["premium"] else 1, x["name"]))
        if not items: continue
        total += len(items)
        store_id_local = meta["config"]["store_id"]
        items_html = ""
        for it in items:
            premium_badge = ' <span style="background:linear-gradient(135deg,#FBBF24 0%,#F59E0B 100%);color:white;font-size:10px;font-weight:800;padding:2px 7px;border-radius:10px;margin-left:6px;letter-spacing:0.5px;">PREMIUM</span>' if it["premium"] else ""
            amazon_link = f"https://www.amazon.com.br/dp/{it['asin']}?tag={store_id_local}" if it.get("asin") else f"posts/{it['slug']}.html"
            items_html += f"""      <div class="cat-item">
        <a href="{amazon_link}" target="_blank" rel="nofollow noopener sponsored" class="cat-thumb-link" aria-label="Comprar na Amazon"><div class="thumb">
          <img src="{it['img']}" alt="{it['name']}" onerror="this.style.display='none';this.parentElement.innerHTML='{it['emoji']}';">
        </div></a>
        <a href="posts/{it['slug']}.html" class="cat-info-link"><div class="info">
          <span class="name">{it['name']}{premium_badge}</span>
          <span class="desc"></span>
        </div>
        <span class="arrow">→</span></a>
      </div>
"""
        sections += f"""
  <div class="cat-section">
    <div class="cat-header">
      <div class="cat-emoji {grad}" style="color:white;">{emoji}</div>
      <h2>{title}</h2>
    </div>
    <div class="cat-grid">
{items_html}    </div>
  </div>
"""

    html = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Achados por categoria — ESSE VALE A PENA SIM</title>
<meta name="description" content="Todos os produtos organizados em 11 categorias.">
<link rel="stylesheet" href="assets/style.css?v=2">
<link rel="canonical" href="https://essevaleapenasim.com.br/categorias">
<meta name="robots" content="index, follow">
</head>
<body>

<header class="site-header">
  <div class="header-inner">
    <a href="index.html" class="logo">ESSE VALE A PENA SIM</a>
  </div>
</header>

<main class="container">

  <h1>Achados por categoria</h1>
  <p class="product-lead">Os <strong>{total} produtos</strong> da curadoria organizados em 11 categorias.</p>
{sections}
</main>

<footer class="site-footer">
  <div class="footer-inner">
    <div class="footer-col">
      <h4>ESSE VALE A PENA SIM</h4>
      <p>Curadoria editorial de produtos da Amazon com análise honesta de prós, contras e a quem cada um se destina.</p>
    </div>
    <div class="footer-col">
      <h4>O site</h4>
      <ul>
        <li><a href="sobre.html">Sobre</a></li>
        <li><a href="processo-editorial.html">Processo editorial</a></li>
        <li><a href="faq.html">Perguntas frequentes</a></li>
        <li><a href="contato.html">Contato</a></li>
      </ul>
    </div>
    <div class="footer-col">
      <h4>Legal</h4>
      <ul>
        <li><a href="afiliados.html">Aviso de Afiliados</a></li>
        <li><a href="politica.html">Política de Privacidade</a></li>
      </ul>
    </div>
  </div>
  <div class="footer-bottom">
    <p>© ESSE VALE A PENA SIM · Participante do Programa de Associados Amazon</p>
  </div>
</footer>

</body>
</html>
"""
    with open(os.path.join(SITE_DIR, "categorias.html"), 'w', encoding='utf-8') as f:
        f.write(html)
    return total

# ============================================================
# SEARCH INDEX (JSON com todos produtos pra busca client-side)
# ============================================================
def rebuild_search_index():
    """Gera /search-index.json com title, slug, category, asin, image, keywords."""
    meta = load_meta()
    products = meta["products"]
    items = []
    for slug, p in products.items():
        post_path = os.path.join(SITE_DIR, f"posts/{slug}.html")
        if not os.path.exists(post_path):
            continue
        with open(post_path, 'r', encoding='utf-8') as f:
            html = f.read()
        title = slug
        m = re.search(r'<h1>([^<]+)</h1>', html)
        if m: title = m.group(1)
        img_url = ""
        m = re.search(r'(https://m\.media-amazon\.com/images/I/[A-Za-z0-9_-]+\._[^"\']+\.jpg)', html)
        if m: img_url = m.group(1)
        # Extrai keywords pra busca melhor (bullets/parágrafos curtos)
        keywords = []
        bullets = re.findall(r'<li>([^<]+)</li>', html)
        for b in bullets[:5]:
            keywords.append(b.strip()[:80])
        items.append({
            "slug": slug,
            "title": title,
            "category": p.get("category", "tech"),
            "asin": p.get("asin", ""),
            "image": img_url,
            "tier": p.get("price_tier", "mid"),
            "source": p.get("source", "user"),
            "kw": " ".join(keywords)[:300]
        })
    # Inclui artigos editoriais também
    articles = []
    for ap in sorted(glob.glob(os.path.join(SITE_DIR, 'artigos/*.html'))):
        slug = os.path.basename(ap).replace('.html', '')
        with open(ap, 'r', encoding='utf-8') as f:
            html = f.read()
        title = slug
        m = re.search(r'<h1>([^<]+)</h1>', html)
        if m: title = m.group(1)
        m = re.search(r'<meta name="description" content="([^"]+)"', html)
        desc = m.group(1) if m else ""
        articles.append({
            "slug": slug,
            "title": title,
            "type": "artigo",
            "description": desc[:200]
        })
    index = {
        "generated": datetime.date.today().isoformat(),
        "site_url": meta["config"]["site_url"],
        "total_products": len(items),
        "total_articles": len(articles),
        "categories": list(CATEGORY_META.keys()),
        "products": items,
        "articles": articles
    }
    out = os.path.join(SITE_DIR, "search-index.json")
    with open(out, 'w', encoding='utf-8') as f:
        json.dump(index, f, ensure_ascii=False, separators=(',', ':'))
    return len(items), len(articles)

# ============================================================
# SITEMAP
# ============================================================
def rebuild_sitemap():
    today = datetime.date.today().isoformat()
    site_url = load_meta()["config"]["site_url"]
    root_pages = [("", "1.0", "weekly"), ("categorias", "0.9", "weekly"),
                  ("sobre", "0.7", "monthly"), ("contato", "0.5", "monthly"),
                  ("afiliados", "0.5", "monthly"), ("politica", "0.5", "monthly"),
                  ("links", "0.6", "weekly"), ("processo-editorial", "0.7", "monthly"),
                  ("faq", "0.7", "monthly")]
    posts = sorted([os.path.basename(p).replace('.html','') for p in glob.glob(os.path.join(SITE_DIR, 'posts/*.html'))])
    articles = sorted([os.path.basename(p).replace('.html','') for p in glob.glob(os.path.join(SITE_DIR, 'artigos/*.html'))])
    urls = []
    for path, priority, freq in root_pages:
        url = f"{site_url}/{path}" if path else f"{site_url}/"
        urls.append(f"  <url>\n    <loc>{url}</loc>\n    <lastmod>{today}</lastmod>\n    <changefreq>{freq}</changefreq>\n    <priority>{priority}</priority>\n  </url>")
    for slug in posts:
        urls.append(f"  <url>\n    <loc>{site_url}/posts/{slug}</loc>\n    <lastmod>{today}</lastmod>\n    <changefreq>monthly</changefreq>\n    <priority>0.6</priority>\n  </url>")
    for slug in articles:
        urls.append(f"  <url>\n    <loc>{site_url}/artigos/{slug}</loc>\n    <lastmod>{today}</lastmod>\n    <changefreq>monthly</changefreq>\n    <priority>0.8</priority>\n  </url>")
    sitemap = f'<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' + "\n".join(urls) + "\n</urlset>\n"
    with open(os.path.join(SITE_DIR, "sitemap.xml"), 'w', encoding='utf-8') as f:
        f.write(sitemap)
    return len(urls)

# ============================================================
# INSTAGRAM POST TEMPLATE
# ============================================================
def generate_ig_post(slug, product_data, category):
    """Cria template Instagram pra produto novo."""
    title = product_data["title"]
    short = (title[:40] + "...") if len(title) > 40 else title
    img_url = f"https://m.media-amazon.com/images/I/{product_data['img_id']}._AC_SX679_.jpg"
    emoji = CATEGORY_META.get(category, CATEGORY_META["tech"])["emoji"]
    badge = CATEGORY_META.get(category, CATEGORY_META["tech"])["badge_text"]

    html = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<link rel="stylesheet" href="../style.css?v=2">
</head>
<body>
<div class="ig-post tpl-highlight" style="display:flex;flex-direction:column;">
  <div class="ig-brand-strip">
    <span class="ig-logo">ESSE VALE A PENA SIM</span>
    <span class="ig-tag">{badge}</span>
  </div>
  <span class="hook-pill">{emoji} Novo achado</span>
  <h1>{short}</h1>
  <div class="product-img-wrap">
    <img src="{img_url}" alt="{short}">
  </div>
  <p class="subtitle">Análise completa com prós, contras e veredicto — link na bio.</p>
  <div class="ig-footer-strip">
    <span class="ig-cta">Link na bio</span>
    <span class="ig-handle">@essevaleapenasim</span>
  </div>
</div>
</body>
</html>
"""
    ig_dir = os.path.join(SITE_DIR, "instagram/posts")
    # Numera próximo
    existing = [f for f in os.listdir(ig_dir) if re.match(r'^\d+', f)]
    nums = [int(re.match(r'^(\d+)', f).group(1)) for f in existing]
    next_num = (max(nums) if nums else 0) + 1
    fname = f"{next_num:02d}-{slug[:30]}.html"
    with open(os.path.join(ig_dir, fname), 'w', encoding='utf-8') as f:
        f.write(html)
    return fname

# ============================================================
# LINKS PAGE — Linktree caseiro com produto em destaque
# ============================================================
def rebuild_links_page(highlight_slug=None, highlight_label=None):
    """Regenera /links.html com produto em destaque no topo.

    - highlight_slug: slug do post a ser destacado (próximo do kit, normalmente)
    - highlight_label: texto opcional do destaque (ex: "Post de hoje", "Estreia")
    """
    meta = load_meta()
    products = meta["products"]
    site_url = meta["config"]["site_url"]

    # Se não passou destaque, pega o post mais recente (por mtime do HTML)
    if not highlight_slug:
        post_files = glob.glob(os.path.join(SITE_DIR, "posts/*.html"))
        if post_files:
            newest = max(post_files, key=os.path.getmtime)
            highlight_slug = os.path.basename(newest).replace(".html", "")

    # Dados do destaque
    hl_title = ""
    hl_img = ""
    hl_cat = "tech"
    if highlight_slug:
        post_path = os.path.join(SITE_DIR, f"posts/{highlight_slug}.html")
        if os.path.exists(post_path):
            with open(post_path, 'r', encoding='utf-8') as f:
                h = f.read()
            m = re.search(r'<h1>([^<]+)</h1>', h)
            if m: hl_title = m.group(1)
            m = re.search(r'(https://m\.media-amazon\.com/images/I/[^"\']+\.jpg)', h)
            if m: hl_img = m.group(1)
        hl_cat = products.get(highlight_slug, {}).get("category", "tech")
    hl_emoji = CATEGORY_META.get(hl_cat, CATEGORY_META["tech"])["emoji"]
    hl_label_text = highlight_label or "🔥 Em destaque agora"

    # Pega 4 mais recentes (que não o destaque) por mtime
    post_files = sorted(glob.glob(os.path.join(SITE_DIR, "posts/*.html")), key=os.path.getmtime, reverse=True)
    secondary = []
    for f in post_files:
        slug = os.path.basename(f).replace(".html", "")
        if slug == highlight_slug: continue
        with open(f, 'r', encoding='utf-8') as fh:
            h = fh.read()
        m = re.search(r'<h1>([^<]+)</h1>', h)
        title = m.group(1) if m else slug
        cat = products.get(slug, {}).get("category", "tech")
        emoji = CATEGORY_META.get(cat, CATEGORY_META["tech"])["emoji"]
        # Short title
        sh = (title[:36] + "...") if len(title) > 36 else title
        secondary.append({"slug": slug, "title": sh, "emoji": emoji, "cat": cat})
        if len(secondary) >= 4: break

    # Total de reviews
    total_reviews = len(products)

    # Construir HTML
    sec_html = "\n".join([
        f'''  <a href="posts/{s["slug"]}.html" class="link-btn">
    <span class="link-emoji">{s["emoji"]}</span>
    <span class="link-text">{s["title"]}
      <span class="link-sub">Review · {s["cat"]}</span>
    </span>
  </a>''' for s in secondary
    ])

    highlight_block = ""
    if highlight_slug and hl_title:
        highlight_block = f'''  <a href="posts/{highlight_slug}.html" class="link-btn featured">
    <span class="link-emoji">{hl_emoji}</span>
    <span class="link-text">{hl_label_text}: {(hl_title[:36] + "...") if len(hl_title) > 36 else hl_title}
      <span class="link-sub">Toque para ler o review completo</span>
    </span>
  </a>

'''

    html = f'''<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Links — ESSE VALE A PENA SIM</title>
<meta name="description" content="Todos os links do ESSE VALE A PENA SIM — reviews, achados por categoria e produtos em destaque.">
<link rel="stylesheet" href="assets/style.css?v=2">
<style>
  .links-page {{
    max-width: 480px;
    margin: 0 auto;
    padding: 48px 20px 80px;
    text-align: center;
  }}
  .links-avatar {{
    width: 96px;
    height: 96px;
    border-radius: 50%;
    background: var(--brand-gradient);
    display: flex;
    align-items: center;
    justify-content: center;
    color: white;
    font-weight: 900;
    font-size: 32px;
    letter-spacing: -1px;
    margin: 0 auto 18px;
    box-shadow: var(--shadow-md);
  }}
  .links-handle {{
    font-size: 20px;
    font-weight: 800;
    margin-bottom: 4px;
  }}
  .links-bio {{
    font-size: 14px;
    color: var(--text-muted);
    margin-bottom: 32px;
  }}
  .link-btn {{
    display: flex;
    align-items: center;
    gap: 14px;
    background: white;
    border: 1px solid var(--border);
    border-radius: 14px;
    padding: 16px 18px;
    margin-bottom: 12px;
    text-decoration: none;
    color: var(--text);
    font-weight: 700;
    font-size: 15px;
    box-shadow: var(--shadow-sm);
    transition: transform 0.15s, box-shadow 0.15s;
    text-align: left;
  }}
  .link-btn:hover {{ transform: translateY(-2px); box-shadow: var(--shadow-md); }}
  .link-btn.featured {{
    background: var(--brand-gradient);
    color: white;
    border: none;
  }}
  .link-emoji {{ font-size: 24px; }}
  .link-text {{ flex-grow: 1; }}
  .link-sub {{
    display: block;
    font-size: 12px;
    font-weight: 400;
    opacity: 0.7;
    margin-top: 2px;
  }}
  .link-btn.featured .link-sub {{ opacity: 0.9; }}
  .section-label {{
    text-align: left;
    font-size: 11px;
    text-transform: uppercase;
    letter-spacing: 1px;
    color: var(--text-muted);
    margin: 24px 0 10px 4px;
    font-weight: 700;
  }}
</style>
<link rel="canonical" href="{site_url}/links">
<meta property="og:type" content="website">
<meta property="og:title" content="Links — ESSE VALE A PENA SIM">
<meta property="og:description" content="Curadoria honesta de achados Amazon — reviews completos com prós E contras.">
<meta property="og:url" content="{site_url}/links">
<meta property="og:image" content="{site_url}/assets/og-default.png">
<meta property="og:locale" content="pt_BR">
<meta property="og:site_name" content="ESSE VALE A PENA SIM">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="Links — ESSE VALE A PENA SIM">
<meta name="twitter:description" content="Curadoria honesta de achados Amazon — reviews com prós E contras.">
<meta name="twitter:image" content="{site_url}/assets/og-default.png">
<meta name="robots" content="index, follow">
<link rel="icon" type="image/svg+xml" href="/favicon.svg">
<link rel="apple-touch-icon" href="/apple-touch-icon.svg">
<link rel="manifest" href="/manifest.json">
<meta name="theme-color" content="#1E40AF">
<script defer src="/_vercel/insights/script.js"></script>
</head>
<body>

<main class="links-page">

  <div class="links-avatar">EVP</div>
  <div class="links-handle">@essevaleapenasim</div>
  <p class="links-bio">🛒 Curadoria honesta de achados Amazon<br>⭐ Reviews com prós E contras — {total_reviews} produtos analisados</p>

{highlight_block}  <a href="index.html" class="link-btn featured">
    <span class="link-emoji">⭐</span>
    <span class="link-text">Ver TODOS os produtos
      <span class="link-sub">{total_reviews} reviews completos no site</span>
    </span>
  </a>

  <a href="categorias.html" class="link-btn">
    <span class="link-emoji">📂</span>
    <span class="link-text">Achados por categoria
      <span class="link-sub">11 categorias organizadas</span>
    </span>
  </a>

  <p class="section-label">📝 Reviews recentes</p>

{sec_html}

  <a href="sobre.html" class="link-btn">
    <span class="link-emoji">💬</span>
    <span class="link-text">Sobre o site
      <span class="link-sub">Como funciona a curadoria</span>
    </span>
  </a>

  <p style="margin-top:40px;font-size:11px;color:var(--text-muted);">
    Participante do Programa de Associados Amazon · O preço é o mesmo que você pagaria entrando direto no site da Amazon
  </p>

</main>

</body>
</html>
'''
    with open(os.path.join(SITE_DIR, "links.html"), 'w', encoding='utf-8') as f:
        f.write(html)
    return highlight_slug

# ============================================================
# STORY TEMPLATE — 1080×1920
# ============================================================
def generate_story_template(slug, product_data, category, label="Novo review"):
    """Cria template Story 1080×1920 pra produto."""
    title = product_data.get("title", slug)
    short = (title[:50] + "...") if len(title) > 50 else title
    img_id = product_data.get("img_id", "")
    if not img_id:
        # tenta extrair do post
        post_path = os.path.join(SITE_DIR, f"posts/{slug}.html")
        if os.path.exists(post_path):
            with open(post_path, 'r', encoding='utf-8') as f:
                h = f.read()
            m = re.search(r'https://m\.media-amazon\.com/images/I/([A-Za-z0-9-]+)\._', h)
            if m: img_id = m.group(1)
    img_url = f"https://m.media-amazon.com/images/I/{img_id}._AC_SX679_.jpg" if img_id else ""
    emoji = CATEGORY_META.get(category, CATEGORY_META["tech"])["emoji"]
    badge = CATEGORY_META.get(category, CATEGORY_META["tech"])["badge_text"]

    html = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<style>
* {{ box-sizing: border-box; margin: 0; padding: 0; }}
body {{
  background: #f3f4f6;
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 30px;
  font-family: -apple-system, BlinkMacSystemFont, "Inter", "Segoe UI", sans-serif;
  gap: 16px;
}}
h2 {{ font-size: 14px; color: #475569; }}
.story {{
  width: 1080px;
  height: 1920px;
  background: linear-gradient(180deg, #1E40AF 0%, #06B6D4 100%);
  position: relative;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  padding: 80px 60px;
}}
.story::before {{
  content: "";
  position: absolute;
  top: -300px;
  right: -300px;
  width: 900px;
  height: 900px;
  background: radial-gradient(circle, rgba(255,255,255,0.20) 0%, transparent 70%);
}}
.brand {{
  position: relative;
  color: white;
  font-weight: 900;
  font-size: 36px;
  letter-spacing: -1px;
  text-align: center;
  margin-bottom: 24px;
}}
.label-pill {{
  position: relative;
  background: rgba(255,255,255,0.18);
  color: white;
  padding: 16px 32px;
  border-radius: 100px;
  font-size: 34px;
  font-weight: 700;
  align-self: center;
  margin-bottom: 40px;
  backdrop-filter: blur(8px);
}}
.title {{
  position: relative;
  color: white;
  font-size: 80px;
  font-weight: 900;
  line-height: 1.05;
  letter-spacing: -2px;
  text-align: center;
  margin-bottom: 50px;
  padding: 0 20px;
}}
.product-card {{
  position: relative;
  background: white;
  border-radius: 32px;
  padding: 60px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-grow: 1;
  margin-bottom: 50px;
  box-shadow: 0 30px 80px rgba(0,0,0,0.3);
}}
.product-card img {{
  max-width: 100%;
  max-height: 800px;
  object-fit: contain;
}}
.cta-arrow {{
  position: relative;
  background: white;
  color: #1E40AF;
  padding: 36px 48px;
  border-radius: 100px;
  font-size: 48px;
  font-weight: 900;
  text-align: center;
  letter-spacing: -1px;
  box-shadow: 0 20px 50px rgba(0,0,0,0.25);
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 20px;
}}
.handle {{
  position: relative;
  color: white;
  font-size: 30px;
  text-align: center;
  margin-top: 32px;
  opacity: 0.9;
  font-weight: 700;
}}
.sticker-hint {{
  position: absolute;
  bottom: 200px;
  right: 80px;
  background: #FBBF24;
  color: #1A1A2E;
  padding: 24px 32px;
  border-radius: 24px;
  font-size: 26px;
  font-weight: 900;
  transform: rotate(-8deg);
  box-shadow: 0 16px 40px rgba(0,0,0,0.25);
  z-index: 5;
}}
</style>
</head>
<body>
<h2>📱 Story 1080×1920 — adicione o adesivo de Link apontando pra: /posts/{slug}</h2>
<div class="story">
  <div class="brand">ESSE VALE A PENA SIM ✓</div>
  <div class="label-pill">{emoji} {label}</div>
  <div class="title">{short}</div>
  <div class="product-card">
    {f'<img src="{img_url}" alt="{short}">' if img_url else '<span style="color:#94a3b8">imagem indisponível</span>'}
  </div>
  <div class="cta-arrow">👆 Adesivo de LINK aqui</div>
  <div class="handle">@essevaleapenasim</div>
  <div class="sticker-hint">VALE<br>A PENA?</div>
</div>
</body>
</html>
"""
    stories_dir = os.path.join(SITE_DIR, "instagram/stories")
    os.makedirs(stories_dir, exist_ok=True)
    fname = f"{slug[:40]}.html"
    with open(os.path.join(stories_dir, fname), 'w', encoding='utf-8') as f:
        f.write(html)
    return fname

# ============================================================
# MONTHLY BATCH GENERATOR — 3:1 ratio
# ============================================================
def generate_month(year_month=None, start_date=None, days_ahead=30):
    """Gera kit mensal com 3 user + 1 auto (alternando bestseller/premium).

    - year_month: 'YYYY-MM' → gera o mês calendário inteiro
    - start_date: datetime.date → gera 'days_ahead' dias a partir dessa data
    - Se nenhum, gera o próximo mês calendário
    """
    meta = load_meta()
    products = meta["products"]

    # Determinar período
    if start_date:
        # Modo "a partir de uma data"
        period_label = f"{start_date.strftime('%Y-%m-%d')}_30dias"
        seed_key = start_date.strftime('%Y%m%d')
        first_date = start_date
        last_date = start_date + datetime.timedelta(days=days_ahead)
    else:
        if not year_month:
            now = datetime.date.today()
            next_month = (now.replace(day=28) + datetime.timedelta(days=4)).replace(day=1)
            year_month = next_month.strftime("%Y-%m")
        period_label = year_month
        seed_key = year_month.replace("-", "")
        year, month = year_month.split("-")
        year, month = int(year), int(month)
        first_date = datetime.date(year, month, 1)
        last_day = (datetime.date(year + (1 if month == 12 else 0), 1 if month == 12 else month+1, 1) - datetime.timedelta(days=1)).day
        last_date = datetime.date(year, month, last_day)

    user_products = [s for s, p in products.items() if p.get("source") == "user"]
    auto_bestsellers = [s for s, p in products.items() if p.get("source") == "auto" and p.get("subsource") == "bestseller"]
    auto_premium = [s for s, p in products.items() if p.get("source") == "auto" and p.get("subsource") == "premium"]
    import random
    rng = random.Random(int(seed_key))
    rng.shuffle(user_products)
    rng.shuffle(auto_bestsellers)
    rng.shuffle(auto_premium)

    # Datas: seg/qua/sex/sáb (sáb é "bônus" pros dias soltos)
    days = []
    d = first_date
    # Se o primeiro dia for sáb/dom, agendamos um post extra de "estreia"
    if d.weekday() == 5:  # sábado de início → post de estreia
        days.append((d, "11:00"))
        d += datetime.timedelta(days=1)
    elif d.weekday() == 6:  # domingo → post de estreia tarde
        days.append((d, "16:00"))
        d += datetime.timedelta(days=1)
    while d <= last_date:
        if d.weekday() in [0, 2, 4]:  # seg, qua, sex
            time = "19:30" if d.weekday() == 0 else ("12:30" if d.weekday() == 2 else "19:00")
            days.append((d, time))
        d += datetime.timedelta(days=1)

    # Schedule com 3:1
    schedule = []
    user_i = bestseller_i = premium_i = 0
    auto_toggle = 0  # 0=bestseller, 1=premium
    n_posts = len(days)
    for i in range(n_posts):
        position = i % 4
        if position < 3:  # 3 user
            if user_i < len(user_products):
                schedule.append({"slug": user_products[user_i], "source": "user"})
                user_i += 1
            else:
                # fallback se esgotou: usa auto
                if auto_toggle == 0 and bestseller_i < len(auto_bestsellers):
                    schedule.append({"slug": auto_bestsellers[bestseller_i], "source": "auto:bestseller"})
                    bestseller_i += 1
                elif premium_i < len(auto_premium):
                    schedule.append({"slug": auto_premium[premium_i], "source": "auto:premium"})
                    premium_i += 1
                auto_toggle = 1 - auto_toggle
        else:  # 1 auto
            if auto_toggle == 0 and bestseller_i < len(auto_bestsellers):
                schedule.append({"slug": auto_bestsellers[bestseller_i], "source": "auto:bestseller"})
                bestseller_i += 1
            elif premium_i < len(auto_premium):
                schedule.append({"slug": auto_premium[premium_i], "source": "auto:premium"})
                premium_i += 1
            elif bestseller_i < len(auto_bestsellers):
                schedule.append({"slug": auto_bestsellers[bestseller_i], "source": "auto:bestseller"})
                bestseller_i += 1
            auto_toggle = 1 - auto_toggle
    days = days[:len(schedule)]

    # Para o label da seção de markdown
    year_month = period_label

    # Gerar markdown
    lines = [f"# 📅 Kit {year_month} — Agendamento Instagram @essevaleapenasim", ""]
    lines.append(f"> Gerado automaticamente seguindo regra 3:1 (3 user-specified + 1 auto)")
    lines.append(f"> Total: {len(schedule)} posts distribuídos no mês")
    lines.append("")
    for i, (post, day_info) in enumerate(zip(schedule, days)):
        date, time = day_info
        weekday = ["Segunda","Terça","Quarta","Quinta","Sexta","Sábado","Domingo"][date.weekday()]
        slug = post["slug"]
        p = products.get(slug, {})
        source_label = {"user":"🟦 USER","auto:bestseller":"🟧 AUTO bestseller","auto:premium":"🟪 AUTO premium"}[post["source"]]
        # Tenta extrair título do post HTML
        post_path = os.path.join(SITE_DIR, f"posts/{slug}.html")
        title = slug
        img = ""
        if os.path.exists(post_path):
            with open(post_path, 'r', encoding='utf-8') as f:
                html = f.read()
            m = re.search(r'<h1>([^<]+)</h1>', html)
            if m: title = m.group(1)
            m = re.search(r'<img[^>]+src="(https://m\.media-amazon\.com[^"]+)"', html)
            if m: img = m.group(1)
        lines.append(f"## Post {i+1} — {weekday} {date.strftime('%d/%m')} {time}")
        lines.append(f"**Origem**: {source_label}")
        lines.append(f"**Produto**: {title}")
        lines.append(f"**Categoria**: {p.get('category','?')}")
        lines.append(f"**Imagem do post IG**: `instagram/posts/` (procure por '{slug[:20]}' ou gere novo)")
        lines.append(f"**Foto produto**: {img}")
        lines.append("")
        lines.append(f"**Legenda sugerida**:")
        cat_emoji = CATEGORY_META.get(p.get("category","tech"), CATEGORY_META["tech"])["emoji"]
        lines.append("```")
        lines.append(f"{cat_emoji} {title}")
        lines.append("")
        lines.append("Análise completa no site — link na bio:")
        lines.append(f"essevaleapenasim.com.br/posts/{slug}")
        lines.append("")
        lines.append("✓ O que gostei | ⚠️ Limitações | 🎯 Vale a pena?")
        lines.append("")
        lines.append("Todos os reviews têm prós E contras — análise honesta sempre.")
        lines.append("```")
        lines.append("")
        lines.append(f"**📌 Comentário fixado (cole NO seu próprio post depois de publicar — depois 3 pontinhos → Fixar comentário)**:")
        lines.append("```")
        lines.append(f"👉 Link pro review completo: essevaleapenasim.com.br/posts/{slug}")
        lines.append("```")
        lines.append("")
        lines.append(f"**📱 Story complementar** (postar na MESMA hora do post): `instagram/stories/{slug[:40]}.html` → screenshot → publicar no story COM adesivo de Link apontando pra `essevaleapenasim.com.br/posts/{slug}`")
        lines.append("")
        lines.append(f"**Hashtags**: #achadosamazon #{p.get('category','')} #valeapena #curadoria #amazonbrasil")
        lines.append("")
        lines.append("---")
        lines.append("")
    out_dir = os.path.join(SITE_DIR, "instagram/mensal")
    os.makedirs(out_dir, exist_ok=True)
    fname = f"{year_month}.md"
    with open(os.path.join(out_dir, fname), 'w', encoding='utf-8') as f:
        f.write("\n".join(lines))
    return fname, len(schedule)

# ============================================================
# REELS — Gerador de vídeo 9:16 com TTS pt-BR
# ============================================================
FFMPEG_BIN = None  # detectado em runtime

def find_ffmpeg():
    """Detecta ffmpeg em locais comuns."""
    global FFMPEG_BIN
    if FFMPEG_BIN: return FFMPEG_BIN
    candidates = [
        os.path.join(SITE_DIR, "automation/bin/ffmpeg"),
        "/opt/homebrew/bin/ffmpeg",
        "/usr/local/bin/ffmpeg",
        "/usr/bin/ffmpeg",
    ]
    for c in candidates:
        if os.path.exists(c) and os.access(c, os.X_OK):
            FFMPEG_BIN = c
            return c
    # PATH
    try:
        result = subprocess.run(["which", "ffmpeg"], capture_output=True, text=True)
        if result.returncode == 0 and result.stdout.strip():
            FFMPEG_BIN = result.stdout.strip()
            return FFMPEG_BIN
    except: pass
    return None

def extract_review_data(slug):
    """Extrai título, prós, contras, veredicto do post HTML."""
    post_path = os.path.join(SITE_DIR, f"posts/{slug}.html")
    if not os.path.exists(post_path):
        return None
    with open(post_path, 'r', encoding='utf-8') as f:
        html = f.read()
    data = {"slug": slug}
    m = re.search(r'<h1>([^<]+)</h1>', html)
    data["title"] = m.group(1).strip() if m else slug
    m = re.search(r'<img[^>]+src="(https://m\.media-amazon\.com/images/I/[^"]+)"', html)
    data["image"] = m.group(1) if m else ""
    # Prós (primeiros 3)
    pros_section = re.search(r'class="pros".*?<ul>(.*?)</ul>', html, re.DOTALL)
    pros = []
    if pros_section:
        pros = re.findall(r'<li>([^<]+)</li>', pros_section.group(1))[:3]
    data["pros"] = [p.strip() for p in pros]
    # Contras (primeiro)
    cons_section = re.search(r'class="cons".*?<ul>(.*?)</ul>', html, re.DOTALL)
    cons = []
    if cons_section:
        cons = re.findall(r'<li>([^<]+)</li>', cons_section.group(1))[:1]
    data["cons"] = [c.strip() for c in cons]
    return data

PHONETIC_DICT = {
    # Marcas K-beauty / americanas aportuguesadas
    "Medicube": "Medikiúbe",
    "Kojic Acid": "ácido cójico",
    "Niacinamide": "niacinamida",
    "Niacinamida": "niacinamida",
    "Skin1004": "Skin mil e quatro",
    "Beauty of Joseon": "Biúti óf Djoson",
    "Cosrx": "Cósrex",
    "TIRTIR": "Tertér",
    "Mise en Scène": "Mizansén",
    "Anua": "Ânua",
    "Hada Labo": "Rada Labô",
    "Innisfree": "Inisfri",
    "Laneige": "Laneije",
    "Etude House": "Etúde Hauz",
    "Frudia": "Fruidia",
    "Celimax": "Celimács",
    "Axis-Y": "Áxis Uái",
    "K-Beauty": "Kei Biúti",
    "K-beauty": "Kei Biúti",
    "kbeauty": "Kei Biúti",
    "Korean": "coreano",
    # Tech / Internacionais
    "Dyson": "Dáison",
    "Airwrap": "Érrap",
    "Airstrait": "Erstreit",
    "Supersonic": "Supersónic",
    "Pure Cool": "Piur cul",
    "Logitech": "Lóji tek",
    "Samsung Galaxy": "Samsung Galáxi",
    "iPhone": "ai fôn",
    "MacBook": "MeqBúk",
    "USB-C": "u s b cê",
    "USB": "u s b",
    "Hub": "rab",
    "Ninja": "Nínja",
    "TPU": "tê pê u",
    "PLA": "pê ele a",
    "ABS": "a bê esse",
    # Skincare/beleza
    "L'Oréal": "Loreal",
    "L'Oreal": "Loreal",
    "Sallve": "Sálve",
    "Cerave": "Seravê",
    "CeraVe": "Seravê",
    "Cetaphil": "Cetafil",
    "ISDIN": "Ísdin",
    "Mustela": "Mustela",
    "NIVEA": "Nívia",
    "Bioderma": "Biodérma",
    "Sebastian": "Sebastián",
    "Redken": "Rédqui",
    "Pink Cheeks": "Pinque Tchíks",
    "Pink Stick": "Pinque Estíq",
    "Photoage": "Fôto eidj",
    "FPS": "f p ésse",
    "PDRN": "p d r ene",
    # Genéricos
    "&": "e",
    "+": "mais",
}

def apply_phonetic(text):
    """Substitui palavras chatas pra TTS pronunciar melhor.
    Usa word boundaries pra não substituir no meio de palavras (ex: 'ABS' em 'absorve')."""
    # Ordena por tamanho decrescente — substitui frases longas antes de palavras curtas
    for orig, replace in sorted(PHONETIC_DICT.items(), key=lambda x: -len(x[0])):
        # \b funciona pra letras ASCII; pra acentos usamos lookahead/lookbehind manuais
        pattern = r'(?<![A-Za-zÀ-ÿ])' + re.escape(orig) + r'(?![A-Za-zÀ-ÿ])'
        text = re.sub(pattern, replace, text, flags=re.IGNORECASE)
    return text

def normalize_for_speech(title):
    """Limpa título pra ficar natural na voz."""
    # Remove medidas e códigos: "30ml", "800g", "FPS 50", "B0XXXX"
    t = title
    # Remove parênteses e tudo dentro
    t = re.sub(r'\([^)]*\)', '', t)
    # Remove brackets
    t = re.sub(r'\[[^\]]*\]', '', t)
    # Remove códigos longos
    t = re.sub(r'\b[A-Z0-9]{6,}\b', '', t)
    # Reduz medidas pra naturalidade
    t = re.sub(r'(\d+)\s*ml', r'\1 mililitros', t)
    t = re.sub(r'(\d+)\s*g\b', r'\1 gramas', t)
    t = re.sub(r'(\d+)\s*kg', r'\1 quilos', t)
    # FPS
    t = re.sub(r'FPS\s*(\d+)', r'fator \1', t)
    # Hifens viram espaços
    t = t.replace('-', ' ').replace('_', ' ').replace('/', ' ou ')
    # Multispace
    t = re.sub(r'\s+', ' ', t).strip()
    # Aplica dicionário fonético
    t = apply_phonetic(t)
    return t

def generate_reel_script(d):
    """Gera narração com estrutura fixa da marca:
    1. ABERTURA (pergunta): 'Esse vale a pena?'
    2. CONTEÚDO: produto + prós + contras
    3. ENCERRAMENTO (afirmação): 'Esse vale a pena sim!'
    """
    title_clean = normalize_for_speech(d["title"])

    # === 1. ABERTURA — sempre a mesma pergunta da marca
    abertura = "Esse vale a pena?"

    # === 2. CONTEÚDO
    # Apresentação do produto (logo após a pergunta)
    apresentacao = f"Hoje a gente analisa: {title_clean}."

    # Prós em frase natural — limitando a 2 prós principais
    pros = d.get("pros", [])[:2]
    pros_clean = []
    for p in pros:
        p_clean = apply_phonetic(p.strip())
        if not p_clean.endswith('.'): p_clean += '.'
        pros_clean.append(p_clean)
    pros_text = " ".join(pros_clean) if pros_clean else ""

    # Contras (1 só, opcional)
    cons_text = ""
    if d.get("cons"):
        cons_clean = apply_phonetic(d["cons"][0].strip())
        if not cons_clean.endswith('.'): cons_clean += '.'
        cons_text = f" Mas atenção: {cons_clean}"

    # CTA + chamada pra DM com palavra-chave "QUERO"
    cta = (
        " Análise completa no link da bio. "
        "Quer saber mais? Escreva QUERO nos comentários que eu te mando o link direto!"
    )

    # === 3. ENCERRAMENTO — sempre a mesma afirmação da marca
    encerramento = "Esse vale a pena sim!"

    return f"{abertura} {apresentacao} {pros_text}{cons_text}{cta} {encerramento}"

def download_image(url, dest):
    """Baixa imagem via curl."""
    try:
        subprocess.run(["curl", "-s", "-L", "-o", dest, url], check=True, timeout=20)
        return os.path.exists(dest) and os.path.getsize(dest) > 1000
    except: return False

def pick_background_music(slug):
    """Escolhe uma música aleatória da pasta automation/music/ (deterministic por slug)."""
    music_dir = os.path.join(SITE_DIR, "automation/music")
    if not os.path.isdir(music_dir):
        return None
    musics = sorted(glob.glob(os.path.join(music_dir, "*.mp3")) +
                    glob.glob(os.path.join(music_dir, "*.m4a")) +
                    glob.glob(os.path.join(music_dir, "*.wav")))
    if not musics:
        return None
    # Hash determinístico do slug → mesma música pro mesmo produto (consistência)
    idx = sum(ord(c) for c in slug) % len(musics)
    return musics[idx]

def generate_reel(slug, voice="pt-BR-FranciscaNeural", rate="+5%"):
    """Gera reel MP4 9:16 (1080×1920) com TTS neural + imagem + texto + música."""
    ffmpeg = find_ffmpeg()
    if not ffmpeg:
        log("❌ ffmpeg não encontrado.", "err")
        return None

    d = extract_review_data(slug)
    if not d or not d.get("image"):
        log(f"❌ Sem dados/imagem pra {slug}", "err")
        return None

    temp_dir = os.path.join(SITE_DIR, "automation/reels-temp")
    out_dir = os.path.join(SITE_DIR, "automation/reels")
    os.makedirs(temp_dir, exist_ok=True)
    os.makedirs(out_dir, exist_ok=True)

    # 1. Baixar imagem
    img_path = os.path.join(temp_dir, f"{slug}.jpg")
    if not download_image(d["image"], img_path):
        log(f"❌ Falha ao baixar imagem de {slug}", "err")
        return None

    # 2. Gerar TTS — Edge TTS (vozes neurais Microsoft) é prioridade
    script = generate_reel_script(d)
    aiff_path = os.path.join(temp_dir, f"{slug}.mp3")  # edge-tts gera mp3
    use_edge = "Neural" in voice or "Multilingual" in voice or "pt-BR-" in voice

    if use_edge:
        # Usa edge-tts (Microsoft neural) — com retry pra timeout
        success = False
        for attempt in range(1, 4):  # 3 tentativas
            try:
                subprocess.run([
                    "python3", "-m", "edge_tts",
                    "--voice", voice,
                    "--text", script,
                    "--rate", rate,
                    "--write-media", aiff_path
                ], check=True, timeout=120, capture_output=True, text=True)
                success = True
                break
            except subprocess.TimeoutExpired:
                log(f"   ⏱️ Edge TTS timeout (tentativa {attempt}/3)", "warn")
                import time
                time.sleep(3 * attempt)  # backoff: 3s, 6s, 9s
            except subprocess.CalledProcessError as e:
                log(f"   ❌ Edge TTS erro (tentativa {attempt}/3): {e.stderr[-200:] if e.stderr else e}", "warn")
                import time
                time.sleep(3 * attempt)

        if not success:
            log(f"   ⚠️ Edge TTS falhou após 3 tentativas. Pulando.", "err")
            return None
    else:
        # Voz Apple (say)
        aiff_path = aiff_path.replace(".mp3", ".aiff")
        try:
            subprocess.run(["say", "-v", voice, "-o", aiff_path, script],
                           check=True, timeout=60, capture_output=True, text=True)
        except subprocess.CalledProcessError as e:
            log(f"❌ TTS falhou: {e.stderr or e}", "err")
            return None

    # Duração do áudio
    duration_result = subprocess.run(
        [ffmpeg, "-i", aiff_path, "-f", "null", "-"],
        capture_output=True, text=True
    )
    m = re.search(r'Duration: (\d+):(\d+):(\d+\.\d+)', duration_result.stderr)
    if m:
        h, mn, s = m.groups()
        audio_dur = int(h)*3600 + int(mn)*60 + float(s)
    else:
        audio_dur = 25.0
    duration = max(audio_dur + 1.0, 10.0)  # +1s pra respirar no fim

    # 3. Textos pra overlay (sanitiza)
    def esc(s):
        # ffmpeg drawtext escapes: : \ '
        return s.replace("\\", "\\\\").replace("'", "").replace(":", " -")[:60]

    # Quebra título em até 2 linhas (~ 22 chars cada)
    full_title = d["title"]
    if len(full_title) > 22:
        words = full_title.split()
        line1, line2 = "", ""
        for w in words:
            if len(line1) + len(w) < 22:
                line1 = (line1 + " " + w).strip()
            else:
                line2 = (line2 + " " + w).strip()
        if len(line2) > 28:
            line2 = line2[:25] + "..."
        title_line1 = esc(line1)
        title_line2 = esc(line2)
    else:
        title_line1 = esc(full_title)
        title_line2 = ""

    out_path = os.path.join(out_dir, f"{slug}.mp4")
    font_path = "/System/Library/Fonts/HelveticaNeue.ttc"

    # 4. Monta vídeo: fundo azul + imagem branca centralizada + textos + áudio
    # Estratégia: pré-processa imagem (scale + pad), depois overlay no canvas
    text_filters = (
        f"drawtext=fontfile={font_path}:text='ESSE VALE A PENA SIM':fontsize=44:fontcolor=white:"
        f"box=1:boxcolor=black@0.4:boxborderw=18:x=(w-text_w)/2:y=140,"
        f"drawtext=fontfile={font_path}:text='{title_line1}':fontsize=58:fontcolor=white:"
        f"box=1:boxcolor=0x06B6D4@0.9:boxborderw=20:x=(w-text_w)/2:y=h-440"
    )
    if title_line2:
        text_filters += (
            f",drawtext=fontfile={font_path}:text='{title_line2}':fontsize=58:fontcolor=white:"
            f"box=1:boxcolor=0x06B6D4@0.9:boxborderw=20:x=(w-text_w)/2:y=h-360"
        )
    text_filters += (
        f",drawtext=fontfile={font_path}:text='@essevaleapenasim':fontsize=38:fontcolor=white:"
        f"box=1:boxcolor=black@0.3:boxborderw=14:x=(w-text_w)/2:y=h-180"
    )

    # 4.1 Seleciona música de fundo (se disponível)
    music_path = pick_background_music(slug)

    # 4.2 Filtros de vídeo — força output 1080x1920 com SAR 1:1 (Meta-friendly)
    video_filter = (
        f"color=c=0x1E40AF:size=1080x1920:duration={duration}:rate=30,setsar=1[bg];"
        f"[1:v]scale=900:900:force_original_aspect_ratio=decrease,"
        f"pad=900:900:(ow-iw)/2:(oh-ih)/2:color=white,setsar=1[img];"
        f"[bg][img]overlay=(W-w)/2:(H-h)/2-80,setsar=1[v1];"
        f"[v1]{text_filters},scale=1080:1920,setsar=1[vout]"
    )

    # Specs Meta Reels: yuv420p (TV range), 3500+ kb/s, CFR 30fps, AAC stereo 44100Hz
    META_VIDEO_OPTS = [
        "-c:v", "libx264",
        "-preset", "medium",
        "-pix_fmt", "yuv420p",          # TV range (NÃO yuvj420p)
        "-profile:v", "high",
        "-level", "4.1",                # 4.1+ pra Instagram
        "-x264-params", "nal-hrd=cbr",  # Constant Bitrate (Meta exige bitrate constante)
        "-b:v", "5000k",                # Bitrate alto pra HD Reels
        "-minrate", "5000k",            # FORÇA o mínimo
        "-maxrate", "5000k",            # FORÇA o máximo (CBR real)
        "-bufsize", "10000k",
        "-fps_mode", "cfr",             # Frame rate constante (Meta exige)
        "-r", "30",
        "-g", "60",                     # Keyframe a cada 2s (Meta recomenda)
        "-color_range", "tv",
        "-colorspace", "bt709",
        "-color_primaries", "bt709",
        "-color_trc", "bt709",
        "-metadata:s:v:0", "rotate=0",  # Garante zero rotação no metadata
    ]

    if music_path:
        # Mix: voz 100% + música 12% (fade in/out) → estéreo
        audio_filter = (
            f"[2:a]volume=1.0,apad=pad_dur={duration}[voice];"
            f"[3:a]aloop=loop=-1:size=2e+9,atrim=duration={duration},"
            f"afade=t=in:st=0:d=1.0,afade=t=out:st={duration-1.5}:d=1.5,"
            f"volume=0.12[music];"
            f"[voice][music]amix=inputs=2:duration=first:dropout_transition=0,"
            f"aformat=channel_layouts=stereo,asetrate=44100[aout]"
        )
        filter_complex = video_filter + ";" + audio_filter
        cmd = [
            ffmpeg, "-y",
            "-f", "lavfi", "-i", f"color=c=0x1E40AF:size=1080x1920:rate=30:duration={duration}",
            "-loop", "1", "-i", img_path,
            "-i", aiff_path,          # [2:a] voz
            "-stream_loop", "-1", "-i", music_path,  # [3:a] música em loop
            "-filter_complex", filter_complex,
            "-map", "[vout]", "-map", "[aout]",
            *META_VIDEO_OPTS,
            "-c:a", "aac", "-b:a", "192k", "-ar", "44100", "-ac", "2",  # stereo
            "-t", str(duration),
            "-movflags", "+faststart",
            out_path
        ]
    else:
        # Sem música — só voz (mas força stereo pra compatibilidade)
        filter_complex = video_filter + f";[2:a]aformat=channel_layouts=stereo,asetrate=44100[aout]"
        cmd = [
            ffmpeg, "-y",
            "-f", "lavfi", "-i", f"color=c=0x1E40AF:size=1080x1920:rate=30:duration={duration}",
            "-loop", "1", "-i", img_path,
            "-i", aiff_path,
            "-filter_complex", filter_complex,
            "-map", "[vout]", "-map", "[aout]",
            *META_VIDEO_OPTS,
            "-c:a", "aac", "-b:a", "192k", "-ar", "44100", "-ac", "2",
            "-shortest",
            "-movflags", "+faststart",
            out_path
        ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        if result.returncode != 0:
            log(f"❌ ffmpeg falhou: {result.stderr[-500:]}", "err")
            return None
    except subprocess.TimeoutExpired:
        log("❌ ffmpeg timeout (60s)", "err")
        return None

    # Limpa temp
    try: os.remove(aiff_path)
    except: pass

    return out_path

def generate_reels_schedule(start_date=None, reels_per_day=2,
                            slot_times=("09:00", "21:00"), only_user=True):
    """Gera cronograma de postagem dos reels. 2 por dia, slots fixos (9h e 21h)."""
    meta = load_meta()
    reels_dir = os.path.join(SITE_DIR, "automation/reels")
    if not os.path.isdir(reels_dir):
        return None
    mp4_files = sorted(glob.glob(os.path.join(reels_dir, "*.mp4")))
    # Remove prefixo NN- se existir, pra ter slug puro
    available_slugs = []
    for f in mp4_files:
        base = os.path.basename(f).replace(".mp4", "")
        m = re.match(r'^\d{2}-(.+)$', base)
        slug = m.group(1) if m else base
        if slug not in available_slugs:
            available_slugs.append(slug)
    if only_user:
        user_slugs = {s for s, p in meta["products"].items() if p.get("source") == "user"}
        available_slugs = [s for s in available_slugs if s in user_slugs]
    import random
    rng = random.Random(20260524)
    rng.shuffle(available_slugs)
    if not start_date:
        start_date = datetime.date.today()
    schedule = []
    current_date = start_date
    slot_idx = 0
    for slug in available_slugs:
        time_str = slot_times[slot_idx % len(slot_times)]
        schedule.append({"date": current_date, "time": time_str, "slug": slug})
        slot_idx += 1
        if slot_idx % reels_per_day == 0:
            current_date = current_date + datetime.timedelta(days=1)
    return schedule

def generate_reels_schedule_md(rename_reels=True):
    """Gera MD com cronograma pra Meta Business Suite.
    Se rename_reels=True, renomeia os MP4 com prefixo NN- pra match.
    """
    schedule = generate_reels_schedule()
    if not schedule:
        return None
    meta = load_meta()
    products = meta["products"]
    site_url = meta["config"]["site_url"]
    reels_dir = os.path.join(SITE_DIR, "automation/reels")

    # Renomeia reels com prefixo numérico pra match com o MD
    if rename_reels:
        # Limpa prefixos antigos primeiro
        for f in glob.glob(os.path.join(reels_dir, "*.mp4")):
            base = os.path.basename(f)
            m = re.match(r'^\d{2}-(.+\.mp4)$', base)
            if m:
                clean = os.path.join(reels_dir, m.group(1))
                if not os.path.exists(clean):
                    os.rename(f, clean)
        # Aplica prefixo na ordem do cronograma
        for i, item in enumerate(schedule, 1):
            slug = item['slug']
            old = os.path.join(reels_dir, f"{slug}.mp4")
            new = os.path.join(reels_dir, f"{i:02d}-{slug}.mp4")
            if os.path.exists(old):
                os.rename(old, new)

    lines = [f"# 🎬 Cronograma de Reels — @essevaleapenasim", ""]
    lines.append(f"> Gerado em {datetime.date.today().isoformat()}")
    lines.append(f"> **{len(schedule)} reels** programados, 2 por dia (9h e 21h)")
    lines.append(f"> Vai de {schedule[0]['date'].strftime('%d/%m')} até {schedule[-1]['date'].strftime('%d/%m')}")
    lines.append("")
    lines.append("> 💡 **Os MP4s estão numerados de 01 a {0}** em `automation/reels/` (mesma ordem deste cronograma).".format(len(schedule)))
    lines.append("")
    lines.append("## 📋 Como agendar no Meta Business Suite")
    lines.append("")
    lines.append("1. `business.facebook.com` → **Planejador**")
    lines.append("2. Pra cada reel abaixo:")
    lines.append("   - **Criar publicação** → tipo **Reel**")
    lines.append("   - Upload do MP4 indicado")
    lines.append("   - Cola legenda")
    lines.append("   - Define data + hora")
    lines.append("   - Marca **Instagram + Facebook**")
    lines.append("   - **Agendar**")
    lines.append("")
    lines.append("---")
    lines.append("")
    for i, item in enumerate(schedule, 1):
        date = item["date"]; time = item["time"]; slug = item["slug"]
        weekday = ["Seg","Ter","Qua","Qui","Sex","Sáb","Dom"][date.weekday()]
        post_path = os.path.join(SITE_DIR, f"posts/{slug}.html")
        title = slug
        if os.path.exists(post_path):
            with open(post_path, 'r', encoding='utf-8') as f: h = f.read()
            m = re.search(r'<h1>([^<]+)</h1>', h)
            if m: title = m.group(1)
        p = products.get(slug, {})
        cat = p.get("category", "tech")
        cat_emoji = CATEGORY_META.get(cat, CATEGORY_META["tech"])["emoji"]
        lines.append(f"## #{i:02d} — {weekday} {date.strftime('%d/%m')} às {time}")
        lines.append("")
        lines.append(f"**Produto**: {title}")
        lines.append(f"**Categoria**: {cat_emoji} {cat}")
        lines.append(f"**📁 MP4**: `{i:02d}-{slug}.mp4` (em `automation/reels/`)")
        lines.append("")
        lines.append(f"**📝 Legenda**:")
        lines.append("```")
        lines.append(f"{cat_emoji} {title}")
        lines.append("")
        lines.append(f"Esse vale a pena sim? Análise honesta com prós e contras.")
        lines.append("")
        lines.append(f"💬 Quer o link direto? Escreve QUERO nos comentários ou DM que eu te mando!")
        lines.append("")
        lines.append(f"Curadoria editorial sem promessa de milagre — só o que avaliamos e indicamos de verdade.")
        lines.append("")
        lines.append(f"#essevaleapenasim #achadosamazon #{cat} #review #curadoria #valeapena #amazonbrasil")
        lines.append("```")
        lines.append("")
        lines.append(f"**📌 Comentário fixado (cola no post depois)**:")
        lines.append("```")
        lines.append(f"👉 Escreve QUERO aqui nos comentários ou na DM que eu te envio o link direto! 💬")
        lines.append(f"")
        lines.append(f"Análise completa também no link da BIO 📲")
        lines.append("```")
        lines.append("")
        lines.append("---")
        lines.append("")
    out_dir = os.path.join(SITE_DIR, "instagram/mensal")
    os.makedirs(out_dir, exist_ok=True)
    fname = f"reels-cronograma-{datetime.date.today().isoformat()}.md"
    out_path = os.path.join(out_dir, fname)
    with open(out_path, 'w', encoding='utf-8') as f:
        f.write("\n".join(lines))
    return out_path

def generate_all_reels(only_user=True, skip_existing=True, force=False):
    """Gera reels pra todos os produtos. Pula os que já existem por padrão."""
    meta = load_meta()
    products = meta["products"]
    slugs = [s for s, p in products.items()
             if (not only_user) or p.get("source") == "user"]
    out_dir = os.path.join(SITE_DIR, "automation/reels")
    pending = []
    skipped = 0
    for s in slugs:
        existing = os.path.join(out_dir, f"{s}.mp4")
        if skip_existing and not force and os.path.exists(existing):
            skipped += 1
        else:
            pending.append(s)
    log(f"→ {len(pending)} reels pendentes ({skipped} já existem, pulando)", "info")
    if not pending:
        log("✓ Nada a fazer — todos os reels já existem.", "ok")
        return 0, 0

    done = failed = 0
    import time
    for i, slug in enumerate(pending, 1):
        log(f"\n[{i}/{len(pending)}] {slug}", "info")
        result = generate_reel(slug)
        if result:
            log(f"✓ {os.path.basename(result)}", "ok")
            done += 1
        else:
            failed += 1
        # Pausa pequena pra não saturar Edge TTS API
        if i < len(pending):
            time.sleep(1.0)
    return done, failed

# ============================================================
# AFFILIATE TAG
# ============================================================
def add_affiliate_tag(store_id):
    pattern = re.compile(r'(https?://(?:www\.)?amazon\.com\.br/(?:[^"\s]*?/)?dp/[A-Z0-9]{10})(?![?&])(["\s])')
    pattern_existing = re.compile(r'(https?://(?:www\.)?amazon\.com\.br/(?:[^"\s]*?/)?dp/[A-Z0-9]{10})\?tag=[a-zA-Z0-9_-]+')
    files = glob.glob(os.path.join(SITE_DIR, '*.html')) + glob.glob(os.path.join(SITE_DIR, 'posts/*.html'))
    changed = added = replaced = 0
    for f in files:
        with open(f, 'r', encoding='utf-8') as fh:
            content = fh.read()
        original = content
        content, n_repl = pattern_existing.subn(lambda m: f"{m.group(1)}?tag={store_id}", content)
        content, n_add = pattern.subn(lambda m: f"{m.group(1)}?tag={store_id}{m.group(2)}", content)
        if content != original:
            with open(f, 'w', encoding='utf-8') as fh:
                fh.write(content)
            changed += 1
            added += n_add
            replaced += n_repl
    return changed, added, replaced

# ============================================================
# GIT OPERATIONS
# ============================================================
def git_publish(message):
    os.chdir(SITE_DIR)
    subprocess.run(['git', 'add', '-A'], check=True)
    result = subprocess.run(['git', 'commit', '-m', message], capture_output=True, text=True)
    if result.returncode != 0 and 'nothing to commit' in result.stdout:
        log("Nada pra commitar.", "warn")
        return False
    subprocess.run(['git', 'push'], check=True)
    return True

# ============================================================
# COMMANDS
# ============================================================
def cmd_add(args):
    if not args:
        log("Uso: evp add <url-ou-asin> [--auto]", "err")
        return
    url = args[0]
    source = "auto" if "--auto" in args else "user"
    log(f"→ Resolvendo URL: {url}", "info")
    asin = resolve_url(url)
    if not asin:
        log("❌ Não consegui extrair ASIN.", "err")
        return
    log(f"✓ ASIN: {asin}", "ok")
    meta = load_meta()
    existing_slug = None
    for s, p in meta["products"].items():
        if p["asin"] == asin:
            existing_slug = s
            break
    if existing_slug:
        log(f"⚠️  Produto já existe no site: {existing_slug}", "warn")
        return
    log("→ Buscando dados na Amazon...", "info")
    pd = fetch_product(asin)
    if not pd or not pd.get("title"):
        log("❌ Não consegui buscar dados do produto.", "err")
        return
    log(f"✓ Título: {pd['title'][:80]}", "ok")
    category = categorize(pd["title"], pd.get("bullets"))
    log(f"✓ Categoria detectada: {category}", "ok")
    slug = slugify(pd["title"][:50])
    if not slug or slug in meta["products"]:
        slug = f"{slug}-{asin[-6:].lower()}"
    store_id = meta["config"]["store_id"]
    # 1. Gerar HTML do review
    html = generate_review_html(slug, pd, category, store_id)
    review_path = os.path.join(SITE_DIR, f"posts/{slug}.html")
    with open(review_path, 'w', encoding='utf-8') as f:
        f.write(html)
    log(f"✓ Review HTML: posts/{slug}.html", "ok")
    # 2. Adicionar à homepage
    img_url = f"https://m.media-amazon.com/images/I/{pd['img_id']}._AC_SX679_.jpg"
    cat_meta = CATEGORY_META.get(category, CATEGORY_META["tech"])
    short_name = (pd["title"][:50] + "...") if len(pd["title"]) > 50 else pd["title"]
    add_to_homepage(slug, short_name, "Análise editorial completa", category, img_url, cat_meta["emoji"], asin=asin, store_id=store_id)
    log("✓ Card adicionado na homepage", "ok")
    # 3. Atualizar metadata
    meta["products"][slug] = {"asin": asin, "source": source, "category": category, "price_tier": "mid"}
    save_meta(meta)
    log("✓ Metadata atualizada", "ok")
    # 4. Rebuild categorias + sitemap + search-index
    total = rebuild_categorias()
    log(f"✓ categorias.html atualizada ({total} produtos)", "ok")
    n_urls = rebuild_sitemap()
    log(f"✓ sitemap.xml atualizado ({n_urls} URLs)", "ok")
    n_prod, n_art = rebuild_search_index()
    log(f"✓ search-index.json atualizado ({n_prod} produtos + {n_art} artigos)", "ok")
    # Cria link curto /p/slug.html → redireciona pra Amazon
    short_url = f"https://www.amazon.com.br/dp/{asin}?tag={store_id}"
    short_template = f"""<!DOCTYPE html>
<html lang="pt-BR"><head>
<meta charset="UTF-8"><title>Redirecionando...</title>
<meta name="robots" content="noindex, nofollow">
<meta http-equiv="refresh" content="0; url={short_url}">
<link rel="canonical" href="{short_url}">
<script>window.location.replace("{short_url}");</script>
<style>body{{font-family:-apple-system,sans-serif;text-align:center;padding:60px 20px;background:#1E40AF;color:white}}a{{color:white}}</style>
</head><body><p>Redirecionando para Amazon...</p>
<p><a href="{short_url}">Clique aqui se não for redirecionado</a></p>
</body></html>"""
    os.makedirs(os.path.join(SITE_DIR, "p"), exist_ok=True)
    with open(os.path.join(SITE_DIR, f"p/{slug}.html"), 'w', encoding='utf-8') as f:
        f.write(short_template)
    log(f"✓ Link curto: essevaleapenasim.com.br/p/{slug}", "ok")
    # 5. Gerar template Instagram
    ig_fname = generate_ig_post(slug, pd, category)
    log(f"✓ Template Instagram: instagram/posts/{ig_fname}", "ok")

    # 6. Gerar Reel automático (se source=user e --no-reel não passado)
    if source == "user" and "--no-reel" not in args:
        if find_ffmpeg():
            log("→ Gerando reel automático (use --no-reel pra pular)...", "info")
            reel_path = generate_reel(slug)
            if reel_path:
                log(f"✓ Reel: automation/reels/{slug}.mp4", "ok")
            else:
                log("⚠️ Reel falhou — você pode tentar depois com 'evp reel " + slug + "'", "warn")
        else:
            log("⚠️ ffmpeg não encontrado — reel não gerado. Configure pra gerar automático.", "warn")

    log(f"\n{C.BOLD}🎉 Produto adicionado com sucesso!{C.END}", "ok")
    log(f"   Próximo: 'python3 evp.py publish \"Add {slug}\"' pra subir no Vercel", "info")

def cmd_month(args):
    # Suporta:
    #  python3 evp.py month                       → próximo mês calendário
    #  python3 evp.py month 2026-07               → mês específico
    #  python3 evp.py month --from-today          → começa HOJE, +30 dias
    #  python3 evp.py month --from=YYYY-MM-DD     → começa em data específica, +30 dias
    start_date = None
    ym = None
    for a in args:
        if a == "--from-today":
            start_date = datetime.date.today()
        elif a.startswith("--from="):
            start_date = datetime.date.fromisoformat(a.split("=", 1)[1])
        elif not a.startswith("--"):
            ym = a
    fname, n = generate_month(year_month=ym, start_date=start_date)
    log(f"✓ Kit gerado: instagram/mensal/{fname} ({n} posts)", "ok")

def cmd_tag(args):
    if not args:
        log("Uso: evp tag <store-id>", "err")
        return
    store_id = args[0]
    changed, added, replaced = add_affiliate_tag(store_id)
    log(f"✓ {changed} arquivos atualizados | {added} tags adicionadas | {replaced} tags substituídas", "ok")

def cmd_publish(args):
    msg = " ".join(args) if args else "Atualização via evp.py"
    if git_publish(msg):
        log("✓ Publicado. Vercel republica em ~30s.", "ok")

def cmd_list(args):
    meta = load_meta()
    cat_filter = None
    for a in args:
        if a.startswith("--category="):
            cat_filter = a.split("=")[1]
    products = meta["products"]
    by_cat = {}
    for slug, p in products.items():
        cat = p.get("category", "?")
        if cat_filter and cat != cat_filter: continue
        by_cat.setdefault(cat, []).append((slug, p))
    for cat in sorted(by_cat):
        log(f"\n{C.BOLD}{cat}{C.END} ({len(by_cat[cat])} produtos)", "info")
        for slug, p in by_cat[cat]:
            src = p.get("source", "?")
            tier = p.get("price_tier", "?")
            label = "🟦" if src == "user" else "🟧"
            print(f"  {label} {slug:50} [{tier:7}] {p['asin']}")

def cmd_status(args):
    meta = load_meta()
    products = meta["products"]
    user = sum(1 for p in products.values() if p.get("source") == "user")
    auto = sum(1 for p in products.values() if p.get("source") == "auto")
    by_cat = {}
    for p in products.values():
        by_cat[p.get("category","?")] = by_cat.get(p.get("category","?"), 0) + 1
    log(f"\n{C.BOLD}📊 Status do site{C.END}", "info")
    print(f"  Total produtos: {len(products)}")
    print(f"  User-specified: {user}")
    print(f"  Auto-fetched:   {auto}")
    print(f"  Store ID:       {meta['config']['store_id']}")
    print(f"  Site URL:       {meta['config']['site_url']}")
    print(f"\n  Por categoria:")
    for cat, n in sorted(by_cat.items(), key=lambda x: -x[1]):
        print(f"    {cat:15} {n}")

def cmd_suggest(args):
    meta = load_meta()
    by_cat = {}
    for p in meta["products"].values():
        by_cat[p.get("category","?")] = by_cat.get(p.get("category","?"), 0) + 1
    log(f"\n{C.BOLD}💡 Sugestões de produtos a adicionar{C.END}", "info")
    SUGGESTIONS = {
        "pele": ["Sérum vitamina C The Ordinary", "La Roche-Posay Effaclar Duo", "Vichy Mineral 89"],
        "cabelo": ["Inoar Argan", "Lola Cosmetics Be(M)dita Ghee", "Wella Oil Reflections"],
        "kbeauty": ["Anua Heartleaf Toner", "Beauty of Joseon Glow Serum", "Cosrx Snail Mucin"],
        "cozinha": ["Mondial Air Fryer Family", "Oster Liquidificador OBL", "Tramontina Allegra"],
        "casa": ["WAP Power Storm aspirador", "Veja Multiuso", "Bombril Pinho Sol"],
        "esporte": ["Optimum Nutrition Gold Whey", "Probiótica Premium Whey", "Centrum Multivit"],
        "pet": ["Premier Pet ração premium", "Friskies gato", "Petisco Pedigree Dentastix"],
        "tech": ["Echo Dot 5", "Kindle Paperwhite", "JBL Go 3"],
        "teenbeauty": ["Vichy Normaderm", "Bioré Pore Strips", "Eucerin AntiAcne"],
        "cuidados": ["Bioderma Atoderm", "QV Skin Lotion", "ADCOS Calmness"],
    }
    for cat, n in sorted(by_cat.items(), key=lambda x: x[1]):
        suggs = SUGGESTIONS.get(cat, [])
        if suggs:
            log(f"\n{cat} ({n} produtos):", "info")
            for s in suggs:
                print(f"  • {s}")
    log(f"\n{C.BOLD}🎯 Como impulsionar vendas{C.END}", "info")
    print("""  1. Foco em PREMIUM: produtos R$500+ pagam mais comissão (até R$50 por venda)
  2. Sazonalidade: agora começa preparação Black Friday (novembro)
  3. Crie 1 artigo comparativo por semana ('X vs Y') → engajamento alto
  4. Posts no IG: 60% educativo + 40% produto (não vire só vitrine)
  5. WhatsApp filtrado: 1 link/semana pra mesma pessoa max
  6. Email signature: assinatura com link do site em emails pessoais
  7. Pinterest: criar conta + 5 pins/dia (tráfego grátis duradouro)""")

def cmd_schedule_reels(args):
    """Gera cronograma de postagem dos 36 reels: 2 por dia, 9h e 21h, começando hoje."""
    out_path = generate_reels_schedule_md()
    if not out_path:
        log("❌ Nenhum reel encontrado em automation/reels/", "err")
        return
    log(f"✓ Cronograma gerado: {out_path}", "ok")
    log(f"   Abre o arquivo pra ver a lista completa de 36 reels com datas/horas/legendas", "info")

def cmd_reel(args):
    """Gera reel(s) MP4 9:16 com TTS neural pt-BR (Francisca Microsoft).

    Uso:
      evp reel                                  → todos os produtos user-indicated
      evp reel <slug>                           → 1 produto específico
      evp reel --all                            → todos (user + auto)
      evp reel --voice=pt-BR-AntonioNeural      → voz masculina
      evp reel --voice=pt-BR-ThalitaMultilingualNeural → voz multilingual
    """
    voice = "pt-BR-FranciscaNeural"  # voz neural Microsoft (qualidade Cortana)
    only_user = True
    slug = None
    for a in args:
        if a.startswith("--voice="):
            voice = a.split("=", 1)[1]
        elif a == "--all":
            only_user = False
        elif not a.startswith("--"):
            slug = a

    ffmpeg = find_ffmpeg()
    if not ffmpeg:
        log("❌ ffmpeg não encontrado.", "err")
        log("Instale via Homebrew: brew install ffmpeg", "info")
        log("Ou baixe binário estático: https://evermeet.cx/ffmpeg/", "info")
        log("E coloque em: automation/bin/ffmpeg (chmod +x)", "info")
        return
    log(f"✓ ffmpeg: {ffmpeg}", "ok")

    if slug:
        log(f"→ Gerando reel pra: {slug}", "info")
        result = generate_reel(slug, voice=voice)
        if result:
            log(f"\n🎬 Reel gerado: {result}", "ok")
            log(f"   Abra com: open '{result}'", "info")
    else:
        done, failed = generate_all_reels(only_user=only_user)
        log(f"\n🎬 {done} reels gerados, {failed} falharam", "ok")
        log(f"   Pasta: automation/reels/", "info")

def cmd_search_index(args):
    """Regenera /search-index.json manualmente."""
    n_prod, n_art = rebuild_search_index()
    log(f"✓ search-index.json gerado: {n_prod} produtos + {n_art} artigos", "ok")

def cmd_links(args):
    """Regenera /links.html. Use 'evp links <slug>' pra destacar um produto específico."""
    slug = None
    label = None
    for a in args:
        if a.startswith("--label="):
            label = a.split("=", 1)[1]
        elif not a.startswith("--"):
            slug = a
    result = rebuild_links_page(highlight_slug=slug, highlight_label=label)
    log(f"✓ /links.html regenerada (destaque: {result or 'mais recente'})", "ok")

def cmd_stories(args):
    """Gera templates de Story 1080×1920 pra todos os produtos do último kit."""
    kit_file = args[0] if args else None
    if not kit_file:
        files = sorted(glob.glob(os.path.join(SITE_DIR, "instagram/mensal/*.md")))
        if not files:
            log("❌ Nenhum kit encontrado.", "err")
            return
        # Pega o mais recente por mtime
        kit_file = max(files, key=os.path.getmtime)
    else:
        if not kit_file.startswith("/"):
            kit_file = os.path.join(SITE_DIR, "instagram/mensal", kit_file)
    log(f"→ Lendo kit: {os.path.basename(kit_file)}", "info")
    with open(kit_file, 'r', encoding='utf-8') as f:
        content = f.read()
    slugs = list(dict.fromkeys(re.findall(r'/posts/([a-z0-9-]+)', content)))
    meta = load_meta()
    generated = 0
    for slug in slugs:
        p = meta["products"].get(slug, {})
        cat = p.get("category", "tech")
        fname = generate_story_template(slug, {}, cat, label="Novo review")
        log(f"  ✓ instagram/stories/{fname}", "ok")
        generated += 1
    log(f"\n✓ {generated} stories gerados", "ok")

def cmd_next(args):
    """Lê o kit atual e prepara o PRÓXIMO post (atualiza /links + gera story)."""
    files = sorted(glob.glob(os.path.join(SITE_DIR, "instagram/mensal/*.md")))
    if not files:
        log("❌ Nenhum kit encontrado.", "err")
        return
    kit_file = max(files, key=os.path.getmtime)
    with open(kit_file, 'r', encoding='utf-8') as f:
        content = f.read()
    # Encontra próximo post baseado na data de hoje
    today = datetime.date.today()
    # Regex que captura cada post: data e slug
    pattern = re.compile(r'## Post \d+ — \w+ (\d{2})/(\d{2}) (\d{2}:\d{2})[\s\S]*?/posts/([a-z0-9-]+)')
    matches = pattern.findall(content)
    next_post = None
    for day, month, time, slug in matches:
        post_date = datetime.date(today.year, int(month), int(day))
        if post_date >= today:
            next_post = (post_date, time, slug)
            break
    if not next_post:
        log("⚠️  Nenhum post futuro no kit atual. Gere um novo com 'evp month --from-today'.", "warn")
        return
    post_date, time, slug = next_post
    log(f"→ Próximo post: {post_date.strftime('%d/%m')} {time} — {slug}", "info")
    rebuild_links_page(highlight_slug=slug, highlight_label=f"🔥 Post de {post_date.strftime('%d/%m')}")
    log(f"✓ /links.html atualizada com '{slug}' em destaque", "ok")
    meta = load_meta()
    p = meta["products"].get(slug, {})
    cat = p.get("category", "tech")
    fname = generate_story_template(slug, {}, cat, label=f"Hoje {post_date.strftime('%d/%m')}")
    log(f"✓ Story gerado: instagram/stories/{fname}", "ok")
    log(f"\n💡 Próximo: 'python3 evp.py publish' pra subir tudo no Vercel.", "info")

def cmd_kit_templates(args):
    """Gera templates Instagram pra todos os produtos do último kit gerado."""
    kit_file = args[0] if args else None
    if not kit_file:
        # Pega o último kit
        files = sorted(glob.glob(os.path.join(SITE_DIR, "instagram/mensal/*.md")))
        if not files:
            log("❌ Nenhum kit encontrado. Rode 'evp month --from-today' primeiro.", "err")
            return
        kit_file = files[-1]
    else:
        if not kit_file.startswith("/"):
            kit_file = os.path.join(SITE_DIR, "instagram/mensal", kit_file)
    log(f"→ Lendo kit: {os.path.basename(kit_file)}", "info")
    with open(kit_file, 'r', encoding='utf-8') as f:
        content = f.read()
    # Extrai slugs
    slugs = re.findall(r'/posts/([a-z0-9-]+)', content)
    slugs = list(dict.fromkeys(slugs))  # dedup mantendo ordem
    meta = load_meta()
    generated = skipped = 0
    for slug in slugs:
        # Já existe template com esse slug?
        existing = glob.glob(os.path.join(SITE_DIR, f"instagram/posts/*{slug[:20]}*"))
        if existing:
            skipped += 1
            continue
        # Recupera dados via post HTML
        post_path = os.path.join(SITE_DIR, f"posts/{slug}.html")
        if not os.path.exists(post_path):
            continue
        with open(post_path, 'r', encoding='utf-8') as f:
            h = f.read()
        title = ""
        m = re.search(r'<h1>([^<]+)</h1>', h)
        if m: title = m.group(1)
        img_id = ""
        m = re.search(r'https://m\.media-amazon\.com/images/I/([A-Za-z0-9-]+)\._', h)
        if m: img_id = m.group(1)
        p = meta["products"].get(slug, {})
        cat = p.get("category", "tech")
        pd = {"title": title, "img_id": img_id}
        fname = generate_ig_post(slug, pd, cat)
        log(f"  ✓ {fname}", "ok")
        generated += 1
    log(f"\n✓ {generated} templates gerados, {skipped} já existentes", "ok")

def cmd_help(args=None):
    print(__doc__)

# ============================================================
# DISPATCHER
# ============================================================
COMMANDS = {
    "add": cmd_add,
    "month": cmd_month,
    "kit-templates": cmd_kit_templates,
    "stories": cmd_stories,
    "links": cmd_links,
    "next": cmd_next,
    "reel": cmd_reel,
    "schedule-reels": cmd_schedule_reels,
    "search-index": cmd_search_index,
    "tag": cmd_tag,
    "publish": cmd_publish,
    "list": cmd_list,
    "status": cmd_status,
    "suggest": cmd_suggest,
    "help": cmd_help,
    "--help": cmd_help,
    "-h": cmd_help,
}

if __name__ == "__main__":
    if len(sys.argv) < 2:
        cmd_help()
        sys.exit(0)
    cmd = sys.argv[1]
    args = sys.argv[2:]
    if cmd not in COMMANDS:
        log(f"Comando desconhecido: {cmd}", "err")
        cmd_help()
        sys.exit(1)
    COMMANDS[cmd](args)
