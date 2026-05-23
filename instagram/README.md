# 📸 Instagram Posts — ESSE VALE PENA!

Templates de posts Instagram (1080×1080) prontos pra exportar em PNG. Workflow leva ~30 segundos por post.

## 🚀 Como usar (passo a passo)

### 1. Abrir a galeria
```
Duplo-clique em: instagram/index.html
```
Abre uma página com prévia de todos os 10 posts + legendas + hashtags prontas pra copiar.

### 2. Exportar 1 post em PNG (30 segundos)
1. Clique em **"Abrir post"** no card desejado
2. O template abre em tamanho real (1080×1080) no navegador
3. Pressione `Cmd + Shift + 4` (Mac) ou `Win + Shift + S` (Windows)
4. **Barra de espaço** para alternar para modo "selecionar janela"
5. Clique na imagem do post → PNG salva no Desktop automaticamente
6. Pronto: arquivo `Captura de Tela ...png` no Desktop, prontinho pra Instagram

### 3. Copiar legenda + hashtags
Volte na galeria (`index.html`):
- Selecione o texto da legenda (clique e arraste)
- `Cmd + C` pra copiar
- Cole no Instagram quando for postar

## 📁 Estrutura dos arquivos

```
instagram/
├── README.md                       (esse arquivo)
├── style.css                       (estilo de todos os posts)
├── index.html                      (galeria + legendas + hashtags)
└── posts/
    ├── 01-sanduicheira.html        (Highlight · gancho de preço)
    ├── 02-dyson-airwrap.html       (Highlight · aspiracional)
    ├── 03-ninja-creami.html        (Highlight · viral)
    ├── 04-hub-usbc.html            (Highlight · utilitário)
    ├── 05a-carrossel-cover.html    (Carrossel · capa "5 achados")
    ├── 05b-carrossel-item01.html   (Carrossel · 1º item)
    ├── 06-airfryer-compare.html    (Comparativo · engajamento)
    ├── 07-mouse-logitech.html      (Review · pros & cons)
    ├── 08-faixas-elasticas.html    (Highlight · treino em casa)
    ├── 09-erros-amazon-cover.html  (Carrossel · dicas)
    └── 10-dyson-v15-statement.html (Reel cover · statement)
```

## 🎨 6 layouts disponíveis (pra criar novos posts)

Os templates CSS no `style.css` cobrem 6 estilos diferentes:

| Classe | Uso | Exemplo |
|---|---|---|
| `tpl-highlight` | 1 produto com hook grande | Posts 1, 2, 3, 4, 8 |
| `tpl-compare` | A vs B com VS no meio | Post 6 |
| `tpl-cover` | Capa de carrossel/série | Posts 5a, 9 |
| `tpl-review` | Pros/Cons + selo de veredicto | Post 7 |
| `tpl-item` | Item numerado de carrossel | Post 5b |
| `tpl-statement` | Frase forte fundo escuro (Reel cover) | Post 10 |

## ✏️ Como criar um post novo

1. Copie um dos arquivos em `posts/` que tenha o layout que quiser
2. Renomeie pra algo descritivo (ex: `11-novo-produto.html`)
3. Abra em editor de texto e altere:
   - **Imagem**: troque a URL `https://m.media-amazon.com/images/I/...`
   - **Título**: dentro de `<h1>`
   - **Subtítulo**: dentro de `<p class="subtitle">` ou similar
   - **Tag**: dentro de `<span class="ig-tag">`
4. Salve e abra pra ver o resultado
5. Faça a screenshot conforme acima

## 📅 Calendário recomendado de publicação

**Semana 1** (apresentação)
- Seg: Post 1 (Sanduicheira — acessível, atrai todo perfil)
- Qua: Carrossel 5 (5 Achados)
- Sex: Post 4 (Hub USB-C)

**Semana 2** (variar tipos)
- Seg: Post 2 (Dyson Airwrap — aspiracional)
- Qua: Post 6 (Comparativo airfryer — engajamento)
- Sex: Post 3 (Ninja Creami — viral)

**Semana 3** (esporte/casa)
- Seg: Post 8 (Faixas Elásticas)
- Qua: Carrossel 9 (3 erros)
- Sex: Post 7 (Mouse Logitech)

**Sábados**: Stories (boxes de perguntas, recap da semana)
**Domingos**: descanso (algoritmo prefere consistência menor)

## 🔗 Link na bio do Instagram

Apontar para: `https://esevalepena.vercel.app/links.html`

Essa página (criada no projeto) substitui o Linktree — é grátis, fica no seu próprio site, e tem visual coerente com a marca.

## 💬 Respostas prontas pra DMs

Salva essas no app Instagram como "respostas rápidas" pra ganhar tempo:

**"O preço é o mesmo da Amazon?"**
> Sim, exatamente o mesmo! A Amazon que paga uma comissãozinha pra mim, não sai do seu bolso. 🙏

**"Posso confiar nos reviews?"**
> Pode! Cada review tem seção "O que não gostei" justamente pra ser honesto. Se um produto for ruim, falo. 😊

**"Tem cupom?"**
> Não trabalho com cupom — o preço é o da própria Amazon. Quando tem promoção lá, reflete aqui!

## ⚠️ Lembrete final

Disclosure obrigatório no Instagram (já está em algumas legendas, mas pode reforçar):
- Use `#publi` ou `#parceria` nos posts onde mencionar comissão explicitamente
- Mantenha o link na bio sempre apontando pra seu site (não direto pra Amazon)
