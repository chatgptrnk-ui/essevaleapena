# ⚙️ Sistema de Automação — `evp.py`

CLI único pra cuidar de TUDO no site **ESSE VALE A PENA SIM**: adicionar produto, gerar conteúdo de Instagram, atualizar tag de afiliado, publicar no Vercel.

> Um comando = adiciona produto na Amazon → review HTML → categorias → sitemap → template Instagram → commit → Vercel.

---

## 🚀 Começar agora (uso diário)

```bash
cd "/Users/alexandrekkipper/Desktop/produtos amazon"

# 1. Adicionar um novo produto (você indica → automação faz o resto)
python3 evp.py add https://amzn.to/3xExEmplo

# 2. Gerar próximas 4 semanas de conteúdo Instagram (3:1)
python3 evp.py month --from-today

# 3. Publicar tudo no Vercel
python3 evp.py publish "Novo produto + kit Instagram"
```

---

## 📋 Comandos disponíveis

### `add` — Adicionar novo produto
```bash
python3 evp.py add <url-ou-asin>          # User-specified (3 da regra)
python3 evp.py add <url-ou-asin> --auto   # Auto (1 da regra)
```

**O que faz automaticamente**:
1. Resolve link curto `amzn.to` → URL completa → ASIN
2. Busca título, bullets, imagem na Amazon
3. **Categoriza** sozinho (pele, cabelo, k-beauty, casa, tech, etc — 11 categorias)
4. Gera HTML de review completo (`/posts/slug.html`)
5. Adiciona card na homepage
6. Atualiza metadata (`automation/products_metadata.json`)
7. Reconstrói `/categorias.html` (todas as 11 categorias)
8. Reconstrói `/sitemap.xml`
9. Gera template Instagram (`/instagram/posts/slug.html`)
10. Adiciona tag de afiliado `?tag=essevaleapena-20`

**Aceita**: link curto (amzn.to), link completo (`amazon.com.br/dp/XXXX`), ou ASIN direto.

---

### `month` — Gerar kit Instagram
```bash
python3 evp.py month                       # Próximo mês calendário
python3 evp.py month 2026-07               # Mês específico
python3 evp.py month --from-today          # Começa HOJE (+30 dias)
python3 evp.py month --from=2026-06-01     # Começa em data específica (+30 dias)
```

**Como funciona a regra 3:1**:
- A cada 4 posts: **3 são produtos user-specified** + **1 é auto-fetched**
- Os auto-fetched **alternam**: bestseller → premium → bestseller → premium…
- Horários otimizados:
  - **Seg** 19:30 (depois do trabalho)
  - **Qua** 12:30 (almoço)
  - **Sex** 19:00 (pré-fim-de-semana, alto engajamento)
  - **Sáb/Dom** 11:00–16:00 (apenas para post de estreia)

**Saída**: `/instagram/mensal/{periodo}.md` com:
- Data, hora, dia da semana
- Origem (🟦 USER / 🟧 AUTO bestseller / 🟪 AUTO premium)
- Legenda pronta pra copiar/colar
- Hashtags otimizadas
- URL da imagem do produto
- Slug do template no `/instagram/posts/`

---

### `tag` — Garantir tag de afiliado
```bash
python3 evp.py tag essevaleapena-20
```

Varre **todos** os `.html` da raiz e `/posts/` e:
- Adiciona `?tag=essevaleapena-20` em links sem tag
- Substitui tag antiga (ex: legado `dracarolribas-20`) pela atual

---

### `publish` — Subir no Vercel
```bash
python3 evp.py publish "Minha mensagem de commit"
python3 evp.py publish    # Mensagem default "Atualização via evp.py"
```

Faz `git add -A` + `git commit` + `git push`. Vercel detecta e republica em ~30s.

---

### `list` — Listar produtos
```bash
python3 evp.py list
python3 evp.py list --category=kbeauty
```

Mostra todos os produtos organizados por categoria, com flag user/auto e tier de preço.

---

### `status` — Diagnóstico rápido
```bash
python3 evp.py status
```

Conta total, user vs auto, e quantos produtos em cada categoria.

---

### `suggest` — Próximos passos
```bash
python3 evp.py suggest
```

Sugere quais categorias estão sub-povoadas e ideias estratégicas.

---

### `help` — Ver tudo
```bash
python3 evp.py help
```

---

### `reel` — Gerar vídeo Reel 9:16 com narração IA

```bash
python3 evp.py reel                  # Gera pra todos os 36 produtos user-indicated
python3 evp.py reel <slug>           # Gera só pra um produto
python3 evp.py reel --all            # Inclui também os auto-fetched (66 produtos)
python3 evp.py reel --voice=pt-BR-AntonioNeural   # Voz masculina
python3 evp.py reel --voice=pt-BR-ThalitaMultilingualNeural   # Voz multilingual
```

**O que produz**: vídeo MP4 1080×1920 (formato Reels/Stories/TikTok), ~22 segundos cada, com:
- Fundo azul gradient
- Imagem do produto centralizada
- Badge "ESSE VALE A PENA SIM ✓" no topo
- Título grande do produto no rodapé
- Marca "@essevaleapenasim · link na bio"
- Narração com voz **Francisca Neural** (Microsoft, gratuita)

**Estrutura fixa da narração** (todos os reels):
```
ABERTURA:     "Esse vale a pena?"           ← pergunta da marca
APRESENTAÇÃO: "Hoje a gente analisa: ..."
PRÓS:         [2 prós do review]
CONTRA:       [1 contra do review]
CTA:          "Análise completa no link da bio."
ENCERRAMENTO: "Esse vale a pena sim!"       ← afirmação da marca
```

**Pasta de saída**: `automation/reels/<slug>.mp4`

**Dicionário fonético** (palavras que TTS pronuncia mal): editável em `evp.py` na variável `PHONETIC_DICT`. Inclui marcas como Medicube → Medikiúbe, Kojic Acid → ácido cójico, Niacinamide → niacinamida, etc.

**Pré-requisitos**:
- FFmpeg em `automation/bin/ffmpeg` (Rosetta 2 ativo se Mac M-series)
- Python lib `edge-tts`: `pip3 install edge-tts`

---

## 🔁 Workflow recomendado (rotina semanal)

### Quinta de manhã (10 min)
```bash
# Olhar Amazon Bestsellers da sua categoria favorita → escolher 1-2 produtos novos
python3 evp.py add https://amzn.to/XXXXX
python3 evp.py add https://amzn.to/YYYYY
python3 evp.py publish "+2 produtos: descrição curta"
```

### Início de cada mês (5 min)
```bash
python3 evp.py month --from-today
python3 evp.py publish "Kit Instagram do mês"

# Depois: abrir /instagram/mensal/*.md e agendar tudo no Meta Business Suite
# (uma sentada de 30 min, 1× por mês)
```

### A qualquer momento que mudar de tag/store ID
```bash
python3 evp.py tag essevaleapena-20
python3 evp.py publish "Update tag de afiliado"
```

---

## 🧠 Como o sistema "pensa"

### Categorização automática
Olha o título + bullets do produto e procura keywords:
- "serum", "vitamina C", "FPS" → **pele**
- "shampoo", "condicionador" → **cabelo**
- "Skin1004", "Beauty of Joseon", "K-beauty" → **kbeauty**
- "fritadeira", "panela", "ninja" → **cozinha**
- "Dyson V" → divide entre **casa** (aspirador) e **cabelo** (Airwrap)
- … e mais 5 categorias

Se não bate em nada → cai em **tech** (fallback).

### Slug
Pega o título, remove acentos, converte pra `kebab-case`, limita a 50 chars. Se já existir, adiciona últimos 6 chars do ASIN.

### Imagem
Extrai o `imageBlockData` da página Amazon (mesma imagem que aparece na listagem). Se Amazon mudar a imagem, basta rodar `add` de novo.

### Schema.org + SEO
Todo review gerado já vem com:
- `Product` + `Review` JSON-LD
- Open Graph + Twitter Card
- Canonical URL
- Lazy loading nas imagens
- Sitemap atualizado

---

## 📊 Estrutura dos arquivos

```
/Users/alexandrekkipper/Desktop/produtos amazon/
├── evp.py                          ← este CLI
├── AUTOMACAO.md                    ← este doc
├── automation/
│   └── products_metadata.json      ← estado central: 97 produtos
├── posts/                          ← 97 reviews HTML
├── instagram/
│   ├── posts/                      ← templates 1080×1080 dos cards
│   ├── mensal/
│   │   └── 2026-05-23_30dias.md    ← kit gerado pelo `month`
│   ├── CALENDARIO.md
│   ├── STORIES.md
│   └── COMENTARIOS_E_DMS.md
├── artigos/                        ← 5 artigos editoriais
├── categorias.html                 ← reconstruído pelo evp.py
├── sitemap.xml                     ← reconstruído pelo evp.py
└── index.html                      ← homepage (card adicionado pelo evp.py)
```

---

## 🚨 Quando algo dá errado

### `❌ Não consegui extrair ASIN`
O link curto pode ter expirado ou o produto saiu do ar. Pega o link novo direto da Amazon (formato `amazon.com.br/dp/XXXXXXXXXX`).

### `❌ Não consegui buscar dados do produto`
Amazon às vezes bloqueia. Espera 30s e tenta de novo. Se persistir, abre o link no navegador, copia o título e adiciona manualmente via metadata.

### `⚠️ Produto já existe no site`
Ótimo — significa que o ASIN já está catalogado. Use `python3 evp.py list` pra achar.

### `git push falha`
Provavelmente token expirou. Renova em `github.com/settings/tokens` e atualiza credenciais com `git config --global credential.helper osxkeychain`.

---

## 🎯 Metas estratégicas

- **3:1 é o coração**: garante que o conteúdo seja autêntico (você escolheu) com complemento de produtos quentes (bestseller) e premium (ticket alto).
- **Bestseller traz volume**; **Premium traz comissão** (1 venda Dyson = 10 vendas baratas).
- **14 posts/mês** é o sweet-spot: ativo o suficiente pro algoritmo, sustentável pra quem mantém.
- **Quinta de manhã** = ritual de adicionar 1-2 produtos novos toda semana. Em 12 meses → +100 produtos.

---

## 📝 Versão

`evp.py` v1.0 — 2026-05-23
Built for @essevaleapenasim · Brasil
