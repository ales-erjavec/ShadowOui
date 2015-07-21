import sys
from orangewidget import gui
from PyQt4.QtGui import QApplication

from orangecontrib.shadow.widgets.gui import ow_optical_element
from orangecontrib.shadow.util import ShadowOpticalElement


class EmptyElement(ow_optical_element.OpticalElement):

    name = "Empty Element"
    description = "Shadow OE: Empty Element"
    icon = "icons/empty_element.png"
    maintainer = "Luca Rebuffi"
    maintainer_email = "luca.rebuffi(@at@)elettra.eu"
    priority = 23
    category = "Optical Elements"
    keywords = ["data", "file", "load", "read"]

    def __init__(self):
        graphical_Options=ow_optical_element.GraphicalOptions(is_empty=True)

        super().__init__(graphical_Options)

        gui.rubber(self.controlArea)

        gui.rubber(self.mainArea)

    ################################################################
    #
    #  SHADOW MANAGEMENT
    #
    ################################################################

    def instantiateShadowOE(self):
        return ShadowOpticalElement.create_empty_oe()

if __name__ == "__main__":
    a = QApplication(sys.argv)
    ow = EmptyElement()
    ow.show()
    a.exec_()
    ow.saveSettings()