"""
Gerador de Keys — Instagram Bot
Uso exclusivo do desenvolvedor.
Dependências: pip install PyQt6
"""

import sys, json, base64, hashlib, hmac, math, time
from datetime import datetime, timezone, timedelta

from PyQt6.QtWidgets import (
    QApplication, QWidget, QLabel, QLineEdit,
    QPushButton, QTextEdit, QComboBox, QFrame
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import (
    QPainter, QColor, QLinearGradient, QPainterPath,
    QPen, QBrush, QFont, QRadialGradient
)

_SECRET = b"SEU_SECRET_AQUI"

# ── Durações disponíveis ──────────────────
DURACOES = {
    "30 minutos"  : 30,
    "1 hora"      : 60,
    "3 horas"     : 180,
    "6 horas"     : 360,
    "12 horas"    : 720,
    "24 horas"    : 1440,
    "7 dias"      : 10080,
    "30 dias"     : 43200,
}

def gerar_key(minutos: int) -> str:
    exp = datetime.now(tz=timezone.utc) + timedelta(minutes=minutos)
    payload = json.dumps({
        "exp"  : int(exp.timestamp()),
        "mins" : minutos,
        "ts"   : int(time.time()),
    }).encode()
    sig = hmac.new(_SECRET, payload, hashlib.sha256).digest()
    return base64.b64encode(payload + sig).decode()

def validar_key(key: str) -> tuple[bool, str]:
    try:
        raw = base64.b64decode(key.strip().encode())
        payload, sig = raw[:-32], raw[-32:]
        expected = hmac.new(_SECRET, payload, hashlib.sha256).digest()
        if not hmac.compare_digest(sig, expected):
            return False, "Assinatura inválida"
        data = json.loads(payload.decode())
        exp  = datetime.fromtimestamp(data["exp"], tz=timezone.utc)
        now  = datetime.now(tz=timezone.utc)
        if now > exp:
            return False, f"Expirada há {int((now-exp).total_seconds()//60)} min"
        diff = exp - now
        m = int(diff.total_seconds()//60)
        s = int(diff.total_seconds()%60)
        return True, f"Válida por {m}min {s}s  |  expira {exp.strftime('%d/%m/%Y %H:%M')} UTC"
    except Exception as e:
        return False, f"Erro: {e}"

# ══════════════════════════════════════════
#  UI
# ══════════════════════════════════════════
W, H = 480, 580

class GenWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Key Generator")
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedSize(W, H)
        sg = QApplication.primaryScreen().geometry()
        self.move((sg.width()-W)//2, (sg.height()-H)//2)
        self._drag_pos = None
        self._build()

    # ── pintura ──────────────────────────
    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        path = QPainterPath()
        path.addRoundedRect(0, 0, W, H, 40, 40)
        p.setClipPath(path)
        g = QLinearGradient(0, 0, 0, H)
        g.setColorAt(0.0, QColor("#FDF6FF"))
        g.setColorAt(1.0, QColor("#F0E4FF"))
        p.fillPath(path, QBrush(g))

        # blob decorativo
        bg2 = QRadialGradient(W*0.85, H*0.15, 130)
        bg2.setColorAt(0, QColor("#E9D5FF", )); bg2.setColorAt(0, QColor(233,213,255,80))
        bg2.setColorAt(1, QColor(233,213,255,0))
        p.setBrush(QBrush(bg2)); p.setPen(Qt.PenStyle.NoPen)
        p.drawEllipse(int(W*0.85-130), int(H*0.15-130), 260, 260)

        p.setClipping(False)
        p.setPen(QPen(QColor("#DCC8F0"), 1.5))
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawPath(path)

    # ── layout ───────────────────────────
    def _build(self):
        # fechar
        btn_x = QPushButton("✕", self)
        btn_x.setGeometry(W-50, 14, 28, 28)
        btn_x.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_x.clicked.connect(self.close)
        btn_x.setStyleSheet("""
            QPushButton{background:#FFD0D0;color:#C0392B;border-radius:14px;
                        font:bold 11px 'Segoe UI';border:none;}
            QPushButton:hover{background:#FFB3B3;}
        """)

        # título
        QLabel("🗝️  Gerador de Keys", self).setGeometry(0, 18, W, 28); \
            self.findChild(QLabel).setAlignment(Qt.AlignmentFlag.AlignHCenter); \
            self.findChild(QLabel).setStyleSheet("color:#1A0533;font:bold 18px 'Segoe UI';background:transparent;")

        lbl = QLabel("🗝️  Gerador de Keys", self)
        lbl.setGeometry(0, 18, W, 28)
        lbl.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        lbl.setStyleSheet("color:#1A0533;font:bold 18px 'Segoe UI';background:transparent;")

        lbl2 = QLabel("Crie chaves de acesso temporárias para seus clientes", self)
        lbl2.setGeometry(0, 48, W, 20)
        lbl2.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        lbl2.setStyleSheet("color:#A78BCA;font:11px 'Segoe UI';background:transparent;")

        # ── separador ─────────────────────
        sep = QFrame(self); sep.setGeometry(28, 76, W-56, 1)
        sep.setStyleSheet("background:#EDE9F8;")

        # ── Duração ──────────────────────
        QLabel("DURAÇÃO DA KEY", self).setGeometry(28, 92, 200, 14) \
            .setStyleSheet("color:#C4B5D4;font:bold 10px 'Segoe UI';letter-spacing:1px;background:transparent;") \
            if False else None
        lbl_dur = QLabel("DURAÇÃO DA KEY", self)
        lbl_dur.setGeometry(28, 92, 200, 14)
        lbl_dur.setStyleSheet("color:#C4B5D4;font:bold 10px 'Segoe UI';letter-spacing:1px;background:transparent;")

        self.combo = QComboBox(self)
        self.combo.setGeometry(28, 110, W-56, 46)
        for d in DURACOES:
            self.combo.addItem(d)
        self.combo.setStyleSheet("""
            QComboBox{background:#F5F0FF;border:1.5px solid #DCC8F0;border-radius:16px;
                      padding:0 16px;font:13px 'Segoe UI';color:#3B0A6E;}
            QComboBox::drop-down{border:none;width:30px;}
            QComboBox::down-arrow{image:none;}
            QComboBox:hover{border:1.5px solid #A855F7;}
            QComboBox QAbstractItemView{background:#F5F0FF;border:1px solid #DCC8F0;
                                        selection-background-color:#EDE9FE;color:#3B0A6E;}
        """)

        # ── botão gerar ──────────────────
        self.btn_gen = QPushButton("✨  Gerar Key", self)
        self.btn_gen.setGeometry(28, 170, W-56, 50)
        self.btn_gen.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_gen.clicked.connect(self._gerar)
        self.btn_gen.setStyleSheet("""
            QPushButton{background:qlineargradient(x1:0,y1:0,x2:1,y2:1,
                          stop:0 #A855F7,stop:0.5 #7C3AED,stop:1 #6D28D9);
                        color:white;border-radius:18px;font:bold 14px 'Segoe UI';border:none;}
            QPushButton:hover{background:qlineargradient(x1:0,y1:0,x2:1,y2:1,
                          stop:0 #9333EA,stop:1 #6D28D9);}
            QPushButton:pressed{padding-top:2px;}
        """)

        # ── key gerada ───────────────────
        lbl_k = QLabel("KEY GERADA", self)
        lbl_k.setGeometry(28, 234, 200, 14)
        lbl_k.setStyleSheet("color:#C4B5D4;font:bold 10px 'Segoe UI';letter-spacing:1px;background:transparent;")

        self.txt_key = QTextEdit(self)
        self.txt_key.setGeometry(28, 252, W-56, 90)
        self.txt_key.setReadOnly(True)
        self.txt_key.setPlaceholderText("A key aparecerá aqui...")
        self.txt_key.setStyleSheet("""
            QTextEdit{background:#F5F0FF;border:1.5px solid #DCC8F0;border-radius:16px;
                      padding:8px 14px;font:10px 'Consolas';color:#3B0A6E;}
            QScrollBar:vertical{width:4px;background:transparent;}
            QScrollBar::handle:vertical{background:#DDD6FE;border-radius:2px;}
        """)

        # botão copiar
        self.btn_copy = QPushButton("📋  Copiar Key", self)
        self.btn_copy.setGeometry(28, 354, W-56, 44)
        self.btn_copy.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_copy.clicked.connect(self._copiar)
        self.btn_copy.setStyleSheet("""
            QPushButton{background:#F5F0FF;color:#7C3AED;border-radius:15px;
                        font:600 13px 'Segoe UI';border:1.5px solid #D8CCEF;}
            QPushButton:hover{background:#EDE9F8;}
        """)

        # ── separador ─────────────────────
        sep2 = QFrame(self); sep2.setGeometry(28, 412, W-56, 1)
        sep2.setStyleSheet("background:#EDE9F8;")

        # ── validador ────────────────────
        lbl_v = QLabel("VERIFICAR KEY", self)
        lbl_v.setGeometry(28, 422, 200, 14)
        lbl_v.setStyleSheet("color:#C4B5D4;font:bold 10px 'Segoe UI';letter-spacing:1px;background:transparent;")

        self.entry_check = QLineEdit(self)
        self.entry_check.setPlaceholderText("Cole uma key para verificar...")
        self.entry_check.setGeometry(28, 440, W-56, 44)
        self.entry_check.setStyleSheet("""
            QLineEdit{background:#F5F0FF;border:1.5px solid #DCC8F0;border-radius:14px;
                      padding:0 14px;font:10px 'Consolas';color:#3B0A6E;}
            QLineEdit:focus{border:1.5px solid #A855F7;}
        """)
        self.entry_check.returnPressed.connect(self._verificar)

        self.btn_check = QPushButton("🔍  Verificar", self)
        self.btn_check.setGeometry(28, 494, W-56, 40)
        self.btn_check.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_check.clicked.connect(self._verificar)
        self.btn_check.setStyleSheet("""
            QPushButton{background:#F5F0FF;color:#7C3AED;border-radius:13px;
                        font:600 12px 'Segoe UI';border:1.5px solid #D8CCEF;}
            QPushButton:hover{background:#EDE9F8;}
        """)

        self.lbl_result = QLabel("", self)
        self.lbl_result.setGeometry(28, 540, W-56, 20)
        self.lbl_result.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        self.lbl_result.setStyleSheet("font:11px 'Segoe UI';background:transparent;")

        # rodapé
        lbl_ft = QLabel("🔒  Use com responsabilidade  ·  Desenvolvedor", self)
        lbl_ft.setGeometry(0, 562, W, 14)
        lbl_ft.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        lbl_ft.setStyleSheet("color:#D4B8F0;font:10px 'Segoe UI';background:transparent;")

    # ── ações ────────────────────────────
    def _gerar(self):
        dur_texto = self.combo.currentText()
        minutos   = DURACOES[dur_texto]
        key = gerar_key(minutos)
        self.txt_key.setPlainText(key)
        exp = datetime.now(tz=timezone.utc) + timedelta(minutes=minutos)
        self.lbl_result.setText(f"✓  Gerada  |  expira {exp.strftime('%d/%m/%Y %H:%M')} UTC")
        self.lbl_result.setStyleSheet("color:#10B981;font:11px 'Segoe UI';background:transparent;")

    def _copiar(self):
        key = self.txt_key.toPlainText().strip()
        if not key:
            return
        QApplication.clipboard().setText(key)
        self.btn_copy.setText("✅  Copiado!")
        QTimer.singleShot(1500, lambda: self.btn_copy.setText("📋  Copiar Key"))

    def _verificar(self):
        key = self.entry_check.text().strip()
        if not key:
            return
        ok, msg = validar_key(key)
        color = "#10B981" if ok else "#EF4444"
        icon  = "✓" if ok else "✗"
        self.lbl_result.setText(f"{icon}  {msg}")
        self.lbl_result.setStyleSheet(f"color:{color};font:11px 'Segoe UI';background:transparent;")

    # ── drag ─────────────────────────────
    def mousePressEvent(self, e):
        if e.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = e.globalPosition().toPoint() - self.frameGeometry().topLeft()

    def mouseMoveEvent(self, e):
        if self._drag_pos and e.buttons() == Qt.MouseButton.LeftButton:
            self.move(e.globalPosition().toPoint() - self._drag_pos)

    def mouseReleaseEvent(self, _):
        self._drag_pos = None


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    win = GenWindow()
    win.show()
    sys.exit(app.exec())