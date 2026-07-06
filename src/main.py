import sys

from PyQt6.QtCore import QLocale
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QApplication

from viewmodel import *
from views import *

def main():
    
    base_path = pathlib.Path(__file__).parent
    if not getattr(sys, 'frozen', False):
        base_path = base_path.parent

    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon(str(base_path / 'resources/icon.png')))
    
    try:
        language_code = QLocale.system().name().split('_')[0]
    except:
        language_code = 'en'
    
    viewmodel = ViewModel(language_code)
    gpx_window = GPXView(viewmodel)
    gpx_window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    
    main()
