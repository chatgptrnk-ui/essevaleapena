#!/usr/bin/env python3
"""
atualizar_tag.py — Insere a tag de afiliado Amazon em todos os links do site.

USO:
    python3 atualizar_tag.py SUA-TAG-20

EXEMPLO:
    python3 atualizar_tag.py essevaleapena-20

O QUE FAZ:
- Varre todos os arquivos .html do site
- Encontra links no formato: https://www.amazon.com.br/dp/CODIGO
- Adiciona ?tag=SUA-TAG-20 ao final
- Idempotente: se a tag já estiver lá, não duplica

DEPOIS DE RODAR:
- git add -A
- git commit -m "Adicionar tag de afiliado"
- git push  (Vercel republica automático)
"""

import os
import re
import sys
import glob

def main():
    if len(sys.argv) != 2:
        print("❌ Uso: python3 atualizar_tag.py SUA-TAG-20")
        print("   Exemplo: python3 atualizar_tag.py essevaleapena-20")
        sys.exit(1)

    tag = sys.argv[1].strip()
    if not re.match(r'^[a-zA-Z0-9_-]+$', tag):
        print(f"❌ Tag inválida: '{tag}'. Use só letras, números, hífen e underscore.")
        sys.exit(1)

    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)

    files = glob.glob('*.html') + glob.glob('posts/*.html') + glob.glob('instagram/**/*.html', recursive=True)
    print(f"📂 {len(files)} arquivos HTML a processar...\n")

    # Regex: matches amazon.com.br/dp/CODIGO sem query string (não duplicar)
    # CODIGO = 10 caracteres alfanuméricos (ASIN)
    pattern = re.compile(
        r'(https?://(?:www\.)?amazon\.com\.br/(?:[^"\s]*?/)?dp/[A-Z0-9]{10})(?![?&])(["\s])'
    )

    # Regex: matches amazon.com.br/dp/CODIGO?tag=ANTIGA (substituir tag antiga)
    pattern_with_tag = re.compile(
        r'(https?://(?:www\.)?amazon\.com\.br/(?:[^"\s]*?/)?dp/[A-Z0-9]{10})\?tag=[a-zA-Z0-9_-]+'
    )

    total_added = 0
    total_replaced = 0
    files_changed = 0

    for f in files:
        with open(f, 'r', encoding='utf-8') as fh:
            content = fh.read()

        original = content

        # 1. Substitui tag antiga se já existir (idempotência)
        def repl_existing(match):
            return f"{match.group(1)}?tag={tag}"
        content, n_replaced = pattern_with_tag.subn(repl_existing, content)

        # 2. Adiciona tag em links que não tem
        def repl_new(match):
            return f"{match.group(1)}?tag={tag}{match.group(2)}"
        content, n_added = pattern.subn(repl_new, content)

        if content != original:
            with open(f, 'w', encoding='utf-8') as fh:
                fh.write(content)
            files_changed += 1
            total_added += n_added
            total_replaced += n_replaced
            print(f"✓ {f}: {n_added} adicionado(s), {n_replaced} atualizado(s)")

    print(f"\n🎯 Resumo:")
    print(f"   Arquivos alterados: {files_changed}")
    print(f"   Tags adicionadas:   {total_added}")
    print(f"   Tags substituídas:  {total_replaced}")
    print(f"   Tag aplicada:       {tag}")

    if files_changed > 0:
        print(f"\n💡 Próximos passos:")
        print(f"   git add -A")
        print(f"   git commit -m 'Adicionar tag de afiliado {tag}'")
        print(f"   git push  → Vercel republica automático em ~30s")
    else:
        print(f"\nℹ️  Nenhuma alteração necessária — tag já estava aplicada em todos os links.")


if __name__ == '__main__':
    main()
