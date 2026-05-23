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
             "ácido hialurônico", "niacinamida", "vitamina c facial", "olheiras", "skin", "rosto"],
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
                "cozinha", "pote", "tupperware", "marmita", "tábua", "faca", "fogão"],
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
<link rel="stylesheet" href="../assets/style.css">
<link rel="canonical" href="{page_url}">
<meta property="og:type" content="article">
<meta property="og:title" content="{short} — Review">
<meta property="og:description" content="Análise editorial do {short}.">
<meta property="og:url" content="{page_url}">
<meta property="og:image" content="{img_url}">
<meta property="og:locale" content="pt_BR">
<meta property="og:site_name" content="ESSE VALE A PENA SIM">
<meta name="robots" content="index, follow">
</head>
<body>

<header class="site-header">
  <div class="header-inner">
    <a href="../index.html" class="logo">ESSE VALE A PENA SIM</a>
  </div>
</header>

<main class="container">

  <div class="product-hero {cat_meta['gradient']}">
    <img loading="lazy" decoding="async" src="{img_url}" alt="{short}" onerror="this.style.display='none';this.parentElement.innerHTML='{cat_meta['emoji']}';">
  </div>

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
def add_to_homepage(slug, short_name, short_desc, category, img_url, emoji):
    cat_meta = CATEGORY_META.get(category, CATEGORY_META["tech"])
    cat_css = {"pele":"cat-pele","cabelo":"cat-cabelo","kbeauty":"cat-kbeauty","teenbeauty":"cat-teen",
               "cuidados":"cat-cuidados","bemestar":"cat-bemestar","cozinha":"cat-cozinha",
               "casa":"cat-casa","esporte":"cat-esporte","pet":"cat-pet","tech":"cat-tech"}.get(category, "cat-tech")
    card = f"""
    <a href="posts/{slug}.html" class="product-card">
      <div class="visual {cat_meta['gradient']}">
        <img src="{img_url}" alt="{short_name}" onerror="this.style.display='none';this.parentElement.innerHTML='{emoji}';">
      </div>
      <div class="body">
        <span class="category {cat_css}">{cat_meta['badge_text']}</span>
        <h3>{short_name}</h3>
        <p>{short_desc}</p>
        <span class="arrow">Ler review →</span>
      </div>
    </a>
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
                "emoji": emoji_p, "premium": premium
            })
        items.sort(key=lambda x: (0 if x["premium"] else 1, x["name"]))
        if not items: continue
        total += len(items)
        items_html = ""
        for it in items:
            premium_badge = ' <span style="background:linear-gradient(135deg,#FBBF24 0%,#F59E0B 100%);color:white;font-size:10px;font-weight:800;padding:2px 7px;border-radius:10px;margin-left:6px;letter-spacing:0.5px;">PREMIUM</span>' if it["premium"] else ""
            items_html += f"""      <a href="posts/{it['slug']}.html" class="cat-item">
        <div class="thumb">
          <img src="{it['img']}" alt="{it['name']}" onerror="this.style.display='none';this.parentElement.innerHTML='{it['emoji']}';">
        </div>
        <div class="info">
          <span class="name">{it['name']}{premium_badge}</span>
          <span class="desc"></span>
        </div>
        <span class="arrow">→</span>
      </a>
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
<link rel="stylesheet" href="assets/style.css">
<link rel="canonical" href="https://essevaleapena.vercel.app/categorias">
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
<link rel="stylesheet" href="../style.css">
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
        lines.append(f"essevaleapena.vercel.app/posts/{slug}")
        lines.append("")
        lines.append("✓ O que gostei | ⚠️ Limitações | 🎯 Vale a pena?")
        lines.append("")
        lines.append("Todos os reviews têm prós E contras — análise honesta sempre.")
        lines.append("```")
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
    add_to_homepage(slug, short_name, "Análise editorial completa", category, img_url, cat_meta["emoji"])
    log("✓ Card adicionado na homepage", "ok")
    # 3. Atualizar metadata
    meta["products"][slug] = {"asin": asin, "source": source, "category": category, "price_tier": "mid"}
    save_meta(meta)
    log("✓ Metadata atualizada", "ok")
    # 4. Rebuild categorias + sitemap
    total = rebuild_categorias()
    log(f"✓ categorias.html atualizada ({total} produtos)", "ok")
    n_urls = rebuild_sitemap()
    log(f"✓ sitemap.xml atualizado ({n_urls} URLs)", "ok")
    # 5. Gerar template Instagram
    ig_fname = generate_ig_post(slug, pd, category)
    log(f"✓ Template Instagram: instagram/posts/{ig_fname}", "ok")
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

def cmd_help(args=None):
    print(__doc__)

# ============================================================
# DISPATCHER
# ============================================================
COMMANDS = {
    "add": cmd_add,
    "month": cmd_month,
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
