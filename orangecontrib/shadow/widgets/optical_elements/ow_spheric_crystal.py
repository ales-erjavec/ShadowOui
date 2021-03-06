import sys
import Orange

from Orange.widgets import gui
from PyQt4.QtGui import QApplication

from orangecontrib.shadow.widgets.gui import ow_spheric_element, ow_optical_element
from orangecontrib.shadow.util import ShadowOpticalElement


class SphericCrystal(ow_spheric_element.SphericElement):

    name = "Spherical Crystal"
    description = "Shadow OE: Spherical Crystal"
    icon = "icons/spherical_crystal.png"
    # icon = "icons/cristal_courbe_2.png"
    maintainer = "Luca Rebuffi"
    maintainer_email = "luca.rebuffi(@at@)elettra.eu"
    priority = 10
    category = "Optical Elements"
    keywords = ["data", "file", "load", "read"]

    def __init__(self):
        graphical_Options=ow_optical_element.GraphicalOptions(is_crystal=True)

        super().__init__(graphical_Options)

        gui.rubber(self.controlArea)

        gui.rubber(self.mainArea)

    def instantiateShadowOE(self):
        return ShadowOpticalElement.create_spherical_crystal()

if __name__ == "__main__":
    a = QApplication(sys.argv)
    ow = SphericCrystal()
    ow.show()
    a.exec_()
    ow.saveSettings()