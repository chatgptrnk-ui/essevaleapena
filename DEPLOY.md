# 🚀 Deploy do ESSE VALE A PENA SIM — Guia completo

Tempo total: **~5 minutos** (depois é automático)

---

## 📋 Antes de começar

Você precisa de:
- [ ] Conta no **GitHub** (gratuita — github.com)
- [ ] Conta no **Vercel** (gratuita — vercel.com — você pode logar com GitHub)
- [ ] Terminal aberto na pasta `produtos amazon` (já estamos lá)

---

## Etapa 1 — Primeiro commit (1 minuto)

Já fizemos `git init`. Agora o primeiro commit:

```bash
cd "/Users/alexandrekkipper/Desktop/produtos amazon"
git add -A
git commit -m "Versão inicial do site ESSE VALE A PENA SIM"
```

> Se der erro pedindo email/nome, configure 1 vez:
> ```
> git config --global user.email "seu-email@gmail.com"
> git config --global user.name "Seu Nome"
> ```

---

## Etapa 2 — Criar repositório no GitHub (2 minutos)

1. Acesse [github.com/new](https://github.com/new)
2. **Repository name**: `essevaleapena`
3. **Description** (opcional): "Site de curadoria Amazon"
4. **Public** ou **Private** — sua escolha
   - 💡 Privado é mais discreto. Vercel funciona com ambos.
5. **NÃO marque** "Initialize with README" (já temos arquivos)
6. Clique **"Create repository"**

GitHub vai te mostrar uma página com comandos. Use os de `push an existing repository`:

```bash
git remote add origin https://github.com/SEU_USUARIO/essevaleapena.git
git branch -M main
git push -u origin main
```

> Substitua `SEU_USUARIO` pelo seu usuário do GitHub.
> Na primeira vez, o GitHub vai abrir uma janela pra autenticar.

---

## Etapa 3 — Conectar ao Vercel (2 minutos)

1. Acesse [vercel.com/new](https://vercel.com/new)
2. Clique em **"Import Git Repository"**
3. Se for o primeiro projeto: clique **"Add GitHub Account"** → autoriza
4. Encontre o repositório `essevaleapena` na lista → clique **"Import"**
5. Configurações do projeto:
   - **Project Name**: `essevaleapena`
   - **Framework Preset**: `Other` (é HTML puro)
   - **Root Directory**: `./` (padrão)
   - **Build Command**: deixe vazio
   - **Output Directory**: deixe vazio
6. Clique **"Deploy"**

⏳ Aguarde ~30 segundos. Vai aparecer **"Congratulations!"** com a URL final:
```
https://essevaleapenasim.com.br
```

---

## Etapa 4 — Teste o site (1 minuto)

Abra a URL e confira:
- [ ] Homepage com 75+ produtos
- [ ] Navegação para `/categorias`
- [ ] Reviews individuais funcionando
- [ ] `/sobre`, `/contato`, `/afiliados`, `/politica`
- [ ] Mobile (abre no celular pra confirmar)

✅ **Está no ar!**

---

## 🔄 Como atualizar daqui pra frente (workflow contínuo)

Qualquer alteração futura segue o mesmo padrão:

```bash
cd "/Users/alexandrekkipper/Desktop/produtos amazon"

# 1. Edita o que quiser (HTML, CSS, etc.)

# 2. Confirma no Git
git add -A
git commit -m "Descrição da mudança"

# 3. Envia pro GitHub
git push

# 4. Vercel republica automático em ~30 segundos
```

Sem precisar fazer nada no Vercel — ele detecta o push e atualiza sozinho.

---

## 🛒 Depois da aprovação Amazon Associados

Quando você receber sua tag (ex: `essevaleapena-20`):

```bash
cd "/Users/alexandrekkipper/Desktop/produtos amazon"
python3 atualizar_tag.py essevaleapena-20
git add -A
git commit -m "Adicionar tag de afiliado"
git push
```

Em ~30s o site está com todos os 75 links monetizados.

---

## 📱 Link para divulgar no WhatsApp

Depois do deploy:
```
https://essevaleapenasim.com.br
```

Ou para uma categoria específica:
```
https://essevaleapenasim.com.br/categorias
```

Ou para um produto específico:
```
https://essevaleapenasim.com.br/posts/dyson-airwrap-kit
```

---

## ❓ Problemas comuns

**"Permission denied" no git push**
- Provavelmente precisa autenticar GitHub. Cria um Personal Access Token em github.com/settings/tokens

**"404" no Vercel após deploy**
- Verifique se `index.html` está na raiz da pasta. Está. ✓

**Quero usar domínio próprio (`essevaleapena.com.br`)**
- Registra no [Registro.br](https://registro.br) (R$ 40/ano)
- No Vercel: Settings > Domains > Add → coloca o domínio
- Vercel te dá os DNS pra configurar no Registro.br
- Em algumas horas o domínio próprio começa a funcionar

---

## 📞 Próximos passos sugeridos

1. ✅ Deploy hoje
2. ⏳ Aguarde 1-2 semanas com o site no ar
3. 🛒 Aplique à Amazon Associados (CPF do operador)
4. 🔧 Receba a tag → rode `atualizar_tag.py`
5. 📱 Comece divulgação no Instagram + WhatsApp filtrado
6. 📊 Adicione Google Analytics (opcional, mas útil)
