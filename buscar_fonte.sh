#!/usr/bin/env bash
# Reconstroi o clone do acervo LPC no pin. Fora do git: 100+ MB reconstruiveis
# por este script, mesmo criterio de `pipeline/dados_brutos/`.
#
# Traz SO o que o build le -- `sources/` (arquivos de edicao, o grosso do
# 1,57 GB do repo) fica de fora via sparse-checkout.
set -euo pipefail
AQUI="$(cd "$(dirname "$0")" && pwd)"
DEST="$AQUI/fontes/lpc"
PIN="$(cat "$AQUI/PIN" 2>/dev/null || echo master)"
REPO=https://github.com/LiberatedPixelCup/Universal-LPC-Spritesheet-Character-Generator

if [ -d "$DEST/.git" ]; then
  echo "== ja existe em $DEST -- atualizando para $PIN"
  git -C "$DEST" fetch --depth 1 origin "$PIN"
  git -C "$DEST" checkout -q FETCH_HEAD
else
  echo "== clonando $REPO no pin $PIN"
  git clone --depth 1 --filter=blob:none --sparse "$REPO" "$DEST"
  git -C "$DEST" sparse-checkout set \
    spritesheets sheet_definitions palette_definitions
  git -C "$DEST" checkout -q "$PIN" 2>/dev/null || true
fi
# CREDITS.csv nao esta no sparse (arquivo de raiz): puxa direto
git -C "$DEST" sparse-checkout add CREDITS.csv 2>/dev/null || true
echo "== pin efetivo: $(git -C "$DEST" rev-parse HEAD)"
du -sh "$DEST"
