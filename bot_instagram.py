"""
Instagram Bot — Liquid Glass UI
Dependências: pip install PyQt6 instagrapi pyperclip keyboard
"""

import sys, threading, random, time, math
import hashlib, hmac, os, json, base64
import pyperclip, keyboard
from instagrapi import Client
from datetime import datetime, timezone

from PyQt6.QtWidgets import (
    QApplication, QWidget, QLabel, QLineEdit,
    QPushButton, QTextEdit, QFrame
)
from PyQt6.QtCore import Qt, QTimer, QPoint, pyqtSignal, QObject
from PyQt6.QtGui import (
    QPainter, QColor, QLinearGradient, QRadialGradient,
    QPen, QBrush, QFont, QPainterPath, QConicalGradient,
    QPixmap, QRegion
)

# ══════════════════════════════════════════
#  SIGNALS (thread-safe comunicação → UI)
# ══════════════════════════════════════════
class BotSignals(QObject):
    log    = pyqtSignal(str)
    status = pyqtSignal(str, str)

signals = BotSignals()


# ══════════════════════════════════════════
#  KEY AUTH SYSTEM
# ══════════════════════════════════════════
_SECRET = b"SEU_SECRET_AQUI"

# ══════════════════════════════════════════
#  CONTROLE DO SISTEMA DE KEY
#  True  = exige key (versão para clientes)
#  False = abre direto (versão pessoal)
# ══════════════════════════════════════════
KEY_AUTH_ATIVO = False

def _key_valida(key: str) -> tuple[bool, str]:
    """Valida a key e retorna (ok, mensagem)."""
    try:
        raw = base64.b64decode(key.strip().encode())
        payload, sig = raw[:-32], raw[-32:]
        expected = hmac.new(_SECRET, payload, hashlib.sha256).digest()
        if not hmac.compare_digest(sig, expected):
            return False, "Key inválida"
        data = json.loads(payload.decode())
        exp = datetime.fromtimestamp(data["exp"], tz=timezone.utc)
        now = datetime.now(tz=timezone.utc)
        if now > exp:
            diff = now - exp
            return False, f"Key expirada há {int(diff.total_seconds()//60)} min"
        restante = exp - now
        mins = int(restante.total_seconds() // 60)
        secs = int(restante.total_seconds() % 60)
        return True, f"✓ Válida por {mins}min {secs}s"
    except Exception as e:
        return False, "Key corrompida"

def _tempo_restante(key: str) -> int:
    """Retorna segundos restantes ou 0 se expirada."""
    try:
        raw = base64.b64decode(key.strip().encode())
        payload = raw[:-32]
        data = json.loads(payload.decode())
        exp = datetime.fromtimestamp(data["exp"], tz=timezone.utc)
        diff = exp - datetime.now(tz=timezone.utc)
        return max(0, int(diff.total_seconds()))
    except:
        return 0

# ── Tela de Login ─────────────────────────
class LoginWindow(QWidget):
    auth_ok = pyqtSignal(str)  # emite a key válida

    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedSize(360, 420)
        sg = QApplication.primaryScreen().geometry()
        self.move((sg.width()-360)//2, (sg.height()-420)//2)
        self._drag_pos = None
        self._build()

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        # fundo
        path = QPainterPath()
        path.addRoundedRect(0, 0, 360, 420, 40, 40)
        p.setClipPath(path)
        g = QLinearGradient(0, 0, 0, 420)
        g.setColorAt(0.0, QColor("#FDF6FF"))
        g.setColorAt(1.0, QColor("#F0E8FF"))
        p.fillPath(path, QBrush(g))
        p.setClipping(False)
        p.setPen(QPen(QColor("#DCC8F0"), 1.5))
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawPath(path)

    def _build(self):
        # fechar
        btn_x = QPushButton("✕", self)
        btn_x.setGeometry(312, 14, 28, 28)
        btn_x.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_x.clicked.connect(self.close)
        btn_x.setStyleSheet("""
            QPushButton{background:#FFD0D0;color:#C0392B;border-radius:14px;
                        font:bold 11px 'Segoe UI';border:none;}
            QPushButton:hover{background:#FFB3B3;}
        """)

        # ícone de cadeado
        lbl_lock = QLabel("🔐", self)
        lbl_lock.setGeometry(0, 52, 360, 60)
        lbl_lock.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        lbl_lock.setStyleSheet("font:52px;background:transparent;")

        # título
        lbl_title = QLabel("Acesso Restrito", self)
        lbl_title.setGeometry(0, 118, 360, 32)
        lbl_title.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        lbl_title.setStyleSheet("color:#1A0533;font:bold 20px 'Segoe UI';background:transparent;")

        lbl_sub = QLabel("Insira sua chave de acesso para continuar", self)
        lbl_sub.setGeometry(0, 152, 360, 20)
        lbl_sub.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        lbl_sub.setStyleSheet("color:#A78BCA;font:11px 'Segoe UI';background:transparent;")

        # label KEY
        lbl_k = QLabel("CHAVE DE ACESSO", self)
        lbl_k.setGeometry(32, 192, 200, 14)
        lbl_k.setStyleSheet("color:#C4B5D4;font:bold 10px 'Segoe UI';letter-spacing:1px;background:transparent;")

        # input key
        self.entry_key = QLineEdit(self)
        self.entry_key.setPlaceholderText("Cole sua key aqui...")
        self.entry_key.setGeometry(32, 210, 296, 48)
        self.entry_key.setStyleSheet("""
            QLineEdit{background:#F5F0FF;border:1.5px solid #DCC8F0;border-radius:16px;
                      padding:0 16px;font:11px 'Consolas';color:#3B0A6E;}
            QLineEdit:focus{border:1.5px solid #A855F7;}
        """)
        self.entry_key.returnPressed.connect(self._verificar)

        # botão entrar
        self.btn_enter = QPushButton("🔓  Entrar", self)
        self.btn_enter.setGeometry(32, 272, 296, 50)
        self.btn_enter.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_enter.clicked.connect(self._verificar)
        self.btn_enter.setStyleSheet("""
            QPushButton{background:qlineargradient(x1:0,y1:0,x2:1,y2:1,
                          stop:0 #A855F7,stop:0.5 #7C3AED,stop:1 #6D28D9);
                        color:white;border-radius:18px;font:bold 14px 'Segoe UI';border:none;}
            QPushButton:hover{background:qlineargradient(x1:0,y1:0,x2:1,y2:1,
                          stop:0 #9333EA,stop:1 #6D28D9);}
            QPushButton:pressed{padding-top:2px;}
        """)

        # mensagem de status
        self.lbl_msg = QLabel("", self)
        self.lbl_msg.setGeometry(32, 332, 296, 20)
        self.lbl_msg.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        self.lbl_msg.setStyleSheet("font:11px 'Segoe UI';background:transparent;")

        # rodapé
        lbl_ft = QLabel("Não tem uma key? Entre em contato com o desenvolvedor", self)
        lbl_ft.setGeometry(0, 382, 360, 30)
        lbl_ft.setAlignment(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter)
        lbl_ft.setWordWrap(True)
        lbl_ft.setStyleSheet("color:#C4B5D4;font:10px 'Segoe UI';background:transparent;")

    def _verificar(self):
        key = self.entry_key.text().strip()
        if not key:
            self._msg("⚠  Cole uma key válida", "#EF4444"); return
        ok, msg = _key_valida(key)
        if ok:
            self._msg(msg, "#10B981")
            QTimer.singleShot(600, lambda: (self.auth_ok.emit(key), self.close()))
        else:
            self._msg(f"✗  {msg}", "#EF4444")
            self.entry_key.setStyleSheet("""
                QLineEdit{background:#FFF0F0;border:1.5px solid #EF4444;border-radius:16px;
                          padding:0 16px;font:11px 'Consolas';color:#3B0A6E;}
            """)

    def _msg(self, text, color):
        self.lbl_msg.setText(text)
        self.lbl_msg.setStyleSheet(f"color:{color};font:11px 'Segoe UI';background:transparent;")

    def mousePressEvent(self, e):
        if e.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = e.globalPosition().toPoint() - self.frameGeometry().topLeft()

    def mouseMoveEvent(self, e):
        if self._drag_pos and e.buttons() == Qt.MouseButton.LeftButton:
            self.move(e.globalPosition().toPoint() - self._drag_pos)

    def mouseReleaseEvent(self, _):
        self._drag_pos = None

# ══════════════════════════════════════════
#  FUNDO — gradiente + blobs animados
# ══════════════════════════════════════════
class Background(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_NoSystemBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_OpaquePaintEvent)
        self._phase = 0.0
        t = QTimer(self)
        t.timeout.connect(self._tick)
        t.start(30)

    def _tick(self):
        self._phase += 0.018
        self.update()

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()

        # Recorta nos cantos arredondados
        clip = QPainterPath()
        clip.addRoundedRect(0, 0, w, h, 44, 44)
        p.setClipPath(clip)

        g = QLinearGradient(0, 0, 0, h)
        g.setColorAt(0.00, QColor("#FDF6FF"))
        g.setColorAt(0.35, QColor("#F5EEFF"))
        g.setColorAt(0.70, QColor("#FFF0F8"))
        g.setColorAt(1.00, QColor("#FFFFFF"))
        p.fillRect(0, 0, w, h, g)

        ph = self._phase
        blobs = [
            (w*0.12 + math.sin(ph*0.7)*18,  h*0.12 + math.cos(ph*0.5)*12,  160, "#E9D5FF", 60),
            (w*0.88 + math.sin(ph*0.9)*14,  h*0.22 + math.cos(ph*0.6)*10,  130, "#FBCFE8", 55),
            (w*0.10 + math.sin(ph*0.6)*16,  h*0.80 + math.cos(ph*0.8)*14,  140, "#DDD6FE", 55),
            (w*0.85 + math.sin(ph*0.8)*12,  h*0.82 + math.cos(ph*0.7)*10,  110, "#FCE7F3", 50),
        ]
        for bx, by, br, col, alpha in blobs:
            rg = QRadialGradient(bx, by, br)
            c  = QColor(col); c.setAlpha(alpha)
            c2 = QColor(col); c2.setAlpha(0)
            rg.setColorAt(0, c); rg.setColorAt(1, c2)
            p.setBrush(QBrush(rg))
            p.setPen(Qt.PenStyle.NoPen)
            p.drawEllipse(int(bx-br), int(by-br), br*2, br*2)

# ══════════════════════════════════════════
#  ORB — Bola de Vidro com Buraco Negro
# ══════════════════════════════════════════
class OrbWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(140, 140)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self._angle   = 0.0    # rotação do disco de acreção
        self._pulse   = 0.0    # pulsação do núcleo
        self._shimmer = 0.0    # brilho da esfera de vidro
        t = QTimer(self); t.timeout.connect(self._tick); t.start(16)

    def _tick(self):
        self._angle   = (self._angle + 1.8) % 360
        self._pulse  += 0.04
        self._shimmer = (self._shimmer + 0.02) % (2 * math.pi)
        self.update()

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        cx = cy = 70
        R = 58   # raio da esfera

        # ── 1. fundo escuro da esfera (universo) ──────────────────
        clip = QPainterPath()
        clip.addEllipse(cx - R, cy - R, R * 2, R * 2)
        p.setClipPath(clip)

        bg = QRadialGradient(cx, cy - 10, R)
        bg.setColorAt(0.00, QColor("#1a0040"))
        bg.setColorAt(0.35, QColor("#0d001a"))
        bg.setColorAt(0.70, QColor("#08000f"))
        bg.setColorAt(1.00, QColor("#000000"))
        p.fillRect(cx - R, cy - R, R * 2, R * 2, bg)

        # ── 2. estrelinhas de fundo ───────────────────────────────
        import random as _rnd
        rng = _rnd.Random(42)
        p.setPen(Qt.PenStyle.NoPen)
        for _ in range(28):
            sx = cx - R + rng.randint(4, R * 2 - 4)
            sy = cy - R + rng.randint(4, R * 2 - 4)
            alpha = rng.randint(80, 220)
            sr = rng.uniform(0.6, 1.4)
            sc = QColor(255, 255, 255, alpha)
            p.setBrush(sc)
            p.drawEllipse(int(sx - sr), int(sy - sr), int(sr * 2), int(sr * 2))

        # ── 3. disco de acreção (anéis giratórios) ────────────────
        p.save()
        p.translate(cx, cy)
        p.rotate(self._angle)

        disk_colors = [
            ("#FF4ECD", 38, 6, 160),  # rosa externo
            ("#A855F7", 30, 5, 180),  # roxo
            ("#7C3AED", 24, 4, 200),  # violeta
            ("#FF6B35", 19, 3, 160),  # laranja
            ("#FFD700", 15, 2, 140),  # dourado interno
        ]
        for col, radius, thickness, alpha in disk_colors:
            c = QColor(col); c.setAlpha(alpha)
            pen = QPen(c, thickness)
            pen.setCapStyle(Qt.PenCapStyle.RoundCap)
            # elipse achatada para efeito de perspectiva
            p.setPen(pen)
            p.setBrush(Qt.BrushStyle.NoBrush)
            p.drawEllipse(-radius, -int(radius * 0.35),
                          radius * 2, int(radius * 0.35 * 2))

        # segundo disco contra-rotação (mais lento)
        p.restore()
        p.save()
        p.translate(cx, cy)
        p.rotate(-self._angle * 0.6)
        for col, radius, thickness, alpha in [
            ("#22D3EE", 42, 3, 100),
            ("#818CF8", 46, 2, 70),
        ]:
            c = QColor(col); c.setAlpha(alpha)
            p.setPen(QPen(c, thickness))
            p.setBrush(Qt.BrushStyle.NoBrush)
            p.drawEllipse(-radius, -int(radius * 0.28),
                          radius * 2, int(radius * 0.28 * 2))
        p.restore()

        # ── 4. núcleo — buraco negro ──────────────────────────────
        pulse_r = 2.0 * math.sin(self._pulse)
        hole_r  = int(11 + pulse_r)

        # aura de Hawking (brilho ao redor do núcleo)
        for ar, aa in [(hole_r + 9, 30), (hole_r + 6, 60), (hole_r + 3, 100)]:
            aura = QRadialGradient(cx, cy, ar)
            aura.setColorAt(0.0, QColor(180, 80, 255, aa))
            aura.setColorAt(1.0, QColor(0, 0, 0, 0))
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(QBrush(aura))
            p.drawEllipse(cx - ar, cy - ar, ar * 2, ar * 2)

        # núcleo preto absoluto
        p.setBrush(QColor(0, 0, 0))
        p.setPen(Qt.PenStyle.NoPen)
        p.drawEllipse(cx - hole_r, cy - hole_r, hole_r * 2, hole_r * 2)

        # ── 5. esfera de vidro por cima ───────────────────────────
        p.setClipping(False)

        # borda sutil com gradiente
        rim = QRadialGradient(cx - 18, cy - 22, R * 1.1)
        rim.setColorAt(0.75, QColor(255, 255, 255, 0))
        rim.setColorAt(0.88, QColor(180, 140, 255, 50))
        rim.setColorAt(1.00, QColor(120, 80, 220, 130))
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QBrush(rim))
        p.drawEllipse(cx - R, cy - R, R * 2, R * 2)

        # reflexo principal (canto superior esquerdo)
        shimmer_a = int(160 + 40 * math.sin(self._shimmer))
        hl = QRadialGradient(cx - 22, cy - 26, 26)
        hl.setColorAt(0.0, QColor(255, 255, 255, shimmer_a))
        hl.setColorAt(0.5, QColor(220, 200, 255, 60))
        hl.setColorAt(1.0, QColor(255, 255, 255, 0))
        p.setBrush(QBrush(hl))
        p.drawEllipse(cx - 46, cy - 50, 48, 34)

        # reflexo secundário (canto inferior direito)
        hl2 = QRadialGradient(cx + 24, cy + 28, 16)
        hl2.setColorAt(0.0, QColor(255, 255, 255, 50))
        hl2.setColorAt(1.0, QColor(255, 255, 255, 0))
        p.setBrush(QBrush(hl2))
        p.drawEllipse(cx + 10, cy + 16, 28, 20)

        # anel externo de vidro (borda fosca)
        pen_rim = QPen(QColor(200, 170, 255, 80), 2.5)
        p.setPen(pen_rim)
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawEllipse(cx - R, cy - R, R * 2, R * 2)

# ══════════════════════════════════════════
#  GLASS CARD
# ══════════════════════════════════════════
class GlassCard(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        path = QPainterPath()
        path.addRoundedRect(0, 0, self.width(), self.height(), 28, 28)
        p.setClipPath(path)
        p.fillPath(path, QColor(255, 255, 255, 210))
        p.setClipping(False)
        p.setPen(QPen(QColor("#DCC8F0"), 1.2))
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawPath(path)

# ══════════════════════════════════════════
#  STATUS PILL animado
# ══════════════════════════════════════════
class StatusPill(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(36)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self._dot_color = QColor("#D4B8F0")
        self._txt_color = QColor("#9878C0")
        self._text      = "Aguardando sessão"
        self._pulse     = 0.0
        t = QTimer(self); t.timeout.connect(self._tick); t.start(40)

    def set_status(self, text, color_hex):
        self._text      = text
        self._dot_color = QColor(color_hex)
        self._txt_color = QColor(color_hex)
        self.update()

    def _tick(self):
        self._pulse = (self._pulse + 0.06) % (2 * math.pi)
        self.update()

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()
        path = QPainterPath()
        path.addRoundedRect(0, 0, w, h, 18, 18)
        p.fillPath(path, QColor("#F5F0FF"))
        p.setPen(QPen(QColor("#DCC8F0"), 1))
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawPath(path)

        pr  = 1.0 + 0.35 * math.sin(self._pulse)
        dr  = int(4 * pr)
        dc  = QColor(self._dot_color); dc.setAlpha(200)
        p.setBrush(dc); p.setPen(Qt.PenStyle.NoPen)
        p.drawEllipse(14-dr, h//2-dr, dr*2, dr*2)

        p.setPen(self._txt_color)
        p.setFont(QFont("Segoe UI", 11))
        p.drawText(30, 0, w-30, h, Qt.AlignmentFlag.AlignVCenter, self._text)

# ══════════════════════════════════════════
#  JANELA PRINCIPAL
# ══════════════════════════════════════════
WIN_W, WIN_H = 390, 720

class BotWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedSize(WIN_W, WIN_H)
        self._drag_pos = None
        sg = QApplication.primaryScreen().geometry()
        self.move((sg.width()-WIN_W)//2, (sg.height()-WIN_H)//2)
        self._build_ui()
        signals.log.connect(self._append_log)
        signals.status.connect(self.status_pill.set_status)

    def paintEvent(self, event):
        """Base transparente — o Background cuida do visual."""
        pass

    def _build_ui(self):
        # fundo animado
        self.bg = Background(self)
        self.bg.setGeometry(0, 0, WIN_W, WIN_H)

        # ── status bar ───────────────────
        self.lbl_time = QLabel(time.strftime("%H:%M"), self)
        self.lbl_time.setGeometry(28, 16, 80, 20)
        self.lbl_time.setStyleSheet("color:#1A0533;font:bold 12px 'Segoe UI';background:transparent;")
        QTimer(self).timeout.connect(lambda: self.lbl_time.setText(time.strftime("%H:%M")))
        t = QTimer(self); t.timeout.connect(lambda: self.lbl_time.setText(time.strftime("%H:%M"))); t.start(1000)

        self.lbl_sig = QLabel("🖥  Ethernet  🔌", self)
        self.lbl_sig.setGeometry(230, 16, 140, 20)
        self.lbl_sig.setStyleSheet("color:#1A0533;font:11px 'Segoe UI';background:transparent;")

        # ── fechar ───────────────────────
        self.btn_close = QPushButton("✕", self)
        self.btn_close.setGeometry(330, 10, 30, 30)
        self.btn_close.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_close.clicked.connect(self.close)
        self.btn_close.setStyleSheet("""
            QPushButton{background:#FFD0D0;color:#C0392B;border-radius:15px;
                        font:bold 12px 'Segoe UI';border:none;}
            QPushButton:hover{background:#FFB3B3;}
        """)

        # ── orb ──────────────────────────
        self.orb = OrbWidget(self)
        self.orb.move((WIN_W-140)//2, 48)

        # ── títulos ──────────────────────
        for text, y, style in [
            ("Instagram Bot",   192,
             "color:#1A0533;font:bold 22px 'Segoe UI';background:transparent;"),
            ("Automação inteligente de comentários", 226,
             "color:#A78BCA;font:12px 'Segoe UI';background:transparent;"),
        ]:
            l = QLabel(text, self)
            l.setGeometry(0, y, WIN_W, 26)
            l.setAlignment(Qt.AlignmentFlag.AlignHCenter)
            l.setStyleSheet(style)

        # ── glass card ───────────────────
        self.card = GlassCard(self)
        self.card.setGeometry(18, 260, 354, 406)

        # SESSION ID
        QLabel("SESSION  ID", self.card).setGeometry(22, 18, 200, 14)
        self.card.findChild(QLabel).setStyleSheet(
            "color:#C4B5D4;font:bold 10px 'Segoe UI';letter-spacing:1px;background:transparent;")

        # input
        self.entry = QLineEdit(self.card)
        self.entry.setPlaceholderText("Cole seu sessionid aqui...")
        self.entry.setGeometry(22, 38, 310, 48)
        self.entry.setStyleSheet("""
            QLineEdit{background:#F5F0FF;border:1.5px solid #DCC8F0;border-radius:16px;
                      padding:0 16px;font:13px 'Segoe UI';color:#3B0A6E;}
            QLineEdit:focus{border:1.5px solid #A855F7;}
        """)

        # status pill
        self.status_pill = StatusPill(self.card)
        self.status_pill.setGeometry(22, 96, 310, 36)

        # btn iniciar
        self.btn_start = QPushButton("▶   Iniciar Bot", self.card)
        self.btn_start.setGeometry(22, 144, 310, 52)
        self.btn_start.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_start.clicked.connect(self._iniciar)
        self.btn_start.setStyleSheet("""
            QPushButton{background:qlineargradient(x1:0,y1:0,x2:1,y2:1,
                          stop:0 #A855F7,stop:0.5 #7C3AED,stop:1 #6D28D9);
                        color:white;border-radius:18px;font:bold 15px 'Segoe UI';border:none;}
            QPushButton:hover{background:qlineargradient(x1:0,y1:0,x2:1,y2:1,
                          stop:0 #9333EA,stop:1 #6D28D9);}
            QPushButton:pressed{padding-top:2px;}
        """)

        # btn parar
        self.btn_stop = QPushButton("⛔   Parar", self.card)
        self.btn_stop.setGeometry(22, 208, 310, 44)
        self.btn_stop.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_stop.clicked.connect(self._parar)
        self.btn_stop.setStyleSheet("""
            QPushButton{background:#F5F0FF;color:#9333EA;border-radius:15px;
                        font:600 13px 'Segoe UI';border:1.5px solid #D8CCEF;}
            QPushButton:hover{background:#EDE9F8;}
        """)

        # divisor
        div = QFrame(self.card)
        div.setGeometry(22, 265, 310, 1)
        div.setStyleSheet("background:#EDE9F8;")

        # log labels
        lbl_log = QLabel("LOG  ·  ATIVIDADE", self.card)
        lbl_log.setGeometry(22, 275, 160, 14)
        lbl_log.setStyleSheet("color:#C4B5D4;font:bold 10px 'Segoe UI';letter-spacing:1px;background:transparent;")

        self.lbl_count = QLabel("0 eventos", self.card)
        self.lbl_count.setGeometry(240, 275, 90, 14)
        self.lbl_count.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.lbl_count.setStyleSheet("color:#D4B8F0;font:10px 'Segoe UI';background:transparent;")

        # log box
        self.log_box = QTextEdit(self.card)
        self.log_box.setGeometry(22, 295, 310, 100)
        self.log_box.setReadOnly(True)
        self.log_box.setStyleSheet("""
            QTextEdit{background:#FAF8FF;border:1px solid #EDE9F8;border-radius:16px;
                      padding:8px 12px;font:11px 'Consolas';color:#6D28D9;}
            QScrollBar:vertical{width:4px;background:transparent;}
            QScrollBar::handle:vertical{background:#DDD6FE;border-radius:2px;}
            QScrollBar::add-line:vertical,QScrollBar::sub-line:vertical{height:0;}
        """)

        # footer
        lbl_ft = QLabel("Feito com ❤️  ·  GitHub", self)
        lbl_ft.setGeometry(0, 696, WIN_W, 18)
        lbl_ft.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        lbl_ft.setStyleSheet("color:#C4B5D4;font:11px 'Segoe UI';background:transparent;")

    # ── log ──────────────────────────────
    _log_total = 0

    def _append_log(self, msg):
        self._log_total += 1
        ts = time.strftime("%H:%M:%S")
        self.log_box.append(
            f'<span style="color:#C4B5D4">[{ts}]</span>'
            f'<span style="color:#6D28D9">&nbsp;&nbsp;{msg}</span>')
        self.lbl_count.setText(f"{self._log_total} eventos")

    # ── drag ─────────────────────────────
    def mousePressEvent(self, e):
        if e.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = e.globalPosition().toPoint() - self.frameGeometry().topLeft()

    def mouseMoveEvent(self, e):
        if self._drag_pos and e.buttons() == Qt.MouseButton.LeftButton:
            self.move(e.globalPosition().toPoint() - self._drag_pos)

    def mouseReleaseEvent(self, _):
        self._drag_pos = None

    # ── bot ──────────────────────────────
    _rodando  = False
    _usuarios = []
    _indice   = 0

    def _iniciar(self):
        sid = self.entry.text().strip()
        if not sid:
            signals.log.emit("⚠  Insira o Session ID")
            signals.status.emit("Session ID ausente", "#EF4444")
            return
        if self._rodando:
            signals.log.emit("⚠  Já está em execução"); return
        self._rodando = True
        signals.status.emit("Iniciando...", "#F59E0B")
        signals.log.emit("▶  Bot iniciado")
        threading.Thread(target=self._rodar_bot, args=(sid,), daemon=True).start()

    def _parar(self):
        self._rodando = False
        signals.status.emit("Parado pelo usuário", "#8B8BA0")
        signals.log.emit("⛔  Bot interrompido")

    def _gerar_comentario(self):
        if self._indice >= len(self._usuarios): return None
        sel = self._usuarios[self._indice:self._indice+2]
        self._indice += 2
        return " ".join(f"@{u}" for u in sel) + " olha isso 😂"

    def _rodar_bot(self, sid):
        try:
            cl = Client(); cl.delay_range = [1,3]
            cl.login_by_sessionid(sid)
            signals.log.emit("✓  Logado com sucesso")
            signals.status.emit("Carregando seguidores...", "#F59E0B")
            seg = cl.user_followers(cl.user_id, amount=100)
            self._usuarios = [u.username for u in seg.values()]
            random.shuffle(self._usuarios)
            self._usuarios = self._usuarios[:100]
            signals.log.emit(f"✓  {len(self._usuarios)} usuários prontos")
            signals.status.emit(f"Ativo · {len(self._usuarios)} usuários", "#10B981")
            self._indice = 0
            while self._rodando:
                c = self._gerar_comentario()
                if not c:
                    signals.log.emit("✓  Concluído"); signals.status.emit("Concluído","#10B981"); break
                pyperclip.copy(c); time.sleep(1)
                keyboard.press_and_release("ctrl+v"); time.sleep(1)
                keyboard.press_and_release("enter")
                signals.log.emit(f"→  {c}")
                time.sleep(random.uniform(8,15))
            self._rodando = False
            signals.status.emit("Parado","#8B8BA0")
        except Exception as e:
            signals.log.emit(f"✗  Erro: {e}")
            signals.status.emit("Erro","#EF4444")
            self._rodando = False

# ══════════════════════════════════════════
# Timer de expiração em tempo real na janela principal
class KeyCountdown(QObject):
    tick = pyqtSignal(int)   # segundos restantes
    expired = pyqtSignal()

    def __init__(self, key):
        super().__init__()
        self._key = key
        t = QTimer(self)
        t.timeout.connect(self._check)
        t.start(1000)

    def _check(self):
        secs = _tempo_restante(self._key)
        self.tick.emit(secs)
        if secs == 0:
            self.expired.emit()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    if KEY_AUTH_ATIVO:
        # ── Modo cliente: exige key ───────────────
        def _abrir_bot(key):
            global _countdown, _bot_win
            _bot_win = BotWindow()

            _bot_win.lbl_key_timer = QLabel("⏱ --:--", _bot_win)
            _bot_win.lbl_key_timer.setGeometry(0, 696, WIN_W, 18)
            _bot_win.lbl_key_timer.setAlignment(Qt.AlignmentFlag.AlignHCenter)
            _bot_win.lbl_key_timer.setStyleSheet("color:#A855F7;font:bold 10px 'Segoe UI';background:transparent;")

            _countdown = KeyCountdown(key)

            def _update_timer(secs):
                mins = secs // 60
                s    = secs % 60
                _bot_win.lbl_key_timer.setText(f"⏱ Key expira em {mins:02d}:{s:02d}")
                if secs <= 60:
                    _bot_win.lbl_key_timer.setStyleSheet(
                        "color:#EF4444;font:bold 10px 'Segoe UI';background:transparent;")

            def _expirou():
                signals.status.emit("Key expirada!", "#EF4444")
                signals.log.emit("✗  Key expirada — feche e adquira uma nova")
                _bot_win.lbl_key_timer.setText("✗ Key expirada")
                _bot_win.lbl_key_timer.setStyleSheet(
                    "color:#EF4444;font:bold 10px 'Segoe UI';background:transparent;")
                _bot_win._rodando = False
                _bot_win.btn_start.setEnabled(False)
                _bot_win.btn_start.setStyleSheet(
                    "QPushButton{background:#D1C4E9;color:#9E9E9E;border-radius:18px;"
                    "font:bold 15px 'Segoe UI';border:none;}")

            _countdown.tick.connect(_update_timer)
            _countdown.expired.connect(_expirou)
            _bot_win.show()
            signals.log.emit("Sistema pronto")

        login = LoginWindow()
        login.auth_ok.connect(_abrir_bot)
        login.show()

    else:
        # ── Modo pessoal: abre direto ─────────────
        win = BotWindow()
        win.show()
        signals.log.emit("Sistema pronto")

    sys.exit(app.exec())