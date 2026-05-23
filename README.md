# ESSE VALE A PENA SIM — Site de afiliados Amazon

Site estático em HTML/CSS puro, design moderno, mobile-first. Pronto pra publicação no Vercel.

## 📁 Estrutura

```
produtos amazon/
├── index.html                       # Homepage (grid colorido de produtos)
├── categorias.html           # Post-âncora (link do WhatsApp)
├── sobre.html                       # Sobre o site
├── politica.html                    # Política de privacidade
├── afiliados.html                   # Aviso de afiliados
├── contato.html                     # Contato
├── assets/
│   ├── style.css                    # Estilo único compartilhado
│   └── img/                         # Pasta das imagens dos produtos
└── posts/
    ├── fita-silicone-vital-derme.html
    ├── massageador-couro-cabeludo.html
    ├── hada-labo-eye-care.html
    ├── celimax-tightening-booster.html
    ├── medicube-kojic-niacinamide.html
    ├── hub-usb-c.html
    ├── filamento-tpu-preto.html
    ├── filamento-tpu-flexivel.html
    ├── silk-amendoa.html
    ├── whey-dux.html
    └── sabao-liquido.html
```

---

## 🎨 Como funciona o design

- **Header minimalista**: só o logo "ESSE VALE A PENA SIM" centralizado, sem nav
- **Hero colorido** na homepage com gradiente rosa-laranja
- **Cards com gradientes por categoria**:
  - 💗 Beleza/Skincare: rosa-laranja
  - 💜 Cuidados Pessoais: roxo
  - 🩵 Bem-estar: azul-verde
  - 💙 Tech: azul-roxo
  - 🍊 Cozinha: laranja
  - 💚 Maker/3D: verde-teal
  - ❤️ Esporte: vermelho-laranja
  - 🌿 Casa: verde
- **Páginas de produto compactas**: imagem hero + lead + prós/contras + veredicto
- **Disclaimer minúsculo no rodapé** (não no topo dos posts)
- **Sobre e Contato no footer**, sem destaque

---

## 🖼️ Como adicionar as fotos dos produtos

### Método 1 — URL direta da Amazon (mais rápido, recomendado)

1. Abra a página do produto na Amazon
2. **Clique com botão direito** na imagem principal → **"Copiar endereço da imagem"**
3. Cole a URL no lugar do placeholder no HTML

Procure pelo padrão:
```html
<img src="../assets/img/PRODUTO.jpg" alt="..." onerror="...">
```
E substitua por:
```html
<img src="https://m.media-amazon.com/images/I/IMAGE_ID._AC_SX679_.jpg" alt="..." onerror="...">
```

**Exemplo já implementado**: Silk Amêndoa (veja `posts/silk-amendoa.html` linha do `product-hero`).

### Método 2 — Baixar e hospedar local

1. Salve a imagem da Amazon como `nome-produto.jpg`
2. Coloque em `assets/img/`
3. Os HTMLs já apontam pra essa pasta com os nomes esperados:
   - `fita-vital-derme.jpg`
   - `massageador.jpg`
   - `hada-labo.jpg`
   - `celimax.jpg`
   - `medicube.jpg`
   - `hub-usb-c.jpg`
   - `tpu-preto.jpg`
   - `tpu-flexivel.jpg`
   - `silk-amendoa.jpg`
   - `whey-dux.jpg`
   - `sabao-liquido.jpg`

### Fallback automático

Se a imagem não carregar (URL quebrada, arquivo ausente), aparece automaticamente um **emoji grande no gradiente colorido da categoria** — visualmente bonito mesmo sem foto.

---

## 🚀 Deploy no Vercel

### Drag-and-drop (1 minuto)

1. Acesse [vercel.com/new](https://vercel.com/new)
2. Arraste a pasta `produtos amazon` inteira
3. Project Name: `achados-da-semana`
4. Clique **"Deploy"**
5. URL: `https://esevalepena.vercel.app`

### Via Git (recomendado para updates fáceis)

```bash
cd "/Users/alexandrekkipper/Desktop/produtos amazon"
git init
git add .
git commit -m "Site inicial"
git remote add origin https://github.com/SEU_USUARIO/achados-da-semana.git
git push -u origin main
```
Depois em [vercel.com/new](https://vercel.com/new) → "Import Git Repository" → escolha o repo. Cada `git push` atualiza o site.

---

## ✅ Checklist antes de aplicar na Amazon

- [ ] Site no ar em URL pública
- [ ] Os 11 reviews acessíveis e funcionando
- [ ] Imagens dos produtos plugadas (Método 1 ou 2 acima)
- [ ] Criar e-mail `essevaleapenasim@gmail.com` no nome do operador da conta
- [ ] Nenhuma menção a "Dra", CRM ou medicina em qualquer página
- [ ] Aguardar 2-3 semanas com o site no ar antes de aplicar

---

## 🛒 Aplicação na Amazon Associados

1. Acesse [associados.amazon.com.br](https://associados.amazon.com.br)
2. Inscreva-se com **e-mail e CPF do operador**
3. URL do site: `https://esevalepena.vercel.app`
4. Tópicos: Tecnologia, Beleza, Casa & Cozinha, Esporte
5. Tag preferida: `esevalepena-20`
6. Conta bancária do operador
7. Aguarde 1-3 dias para gerar links

---

## 🔄 Depois da aprovação — adicionar tag aos links

Find/replace em todos os HTMLs:

**De:**
```
href="https://www.amazon.com.br/dp/CODIGO" target="_blank"
```
**Para:**
```
href="https://www.amazon.com.br/dp/CODIGO?tag=esevalepena-20" target="_blank"
```

No VSCode: `Cmd+Shift+H` → busca em todos os arquivos. Ou me pede um script.

---

## 📱 Divulgação no WhatsApp

**Link único pro WhatsApp:**
```
https://esevalepena.vercel.app/categorias.html
```

Sugestão de mensagem:
> Tô organizando aqui os produtos que ando testando. Dei uma olhada no que vale a pena na Amazon, escrevi review de cada um — passa lá se quiser:
> https://esevalepena.vercel.app/categorias.html

**⚠️ Lembretes**:
- NÃO mandar pra pacientes (atuais ou antigos)
- NÃO mandar pra grupos profissionais médicos
- ✅ OK pra família e amigos pessoais
- NUNCA encurtar com bit.ly
- NUNCA mandar link direto da Amazon

---

## 🔧 Próximos passos sugeridos

1. **Plugar as 10 imagens restantes** (siga Método 1 acima — leva ~5 min)
2. **Adicionar 5-10 produtos neutros** (airfryer, livros, fone) pra diluir as categorias de risco
3. **Postar 1 review novo por semana** pra manter o site "vivo"
4. **Google Analytics** (opcional)

Qualquer ajuste, é só pedir.
