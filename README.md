# PDF Reader Pro

Leitor/editor de PDF estilo Adobe Acrobat, feito em Python com PyQt6 + PyMuPDF.

## Instalação

```bash
pip install -r requirements.txt
```

## Executar

```bash
python main.py
```

Ou abrindo um arquivo direto:

```bash
python main.py caminho\para\arquivo.pdf
```

## Funcionalidades (v1)

- Visualização com abas (múltiplos PDFs abertos)
- Zoom (+/-), rotação, painel de miniaturas clicável
- Busca de texto com navegação entre resultados
- Anotações: grifar, sublinhar, riscar, nota de texto, desenho livre
- Extrair páginas específicas para novo arquivo
- Excluir páginas do documento atual
- Juntar (merge) outro PDF ao final do atual
- Salvar / Salvar como
- Modo escuro
- Aviso de alterações não salvas ao fechar aba

## Próximas versões (a pedido)

- Preenchimento de formulários PDF (AcroForms)
- Assinatura digital / imagem de assinatura
- OCR para PDFs escaneados (via Tesseract)
- Comparação lado a lado de dois PDFs
- Modo apresentação (fullscreen)
- Exportar para imagem / Word

## Estrutura

```
pdfreader/
├── main.py          # aplicação completa
├── requirements.txt
└── README.md
```

## Notas técnicas

- Anotações são salvas diretamente no PDF via PyMuPDF (compatíveis com Adobe Acrobat).
- Renderização usa cache simples: recalcula ao mudar zoom/rotação (poderá ser otimizado com cache de página visível em versões futuras, para documentos muito grandes).
- `Salvar` usa gravação incremental quando salva no mesmo arquivo (mais rápido); `Salvar como` grava um novo arquivo completo.
# Pdf-editor
Open Source pdf editor.
