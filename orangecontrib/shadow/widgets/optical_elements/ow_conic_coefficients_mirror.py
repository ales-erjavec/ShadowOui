import sys
from Orange.widgets import gui
from PyQt4.QtGui import QApplication

from orangecontrib.shadow.widgets.gui import ow_conic_coefficients_element, ow_optical_element
from orangecontrib.shadow.util import ShadowOpticalElement


class ConicCoefficientsMirror(ow_conic_coefficients_element.ConicCoefficientsElement):

    name = "Conic Coefficients Mirror"
    description = "Shadow OE: Conic Coefficients Mirror"
    icon = "icons/conic_coefficients_mirror.png"
    maintainer = "Luca Rebuffi"
    maintainer_email = "luca.rebuffi(@at@)elettra.eu"
    priority = 8
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
        return ShadowOpticalElement.create_conic_coefficients_mirror()

if __name__ == "__main__":
    a = QApplication(sys.argv)
    ow = ConicCoefficientsMirror()
    ow.show()
    a.exec_()
    ow.saveSettings()