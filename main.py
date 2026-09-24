"""
PDF Reader Pro - Um leitor/editor de PDF estilo Adobe Acrobat
Requisitos: pip install PyMuPDF PyQt6
Execução: python main.py
"""
import sys
import os
import tempfile
import fitz  # PyMuPDF
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QTabWidget, QToolBar, QFileDialog,
    QVBoxLayout, QHBoxLayout, QWidget, QLabel, QScrollArea, QListWidget,
    QListWidgetItem, QDockWidget, QLineEdit, QPushButton, QMessageBox,
    QSlider, QStatusBar, QMenu, QInputDialog, QColorDialog, QSplitter,
    QComboBox, QSpinBox, QToolButton, QButtonGroup, QSizePolicy,
    QGraphicsDropShadowEffect, QFrame
)
from PyQt6.QtGui import (
    QPixmap, QImage, QIcon, QAction, QPainter, QPen, QColor, QCursor,
    QKeySequence, QFont
)
from PyQt6.QtCore import Qt, QSize, QPoint, QRectF, pyqtSignal


# ----------------------------------------------------------------------
# Paleta e folha de estilo (visual inspirado no Adobe Acrobat)
# ----------------------------------------------------------------------
ACROBAT_RED = "#DE3831"
ACROBAT_RED_HOVER = "#C82F29"
PANEL_DARK = "#323639"
PANEL_DARKER = "#242729"
PANEL_BORDER = "#3f4347"
TEXT_LIGHT = "#E8E9EA"
TEXT_MUTED = "#9BA0A5"
CANVAS_BG = "#52565A"

STYLE_SHEET = f"""
QMainWindow {{ background-color: {CANVAS_BG}; }}

QToolBar {{
    background-color: {PANEL_DARK};
    border: none;
    padding: 4px;
    spacing: 2px;
}}
QToolBar QToolButton {{
    color: {TEXT_LIGHT};
    background: transparent;
    border-radius: 3px;
    padding: 6px 10px;
    font-size: 12px;
}}
QToolBar QToolButton:hover {{
    background-color: #45494d;
}}
QToolBar QToolButton:checked {{
    background-color: {ACROBAT_RED};
    color: white;
}}

QDockWidget {{
    color: {TEXT_LIGHT};
    background-color: {PANEL_DARKER};
}}
QDockWidget::title {{
    background-color: {PANEL_DARKER};
    padding: 8px;
    font-weight: 600;
    border-bottom: 1px solid {PANEL_BORDER};
}}

QListWidget {{
    background-color: {PANEL_DARKER};
    color: {TEXT_MUTED};
    border: none;
    outline: none;
}}
QListWidget::item {{
    padding: 8px;
    margin: 2px 6px;
    border-radius: 3px;
}}
QListWidget::item:selected {{
    background-color: {ACROBAT_RED};
    color: white;
}}
QListWidget::item:hover:!selected {{
    background-color: #3a3e42;
}}

QTabWidget::pane {{
    border: none;
    background-color: {CANVAS_BG};
}}
QTabBar::tab {{
    background-color: {PANEL_DARKER};
    color: {TEXT_MUTED};
    padding: 7px 16px;
    margin-right: 1px;
    border-top: 2px solid transparent;
}}
QTabBar::tab:selected {{
    background-color: {CANVAS_BG};
    color: {TEXT_LIGHT};
    border-top: 2px solid {ACROBAT_RED};
}}
QTabBar::tab:hover:!selected {{
    background-color: #3a3e42;
}}
QTabBar::close-button {{
    subcontrol-position: right;
}}

QLineEdit {{
    background-color: #454a4e;
    color: {TEXT_LIGHT};
    border: 1px solid {PANEL_BORDER};
    border-radius: 4px;
    padding: 5px 8px;
    selection-background-color: {ACROBAT_RED};
}}
QLineEdit:focus {{ border: 1px solid {ACROBAT_RED}; }}

QComboBox {{
    background-color: #454a4e;
    color: {TEXT_LIGHT};
    border: 1px solid {PANEL_BORDER};
    border-radius: 4px;
    padding: 5px 8px;
}}
QComboBox QAbstractItemView {{
    background-color: {PANEL_DARK};
    color: {TEXT_LIGHT};
    selection-background-color: {ACROBAT_RED};
}}

QStatusBar {{
    background-color: {PANEL_DARK};
    color: {TEXT_MUTED};
    border-top: 1px solid {PANEL_BORDER};
}}

QScrollArea {{ background-color: {CANVAS_BG}; border: none; }}
QScrollBar:vertical {{
    background: {CANVAS_BG};
    width: 12px;
    margin: 0;
}}
QScrollBar::handle:vertical {{
    background: #6b7075;
    border-radius: 5px;
    min-height: 24px;
}}
QScrollBar::handle:vertical:hover {{ background: #83898f; }}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}

QMessageBox, QInputDialog {{
    background-color: {PANEL_DARK};
    color: {TEXT_LIGHT};
}}
QPushButton {{
    background-color: #454a4e;
    color: {TEXT_LIGHT};
    border: 1px solid {PANEL_BORDER};
    border-radius: 4px;
    padding: 5px 14px;
}}
QPushButton:hover {{ background-color: #52585c; }}
QPushButton:default {{
    background-color: {ACROBAT_RED};
    border: none;
}}
QPushButton:default:hover {{ background-color: {ACROBAT_RED_HOVER}; }}
"""


# ----------------------------------------------------------------------
# Widget de página individual (renderização + interação de anotação)
# ----------------------------------------------------------------------
class PageLabel(QLabel):
    """Renderiza uma página do PDF e captura cliques para anotações."""

    annotationRequested = pyqtSignal(int, str, object)  # page_num, tool, data

    def __init__(self, page_num, parent_viewer):
        super().__init__()
        self.page_num = page_num
        self.viewer = parent_viewer
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setMouseTracking(True)
        self._drag_start = None
        self._drawing_points = []
        # sombra sutil ao redor da página, como no Acrobat
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(18)
        shadow.setOffset(0, 3)
        shadow.setColor(QColor(0, 0, 0, 140))
        self.setGraphicsEffect(shadow)

    def mousePressEvent(self, event):
        tool = self.viewer.current_tool
        if tool in ("highlight", "underline", "strikeout"):
            self._drag_start = event.position().toPoint()
        elif tool == "note":
            pos = event.position().toPoint()
            text, ok = QInputDialog.getMultiLineText(self, "Nova nota", "Comentário:")
            if ok and text:
                self.annotationRequested.emit(self.page_num, "note", (pos, text))
        elif tool == "draw":
            self._drawing_points = [event.position().toPoint()]
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self.viewer.current_tool == "draw" and event.buttons() & Qt.MouseButton.LeftButton:
            self._drawing_points.append(event.position().toPoint())
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        tool = self.viewer.current_tool
        if tool in ("highlight", "underline", "strikeout") and self._drag_start:
            end = event.position().toPoint()
            # ignora cliques sem arraste real (área quase zero) — evita anotação inútil/inválida
            if (end - self._drag_start).manhattanLength() > 4:
                rect = (self._drag_start, end)
                self.annotationRequested.emit(self.page_num, tool, rect)
            self._drag_start = None
        elif tool == "draw" and len(self._drawing_points) > 1:
            self.annotationRequested.emit(self.page_num, "draw", list(self._drawing_points))
            self._drawing_points = []
        super().mouseReleaseEvent(event)


# ----------------------------------------------------------------------
# Widget principal de visualização de um documento (uma aba)
# ----------------------------------------------------------------------
class PDFViewer(QWidget):
    def __init__(self, filepath, main_window):
        super().__init__()
        self.main_window = main_window
        self.filepath = filepath
        self.doc = fitz.open(filepath)
        self._original_path = filepath  # salvamento incremental só é válido nesse arquivo
        self.zoom = 1.4
        self.rotation = 0
        self.current_tool = "select"
        self.annotation_color = QColor(255, 255, 0, 120)
        self.page_labels = []
        self.search_results = []
        self.search_index = -1

        self._build_ui()
        self.render_all_pages()

    # ---------------- UI ----------------
    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.pages_container = QWidget()
        self.pages_container.setStyleSheet(f"background-color: {CANVAS_BG};")
        self.pages_layout = QVBoxLayout(self.pages_container)
        self.pages_layout.setContentsMargins(0, 20, 0, 20)
        self.pages_layout.setSpacing(20)
        self.scroll.setWidget(self.pages_container)
        layout.addWidget(self.scroll)

    # ---------------- Renderização ----------------
    def render_all_pages(self):
        # limpa
        for lbl in self.page_labels:
            lbl.setParent(None)
        self.page_labels = []

        for i in range(len(self.doc)):
            lbl = PageLabel(i, self)
            lbl.annotationRequested.connect(self.handle_annotation)
            self.pages_layout.addWidget(lbl)
            self.page_labels.append(lbl)
        self.refresh_pages()

    def refresh_pages(self):
        mat = fitz.Matrix(self.zoom, self.zoom).prerotate(self.rotation)
        for i, page in enumerate(self.doc):
            pix = page.get_pixmap(matrix=mat, alpha=False)
            img = QImage(pix.samples, pix.width, pix.height, pix.stride,
                         QImage.Format.Format_RGB888)
            pixmap = QPixmap.fromImage(img)
            self.page_labels[i].setPixmap(pixmap)
            self.page_labels[i].setFixedSize(pixmap.size())

    def set_zoom(self, factor):
        self.zoom = max(0.2, min(6.0, factor))
        self.refresh_pages()

    def zoom_in(self):
        self.set_zoom(self.zoom * 1.15)

    def zoom_out(self):
        self.set_zoom(self.zoom / 1.15)

    def rotate(self, degrees):
        self.rotation = (self.rotation + degrees) % 360
        self.refresh_pages()

    # ---------------- Anotações ----------------
    def handle_annotation(self, page_num, tool, data):
        page = self.doc[page_num]
        inv_zoom = 1.0 / self.zoom

        try:
            if tool in ("highlight", "underline", "strikeout"):
                p1, p2 = data
                x0, y0 = p1.x() * inv_zoom, p1.y() * inv_zoom
                x1, y1 = p2.x() * inv_zoom, p2.y() * inv_zoom
                rect = fitz.Rect(min(x0, x1), min(y0, y1), max(x0, x1), max(y0, y1))
                if tool == "highlight":
                    annot = page.add_highlight_annot(rect)
                elif tool == "underline":
                    annot = page.add_underline_annot(rect)
                else:
                    annot = page.add_strikeout_annot(rect)
                annot.set_colors(stroke=(1, 1, 0) if tool == "highlight" else (1, 0, 0))
                annot.update()

            elif tool == "note":
                pos, text = data
                x, y = pos.x() * inv_zoom, pos.y() * inv_zoom
                annot = page.add_text_annot(fitz.Point(x, y), text)
                annot.update()

            elif tool == "draw":
                pts = [fitz.Point(p.x() * inv_zoom, p.y() * inv_zoom) for p in data]
                annot = page.add_ink_annot([pts])
                annot.set_colors(stroke=(1, 0, 0))
                annot.set_border(width=2)
                annot.update()
        except Exception as e:
            QMessageBox.warning(self.main_window, "Não foi possível anotar", str(e))
            return

        self.refresh_pages()
        self.main_window.mark_dirty(self)

    def extract_text(self):
        return "\n".join(page.get_text() for page in self.doc)

    # ---------------- Busca ----------------
    def search(self, term):
        self.search_results = []
        if not term:
            return 0
        for i, page in enumerate(self.doc):
            rects = page.search_for(term)
            for r in rects:
                self.search_results.append((i, r))
        self.search_index = -1
        return len(self.search_results)

    def goto_next_result(self):
        if not self.search_results:
            return
        self.search_index = (self.search_index + 1) % len(self.search_results)
        page_num, rect = self.search_results[self.search_index]
        self.scroll.ensureWidgetVisible(self.page_labels[page_num])

    # ---------------- Salvar ----------------
    def save(self, path=None):
        target = path or self.filepath
        # Salvamento incremental só é válido gravando no arquivo original E sem
        # alterações estruturais (páginas excluídas/inseridas). Fora disso, PyMuPDF
        # rejeita ou corrompe o arquivo — então usamos salvamento completo.
        can_incremental = (
            target == self._original_path
            and self.filepath == self._original_path
            and self.doc.can_save_incrementally()
        )
        if can_incremental:
            try:
                self.doc.save(target, incremental=True, encryption=fitz.PDF_ENCRYPT_KEEP)
                self.filepath = target
                return
            except Exception:
                pass  # cai para o salvamento completo abaixo

        if target == self.doc.name:
            # O PyMuPDF não permite salvamento completo sobre o próprio arquivo
            # que está aberto (só incremental). Salva num arquivo temporário e
            # substitui o original — evita o erro/crash nesse caso.
            fd, tmp_path = tempfile.mkstemp(suffix=".pdf", dir=os.path.dirname(target) or None)
            os.close(fd)
            try:
                self.doc.save(tmp_path, garbage=3, deflate=True)
                os.replace(tmp_path, target)
            except Exception:
                if os.path.exists(tmp_path):
                    os.remove(tmp_path)
                raise
        else:
            self.doc.save(target, garbage=3, deflate=True)
        self.filepath = target

    # ---------------- Páginas: extrair / dividir / juntar ----------------
    def extract_pages(self, indices, out_path):
        new_doc = fitz.open()
        for i in indices:
            new_doc.insert_pdf(self.doc, from_page=i, to_page=i)
        new_doc.save(out_path)
        new_doc.close()

    def delete_pages(self, indices):
        for i in sorted(indices, reverse=True):
            self.doc.delete_page(i)
        # resultados de busca antigos podem apontar pra páginas que não existem mais
        self.search_results = []
        self.search_index = -1
        self.render_all_pages()

    def merge_with(self, other_path):
        other = fitz.open(other_path)
        self.doc.insert_pdf(other)
        other.close()
        self.render_all_pages()


# ----------------------------------------------------------------------
# Janela principal
# ----------------------------------------------------------------------
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PDF Reader Pro")
        self.resize(1200, 800)
        self.dirty_tabs = set()
        self.dark_mode = False

        self.tabs = QTabWidget()
        self.tabs.setTabsClosable(True)
        self.tabs.tabCloseRequested.connect(self.close_tab)
        self.tabs.currentChanged.connect(self.on_tab_changed)
        self.setCentralWidget(self.tabs)

        self._build_toolbar()
        self._build_tool_rail()
        self._build_thumbnail_dock()
        self.setStatusBar(QStatusBar())
        self.statusBar().showMessage("Pronto")

    # ---------------- Toolbar superior ----------------
    def _build_toolbar(self):
        tb = QToolBar("Principal")
        tb.setMovable(False)
        tb.setIconSize(QSize(18, 18))
        self.addToolBar(tb)

        def add_action(text, slot, shortcut=None):
            act = QAction(text, self)
            act.triggered.connect(slot)
            if shortcut:
                act.setShortcut(QKeySequence(shortcut))
            tb.addAction(act)
            return act

        add_action("📂 Abrir", self.open_file, "Ctrl+O")
        add_action("💾 Salvar", self.save_current, "Ctrl+S")
        add_action("Salvar como", self.save_as)
        tb.addSeparator()
        add_action("🔍−", self.zoom_out, "Ctrl+-")
        add_action("🔍+", self.zoom_in, "Ctrl+=")
        add_action("⟳ Girar", self.rotate_page)
        tb.addSeparator()

        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("Buscar no documento...")
        self.search_box.setFixedWidth(220)
        self.search_box.returnPressed.connect(self.do_search)
        tb.addWidget(self.search_box)
        add_action("Buscar", self.do_search)
        add_action("Próximo ↓", self.next_result)
        tb.addSeparator()

        add_action("Extrair páginas", self.extract_pages_dialog)
        add_action("Excluir páginas", self.delete_pages_dialog)
        add_action("Juntar PDF", self.merge_dialog)

        # espaçador empurra o botão de modo escuro pra ponta direita
        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        tb.addWidget(spacer)
        add_action("🌙 Modo escuro", self.toggle_dark_mode)

    # ---------------- Rail lateral de ferramentas de anotação ----------------
    def _build_tool_rail(self):
        rail = QToolBar("Ferramentas")
        rail.setMovable(False)
        rail.setOrientation(Qt.Orientation.Vertical)
        rail.setIconSize(QSize(20, 20))
        rail.setStyleSheet(f"QToolBar {{ background-color: {PANEL_DARKER}; border-right: 1px solid {PANEL_BORDER}; }}")

        self.tool_group = QButtonGroup(self)
        self.tool_group.setExclusive(True)

        tools = [
            ("select", "↖", "Selecionar"),
            ("highlight", "✎", "Grifar"),
            ("underline", "U", "Sublinhar"),
            ("strikeout", "S", "Riscar"),
            ("note", "🗨", "Nota"),
            ("draw", "✏", "Desenhar"),
        ]
        for key, symbol, tooltip in tools:
            btn = QToolButton()
            btn.setText(symbol)
            btn.setToolTip(tooltip)
            btn.setCheckable(True)
            btn.setFixedSize(40, 40)
            btn.setFont(QFont("Segoe UI", 13))
            btn.clicked.connect(lambda checked, k=key: self.set_tool(k))
            self.tool_group.addButton(btn)
            rail.addWidget(btn)
            if key == "select":
                btn.setChecked(True)

        self.addToolBar(Qt.ToolBarArea.LeftToolBarArea, rail)

    def set_tool(self, tool_key):
        v = self.current_viewer()
        if v:
            v.current_tool = tool_key
        self.statusBar().showMessage(f"Ferramenta: {tool_key}", 2000)

    def _build_thumbnail_dock(self):
        self.thumb_list = QListWidget()
        self.thumb_list.setIconSize(QSize(90, 120))
        self.thumb_list.itemClicked.connect(self.goto_thumbnail)
        dock = QDockWidget("Páginas", self)
        dock.setMinimumWidth(160)
        dock.setFeatures(
            QDockWidget.DockWidgetFeature.DockWidgetMovable
            | QDockWidget.DockWidgetFeature.DockWidgetFloatable
        )  # sem botão de fechar: evita perder o painel sem forma de reabrir
        dock.setWidget(self.thumb_list)
        self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, dock)

    # ---------------- Abertura / abas ----------------
    def open_file(self):
        path, _ = QFileDialog.getOpenFileName(self, "Abrir PDF", "", "PDF Files (*.pdf)")
        if path:
            self.open_path(path)

    def open_path(self, path):
        viewer = PDFViewer(path, self)
        # respeita o modo escuro já ativo, se houver
        bg = "#1e1e1e" if self.dark_mode else CANVAS_BG
        viewer.pages_container.setStyleSheet(f"background-color: {bg};")
        idx = self.tabs.addTab(viewer, os.path.basename(path))
        self.tabs.setCurrentIndex(idx)  # já dispara on_tab_changed -> atualiza miniaturas

    def current_viewer(self):
        return self.tabs.currentWidget()

    def on_tab_changed(self, index):
        viewer = self.tabs.widget(index)
        if viewer is not None:
            self.update_thumbnails(viewer)
        else:
            self.thumb_list.clear()

    def close_tab(self, index):
        widget = self.tabs.widget(index)
        if widget in self.dirty_tabs:
            resp = QMessageBox.question(
                self, "Salvar alterações?",
                "Este documento tem alterações não salvas. Salvar antes de fechar?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No | QMessageBox.StandardButton.Cancel
            )
            if resp == QMessageBox.StandardButton.Cancel:
                return
            if resp == QMessageBox.StandardButton.Yes:
                try:
                    widget.save()
                except Exception as e:
                    QMessageBox.critical(self, "Erro ao salvar", f"Não foi possível salvar o arquivo:\n{e}")
                    return
        self.dirty_tabs.discard(widget)  # remove a referência independente da resposta
        self.tabs.removeTab(index)
        try:
            widget.doc.close()
        except Exception:
            pass
        widget.deleteLater()

    def mark_dirty(self, viewer):
        self.dirty_tabs.add(viewer)
        idx = self.tabs.indexOf(viewer)
        title = self.tabs.tabText(idx)
        if not title.endswith("*"):
            self.tabs.setTabText(idx, title + "*")

    # ---------------- Ações de toolbar ----------------
    def zoom_in(self):
        v = self.current_viewer()
        if v:
            v.zoom_in()

    def zoom_out(self):
        v = self.current_viewer()
        if v:
            v.zoom_out()

    def rotate_page(self):
        v = self.current_viewer()
        if v:
            v.rotate(90)

    def do_search(self):
        v = self.current_viewer()
        if not v:
            return
        term = self.search_box.text()
        count = v.search(term)
        self.statusBar().showMessage(f"{count} resultado(s) encontrado(s)")
        if count:
            v.goto_next_result()

    def next_result(self):
        v = self.current_viewer()
        if v:
            v.goto_next_result()

    def save_current(self):
        v = self.current_viewer()
        if not v:
            return
        try:
            v.save()
        except Exception as e:
            QMessageBox.critical(self, "Erro ao salvar", f"Não foi possível salvar o arquivo:\n{e}")
            return
        self.dirty_tabs.discard(v)
        idx = self.tabs.indexOf(v)
        self.tabs.setTabText(idx, os.path.basename(v.filepath))
        self.statusBar().showMessage("Salvo com sucesso", 3000)

    def save_as(self):
        v = self.current_viewer()
        if not v:
            return
        path, _ = QFileDialog.getSaveFileName(self, "Salvar como", "", "PDF Files (*.pdf)")
        if not path:
            return
        try:
            v.save(path)
        except Exception as e:
            QMessageBox.critical(self, "Erro ao salvar", f"Não foi possível salvar o arquivo:\n{e}")
            return
        idx = self.tabs.indexOf(v)
        self.tabs.setTabText(idx, os.path.basename(path))
        self.dirty_tabs.discard(v)

    def extract_pages_dialog(self):
        v = self.current_viewer()
        if not v:
            return
        text, ok = QInputDialog.getText(
            self, "Extrair páginas", "Páginas (ex: 1,3,5-7):"
        )
        if ok and text:
            try:
                indices = self._parse_page_ranges(text, len(v.doc))
            except ValueError as e:
                QMessageBox.warning(self, "Entrada inválida", str(e))
                return
            out_path, _ = QFileDialog.getSaveFileName(self, "Salvar extração", "", "PDF Files (*.pdf)")
            if out_path:
                try:
                    v.extract_pages(indices, out_path)
                except Exception as e:
                    QMessageBox.critical(self, "Erro ao extrair", f"Não foi possível extrair as páginas:\n{e}")
                    return
                self.statusBar().showMessage(f"{len(indices)} página(s) extraída(s)", 3000)

    def delete_pages_dialog(self):
        v = self.current_viewer()
        if not v:
            return
        text, ok = QInputDialog.getText(
            self, "Excluir páginas", "Páginas (ex: 1,3,5-7):"
        )
        if ok and text:
            try:
                indices = self._parse_page_ranges(text, len(v.doc))
            except ValueError as e:
                QMessageBox.warning(self, "Entrada inválida", str(e))
                return
            if len(indices) >= len(v.doc):
                QMessageBox.warning(self, "Operação inválida", "Não é possível excluir todas as páginas do documento.")
                return
            try:
                v.delete_pages(indices)
            except Exception as e:
                QMessageBox.critical(self, "Erro ao excluir", f"Não foi possível excluir as páginas:\n{e}")
                return
            self.mark_dirty(v)
            self.update_thumbnails(v)

    def merge_dialog(self):
        v = self.current_viewer()
        if not v:
            return
        path, _ = QFileDialog.getOpenFileName(self, "Selecionar PDF para juntar", "", "PDF Files (*.pdf)")
        if path:
            try:
                v.merge_with(path)
            except Exception as e:
                QMessageBox.critical(self, "Erro ao juntar", f"Não foi possível juntar o PDF:\n{e}")
                return
            self.mark_dirty(v)
            self.update_thumbnails(v)

    def _parse_page_ranges(self, text, total_pages):
        """Converte texto tipo '1,3,5-7' em índices de página (0-based).
        Levanta ValueError com mensagem clara se o formato for inválido."""
        indices = set()
        for part in text.split(","):
            part = part.strip()
            if not part:
                continue
            if "-" in part:
                a, b = part.split("-", 1)
                a, b = a.strip(), b.strip()
                if not (a.isdigit() and b.isdigit()):
                    raise ValueError(f"Intervalo inválido: '{part}'")
                start, end = int(a), int(b)
                if start > end:
                    start, end = end, start
                indices.update(range(start - 1, end))
            elif part.isdigit():
                indices.add(int(part) - 1)
            else:
                raise ValueError(f"Página inválida: '{part}'")
        result = sorted(i for i in indices if 0 <= i < total_pages)
        if not result:
            raise ValueError("Nenhuma página válida foi informada.")
        return result

    def update_thumbnails(self, viewer):
        self.thumb_list.clear()
        mat = fitz.Matrix(0.2, 0.2)
        for i, page in enumerate(viewer.doc):
            pix = page.get_pixmap(matrix=mat, alpha=False)
            img = QImage(pix.samples, pix.width, pix.height, pix.stride,
                         QImage.Format.Format_RGB888)
            item = QListWidgetItem(QIcon(QPixmap.fromImage(img)), f"Página {i + 1}")
            self.thumb_list.addItem(item)

    def goto_thumbnail(self, item):
        v = self.current_viewer()
        if not v:
            return
        idx = self.thumb_list.row(item)
        v.scroll.ensureWidgetVisible(v.page_labels[idx])

    def toggle_dark_mode(self):
        """Alterna o fundo da área de leitura (páginas) entre claro e escuro.
        O chrome da interface (barras, painéis) já é escuro por padrão, como no Acrobat."""
        self.dark_mode = not self.dark_mode
        bg = "#1e1e1e" if self.dark_mode else CANVAS_BG
        for i in range(self.tabs.count()):
            viewer = self.tabs.widget(i)
            viewer.pages_container.setStyleSheet(f"background-color: {bg};")


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("PDF Reader Pro")
    app.setStyleSheet(STYLE_SHEET)
    window = MainWindow()
    window.show()

    if len(sys.argv) > 1 and sys.argv[1].lower().endswith(".pdf"):
        window.open_path(sys.argv[1])

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
