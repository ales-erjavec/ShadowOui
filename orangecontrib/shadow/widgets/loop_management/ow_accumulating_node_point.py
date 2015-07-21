import sys, numpy, copy

from orangewidget import gui
from orangewidget.settings import Setting

from PyQt4 import QtGui
from PyQt4.QtGui import QPalette, QColor, QFont

from orangecontrib.shadow.widgets.gui.ow_automatic_element import AutomaticElement
from orangecontrib.shadow.util.shadow_util import ShadowGui, ConfirmDialog
from orangecontrib.shadow.util.shadow_objects import ShadowBeam, ShadowTriggerIn


class AccumulatingLoopPoint(AutomaticElement):
    name = "Beam Accumulating Point"
    description = "User Defined: Beam Accumulating Point"
    icon = "icons/beam_accumulating.png"
    maintainer = "Luca Rebuffi"
    maintainer_email = "luca.rebuffi(@at@)elettra.eu"
    priority = 3
    category = "User Defined"
    keywords = ["data", "file", "load", "read"]

    inputs = [("Input Beam", ShadowBeam, "setBeam")]

    outputs = [{"name": "Accumulated Beam",
                "type": ShadowBeam,
                "doc": "Shadow Beam",
                "id": "beam"},
               {"name": "Trigger",
                "type": ShadowTriggerIn,
                "doc": "Feedback signal to start a new beam simulation",
                "id": "Trigger"}]

    input_beam = None

    want_main_area = 0

    number_of_accumulated_rays = Setting(10)
    current_number_of_rays = 0
    keep_go_rays = Setting(1)

    #################################
    process_last = True
    #################################

    def __init__(self):
        super().__init__()

        self.setFixedWidth(500)
        self.setFixedHeight(300)

        left_box_1 = ShadowGui.widgetBox(self.controlArea, "Accumulating Loop Management", addSpace=True, orientation="vertical", height=120)

        ShadowGui.lineEdit(left_box_1, self, "number_of_accumulated_rays", "Number of accumulated good rays\n(before sending signal)", labelWidth=350, valueType=int,
                           orientation="horizontal")

        le = ShadowGui.lineEdit(left_box_1, self, "current_number_of_rays", "Current number of good rays", labelWidth=350, valueType=int, orientation="horizontal")
        le.setReadOnly(True)
        font = QtGui.QFont(le.font())
        font.setBold(True)
        le.setFont(font)
        palette = QtGui.QPalette(le.palette())  # make a copy of the palette
        palette.setColor(QtGui.QPalette.Text, QtGui.QColor('dark blue'))
        palette.setColor(QtGui.QPalette.Base, QtGui.QColor(243, 240, 160))
        le.setPalette(palette)

        gui.comboBox(left_box_1, self, "keep_go_rays", label="Remove lost rays from beam", labelWidth=350, items=["No", "Yes"], sendSelectedValue=False, orientation="horizontal")


        button_box = gui.widgetBox(self.controlArea, "", addSpace=True, orientation="horizontal")

        self.start_button = gui.button(button_box, self, "Send Beam", callback=self.sendSignal)
        self.start_button.setFixedHeight(45)

        button = gui.button(button_box, self, "Reset Accumulation", callback=self.callResetSettings)
        font = QFont(button.font())
        font.setItalic(True)
        button.setFont(font)
        palette = QPalette(button.palette())  # make a copy of the palette
        palette.setColor(QPalette.ButtonText, QColor('Dark Red'))
        button.setPalette(palette)  # assign new palette
        button.setFixedHeight(45)

        gui.rubber(self.controlArea)

    def sendSignal(self):
        self.send("Accumulated Beam", self.input_beam)
        self.send("Trigger", ShadowTriggerIn(new_beam=True))

    def callResetSettings(self):
        if ConfirmDialog.confirmed(parent=self, message="Confirm Reset of the accumulated beam"):
            self.current_number_of_rays = 0
            self.input_beam = None

    def setBeam(self, beam):
        if ShadowGui.checkEmptyBeam(beam):
            proceed = True

            if not ShadowGui.checkGoodBeam(beam):
                if not ConfirmDialog.confirmed(parent=self, message="Beam contains bad values, skip it?"):
                    proceed = False

            if proceed:
                go = numpy.where(beam.beam.rays[:, 9] == 1)

                self.current_number_of_rays = self.current_number_of_rays + len(beam.beam.rays[go])

                if self.current_number_of_rays <= self.number_of_accumulated_rays:
                    if self.keep_go_rays == 1:
                        beam.beam.rays = copy.deepcopy(beam.beam.rays[go])

                    if not self.input_beam is None:
                        self.input_beam = ShadowBeam.mergeBeams(self.input_beam, beam)
                    else:
                        self.input_beam = beam

                    self.send("Trigger", ShadowTriggerIn(new_beam=True))
                else:
                    if self.is_automatic_run:
                        self.sendSignal()

                        self.current_number_of_rays = 0
                        self.input_beam = None
                    else:
                        QtGui.QMessageBox.critical(self, "QMessageBox.critical()",
                                                   "Number of Accumulated Rays reached, please push \'Send Signal\' button",
                                                   QtGui.QMessageBox.Ok)


if __name__ == "__main__":
    a = QtGui.QApplication(sys.argv)
    ow = AccumulatingLoopPoint()
    ow.show()
    a.exec_()
    ow.saveSettings()
