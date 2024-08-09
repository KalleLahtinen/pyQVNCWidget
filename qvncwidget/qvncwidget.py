"""
Qt Widget for displaying VNC framebuffer using RFB protocol

(c) zocker-160 2024
licensed under GPLv3
"""

import logging
import time

from PySide6.QtCore import (
    QSize,
    Qt,
    Signal as pyqtSignal,
    QSemaphore
)
from PySide6.QtGui import (
    QImage,
    QPaintEvent,
    QPainter,
    QColor,
    QBrush,
    QPixmap,
    QResizeEvent,
    QKeyEvent,
    QMouseEvent
)

from PySide6.QtWidgets import (
    QWidget,
    QLabel
)

from PySide6.QtOpenGLWidgets import QOpenGLWidget

from qvncwidget.rfb import RFBClient
from qvncwidget.rfbhelpers import RFBPixelformat, RFBInput

log = logging.getLogger("QVNCWidget")

class QVNCWidget(QWidget):

    onInitialResize = pyqtSignal(QSize)

    def __init__(self, parent: QWidget,
                 host: str, port = 5900, password: str = None,
                 readOnly = False):
        
        super().__init__(parent)
        self.rfb_client = RFBClient(self, host=host, port=port, password=password)

        self.readOnly = readOnly

        self.backbuffer: QImage = None
        self.frontbuffer: QImage = None

        self.setMouseTracking(not self.readOnly)
        self.setMinimumSize(1, 1) # make window scalable

        self.mouseButtonMask = 0

    def start(self):
        self.rfb_client.startConnection()

    def stop(self):
        self.rfb_client.closeConnection()

    def onConnectionMade(self):
        log.info("VNC handshake done")

        self.rfb_client.setPixelFormat(RFBPixelformat.getRGB32())

        self.PIX_FORMAT = QImage.Format.Format_RGB32
        self.backbuffer = QImage(self.rfb_client._vncWidth, self.rfb_client._vncHeight, self.PIX_FORMAT)
        self.onInitialResize.emit(QSize(self.rfb_client._vncWidth, self.rfb_client._vncHeight))

    def onRectangleUpdate(self,
            x: int, y: int, width: int, height: int, data: bytes):

        if self.backbuffer is None:
            log.warning("backbuffer is None")
            return
        else:
            log.debug("drawing backbuffer")

        #with open(f"{width}x{height}.data", "wb") as f:
        #    f.write(data)

        t1 = time.time()

        painter = QPainter(self.backbuffer)
        painter.drawImage(x, y, QImage(data, width, height, self.PIX_FORMAT))
        painter.end()

        log.debug(f"painting took: {(time.time() - t1)*1e3} ms")

        del painter
        del data

    def onFramebufferUpdateFinished(self):
        log.debug("FB Update finished")
        self.update()

    def paintEvent(self, a0: QPaintEvent):
        #log.debug("Paint event")
        painter = QPainter(self)

        if self.backbuffer is None:
            log.debug("backbuffer is None")
            painter.fillRect(0, 0, self.width(), self.height(), Qt.GlobalColor.black)

        else:
            self.frontbuffer = self.backbuffer.scaled(
                    self.width(), self.height(),
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation
                )
            painter.drawImage(0, 0, self.frontbuffer)

        painter.end()

    # Mouse events

    def mousePressEvent(self, ev: QMouseEvent):
        if self.readOnly or not self.frontbuffer: return
        self.mouseButtonMask = RFBInput.fromQMouseEvent(ev, True, self.mouseButtonMask)
        self.pointerEvent(*self._getRemoteRel(ev), self.mouseButtonMask)

    def mouseReleaseEvent(self, ev: QMouseEvent):
        if self.readOnly or not self.frontbuffer: return
        self.mouseButtonMask = RFBInput.fromQMouseEvent(ev, False, self.mouseButtonMask)
        self.pointerEvent(*self._getRemoteRel(ev), self.mouseButtonMask)

    def mouseMoveEvent(self, ev: QMouseEvent):
        if self.readOnly or not self.frontbuffer: return
        self.pointerEvent(*self._getRemoteRel(ev), self.mouseButtonMask)

    def _getRemoteRel(self, ev: QMouseEvent) -> tuple:
        xPos = (ev.localPos().x() / self.frontbuffer.width()) * self.vncWidth
        yPos = (ev.localPos().y() / self.frontbuffer.height()) * self.vncHeight

        return int(xPos), int(yPos)

    # Key events

    def keyPressEvent(self, ev: QKeyEvent):
        if self.readOnly: return
        self.keyEvent(RFBInput.fromQKeyEvent(ev.key(), ev.text()), down=1)

    def keyReleaseEvent(self, ev: QKeyEvent):
        if self.readOnly: return
        self.keyEvent(RFBInput.fromQKeyEvent(ev.key(), ev.text()), down=0)