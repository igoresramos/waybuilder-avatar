# Validacao visual do acervo

Evidencia das decisoes da spec `specs/2026-08-01-avatar-do-personagem.md`.
Nao sao decorativos: cada um prova uma decisao que o texto afirma.

| arquivo | prova |
|---|---|
| `2026-08-01_direcoes-corpo.png` | as 4 direcoes da folha, so o corpo -- inconclusivo sozinho, porque o LPC guarda a cabeca em camada separada |
| `2026-08-01_direcoes-corpo-e-cabeca.png` | **decisao 3b3**: com a cabeca composta, a ordem e `[costas, perfil-esq, FRENTE, perfil-dir]`. A linha 2 encara. Errar isso poria o acervo inteiro de costas |
| `2026-08-01_composicao-v1.png` | primeira composicao a partir do catalogo (formato de 1 arquivo por cor) -- zPos ordenando arma atras e na frente do corpo |
| `2026-08-01_composicao-atlas.png` | mesma composicao apos consolidar as cores em atlas, provando que os offsets `x` (animacao) e `y` (cor) casam |
