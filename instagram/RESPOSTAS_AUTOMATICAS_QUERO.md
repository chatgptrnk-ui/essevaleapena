# 🤖 Setup: Resposta automática "QUERO" no Instagram

Configuração pra que quando alguém escrever **"QUERO"** num comentário ou DM, o Instagram responda automaticamente com o link.

---

## 📍 PARTE 1 — Resposta automática nos COMENTÁRIOS dos Reels

> ⚠️ Limitação: Instagram só permite resposta automática em comentários se você tiver **conta Business** e estar usando o **Meta Business Suite**.

### Passo a passo:

1. Acessa **`business.facebook.com`** (já logada)
2. Menu lateral → **Caixa de entrada** (ou **Inbox**)
3. ⚙️ engrenagem (canto superior direito) → **Automatizações**
4. Procura **"Comentários e mensagens"** → **"Resposta automática a comentários"**
5. **Criar regra nova**:

| Campo | Valor |
|---|---|
| **Nome** | "QUERO — envio link" |
| **Onde aplicar** | Instagram (todos os Reels e Posts) |
| **Gatilho** | **Palavras-chave específicas** |
| **Palavras** | `quero` (só essa) |
| **Match exato?** | Não (qualquer mensagem que CONTÉM "quero") |

6. **Resposta automática** (escolhe **2 ações**):

**Ação 1 — Comentar publicamente:**
```
@usuário oi! ✨ Acabei de te mandar o link na DM 💬
```

**Ação 2 — Enviar DM privada:**
```
Oi! 👋

Vi que você quer o link do produto do reel — segue:

🛒 Página completa com TODOS os reviews:
essevaleapenasim.com.br/links

Lá você acha o produto + a análise completa + o link direto pra Amazon.

(o preço é o mesmo que entrando direto na Amazon — só ganho uma comissão pelas indicações)

Qualquer dúvida, é só me chamar! ✨
```

7. **Ativar regra** ✅

Pronto — agora **toda vez que alguém escrever "QUERO" em qualquer reel/post**, ele:
- Comenta publicamente marcando a pessoa
- Manda DM com o link

---

## 📍 PARTE 2 — Resposta automática nas DMs (Direct Messages)

### Passo a passo:

1. **Caixa de entrada** → ⚙️ → **Automatizações**
2. Procura **"Mensagem instantânea"** ou **"Resposta automática a mensagens"**
3. **Criar nova regra**:

| Campo | Valor |
|---|---|
| **Nome** | "QUERO via DM — envio link" |
| **Gatilho** | Palavra-chave: `quero` |
| **Plataforma** | Instagram |
| **Ativar** | Sempre ativo (24/7) |

4. **Mensagem de resposta** (mesma da Ação 2 acima):
```
Oi! 👋

Vi que você quer o link do produto — segue:

🛒 Página completa com TODOS os reviews:
essevaleapenasim.com.br/links

Lá você acha o produto + a análise completa + o link direto pra Amazon.

(o preço é o mesmo que entrando direto na Amazon — só ganho uma comissão pelas indicações)

Qualquer dúvida, é só me chamar! ✨
```

5. **Salvar e ativar** ✅

---

## 🎯 Resultado esperado

| Cenário | O que acontece |
|---|---|
| Pessoa vê reel → comenta "QUERO" | ✅ Em < 30s recebe resposta pública + DM com link |
| Pessoa manda DM com "QUERO" | ✅ Em < 30s recebe link de volta |
| Pessoa manda DM com "MEDICUBE" / "DYSON" | ❌ Não cai na regra (palavra precisa ser "quero") |
| Pessoa escreve "EU QUERO!" | ✅ Cai na regra (contém "quero") |

---

## 💡 Versão avançada (opcional) — respostas específicas por produto

Se quiser que cada palavra-chave envie o link DIRETO do produto (ex: "MEDICUBE" → link do Medicube), precisaria criar **36 regras separadas** OU usar uma ferramenta de chatbot como **ManyChat** (~R$ 25/mês).

**Versão básica acima é suficiente pra começar** — todo mundo cai na `/links`, que tem tudo bem organizado.

---

## ⚠️ Limitações do Meta

- A regra de "Resposta a comentários" só funciona se você estiver com **Página Facebook vinculada** à conta Instagram Business (você já está)
- Algumas funcionalidades aparecem só **depois de 24-48h** após criar conta Business nova
- Se não encontrar a opção "Automatizações", procura também em:
  - **Caixa de entrada** → ícone de raio ⚡
  - **Configurações da página Facebook vinculada** → **Mensagens automatizadas**
  - App Instagram → **Configurações** → **Negócios** → **Configurações de mensagens**

---

## 🧪 Como testar se está funcionando

1. Depois de ativar, peça pra **uma amiga** comentar "quero" num post seu
2. Aguarde 30 segundos
3. Confira se:
   - ✅ Apareceu uma resposta pública sua marcando ela
   - ✅ Chegou DM pra ela com o link

Se não funcionar, geralmente é:
- Conta não é Business ainda → **Settings → Account → Switch to Professional Account**
- Página FB não está vinculada → **Settings → Accounts Center**

---

## 📊 Acompanhamento

Toda semana, vai em **Caixa de Entrada** e olha quantas DMs automáticas saíram. Pico de DMs = pico de interesse → boa hora pra reforçar com Story manual ou adicionar produto novo dessa categoria.
