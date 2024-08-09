#! /usr/bin/env python3

import sys
import logging

from PySide6.QtWidgets import QApplication, QMainWindow
from PySide6.QtGui import QKeyEvent
from qvncwidget.qvncwidget import QVNCWidget

log = logging.getLogger("testing")

class Window(QMainWindow):
    def __init__(self, app: QApplication):
        super(Window, self).__init__()

        self.app = app
        self.initUI()

    def initUI(self):
        self.setWindowTitle("QVNCWidget")

        self.vnc = QVNCWidget(
            parent=self,
            host="127.0.0.1", port=5900,
            password="1234",
            readOnly=True
        )
        
        self.setCentralWidget(self.vnc)
        #self.vnc.setFocus()
        #self.vnc.onInitialResize.connect(self.resize)
        self.vnc.start()

    def keyPressEvent(self, ev: QKeyEvent):
        #print(ev.nativeScanCode(), ev.text(), ord(ev.text()), ev.key())
        self.vnc.keyPressEvent(ev)

    def keyReleaseEvent(self, ev: QKeyEvent):
        #print(ev.nativeScanCode(), ev.text(), ord(ev.text()), ev.key())
        self.vnc.keyReleaseEvent(ev)

    def closeEvent(self, ev):
        self.vnc.stop()
        return super().closeEvent(ev)

    def center(self):
        qr = self.frameGeometry()
        cp = self.app.primaryScreen().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())


logging.basicConfig(
    format="[%(name)s] %(levelname)s: %(message)s", level=logging.DEBUG
)

app = QApplication(sys.argv)
window = Window(app)
#window.setFixedSize(800, 600)
window.resize(800, 600)
window.center()
window.show()

sys.exit(app.exec_())
