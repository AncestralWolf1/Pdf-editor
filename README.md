[🇧🇷 Versão em Português](#-versão-em-português) | [🇺🇸 English Version](#-english-version)

---

# 🇧🇷 Versão em Português

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
```text
pdfreader/
├── main.py          # aplicação completa
├── requirements.txt
└── README.md
```

## Notas técnicas
- Anotações são salvas diretamente no PDF via PyMuPDF (compatíveis com Adobe Acrobat).
- Renderização usa cache simples: recalcula ao mudar zoom/rotação (poderá ser otimizado com cache de página visível em versões futuras, para documentos muito grandes).
- `Salvar` usa gravação incremental quando salva no mesmo arquivo (mais rápido); `Salvar como` grava um novo arquivo completo.

---

# 🇺🇸 English Version

# PDF Reader Pro
Adobe Acrobat-style PDF reader/editor, built in Python with PyQt6 + PyMuPDF.

## Installation
```bash
pip install -r requirements.txt
```

## Usage
```bash
python main.py
```
Or opening a file directly:
```bash
python main.py path\to\file.pdf
```

## Features (v1)
- Tabbed viewing (multiple PDFs open simultaneously)
- Zoom (+/-), rotation, clickable thumbnail panel
- Text search with result navigation
- Annotations: highlight, underline, strikethrough, text note, free drawing
- Extract specific pages to a new file
- Delete pages from the current document
- Merge another PDF to the end of the current one
- Save / Save as
- Dark mode
- Unsaved changes warning when closing a tab

## Upcoming Features (planned)
- PDF form filling (AcroForms)
- Digital signature / signature image insertion
- OCR for scanned PDFs (via Tesseract)
- Side-by-side PDF comparison
- Presentation mode (fullscreen)
- Export to image / Word

## Project Structure
```text
pdfreader/
├── main.py          # main application
├── requirements.txt
└── README.md
```

## Technical Notes
- Annotations are saved directly to the PDF via PyMuPDF (fully compatible with Adobe Acrobat).
- Rendering uses simple caching: it recalculates upon zooming/rotating (future versions may optimize this by caching only the visible pages for very large documents).
- `Save` uses incremental writing when saving to the same file (faster); `Save as` writes a completely new file.
