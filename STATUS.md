# 📊 Status do Projeto — ESSE VALE A PENA SIM

> Atualizado: 23/05/2026 — dia da estreia

---

## 🌐 Domínios

| Domínio | Status | Notas |
|---|---|---|
| `essevaleapena.vercel.app` | ✅ Ativo (backup) | Continua funcionando até DNS propagar |
| `essevaleapenasim.com.br` | ⏳ Aguardando DNS (~2h) | Comprado em 23/05, transição em curso |
| `www.essevaleapenasim.com.br` | ⏳ Aguardando DNS | Mesmo |

**Próximo passo**: configurar 2 registros DNS no Registro.br após transição.

| Tipo | Nome | Valor |
|---|---|---|
| A | (vazio) | `216.198.79.1` |
| CNAME | `www` | `fc13df2596cf680e.vercel-dns-017.com.` |

---

## 🛒 Amazon Associates

| Item | Valor |
|---|---|
| Conta ativa | ✅ Aprovada |
| Tag de afiliado | `essevaleapena-20` |
| Operador | Alexandre Kuze Kipper |
| Meta 180 dias | Mínimo 3 vendas qualificadas |
| Vendas atuais | 0 (estreia hoje) |

---

## 📱 Instagram

| Item | Valor |
|---|---|
| Handle | @essevaleapenasim |
| Posts agendados | 14 (de 23/05 até 22/06) |
| Bio | Link na bio → `essevaleapena.vercel.app/links` (atualizar pra `essevaleapenasim.com.br/links` quando DNS propagar) |
| Stories prontos | 14 templates em `/instagram/stories/` |
| Templates de feed prontos | 14 em `/instagram/posts/` (24-37) |

---

## 📦 Site

| Métrica | Valor |
|---|---|
| Produtos catalogados | 102 |
| Reviews HTML | 102 |
| Artigos editoriais | 5 |
| Páginas institucionais | 7 (sobre, contato, faq, afiliados, política, processo-editorial, categorias) |
| URLs no sitemap | 116 |
| Total HTMLs | 125+ |
| Categorias | 11 (pele, cabelo, kbeauty, teenbeauty, cuidados, bemestar, cozinha, casa, esporte, pet, tech) |

---

## 🔧 Infraestrutura

| Item | Status |
|---|---|
| Hospedagem | ✅ Vercel (gratuito) |
| Deploy automático | ✅ Git push → Vercel rebuild ~30s |
| HTTPS | ✅ Vercel SSL automático |
| CDN | ✅ Edge global |
| Analytics | ⏳ Vercel Analytics script adicionado, aguardando ativação no painel |
| Favicon + PWA manifest | ✅ Adicionado em todos os 125 HTMLs |
| Schema.org SEO | ✅ Product + Review em cada post |
| Open Graph | ✅ Em todos os HTMLs |
| robots.txt + sitemap.xml | ✅ Atualizado automaticamente |

---

## 🤖 Automação (`evp.py`)

Comandos disponíveis:
- `add <url>` — adiciona produto (1 comando faz tudo)
- `month --from-today` — gera kit IG com regra 3:1
- `kit-templates` — gera cards 1080×1080
- `stories` — gera stories 1080×1920
- `next` — atualiza /links com próximo post
- `links` — regenera /links manualmente
- `tag <store-id>` — atualiza tag de afiliado em massa
- `publish "msg"` — git add + commit + push
- `list`, `status`, `suggest`, `help`

Documentação: `AUTOMACAO.md`

---

## ⏰ Próximas ações na ordem

### Hoje (23/05) — dia da estreia
- [x] Primeiro post Instagram às 11h (já saiu)
- [ ] DNS propagar (~21h45)
- [ ] Configurar 2 registros DNS no Registro.br
- [ ] Verificar `essevaleapenasim.com.br` no ar

### Amanhã (24/05) — quando DNS propagar
- [ ] Atualizar bio do Instagram pro novo domínio
- [ ] Atualizar conta Amazon Associates com novo URL
- [ ] Cadastrar `essevaleapenasim.com.br` no Google Search Console

### Próxima semana
- [ ] Cadastrar Pinterest @essevaleapenasim
- [ ] Adicionar Google Analytics 4 (opcional)
- [ ] Adicionar 2-3 produtos novos (rotina semanal)

### Daqui a 30 dias (22/06)
- [ ] Gerar próximo kit: `python3 evp.py month --from-today`
- [ ] Reagendar próximos 14 posts no Meta Business Suite
- [ ] Conferir métricas: visitantes, cliques, comissões

### Daqui a 180 dias (novembro 2026)
- [ ] Garantir 3 vendas mínimas pra manter conta Amazon
- [ ] Preparar conteúdo Black Friday

---

## 📁 Estrutura do projeto

```
/Users/alexandrekkipper/Desktop/produtos amazon/
├── evp.py                          ← CLI principal
├── AUTOMACAO.md                    ← docs do CLI
├── STATUS.md                       ← este arquivo
├── README.md                       ← onboarding inicial
├── automation/
│   └── products_metadata.json      ← 102 produtos + config
├── posts/                          ← 102 reviews
├── instagram/
│   ├── posts/                      ← 37 templates feed
│   ├── stories/                    ← 14 templates story
│   └── mensal/2026-05-23_30dias.md ← kit ativo
├── artigos/                        ← 5 artigos editoriais
├── assets/
│   ├── style.css
│   └── og-default.png
├── favicon.svg + apple-touch-icon.svg + manifest.json
├── index.html, links.html, categorias.html, sobre.html, etc
├── sitemap.xml, robots.txt
└── vercel.json
```
