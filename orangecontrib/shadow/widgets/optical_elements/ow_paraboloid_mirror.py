import sys
from numpy import array
import Orange

from Orange.widgets import gui
from PyQt4.QtGui import QApplication

from orangecontrib.shadow.widgets.gui import ow_paraboloid_element, ow_optical_element
from orangecontrib.shadow.util import ShadowOpticalElement


class ParaboloidMirror(ow_paraboloid_element.ParaboloidElement):

    name = "Paraboloid Mirror"
    description = "Shadow OE: Paraboloid Mirror"
    icon = "icons/paraboloid_mirror.png"
    maintainer = "Luca Rebuffi"
    maintainer_email = "luca.rebuffi(@at@)elettra.eu"
    priority = 5
    category = "Optical Elements"
    keywords = ["data", "file", "load", "read"]

    def __init__(self):
        graphical_Options=ow_optical_element.GraphicalOptions(is_mirror=True)

        super().__init__(graphical_Options)

        gui.rubber(self.controlArea)

        gui.rubber(self.mainArea)

    ################################################################
    #
    #  SHADOW MANAGEMENT
    #
    ################################################################

    def instantiateShadowOE(self):
        return ShadowOpticalElement.create_paraboloid_mirror()

if __name__ == "__main__":
    a = QApplication(sys.argv)
    ow = ParaboloidMirror()
    ow.show()
    a.exec_()
    ow.saveSettings()