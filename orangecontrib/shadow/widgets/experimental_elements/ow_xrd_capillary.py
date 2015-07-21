import os, sys, scipy, copy, numpy, random, shutil, time

from orangewidget import gui
from orangewidget.settings import Setting
from PyQt4 import QtCore, QtGui
from PyQt4.QtGui import QApplication, QPalette, QColor, QFont, QDialog

import xraylib

import orangecanvas.resources as resources

from orangecontrib.shadow.util.shadow_objects import ShadowTriggerIn

from orangecontrib.shadow.widgets.gui import ow_automatic_element
from orangecontrib.shadow.util.shadow_util import ShadowGui, ShadowMath, ShadowPhysics, ConfirmDialog
from orangecontrib.shadow.util.shadow_objects import ShadowBeam, ShadowOpticalElement, EmittingStream, TTYGrabber
from orangecontrib.shadow.widgets.experimental_elements.random_generator import RandomGenerator

from PyMca5.PyMcaGui.plotting.PlotWindow import PlotWindow
from PyMca5.PyMcaGui.plotting.MaskImageWidget import MaskImageWidget

class XRDCapillary(ow_automatic_element.AutomaticElement):
    name = "XRD Capillary"
    description = "Shadow OE: XRD Capillary"
    icon = "icons/xrd_capillary.png"
    maintainer = "Luca Rebuffi"
    maintainer_email = "luca.rebuffi(@at@)elettra.eu"
    priority = 1
    category = "Experimental Elements"
    keywords = ["data", "file", "load", "read"]

    inputs = [("Input Beam", ShadowBeam, "setBeam")]

    outputs = [{"name":"Trigger",
                "type": ShadowTriggerIn,
                "doc":"Feedback signal to start a new beam simulation",
                "id":"Trigger"},
               {"name":"Beam",
                "type": ShadowBeam,
                "doc":"Diffracted Beam",
                "id":"Beam"}]

    input_beam = None

    TABS_AREA_HEIGHT = 690
    TABS_AREA_WIDTH = 442
    CONTROL_AREA_WIDTH = 450

    IMAGE_WIDTH = 920
    IMAGE_HEIGHT = 815

    capillary_diameter = Setting(0.3)
    capillary_thickness = Setting(0.01)
    capillary_material = Setting(0)
    sample_material = Setting(0)
    packing_factor = Setting(0.6)
    residual_average_size = Setting(0.0)
    positioning_error = Setting(0.0)

    horizontal_displacement = Setting(0.0)
    vertical_displacement = Setting(0.0)
    calculate_absorption = Setting(0.0)
    absorption_normalization_factor = 0.0

    shift_2theta = Setting(0.000)

    slit_1_vertical_displacement = Setting(0.0)
    slit_2_vertical_displacement = Setting(0.0)
    slit_1_horizontal_displacement = Setting(0.0)
    slit_2_horizontal_displacement = Setting(0.0)

    x_sour_offset = Setting(0.0)
    x_sour_rotation = Setting(0.000)
    y_sour_offset = Setting(0.0)
    y_sour_rotation = Setting(0.000)
    z_sour_offset = Setting(0.0)
    z_sour_rotation = Setting(0.000)

    detector_distance = Setting(0.0)

    diffracted_arm_type = Setting(0)

    slit_1_distance = Setting(0.0)
    slit_1_vertical_aperture = Setting(0.0)
    slit_1_horizontal_aperture = Setting(0.0)
    slit_2_distance = Setting(0.0)
    slit_2_vertical_aperture = Setting(0.0)
    slit_2_horizontal_aperture = Setting(0.0)

    acceptance_slit_distance = Setting(0.0)
    acceptance_slit_vertical_aperture = Setting(0.0)
    acceptance_slit_horizontal_aperture = Setting(0.0)
    analyzer_distance = Setting(0.0)
    analyzer_bragg_angle = Setting(0.0)
    rocking_curve_file = Setting("NONE SPECIFIED")
    mosaic_angle_spread_fwhm = Setting(0.000)

    area_detector_distance = Setting(0.0)
    area_detector_height = Setting(24.5)
    area_detector_width = Setting(28.9)
    area_detector_pixel_size = Setting(100.0)

    start_angle_na = Setting(10.0)
    stop_angle_na = Setting(120.0)
    step = Setting(0.002)
    start_angle = 0.0
    stop_angle = 0.0

    set_number_of_peaks = Setting(0)
    number_of_peaks = Setting(1)

    incremental = Setting(0)
    number_of_executions = Setting(1)
    current_execution = 0

    keep_result = Setting(0)
    number_of_origin_points = Setting(1)
    number_of_rotated_rays = Setting(5)
    normalize = Setting(1)
    degrees_around_peak = Setting(0.01)

    beam_energy = Setting(0.0)
    beam_wavelength = Setting(0.0)
    beam_units_in_use = Setting(0)

    output_file_name = Setting('XRD_Profile.xy')

    add_lorentz_polarization_factor = Setting(1)
    pm2k_fullprof = Setting(0)
    degree_of_polarization = Setting(0.95)
    monochromator_angle = Setting(14.223)

    add_debye_waller_factor = Setting(1)
    use_default_dwf = Setting(1)
    default_debye_waller_B = 0.0
    new_debye_waller_B = Setting(0.000)

    add_background = Setting(0)
    n_sigma=Setting(0)

    add_constant = Setting(0)
    constant_value = Setting(0.0)

    add_chebyshev = Setting(0)
    cheb_coeff_0 = Setting(0.0)
    cheb_coeff_1 = Setting(0.0)
    cheb_coeff_2 = Setting(0.0)
    cheb_coeff_3 = Setting(0.0)
    cheb_coeff_4 = Setting(0.0)
    cheb_coeff_5 = Setting(0.0)

    add_expdecay = Setting(0)
    expd_coeff_0 = Setting(0.0)
    expd_coeff_1 = Setting(0.0)
    expd_coeff_2 = Setting(0.0)
    expd_coeff_3 = Setting(0.0)
    expd_coeff_4 = Setting(0.0)
    expd_coeff_5 = Setting(0.0)
    expd_decayp_0 = Setting(0.0)
    expd_decayp_1 = Setting(0.0)
    expd_decayp_2 = Setting(0.0)
    expd_decayp_3 = Setting(0.0)
    expd_decayp_4 = Setting(0.0)
    expd_decayp_5 = Setting(0.0)

    average_absorption_coefficient = 0.0
    sample_transmittance = 0.0
    muR = 0.0

    caglioti_U = 0.0
    caglioti_V = 0.0
    caglioti_W = 0.0

    run_simulation=True
    reset_button_pressed=False

    want_main_area=1
    plot_canvas=None

    twotheta_angles = []
    current_counts = []
    squared_counts = []
    points_per_bin = []
    counts = []
    caglioti_fits = []
    noise = []
    absorption_coefficients = []
    caglioti_angles = []
    caglioti_fwhm = []
    caglioti_fwhm_fit = []
    caglioti_shift = []
    materials = []
    capillary_materials = []
    rocking_data = []

    random_generator_flat = random.Random()

    area_detector_beam = None

    def __init__(self):
        super().__init__()

        self.readCapillaryMaterialConfigurationFiles()
        self.readMaterialConfigurationFiles()

        self.controlArea.setFixedWidth(self.CONTROL_AREA_WIDTH)

        tabs = ShadowGui.tabWidget(self.controlArea, height=self.TABS_AREA_HEIGHT, width=self.TABS_AREA_WIDTH)

        self.tab_simulation = ShadowGui.createTabPage(tabs, "Simulation")
        self.tab_physical = ShadowGui.createTabPage(tabs, "Experiment")
        self.tab_beam = ShadowGui.createTabPage(tabs, "Beam")
        self.tab_aberrations = ShadowGui.createTabPage(tabs, "Aberrations")
        self.tab_background = ShadowGui.createTabPage(tabs, "Background")
        self.tab_output = ShadowGui.createTabPage(tabs, "Output")

        #####################

        box_rays = ShadowGui.widgetBox(self.tab_simulation, "Rays Generation", addSpace=True, orientation="vertical")

        ShadowGui.lineEdit(box_rays, self, "number_of_origin_points", "Number of Origin Points into the Capillary", labelWidth=355, valueType=int, orientation="horizontal")
        ShadowGui.lineEdit(box_rays, self, "number_of_rotated_rays", "Number of Generated Rays in the Powder Diffraction Arc",  valueType=int, orientation="horizontal")

        gui.comboBox(box_rays, self, "normalize", label="Normalize", labelWidth=370, items=["No", "Yes"], sendSelectedValue=False, orientation="horizontal")

        box_simulation = ShadowGui.widgetBox(self.tab_simulation, "Simulation Management", addSpace=True, orientation="vertical")

        ShadowGui.lineEdit(box_simulation, self, "output_file_name", "Output File Name", labelWidth=120, valueType=str, orientation="horizontal")
        gui.separator(box_simulation)

        gui.checkBox(box_simulation, self, "keep_result", "Keep Result")
        gui.separator(box_simulation)

        gui.checkBox(box_simulation, self, "incremental", "Incremental Simulation", callback=self.setIncremental)
        self.le_number_of_executions = ShadowGui.lineEdit(box_simulation, self, "number_of_executions", "Number of Executions", labelWidth=350, valueType=int, orientation="horizontal")

        self.setIncremental()

        self.le_current_execution = ShadowGui.lineEdit(box_simulation, self, "current_execution", "Current Execution", labelWidth=350, valueType=int, orientation="horizontal")
        self.le_current_execution.setReadOnly(True)
        font = QFont(self.le_current_execution.font())
        font.setBold(True)
        self.le_current_execution.setFont(font)
        palette = QPalette(self.le_current_execution.palette())
        palette.setColor(QPalette.Text, QColor('dark blue'))
        palette.setColor(QPalette.Base, QColor(243, 240, 160))
        self.le_current_execution.setPalette(palette)

        box_ray_tracing = ShadowGui.widgetBox(self.tab_simulation, "Ray Tracing Management", addSpace=True, orientation="vertical")

        ShadowGui.lineEdit(box_ray_tracing, self, "degrees_around_peak", "Degrees around Peak", labelWidth=355, valueType=float, orientation="horizontal")

        gui.separator(box_ray_tracing)

        gui.comboBox(box_ray_tracing, self, "beam_units_in_use", label="Units in use", labelWidth=350,
                     items=["eV", "Angstroms"],
                     callback=self.setBeamUnitsInUse, sendSelectedValue=False, orientation="horizontal")

        self.box_ray_tracing_1 = ShadowGui.widgetBox(box_ray_tracing, "", addSpace=False, orientation="vertical")

        ShadowGui.lineEdit(self.box_ray_tracing_1, self, "beam_energy", "Set Beam energy [eV]", labelWidth=300, valueType=float, orientation="horizontal")

        self.box_ray_tracing_2 = ShadowGui.widgetBox(box_ray_tracing, "", addSpace=False, orientation="vertical")

        ShadowGui.lineEdit(self.box_ray_tracing_2, self, "beam_wavelength", "Beam wavelength [Å]", labelWidth=300, valueType=float, orientation="horizontal")

        self.setBeamUnitsInUse()

        #####################

        box_sample = ShadowGui.widgetBox(self.tab_physical, "Sample Parameters", addSpace=True, orientation="vertical")

        box_capillary = ShadowGui.widgetBox(box_sample, "", addSpace=False, orientation="horizontal")

        ShadowGui.lineEdit(box_capillary, self, "capillary_diameter", "Capillary:  Diameter [mm]", labelWidth=160, valueType=float, orientation="horizontal")
        ShadowGui.lineEdit(box_capillary, self, "capillary_thickness", "          Thickness [mm]", labelWidth=140, valueType=float, orientation="horizontal")

        capillary_names = []

        for capillary_material in self.capillary_materials:
            capillary_names.append(capillary_material.name)

        gui.comboBox(box_sample, self, "capillary_material", label="Capillary Material", labelWidth=300, items=capillary_names, sendSelectedValue=False, orientation="horizontal")

        chemical_formulas = []

        for material in self.materials:
            chemical_formulas.append(material.chemical_formula)

        gui.comboBox(box_sample, self, "sample_material", label="Sample Material", items=chemical_formulas, labelWidth=300, sendSelectedValue=False, orientation="horizontal", callback=self.setSampleMaterial)

        ShadowGui.lineEdit(box_sample, self, "packing_factor", "Packing Factor (0.0 ... 1.0)", labelWidth=350, valueType=float, orientation="horizontal")
        ShadowGui.lineEdit(box_sample, self, "residual_average_size", "Residual Average Size [um]", labelWidth=350, valueType=float, orientation="horizontal")

        box_2theta_arm = ShadowGui.widgetBox(self.tab_physical, "2Theta Arm Parameters", addSpace=True, orientation="vertical", height=260)

        gui.comboBox(box_2theta_arm, self, "diffracted_arm_type", label="Diffracted Arm Setup", items=["Slits", "Analyzer", "Area Detector"], labelWidth=300, sendSelectedValue=False, orientation="horizontal", callback=self.setDiffractedArmType)

        self.box_2theta_arm_1 = ShadowGui.widgetBox(box_2theta_arm, "", addSpace=False, orientation="vertical")

        ShadowGui.lineEdit(self.box_2theta_arm_1, self, "detector_distance", "Detector Distance [cm]", labelWidth=300, tooltip="Detector Distance [cm]", valueType=float, orientation="horizontal")

        gui.separator(self.box_2theta_arm_1)

        ShadowGui.lineEdit(self.box_2theta_arm_1, self, "slit_1_distance", "Slit 1 Distance from Goniometer Center [cm]", labelWidth=300, valueType=float, orientation="horizontal")
        ShadowGui.lineEdit(self.box_2theta_arm_1, self, "slit_1_vertical_aperture", "Slit 1 Vertical Aperture [um]",  labelWidth=300, valueType=float, orientation="horizontal")
        ShadowGui.lineEdit(self.box_2theta_arm_1, self, "slit_1_horizontal_aperture", "Slit 1 Horizontal Aperture [um]",  labelWidth=300, valueType=float, orientation="horizontal")

        gui.separator(self.box_2theta_arm_1)

        ShadowGui.lineEdit(self.box_2theta_arm_1, self, "slit_2_distance", "Slit 2 Distance from Goniometer Center [cm]", labelWidth=300, valueType=float, orientation="horizontal")
        ShadowGui.lineEdit(self.box_2theta_arm_1, self, "slit_2_vertical_aperture", "Slit 2 Vertical Aperture [um]", labelWidth=300, valueType=float, orientation="horizontal")
        ShadowGui.lineEdit(self.box_2theta_arm_1, self, "slit_2_horizontal_aperture", "Slit 2 Horizontal Aperture [um]", labelWidth=300, valueType=float, orientation="horizontal")

        self.box_2theta_arm_2 = ShadowGui.widgetBox(box_2theta_arm, "", addSpace=False, orientation="vertical")

        ShadowGui.lineEdit(self.box_2theta_arm_2, self, "acceptance_slit_distance", "Slit Distance from Goniometer Center [cm]", labelWidth=300, valueType=float, orientation="horizontal")
        ShadowGui.lineEdit(self.box_2theta_arm_2, self, "acceptance_slit_vertical_aperture", "Slit Vertical Aperture [um]",  labelWidth=300, valueType=float, orientation="horizontal")
        ShadowGui.lineEdit(self.box_2theta_arm_2, self, "acceptance_slit_horizontal_aperture", "Slit Horizontal Aperture [um]",  labelWidth=300, valueType=float, orientation="horizontal")

        gui.separator(self.box_2theta_arm_2)

        ShadowGui.lineEdit(self.box_2theta_arm_2, self, "analyzer_distance", "Crystal Distance from Goniometer Center [cm]", labelWidth=300, valueType=float, orientation="horizontal")
        ShadowGui.lineEdit(self.box_2theta_arm_2, self, "analyzer_bragg_angle", "Analyzer Incidence Angle [deg]", labelWidth=300, valueType=float, orientation="horizontal")
        ShadowGui.lineEdit(self.box_2theta_arm_2, self, "rocking_curve_file", "File with Crystal parameter",  labelWidth=180, valueType=str, orientation="horizontal")
        ShadowGui.lineEdit(self.box_2theta_arm_2, self, "mosaic_angle_spread_fwhm", "Mosaic Angle Spread FWHM [deg]", labelWidth=300, valueType=float, orientation="horizontal")

        self.box_2theta_arm_3 = ShadowGui.widgetBox(box_2theta_arm, "", addSpace=False, orientation="vertical")

        gui.separator(self.box_2theta_arm_3)

        ShadowGui.lineEdit(self.box_2theta_arm_3, self, "area_detector_distance", "Detector Distance [cm]",
                           labelWidth=300, tooltip="Detector Distance [cm]", valueType=float, orientation="horizontal")
        ShadowGui.lineEdit(self.box_2theta_arm_3, self, "area_detector_height", "Detector Height [cm]", labelWidth=300,
                           tooltip="Detector Height [cm]", valueType=float, orientation="horizontal")
        ShadowGui.lineEdit(self.box_2theta_arm_3, self, "area_detector_width", "Detector Width [cm]", labelWidth=300,
                           tooltip="Detector Width [cm]", valueType=float, orientation="horizontal")
        ShadowGui.lineEdit(self.box_2theta_arm_3, self, "area_detector_pixel_size", "Pixel Size [um]", labelWidth=300,
                           tooltip="Pixel Size [um]", valueType=float, orientation="horizontal")

        box_scan = ShadowGui.widgetBox(self.tab_physical, "Scan Parameters", addSpace=True, orientation="vertical")

        ShadowGui.lineEdit(box_scan, self, "start_angle_na", "Start Angle [deg]", labelWidth=350, valueType=float, orientation="horizontal")
        ShadowGui.lineEdit(box_scan, self, "stop_angle_na", "Stop Angle [deg]", labelWidth=350, valueType=float, orientation="horizontal")
        ShadowGui.lineEdit(box_scan, self, "step", "Step [deg]", labelWidth=340, valueType=float, orientation="horizontal")

        box_diffraction = ShadowGui.widgetBox(self.tab_physical, "Diffraction Parameters", addSpace=True, orientation="vertical")

        gui.comboBox(box_diffraction, self, "set_number_of_peaks", label="set Number of Peaks", labelWidth=370, callback=self.setNumberOfPeaks, items=["No", "Yes"], sendSelectedValue=False, orientation="horizontal")
        self.le_number_of_peaks = ShadowGui.lineEdit(box_diffraction, self, "number_of_peaks", "Number of Peaks", labelWidth=358, valueType=int, orientation="horizontal")
        gui.separator(box_diffraction)

        self.setNumberOfPeaks()

        #####################

        box_beam = ShadowGui.widgetBox(self.tab_beam, "Lorentz-Polarization Factor", addSpace=True, orientation="vertical")

        gui.comboBox(box_beam, self, "add_lorentz_polarization_factor", label="Add Lorentz-Polarization Factor", labelWidth=370, items=["No", "Yes"], sendSelectedValue=False, orientation="horizontal", callback=self.setPolarization)

        gui.separator(box_beam)

        self.box_polarization =  ShadowGui.widgetBox(box_beam, "", addSpace=True, orientation="vertical")

        gui.comboBox(self.box_polarization, self, "pm2k_fullprof", label="Kind of Calculation", labelWidth=340, items=["PM2K", "FULLPROF"], sendSelectedValue=False, orientation="horizontal", callback=self.setKindOfCalculation)

        self.box_degree_of_polarization_pm2k =  ShadowGui.widgetBox(self.box_polarization, "", addSpace=True, orientation="vertical")
        ShadowGui.lineEdit(self.box_degree_of_polarization_pm2k, self, "degree_of_polarization", "Q Factor [(Ih-Iv)/(Ih+Iv)]", labelWidth=350, valueType=float, orientation="horizontal")
        self.box_degree_of_polarization_fullprof =  ShadowGui.widgetBox(self.box_polarization, "", addSpace=True, orientation="vertical")
        ShadowGui.lineEdit(self.box_degree_of_polarization_fullprof, self, "degree_of_polarization", "K Factor", labelWidth=350, valueType=float, orientation="horizontal")

        ShadowGui.lineEdit(self.box_polarization, self, "monochromator_angle", "Monochromator Theta Angle [deg]", labelWidth=300, valueType=float, orientation="horizontal")

        self.setPolarization()

        box_beam_2 = ShadowGui.widgetBox(self.tab_beam, "Debye-Waller Factor", addSpace=True, orientation="vertical")

        gui.comboBox(box_beam_2, self, "add_debye_waller_factor", label="Add Debye-Waller Factor", labelWidth=370, items=["No", "Yes"], sendSelectedValue=False, orientation="horizontal", callback=self.setDebyeWallerFactor)

        gui.separator(box_beam_2)

        self.box_debye_waller =  ShadowGui.widgetBox(box_beam_2, "", addSpace=True, orientation="vertical")

        gui.comboBox(self.box_debye_waller, self, "use_default_dwf", label="Use Stored D.W.F. (B) [Angstrom-2]", labelWidth=370, items=["No", "Yes"], sendSelectedValue=False, orientation="horizontal", callback=self.setUseDefaultDWF)

        self.box_use_default_dwf_1 =  ShadowGui.widgetBox(self.box_debye_waller, "", addSpace=True, orientation="vertical")
        ShadowGui.lineEdit(self.box_use_default_dwf_1, self, "new_debye_waller_B", "Debye-Waller Factor (B)", labelWidth=300, valueType=float, orientation="horizontal")
        self.box_use_default_dwf_2 =  ShadowGui.widgetBox(self.box_debye_waller, "", addSpace=True, orientation="vertical")
        le_dwf = ShadowGui.lineEdit(self.box_use_default_dwf_2, self, "default_debye_waller_B", "Stored Debye-Waller Factor (B) [Angstrom-2]", labelWidth=300, valueType=float, orientation="horizontal")
        le_dwf.setReadOnly(True)
        font = QFont(le_dwf.font())
        font.setBold(True)
        le_dwf.setFont(font)
        palette = QPalette(le_dwf.palette())
        palette.setColor(QPalette.Text, QColor('dark blue'))
        palette.setColor(QPalette.Base, QColor(243, 240, 160))
        le_dwf.setPalette(palette)

        self.setDebyeWallerFactor()

        #####################

        box_cap_aberrations = ShadowGui.widgetBox(self.tab_aberrations, "Capillary Aberrations", addSpace=True, orientation="vertical")

        ShadowGui.lineEdit(box_cap_aberrations, self, "positioning_error", "Position Error % (wobbling)", labelWidth=350, valueType=float, orientation="horizontal")
        gui.separator(box_cap_aberrations)
        ShadowGui.lineEdit(box_cap_aberrations, self, "horizontal_displacement", "Horizontal Displacement [um]", labelWidth=300, valueType=float, orientation="horizontal")
        ShadowGui.lineEdit(box_cap_aberrations, self, "vertical_displacement", "Vertical Displacement [um]", labelWidth=300, valueType=float, orientation="horizontal")
        gui.separator(box_cap_aberrations)
        gui.comboBox(box_cap_aberrations, self, "calculate_absorption", label="Calculate Absorption", labelWidth=370, items=["No", "Yes"], sendSelectedValue=False, orientation="horizontal", callback=self.setAbsorption)

        box_gon_aberrations = ShadowGui.widgetBox(self.tab_aberrations, "Goniometer Aberrations", addSpace=True, orientation="vertical")

        gonabb_label = gui.label(box_gon_aberrations, self, "Goniometer 2Theta Axis System misalignement respect to \ngoniometric center")
        font = QFont(gonabb_label)
        font.setBold(True)
        gonabb_label.setFont(font)
        gonabb_label.setAlignment(QtCore.Qt.AlignCenter)

        gui.separator(box_gon_aberrations)

        box_button = ShadowGui.widgetBox(box_gon_aberrations, "", addSpace=True, orientation="horizontal")

        gui.label(box_button, self, "")

        axisbutton = gui.button(box_button, self, "Show Axis System", callback=self.showAxisSystem)
        axisbutton.setFixedWidth(200)

        gui.separator(box_gon_aberrations)

        ShadowGui.lineEdit(box_gon_aberrations, self, "x_sour_offset", "Offset along X [um]", labelWidth=300, valueType=float, orientation="horizontal")
        ShadowGui.lineEdit(box_gon_aberrations, self, "x_sour_rotation", "CW rotation around X [deg] (2Theta shift)", labelWidth=300, valueType=float, orientation="horizontal")

        ShadowGui.lineEdit(box_gon_aberrations, self, "y_sour_offset", "Offset along Y [um]", labelWidth=300, valueType=float, orientation="horizontal")
        ShadowGui.lineEdit(box_gon_aberrations, self, "y_sour_rotation", "CW rotation around Y [deg]", labelWidth=300, valueType=float, orientation="horizontal")

        ShadowGui.lineEdit(box_gon_aberrations, self, "z_sour_offset", "Offset along Z [um]", labelWidth=300, valueType=float, orientation="horizontal")
        ShadowGui.lineEdit(box_gon_aberrations, self, "z_sour_rotation", "CW rotation around Z [deg]", labelWidth=300, valueType=float, orientation="horizontal")


        box_det_aberrations = ShadowGui.widgetBox(self.tab_aberrations, "Detector Arm Aberrations", addSpace=True, orientation="vertical")

        self.slit_1_vertical_displacement_le = ShadowGui.lineEdit(box_det_aberrations, self,
                                                                  "slit_1_vertical_displacement",
                                                                  "Slit 1 V Displacement [um]", labelWidth=300,
                                                                  valueType=float, orientation="horizontal")
        self.slit_1_horizontal_displacement_le = ShadowGui.lineEdit(box_det_aberrations, self,
                                                                    "slit_1_horizontal_displacement",
                                                                    "Slit 1 H Displacement [um]", labelWidth=300,
                                                                    valueType=float, orientation="horizontal")
        gui.separator(box_det_aberrations)
        self.slit_2_vertical_displacement_le = ShadowGui.lineEdit(box_det_aberrations, self, "slit_2_vertical_displacement", "Slit 2 V Displacement [um]", labelWidth=300, valueType=float, orientation="horizontal")
        self.slit_2_horizontal_displacement_le = ShadowGui.lineEdit(box_det_aberrations, self, "slit_2_horizontal_displacement", "Slit 2 H Displacement [um]", labelWidth=300, valueType=float, orientation="horizontal")

        #####################

        box_background = ShadowGui.widgetBox(self.tab_background, "Background Parameters", addSpace=True,
                                             orientation="vertical", height=630, width=420)

        gui.comboBox(box_background, self, "add_background", label="Add Background", labelWidth=370, items=["No", "Yes"],
                     callback=self.setAddBackground, sendSelectedValue=False, orientation="horizontal")

        gui.separator(box_background)

        self.box_background_1_hidden = ShadowGui.widgetBox(box_background, "", addSpace=True, orientation="vertical", width=410)
        self.box_background_1 = ShadowGui.widgetBox(box_background, "", addSpace=True, orientation="vertical")

        gui.comboBox(self.box_background_1, self, "n_sigma", label="Noise (Nr. Sigma)", labelWidth=347, items=["0.5", "1", "1.5", "2", "2.5", "3"], sendSelectedValue=False, orientation="horizontal")

        self.box_background_const  = ShadowGui.widgetBox(box_background, "Constant", addSpace=True, orientation="vertical")

        gui.checkBox(self.box_background_const, self, "add_constant", "add Background", callback=self.setConstant)
        gui.separator(self.box_background_const)

        self.box_background_const_2 = ShadowGui.widgetBox(self.box_background_const, "", addSpace=True, orientation="vertical")

        ShadowGui.lineEdit(self.box_background_const_2, self, "constant_value", "Value", labelWidth=300, valueType=float, orientation="horizontal")

        self.box_background_2 = ShadowGui.widgetBox(box_background, "", addSpace=True, orientation="horizontal")

        self.box_chebyshev = ShadowGui.widgetBox(self.box_background_2, "Chebyshev", addSpace=True, orientation="vertical")
        gui.checkBox(self.box_chebyshev, self, "add_chebyshev", "add Background", callback=self.setChebyshev)
        gui.separator(self.box_chebyshev)
        self.box_chebyshev_2 = ShadowGui.widgetBox(self.box_chebyshev, "", addSpace=True, orientation="vertical")
        ShadowGui.lineEdit(self.box_chebyshev_2, self, "cheb_coeff_0", "A0", labelWidth=70, valueType=float, orientation="horizontal")
        ShadowGui.lineEdit(self.box_chebyshev_2, self, "cheb_coeff_1", "A1", labelWidth=70, valueType=float, orientation="horizontal")
        ShadowGui.lineEdit(self.box_chebyshev_2, self, "cheb_coeff_2", "A2", labelWidth=70, valueType=float, orientation="horizontal")
        ShadowGui.lineEdit(self.box_chebyshev_2, self, "cheb_coeff_3", "A3", labelWidth=70, valueType=float, orientation="horizontal")
        ShadowGui.lineEdit(self.box_chebyshev_2, self, "cheb_coeff_4", "A4", labelWidth=70, valueType=float, orientation="horizontal")
        ShadowGui.lineEdit(self.box_chebyshev_2, self, "cheb_coeff_5", "A5", labelWidth=70, valueType=float, orientation="horizontal")
         
        self.box_expdecay = ShadowGui.widgetBox(self.box_background_2, "Exp Decay", addSpace=True, orientation="vertical")
        gui.checkBox(self.box_expdecay, self, "add_expdecay", "add Background", callback=self.setExpDecay)
        gui.separator(self.box_expdecay)
        self.box_expdecay_2 = ShadowGui.widgetBox(self.box_expdecay, "", addSpace=True, orientation="vertical")
        ShadowGui.lineEdit(self.box_expdecay_2, self, "expd_coeff_0", "A0", labelWidth=70, valueType=float, orientation="horizontal")
        ShadowGui.lineEdit(self.box_expdecay_2, self, "expd_coeff_1", "A1", labelWidth=70, valueType=float, orientation="horizontal")
        ShadowGui.lineEdit(self.box_expdecay_2, self, "expd_coeff_2", "A2", labelWidth=70, valueType=float, orientation="horizontal")
        ShadowGui.lineEdit(self.box_expdecay_2, self, "expd_coeff_3", "A3", labelWidth=70, valueType=float, orientation="horizontal")
        ShadowGui.lineEdit(self.box_expdecay_2, self, "expd_coeff_4", "A4", labelWidth=70, valueType=float, orientation="horizontal")
        ShadowGui.lineEdit(self.box_expdecay_2, self, "expd_coeff_5", "A5", labelWidth=70, valueType=float, orientation="horizontal")
        gui.separator(self.box_expdecay_2)
        ShadowGui.lineEdit(self.box_expdecay_2, self, "expd_decayp_0", "H0", labelWidth=70, valueType=float, orientation="horizontal")
        ShadowGui.lineEdit(self.box_expdecay_2, self, "expd_decayp_1", "H1", labelWidth=70, valueType=float, orientation="horizontal")
        ShadowGui.lineEdit(self.box_expdecay_2, self, "expd_decayp_2", "H2", labelWidth=70, valueType=float, orientation="horizontal")
        ShadowGui.lineEdit(self.box_expdecay_2, self, "expd_decayp_3", "H3", labelWidth=70, valueType=float, orientation="horizontal")
        ShadowGui.lineEdit(self.box_expdecay_2, self, "expd_decayp_4", "H4", labelWidth=70, valueType=float, orientation="horizontal")
        ShadowGui.lineEdit(self.box_expdecay_2, self, "expd_decayp_5", "H5", labelWidth=70, valueType=float, orientation="horizontal")

        #####################

        self.shadow_output = QtGui.QTextEdit()
        self.shadow_output.setReadOnly(True)

        out_box = gui.widgetBox(self.tab_output, "System Output", addSpace=True, orientation="horizontal")
        out_box.layout().addWidget(self.shadow_output)

        self.shadow_output.setFixedHeight(600)

        #####################

        gui.separator(self.controlArea, height=20)

        button_box = ShadowGui.widgetBox(self.controlArea, "", addSpace=True, orientation="horizontal", height=30)

        self.start_button = gui.button(button_box, self, "Simulate Diffraction", callback=self.simulate)
        self.start_button.setFixedHeight(30)

        self.background_button = gui.button(button_box, self, "Simulate Background", callback=self.simulateBackground)
        self.background_button.setFixedHeight(30)
        palette = QPalette(self.background_button.palette()) # make a copy of the palette
        palette.setColor(QPalette.ButtonText, QColor('dark blue'))
        self.background_button.setPalette(palette) # assign new palette

        stop_button = gui.button(button_box, self, "Interrupt", callback=self.stopSimulation)
        stop_button.setFixedHeight(30)
        font = QFont(stop_button.font())
        font.setBold(True)
        stop_button.setFont(font)
        palette = QPalette(stop_button.palette()) # make a copy of the palette
        palette.setColor(QPalette.ButtonText, QColor('red'))
        stop_button.setPalette(palette) # assign new palette

        button_box_2 = ShadowGui.widgetBox(self.controlArea, "", addSpace=False, orientation="horizontal", height=30)

        self.reset_fields_button = gui.button(button_box_2, self, "Reset Fields", callback=self.callResetSettings)
        font = QFont(self.reset_fields_button.font())
        font.setItalic(True)
        self.reset_fields_button.setFont(font)
        self.reset_fields_button.setFixedHeight(30)

        self.reset_bkg_button = gui.button(button_box_2, self, "Reset Background", callback=self.resetBackground)
        self.reset_bkg_button.setFixedHeight(30)
        font = QFont(self.reset_bkg_button.font())
        font.setItalic(True)
        self.reset_bkg_button.setFont(font)
        palette = QPalette(self.reset_bkg_button.palette()) # make a copy of the palette
        palette.setColor(QPalette.ButtonText, QColor('dark blue'))
        self.reset_bkg_button.setPalette(palette) # assign new palette

        self.reset_button = gui.button(button_box_2, self, "Reset Simulation", callback=self.resetSimulation)
        self.reset_button.setFixedHeight(30)
        font = QFont(self.reset_button.font())
        font.setItalic(True)
        self.reset_button.setFont(font)
        palette = QPalette(self.reset_button.palette()) # make a copy of the palette
        palette.setColor(QPalette.ButtonText, QColor('red'))
        self.reset_button.setPalette(palette) # assign new palette

        self.setAddBackground()

        gui.rubber(self.controlArea)

        self.plot_tabs = gui.tabWidget(self.mainArea)

        # ---------------------------------------------

        self.tab_results_area = gui.createTabPage(self.plot_tabs, "XRD 2D Pattern")

        self.area_image_box = gui.widgetBox(self.tab_results_area, "", addSpace=True, orientation="vertical")
        self.area_image_box.setFixedHeight(self.IMAGE_HEIGHT)
        self.area_image_box.setFixedWidth(self.IMAGE_WIDTH)

        self.plot_canvas_area = MaskImageWidget(colormap=True, selection=False, imageicons=False, aspect=True)
        self.plot_canvas_area.setDefaultColormap(6, False)
        self.plot_canvas_area.setXLabel("X [pixels]")
        self.plot_canvas_area.setYLabel("Z [pixels]")

        gui.separator(self.area_image_box)

        self.area_image_box.layout().addWidget(self.plot_canvas_area)

        #---------------------------------------------

        tab_results = gui.createTabPage(self.plot_tabs, "XRD Pattern")
        tab_caglioti_fwhm = gui.createTabPage(self.plot_tabs, "Instrumental Broadening")
        tab_caglioti_shift = gui.createTabPage(self.plot_tabs, "Instrumental Peak Shift")

        self.image_box = gui.widgetBox(tab_results, "", addSpace=True, orientation="vertical")
        self.image_box.setFixedHeight(self.IMAGE_HEIGHT)
        self.image_box.setFixedWidth(self.IMAGE_WIDTH)

        self.absorption_coefficient_box = gui.widgetBox(self.image_box, "", addSpace=True, orientation="vertical")
        self.absorption_coefficient_box.setFixedWidth(420)

        gui.separator(self.absorption_coefficient_box)
        aac = ShadowGui.lineEdit(self.absorption_coefficient_box, self, "average_absorption_coefficient", "Sample Linear Absorption Coefficient [cm-1]", labelWidth=290, valueType=float, orientation="horizontal")
        tra = ShadowGui.lineEdit(self.absorption_coefficient_box, self, "sample_transmittance", "Sample Transmittance [%]", labelWidth=290, valueType=float, orientation="horizontal")
        mur = ShadowGui.lineEdit(self.absorption_coefficient_box, self, "muR",                            "muR", labelWidth=290, valueType=float, orientation="horizontal")

        tra.setReadOnly(True)
        font = QFont(tra.font())
        font.setBold(True)
        tra.setFont(font)
        palette = QPalette(tra)
        palette.setColor(QPalette.Text, QColor('dark blue'))
        palette.setColor(QPalette.Base, QColor(243, 240, 160))
        tra.setPalette(palette)

        aac.setReadOnly(True)
        font = QFont(aac.font())
        font.setBold(True)
        aac.setFont(font)
        palette = QPalette(aac)
        palette.setColor(QPalette.Text, QColor('dark blue'))
        palette.setColor(QPalette.Base, QColor(243, 240, 160))
        aac.setPalette(palette)

        mur.setReadOnly(True)
        font = QFont(mur.font())
        font.setBold(True)
        mur.setFont(font)
        palette = QPalette(mur)
        palette.setColor(QPalette.Text, QColor('dark blue'))
        palette.setColor(QPalette.Base, QColor(243, 240, 160))
        mur.setPalette(palette)

        self.setAbsorption()

        self.plot_canvas = PlotWindow(roi=False, control=False, position=False, plugins=False)
        self.plot_canvas.setGraphXLabel("2Theta [deg]")
        self.plot_canvas.setGraphYLabel("Intensity (arbitrary units)")
        self.plot_canvas.setDefaultPlotLines(True)
        self.plot_canvas.setActiveCurveColor(color='darkblue')

        self.image_box.layout().addWidget(self.plot_canvas)

        self.caglioti_fwhm_image_box = gui.widgetBox(tab_caglioti_fwhm, "", addSpace=True, orientation="vertical")
        self.caglioti_fwhm_image_box.setFixedHeight(self.IMAGE_HEIGHT)
        self.caglioti_fwhm_image_box.setFixedWidth(self.IMAGE_WIDTH)

        self.caglioti_fwhm_coefficient_box = gui.widgetBox(self.caglioti_fwhm_image_box, "", addSpace=True, orientation="vertical")
        self.caglioti_fwhm_coefficient_box.setFixedWidth(200)

        gui.separator(self.caglioti_fwhm_coefficient_box)
        c_U = ShadowGui.lineEdit(self.caglioti_fwhm_coefficient_box, self, "caglioti_U", "U [deg]", labelWidth=100, valueType=float, orientation="horizontal")
        c_V = ShadowGui.lineEdit(self.caglioti_fwhm_coefficient_box, self, "caglioti_V", "V [deg-1]", labelWidth=100, valueType=float, orientation="horizontal")
        c_W = ShadowGui.lineEdit(self.caglioti_fwhm_coefficient_box, self, "caglioti_W", "W [deg-2]", labelWidth=100, valueType=float, orientation="horizontal")

        c_U.setReadOnly(True)
        font = QFont(c_U.font())
        font.setBold(True)
        c_U.setFont(font)
        palette = QPalette(c_U)
        palette.setColor(QPalette.Text, QColor('dark blue'))
        palette.setColor(QPalette.Base, QColor(243, 240, 160))
        c_U.setPalette(palette)

        c_V.setReadOnly(True)
        font = QFont(c_V.font())
        font.setBold(True)
        c_V.setFont(font)
        palette = QPalette(c_V)
        palette.setColor(QPalette.Text, QColor('dark blue'))
        palette.setColor(QPalette.Base, QColor(243, 240, 160))
        c_V.setPalette(palette)

        c_W.setReadOnly(True)
        font = QFont(c_W.font())
        font.setBold(True)
        c_W.setFont(font)
        palette = QPalette(c_W)
        palette.setColor(QPalette.Text, QColor('dark blue'))
        palette.setColor(QPalette.Base, QColor(243, 240, 160))
        c_W.setPalette(palette)

        self.caglioti_fwhm_canvas = PlotWindow(roi=False, control=False, position=False, plugins=False)
        self.caglioti_fwhm_canvas.setGraphXLabel("2Theta [deg]")
        self.caglioti_fwhm_canvas.setGraphYLabel("FWHM [deg]")
        self.caglioti_fwhm_canvas.setDefaultPlotLines(True)
        self.caglioti_fwhm_canvas.setActiveCurveColor(color='darkblue')

        self.caglioti_fwhm_image_box.layout().addWidget(self.caglioti_fwhm_canvas)

        self.caglioti_shift_image_box = gui.widgetBox(tab_caglioti_shift, "", addSpace=True, orientation="vertical")
        self.caglioti_shift_image_box.setFixedHeight(self.IMAGE_HEIGHT)
        self.caglioti_shift_image_box.setFixedWidth(self.IMAGE_WIDTH)

        self.caglioti_shift_canvas = PlotWindow(roi=False, control=False, position=False, plugins=False)
        self.caglioti_shift_canvas.setGraphXLabel("2Theta [deg]")
        self.caglioti_shift_canvas.setGraphYLabel("(2Theta_Bragg - 2Theta) [deg]")
        self.caglioti_shift_canvas.setDefaultPlotLines(True)
        self.caglioti_shift_canvas.setActiveCurveColor(color='darkblue')

        self.caglioti_shift_image_box.layout().addWidget(self.caglioti_shift_canvas)

        self.setDiffractedArmType()

        gui.rubber(self.mainArea)

    def setBeam(self, beam):
        if ShadowGui.checkEmptyBeam(beam):
            self.input_beam = beam

            if self.is_automatic_run:
                self.simulate()

    ############################################################
    # GUI MANAGEMENT METHODS
    ############################################################

    def callResetSettings(self):
        super().callResetSettings()

        self.setIncremental()
        self.setNumberOfPeaks()
        self.setPolarization()
        self.setDebyeWallerFactor()
        self.setAddBackground()
        self.setAbsorption()

    def setAbsorption(self):
        self.absorption_coefficient_box.setVisible(self.calculate_absorption==1)

    def setTabsAndButtonsEnabled(self, enabled=True):
        self.tab_simulation.setEnabled(enabled)
        self.tab_physical.setEnabled(enabled)
        self.tab_beam.setEnabled(enabled)
        self.tab_aberrations.setEnabled(enabled)
        self.tab_background.setEnabled(enabled)
        self.tab_output.setEnabled(enabled)

        self.start_button.setEnabled(enabled)
        self.reset_fields_button.setEnabled(enabled)
        self.reset_button.setEnabled(enabled)

        if not enabled:
            self.background_button.setEnabled(False)
            self.reset_bkg_button.setEnabled(False)
        else:
            self.background_button.setEnabled(self.add_background == 1)
            self.reset_bkg_button.setEnabled(self.add_background == 1)

    def setSimulationTabsAndButtonsEnabled(self, enabled=True):
        self.tab_background.setEnabled(enabled)

        self.start_button.setEnabled(enabled)
        self.reset_button.setEnabled(enabled)

        if not enabled:
            self.background_button.setEnabled(False)
            self.reset_bkg_button.setEnabled(False)
        else:
            self.background_button.setEnabled(self.add_background == 1)
            self.reset_bkg_button.setEnabled(self.add_background == 1)

    def setIncremental(self):
        self.le_number_of_executions.setEnabled(self.incremental == 1)

    def setBeamUnitsInUse(self):
        self.box_ray_tracing_1.setVisible(self.beam_units_in_use == 0)
        self.box_ray_tracing_2.setVisible(self.beam_units_in_use == 1)

    def setDiffractedArmType(self):
        self.box_2theta_arm_1.setVisible(self.diffracted_arm_type == 0)
        self.box_2theta_arm_2.setVisible(self.diffracted_arm_type == 1)
        self.box_2theta_arm_3.setVisible(self.diffracted_arm_type == 2)

        self.slit_1_vertical_displacement_le.setEnabled(self.diffracted_arm_type != 2)
        self.slit_1_horizontal_displacement_le.setEnabled(self.diffracted_arm_type != 2)

        self.slit_2_vertical_displacement_le.setEnabled(self.diffracted_arm_type == 0)
        self.slit_2_horizontal_displacement_le.setEnabled(self.diffracted_arm_type == 0)

        if self.diffracted_arm_type != 2:
            if (self.plot_tabs.count() == 4): self.plot_tabs.removeTab(0)
        else:
            if (self.plot_tabs.count() == 3): self.plot_tabs.insertTab(0, self.tab_results_area, "XRD Pattern 2D")

    def setNumberOfPeaks(self):
        self.le_number_of_peaks.setEnabled(self.set_number_of_peaks == 1)

    def setSampleMaterial(self):
        self.default_debye_waller_B = self.getDebyeWallerB(self.sample_material)

    def setKindOfCalculation(self):
        self.box_degree_of_polarization_pm2k.setVisible(self.pm2k_fullprof==0)
        self.box_degree_of_polarization_fullprof.setVisible(self.pm2k_fullprof==1)

    def setPolarization(self):
        self.box_polarization.setVisible(self.add_lorentz_polarization_factor == 1)
        if (self.add_lorentz_polarization_factor==1): self.setKindOfCalculation()

    def setUseDefaultDWF(self):
        self.box_use_default_dwf_1.setVisible(self.use_default_dwf==0)
        self.box_use_default_dwf_2.setVisible(self.use_default_dwf==1)

    def setDebyeWallerFactor(self):
        self.box_debye_waller.setVisible(self.add_debye_waller_factor == 1)
        if (self.add_debye_waller_factor==1):
            self.setUseDefaultDWF()
            self.setSampleMaterial()

    class ShowAxisSystemDialog(QDialog):

        def __init__(self, parent=None):
            QDialog.__init__(self, parent)
            self.setWindowTitle('Axis System')
            layout = QtGui.QVBoxLayout(self)
            label = QtGui.QLabel("")

            directory_files = resources.package_dirname("orangecontrib.shadow.widgets.experimental_elements")

            label.setPixmap(QtGui.QPixmap(directory_files + "/axis.png"))

            bbox = QtGui.QDialogButtonBox(QtGui.QDialogButtonBox.Ok)

            bbox.accepted.connect(self.accept)
            layout.addWidget(label)
            layout.addWidget(bbox)


    def showAxisSystem(self):
        dialog = XRDCapillary.ShowAxisSystemDialog(parent=self)
        dialog.show()


    def setAddBackground(self):
        self.box_background_1_hidden.setVisible(self.add_background == 0)
        self.box_background_1.setVisible(self.add_background == 1)
        self.box_background_const.setVisible(self.add_background == 1)
        self.box_background_2.setVisible(self.add_background == 1)

        self.setConstant()
        self.setChebyshev()
        self.setExpDecay()
        self.background_button.setEnabled(self.add_background == 1)
        self.reset_bkg_button.setEnabled(self.add_background == 1)

    def setConstant(self):
        self.box_background_const_2.setEnabled(self.add_constant == 1)

    def setChebyshev(self):
        self.box_chebyshev_2.setEnabled(self.add_chebyshev == 1)
        
    def setExpDecay(self):
        self.box_expdecay_2.setEnabled(self.add_expdecay == 1)

    def plot2DResults(self):
        if not self.area_detector_beam is None:
            nbins_h = int(numpy.floor(self.area_detector_width / (self.area_detector_pixel_size * 1e-4)))
            nbins_v = int(numpy.floor(self.area_detector_height / (self.area_detector_pixel_size * 1e-4)))

            ticket = self.area_detector_beam.beam.histo2(1, 3, nbins_h=nbins_h, nbins_v=nbins_v)
            normalized_data = (ticket['histogram'] / ticket['histogram'].max()) * 100000  # just for the quality of the plot

            # inversion of axis for pyMCA
            data_to_plot = []
            for y_index in range(0, nbins_v):
                x_values = []
                for x_index in range(0, nbins_h):
                    x_values.append(normalized_data[x_index][y_index])

                data_to_plot.append(x_values)

            self.plot_canvas_area.setImageData(numpy.array(data_to_plot))
            self.plot_canvas_area.setDefaultColormap(6, False)
            self.plot_canvas_area.setXLabel("X [pixels]")
            self.plot_canvas_area.setYLabel("Z [pixels]")
            self.plot_canvas_area.graphWidget.keepDataAspectRatio(True)

            time.sleep(0.5)

    def plotResult(self, clear_caglioti=True, reflections=None):
        if not len(self.twotheta_angles)==0:
            data = numpy.add(self.counts, self.noise)
            self.plot_canvas.clearCurves()
            self.plot_canvas.addCurve(self.twotheta_angles, data, "XRD Diffraction pattern", symbol=',', color='blue', replace=True) #'+', '^',
            self.plot_canvas.setGraphXLabel("2Theta [deg]")
            self.plot_canvas.setGraphYLabel("Intensity (arbitrary units)")

            if clear_caglioti:
                self.caglioti_fwhm_canvas.clearCurves()
                self.caglioti_shift_canvas.clearCurves()

            if not reflections is None:
                self.caglioti_angles, self.caglioti_fwhm, self.caglioti_shift = self.getCagliotisData(reflections)

                self.plot_canvas.addCurve(self.twotheta_angles, self.caglioti_fits, "Caglioti Fits", symbol=',', color='red', linestyle="dashed") #'+', '^',

                self.caglioti_fwhm_canvas.addCurve(self.caglioti_angles, self.caglioti_fwhm, "FWHM (Gaussian)", symbol=',', color='blue', replace=True) #'+', '^',
                self.caglioti_shift_canvas.addCurve(self.caglioti_angles, self.caglioti_shift, "Peak Shift", symbol=',', color='blue', replace=True) #'+', '^',
                self.caglioti_fwhm_canvas.setGraphXLabel("2Theta [deg]")
                self.caglioti_fwhm_canvas.setGraphYLabel("FWHM [deg]")
                self.caglioti_shift_canvas.setGraphXLabel("2Theta [deg]")
                self.caglioti_shift_canvas.setGraphYLabel("(2Theta_Bragg - 2Theta) [deg]")

                if not (len(self.caglioti_angles) < 3):
                    try:
                        parameters, covariance_matrix = ShadowMath.caglioti_broadening_fit(data_x=self.caglioti_angles, data_y=self.caglioti_fwhm)

                        def caglioti_broadening_function(x, U, V, W):
                            return numpy.sqrt(W + V * (numpy.tan(x*numpy.pi/360)) + U * (numpy.tan(x*numpy.pi/360))**2)

                        self.caglioti_U = round(parameters[0], 7)
                        self.caglioti_V = round(parameters[1], 7)
                        self.caglioti_W = round(parameters[2], 7)

                        self.caglioti_fwhm_fit = numpy.zeros(len(self.caglioti_angles))

                        for index in range(0, len(self.caglioti_angles)):
                            self.caglioti_fwhm_fit[index] = caglioti_broadening_function(self.caglioti_angles[index], parameters[0], parameters[1], parameters[2])

                        self.caglioti_fwhm_canvas.addCurve(self.caglioti_angles, self.caglioti_fwhm_fit, symbol=',', color='red', linestyle="dashed") #'+', '^',

                    except:
                        self.caglioti_U = -1.000
                        self.caglioti_V = -1.000
                        self.caglioti_W = -1.000
                else:
                    self.caglioti_U = 0.000
                    self.caglioti_V = 0.000
                    self.caglioti_W = 0.000




    ############################################################
    # EVENT MANAGEMENT METHODS
    ############################################################

    def stopSimulation(self):
        if ConfirmDialog.confirmed(parent=self, message="Confirm Interruption of the Simulation?"):
            self.run_simulation = False

    def resetBackground(self):
        if ConfirmDialog.confirmed(parent=self, message="Confirm Reset of the Simulated Background?"):
            cursor = range(0, len(self.noise))

            for angle_index in cursor:
                self.noise[angle_index] = 0

            self.plotResult(clear_caglioti=False)
            self.writeOutFile()

    def resetSimulation(self):
        if ConfirmDialog.confirmed(parent=self, message="Confirm Reset of the Simulated Data?"):
            self.current_new_beam = 0

            cursor = range(0, len(self.counts))

            for angle_index in cursor:
                self.current_counts[angle_index] = 0.0
                self.counts[angle_index] = 0.0
                self.squared_counts[angle_index] = 0.0
                self.points_per_bin[angle_index] = 0

            cursor =  range(0, len(self.absorption_coefficients))

            for index in cursor:
                self.absorption_coefficients[index] = 0.0

            cursor = range(0, len(self.noise))

            for angle_index in cursor:
                self.noise[angle_index] = 0

            self.plotResult()
            self.writeOutFile()

            self.setTabsAndButtonsEnabled(True)

            self.reset_button_pressed = True

    def checkFields(self):
        self.number_of_origin_points = ShadowGui.checkStrictlyPositiveNumber(self.number_of_origin_points, "Number of Origin Points into the Capillary")
        self.number_of_rotated_rays = ShadowGui.checkStrictlyPositiveNumber(self.number_of_rotated_rays, "Number of Generated Rays in the Powder Diffraction Arc")

        if self.incremental == 1:
            self.number_of_executions = ShadowGui.checkStrictlyPositiveNumber(self.number_of_executions, "Number of Executions")

        self.degrees_around_peak = ShadowGui.checkStrictlyPositiveNumber(self.degrees_around_peak, "Degrees around Peak")

        if self.beam_units_in_use == 0:
            self.beam_energy = ShadowGui.checkStrictlyPositiveNumber(self.beam_energy, "Beam Energy")
        else:
            self.beam_wavelength = ShadowGui.checkStrictlyPositiveNumber(self.beam_wavelength, "Wavelength")

        #############

        self.capillary_diameter = ShadowGui.checkStrictlyPositiveNumber(self.capillary_diameter, "Capillary Diameter")
        self.capillary_thickness = ShadowGui.checkStrictlyPositiveNumber(self.capillary_thickness, "Capillary Thickness")
        self.packing_factor = ShadowGui.checkStrictlyPositiveNumber(self.packing_factor, "Packing Factor")
        self.residual_average_size = ShadowGui.checkPositiveNumber(self.residual_average_size, "Residual Average Size")

        if self.diffracted_arm_type == 0:
            self.detector_distance = ShadowGui.checkStrictlyPositiveNumber(self.detector_distance, "Detector Distance")
            self.slit_1_distance = ShadowGui.checkStrictlyPositiveNumber(self.slit_1_distance, "Slit 1 Distance from Goniometer Center")
            self.slit_1_vertical_aperture = ShadowGui.checkStrictlyPositiveNumber(self.slit_1_vertical_aperture, "Slit 1 Vertical Aperture")
            self.slit_1_horizontal_aperture = ShadowGui.checkStrictlyPositiveNumber(self.slit_1_horizontal_aperture, "Slit 1 Horizontal Aperture")
            self.slit_2_distance = ShadowGui.checkStrictlyPositiveNumber(self.slit_2_distance, "Slit 2 Distance from Goniometer Center")
            self.slit_2_vertical_aperture = ShadowGui.checkStrictlyPositiveNumber(self.slit_2_vertical_aperture, "Slit 2 Vertical Aperture")
            self.slit_2_horizontal_aperture = ShadowGui.checkStrictlyPositiveNumber(self.slit_2_horizontal_aperture, "Slit 2 Horizontal Aperture")
            if self.slit_1_distance >= self.slit_2_distance: raise Exception("Slit 1 Distance from Goniometer Center >= Slit 2 Distance from Goniometer Center")
        elif self.diffracted_arm_type == 1:
            self.acceptance_slit_distance = ShadowGui.checkStrictlyPositiveNumber(self.acceptance_slit_distance, "Slit Distance from Goniometer Center")
            self.acceptance_slit_vertical_aperture = ShadowGui.checkStrictlyPositiveNumber(self.acceptance_slit_vertical_aperture, "Slit Vertical Aperture")
            self.acceptance_slit_horizontal_aperture = ShadowGui.checkStrictlyPositiveNumber(self.acceptance_slit_horizontal_aperture, "Slit Horizontal Aperture")
            self.analyzer_distance = ShadowGui.checkStrictlyPositiveNumber(self.analyzer_distance, "Crystal Distance from Goniometer Center")
            self.analyzer_bragg_angle = ShadowGui.checkStrictlyPositiveNumber(self.analyzer_bragg_angle, "Analyzer Incidence Angle")
            if self.analyzer_bragg_angle >= 90: raise Exception("Analyzer Incidence Angle >= 90 deg")
            ShadowGui.checkFile(self.rocking_curve_file)
            self.mosaic_angle_spread_fwhm = ShadowGui.checkPositiveNumber(self.mosaic_angle_spread_fwhm, "Mosaic Angle Spread FWHM")
            if self.acceptance_slit_distance >= self.analyzer_distance: raise Exception("Slit Distance from Goniometer Center >= Crystal Distance from Goniometer Center")
        elif self.diffracted_arm_type == 2:
            self.area_detector_distance = ShadowGui.checkStrictlyPositiveNumber(self.area_detector_distance,
                                                                                "Detector Distance")
            self.area_detector_height = ShadowGui.checkStrictlyPositiveNumber(self.area_detector_height,
                                                                              "Detector Height")
            self.area_detector_width = ShadowGui.checkStrictlyPositiveNumber(self.area_detector_width, "Detector Width")
            self.area_detector_pixel_size = ShadowGui.checkStrictlyPositiveNumber(self.area_detector_pixel_size,
                                                                                  "Pixel Size")

        self.start_angle_na = ShadowGui.checkPositiveAngle(self.start_angle_na, "Start Angle")
        self.stop_angle_na = ShadowGui.checkPositiveAngle(self.stop_angle_na, "Stop Angle")
        if self.start_angle_na >= self.stop_angle_na: raise Exception("Start Angle >= Stop Angle")
        if self.stop_angle_na > 180: raise Exception("Stop Angle > 180 deg")

        self.step = ShadowGui.checkPositiveAngle(self.step, "Step")

        if self.set_number_of_peaks == 1:
            self.number_of_peaks = ShadowGui.checkStrictlyPositiveNumber(self.number_of_peaks, "Number of Peaks")

        #############

        if self.add_lorentz_polarization_factor == 1:
            if self.pm2k_fullprof == 0:
                self.degree_of_polarization = ShadowGui.checkPositiveNumber(self.degree_of_polarization, "Q Factor")
            else:
                self.degree_of_polarization = ShadowGui.checkPositiveNumber(self.degree_of_polarization, "K Factor")

            self.monochromator_angle = ShadowGui.checkPositiveAngle(self.monochromator_angle, "Monochromator Theta Angle")
            if self.monochromator_angle >= 90: raise Exception("Monochromator Theta Angle >= 90 deg")

        if self.add_debye_waller_factor == 1 and self.use_default_dwf == 0:
            self.new_debye_waller_B = ShadowGui.checkPositiveNumber(self.new_debye_waller_B, "Debye-Waller Factor (B)")

        #############

        self.positioning_error = ShadowGui.checkPositiveNumber(self.positioning_error, "Position Error")

        #############

        if self.add_constant == 1:
            self.constant_value = ShadowGui.checkStrictlyPositiveNumber(self.constant_value, "Constant Background Value")

    ############################################################
    # MAIN METHOD - SIMULATION ALGORITHM
    ############################################################

    def simulate(self):
        try:
            if self.input_beam is None: raise Exception("No input beam, run the optical simulation first")
            elif not hasattr(self.input_beam.beam, "rays"): raise Exception("No good rays, modify the optical simulation")

            sys.stdout = EmittingStream(textWritten=self.writeStdOut)

            if self.trace_shadow:
                grabber = TTYGrabber()
                grabber.start()

            self.error(self.error_id)

            go = numpy.where(self.input_beam.beam.rays[:,9] == 1)

            go_input_beam = ShadowBeam()
            go_input_beam.beam.rays = copy.deepcopy(self.input_beam.beam.rays[go])

            number_of_input_rays = len(go_input_beam.beam.rays)

            if number_of_input_rays == 0: raise Exception("No good rays, modify the optical simulation")

            self.random_generator_flat.seed()

            input_rays = range(0, number_of_input_rays)

            self.checkFields()

            self.backupOutFile()

            self.run_simulation = True
            self.setTabsAndButtonsEnabled(False)

            executions = range(0,1)

            if (self.incremental==1):
                executions = range(0, self.number_of_executions)

            ################################
            # ARRAYS FOR OUTPUT AND PLOTS

            steps = self.initialize()

            ################################
            # PARAMETERS CALCULATED ONCE

            # distances in CM

            capillary_radius = self.capillary_diameter*(1+self.positioning_error*0.01)*0.1*0.5
            displacement_h = self.horizontal_displacement*1e-4
            displacement_v = self.vertical_displacement*1e-4

            self.D_1 = self.slit_1_distance
            self.D_2 = self.slit_2_distance

            self.horizontal_acceptance_slit_1 = self.slit_1_horizontal_aperture*1e-4
            self.vertical_acceptance_slit_1 = self.slit_1_vertical_aperture*1e-4
            self.horizontal_acceptance_slit_2 = self.slit_2_horizontal_aperture*1e-4
            self.vertical_acceptance_slit_2 = self.slit_2_vertical_aperture*1e-4

            self.slit_1_vertical_displacement_cm = self.slit_1_vertical_displacement*1e-4
            self.slit_2_vertical_displacement_cm = self.slit_2_vertical_displacement*1e-4
            self.slit_1_horizontal_displacement_cm = self.slit_1_horizontal_displacement*1e-4
            self.slit_2_horizontal_displacement_cm = self.slit_2_horizontal_displacement*1e-4

            self.x_sour_offset_cm = self.x_sour_offset*1e-4
            self.y_sour_offset_cm = self.y_sour_offset*1e-4
            self.z_sour_offset_cm = self.z_sour_offset*1e-4

            self.horizontal_acceptance_analyzer = self.acceptance_slit_horizontal_aperture*1e-4
            self.vertical_acceptance_analyzer = self.acceptance_slit_vertical_aperture*1e-4

            if self.beam_units_in_use == 0 : #eV
                avg_wavelength = ShadowPhysics.getWavelengthFromEnergy(self.beam_energy)
            else:
                avg_wavelength = self.beam_wavelength # in Angstrom

            if self.set_number_of_peaks == 1:
                reflections = self.getReflections(self.sample_material, self.number_of_peaks, avg_wavelength=avg_wavelength)
            else:
                reflections = self.getReflections(self.sample_material, avg_wavelength=avg_wavelength)

            if self.calculate_absorption == 1:
                self.absorption_normalization_factor = 1/self.getTransmittance(capillary_radius*2, avg_wavelength)

            ################################
            # EXECUTION CYCLES

            for execution in executions:
                if not self.run_simulation: break

                self.resetCurrentCounts(steps)

                self.le_current_execution.setText(str(execution+1))

                self.progressBarInit()

                if (self.incremental == 1 and self.number_of_executions > 1):
                    self.setStatusMessage("Running XRD Capillary Simulation on " + str(number_of_input_rays)+ " rays: " + str(execution+1) + " of " + str(self.number_of_executions))
                else:
                    self.setStatusMessage("Running XRD Capillary Simulation on " + str(number_of_input_rays)+ " rays")

                self.progressBarSet(0)

                bar_value, diffracted_rays = self.generateDiffractedRays(0,
                                                                         capillary_radius,
                                                                         displacement_h,
                                                                         displacement_v,
                                                                         go_input_beam,
                                                                         input_rays,
                                                                         (50/number_of_input_rays),
                                                                         reflections)

                self.average_absorption_coefficient = round(numpy.array(self.absorption_coefficients).mean(), 2)
                self.sample_transmittance = round(100*numpy.exp(-self.average_absorption_coefficient*self.capillary_diameter*0.5*0.1), 2)
                self.muR = round(self.average_absorption_coefficient*self.capillary_diameter*0.5*0.1, 2)

                if (self.incremental == 1 and self.number_of_executions > 1):
                    self.setStatusMessage("Running XRD Capillary Simulation on " + str(len(diffracted_rays))+ " diffracted rays: " + str(execution+1) + " of " + str(self.number_of_executions))
                else:
                    self.setStatusMessage("Running XRD Capillary Simulation on " + str(len(diffracted_rays))+ " diffracted rays")

                self.send("Beam", self.generateXRDPattern(bar_value, diffracted_rays, avg_wavelength, reflections))

            self.writeOutFile()

            self.progressBarSet(100)
            self.setSimulationTabsAndButtonsEnabled(True)

            self.setStatusMessage("")

            self.progressBarFinished()

            if self.trace_shadow:
                grabber.stop()

                for row in grabber.ttyData:
                    self.writeStdOut(row)

            if self.run_simulation == True:
                self.send("Trigger", ShadowTriggerIn(new_beam=True))
            else:
                self.run_simulation=True
                self.send("Trigger", ShadowTriggerIn(interrupt=True))
        except Exception as exception:
            self.error_id = self.error_id + 1
            self.error(self.error_id, "Exception occurred: " + str(exception))

            QtGui.QMessageBox.critical(self, "QMessageBox.critical()",
                exception.args[0],
                QtGui.QMessageBox.Ok)
            #raise exception

    #######################################################

    def simulateBackground(self):
        if self.input_beam is None: return

        sys.stdout = EmittingStream(textWritten=self.writeStdOut)

        if len(self.twotheta_angles) == 0:
            self.initialize()

        if self.add_background ==  1:
            self.calculateBackground(0)
            self.plotResult(clear_caglioti=False)
            self.writeOutFile()

        self.progressBarFinished()

    ############################################################
    # SIMULATION ALGORITHM METHODS
    ############################################################

    def generateDiffractedRays(self, bar_value, capillary_radius, displacement_h, displacement_v, go_input_beam, input_rays, percentage_fraction, reflections):

        #self.out_file = open("diff.dat", "w")
        #self.out_file_2 = open("diff2.dat", "w")
        # self.out_file_3 = open("entry.dat", "w")
        # self.out_file_4 = open("exit_cap.dat", "w")
        # self.out_file_5 = open("origin.dat", "w")

        diffracted_rays = []

        no_prog = False

        for ray_index in input_rays:
            if not self.run_simulation: break
            # costruzione intersezione con capillare (interno ed esterno x assorbimento) + displacement del capillare

            Es_x = go_input_beam.beam.rays[ray_index, 6]
            Es_y = go_input_beam.beam.rays[ray_index, 7]
            Es_z = go_input_beam.beam.rays[ray_index, 8]
            k_mod = go_input_beam.beam.rays[ray_index, 10]
            Es_phi = go_input_beam.beam.rays[ray_index, 13]
            Ep_phi = go_input_beam.beam.rays[ray_index, 14]
            Ep_x = go_input_beam.beam.rays[ray_index, 15]
            Ep_y = go_input_beam.beam.rays[ray_index, 16]
            Ep_z = go_input_beam.beam.rays[ray_index, 17]

            wrong_numbers = numpy.isnan(Es_x) or numpy.isnan(Es_y) or numpy.isnan(Es_z) or \
                            numpy.isnan(Ep_x) or numpy.isnan(Ep_y) or numpy.isnan(Ep_z) or \
                            numpy.isnan(Es_phi) or numpy.isnan(Ep_phi) or numpy.isnan(k_mod)

            if not wrong_numbers:
                x_0 = go_input_beam.beam.rays[ray_index, 0]
                y_0 = go_input_beam.beam.rays[ray_index, 1]
                z_0 = go_input_beam.beam.rays[ray_index, 2]

                if (y_0 ** 2 + z_0 ** 2 < capillary_radius ** 2):
                    v_0_x = go_input_beam.beam.rays[ray_index, 3]
                    v_0_y = go_input_beam.beam.rays[ray_index, 4]
                    v_0_z = go_input_beam.beam.rays[ray_index, 5]

                    k_1 = v_0_y / v_0_x
                    k_2 = v_0_z / v_0_x

                    a = (k_1 ** 2 + k_2 ** 2)
                    b = 2 * (k_1 * (y_0 + displacement_h) + k_2 * (z_0 + displacement_v))
                    c = (y_0 ** 2 + z_0 ** 2 + 2 * displacement_h * y_0 + 2 * displacement_v * z_0) - \
                        capillary_radius ** 2 + (displacement_h ** 2 + displacement_v ** 2)

                    if (self.calculate_absorption == 1): c_2 = (
                                                               y_0 ** 2 + z_0 ** 2 + 2 * displacement_h * y_0 + 2 * displacement_v * z_0) - \
                                                               (capillary_radius + (
                                                               self.capillary_thickness * 0.1)) ** 2 + (
                                                               displacement_h ** 2 + displacement_v ** 2)

                    discriminant = b ** 2 - 4 * a * c
                    if (self.calculate_absorption == 1): discriminant_2 = b ** 2 - 4 * a * c_2

                    if discriminant > 0.0:
                        x_sol_1 = (-b - numpy.sqrt(discriminant)) / (2 * a)
                        x_1 = x_0 + x_sol_1
                        y_1 = y_0 + k_1 * x_sol_1
                        z_1 = z_0 + k_2 * x_sol_1

                        x_sol_2 = (-b + numpy.sqrt(discriminant)) / (2 * a)
                        x_2 = x_0 + x_sol_2
                        y_2 = y_0 + k_1 * x_sol_2
                        z_2 = z_0 + k_2 * x_sol_2

                        if (self.calculate_absorption == 1):
                            x_sol_1_out = (-b - numpy.sqrt(discriminant_2)) / (2 * a)
                            x_1_out = x_0 + x_sol_1_out
                            y_1_out = y_0 + k_1 * x_sol_1_out
                            z_1_out = z_0 + k_2 * x_sol_1_out

                            x_sol_2_out = (-b + numpy.sqrt(discriminant_2)) / (2 * a)
                            x_2_out = x_0 + x_sol_2_out
                            y_2_out = y_0 + k_1 * x_sol_2
                            z_2_out = z_0 + k_2 * x_sol_2

                        if (y_1 < y_2):
                            entry_point = [x_1, y_1, z_1]
                            if (self.calculate_absorption == 1): entry_point_out = [x_1_out, y_1_out, z_1_out]
                            exit_point = [x_2, y_2, z_2]
                        else:
                            entry_point = [x_2, y_2, z_2]
                            if (self.calculate_absorption == 1): entry_point_out = [x_2_out, y_2_out, z_2_out]
                            exit_point = [x_1, y_1, z_1]

                        path = ShadowMath.vector_modulus(ShadowMath.vector_difference(exit_point, entry_point))

                        x_axis = [1, 0, 0]
                        v_in = [v_0_x, v_0_y, v_0_z]

                        z_axis_ray = ShadowMath.vectorial_product(x_axis, v_in)
                        rotation_axis_diffraction = ShadowMath.vectorial_product(v_in, z_axis_ray)
                        rotation_axis_debye_circle = v_in

                        wavelength = ShadowPhysics.getWavelengthfromShadowK(k_mod)

                        if self.calculate_absorption == 1:
                            mu = self.getLinearAbsorptionCoefficient(wavelength)
                            self.absorption_coefficients.append(mu)
                            random_generator_absorption = RandomGenerator(mu, path)

                        for origin_point_index in range(0, int(self.number_of_origin_points)):

                            if self.calculate_absorption == 1:
                                random_path = random_generator_absorption.random()
                            else:
                                random_path = path * self.random_generator_flat.random()

                            # calcolo di un punto casuale sul segmento congiungente.

                            x_point = entry_point[0] + random_path * v_in[0]
                            y_point = entry_point[1] + random_path * v_in[1]
                            z_point = entry_point[2] + random_path * v_in[2]

                            origin_point = [x_point, y_point, z_point]

                            for reflection in reflections:
                                if not self.run_simulation: break

                                ray_bragg_angle = self.calculateBraggAngle(reflection, wavelength)

                                delta_theta_darwin = (2 * numpy.random.random() - 1) * self.calculateDarwinWidth(
                                    reflection, wavelength, ray_bragg_angle)  # darwin width fluctuations

                                if self.residual_average_size > 0:
                                    delta_theta_size = 2 * numpy.random.normal(0.0, (0.94 * wavelength) / (
                                        self.residual_average_size * 1e4), 1)  # residual size effects
                                else:
                                    delta_theta_size = 0.0

                                twotheta_reflection = 2 * ray_bragg_angle + delta_theta_darwin + delta_theta_size

                                # rotazione del vettore d'onda pari all'angolo di bragg
                                #
                                # calcolo del vettore ruotato di 2theta bragg, con la formula di Rodrigues:
                                #
                                # k_diffracted = k * cos(2th) + (asse_rot x k) * sin(2th) + asse_rot*(asse_rot . k)(1 - cos(2th))
                                #

                                # v_out_temp_1 = ShadowMath.vector_multiply(v_in, numpy.cos(twotheta_reflection))
                                # v_out_temp_2 = ShadowMath.vector_multiply(ShadowMath.vectorial_product(rotation_axis_diffraction, v_in),
                                #                                           numpy.sin(twotheta_reflection))
                                # v_out_temp_3 = ShadowMath.vector_multiply(rotation_axis_diffraction,
                                #                                           ShadowMath.scalar_product(rotation_axis_diffraction, v_in) * (1 - numpy.cos(twotheta_reflection)))
                                #
                                # v_out_temp = ShadowMath.vector_sum(v_out_temp_1,
                                #                                    ShadowMath.vector_sum(v_out_temp_2, v_out_temp_3))

                                v_out_temp = ShadowMath.vector_rotate(rotation_axis_diffraction, twotheta_reflection, v_in)

                                # self.out_file.write(str(origin_point[0] + v_out_temp[0]*self.detector_distance) + " " + \
                                #                    str(origin_point[1] + v_out_temp[1]*self.detector_distance) + " " + \
                                #                    str(origin_point[2] + v_out_temp[2]*self.detector_distance) + "\n")

                                # intersezione raggi con sfera di raggio distanza con il detector. le intersezioni con Z < 0 vengono rigettate
                                #
                                # retta P = origin_point + v t
                                #
                                # punto P0 minima distanza con il centro della sfera in 0,0,0
                                #
                                # (P0 - O) * v = 0 => P0 * v = 0 => (origin_point + v t0) * v = 0
                                #
                                # => t0 = - origin_point * v

                                t_0 = -1 * ShadowMath.scalar_product(origin_point, v_out_temp)
                                P_0 = ShadowMath.vector_sum(origin_point, ShadowMath.vector_multiply(v_out_temp, t_0))

                                b = ShadowMath.vector_modulus(P_0)
                                a = numpy.sqrt(self.detector_distance ** 2 - b ** 2)

                                # N.B. punti di uscita hanno solo direzione in avanti.
                                P_2 = ShadowMath.vector_sum(origin_point,
                                                            ShadowMath.vector_multiply(v_out_temp, t_0 + a))

                                # ok se P2 con z > 0
                                if (P_2[2] >= 0):

                                    #
                                    # genesi del nuovo raggio diffratto attenuato dell'intensità relativa e dell'assorbimento
                                    #

                                    delta_angles = self.calculateDeltaAngles(twotheta_reflection)

                                    for delta_index in range(0, len(delta_angles)):

                                        delta_angle = delta_angles[delta_index]

                                        #
                                        # calcolo del vettore ruotato di delta, con la formula di Rodrigues:
                                        #
                                        # v_out_new = v_out * cos(delta) + (asse_rot x v_out ) * sin(delta) + asse_rot*(asse_rot . v_out )(1 - cos(delta))
                                        #
                                        # asse rot = v_in
                                        #

                                        # v_out_1 = ShadowMath.vector_multiply(v_out_temp, numpy.cos(delta_angle))
                                        # v_out_2 = ShadowMath.vector_multiply(
                                        #     ShadowMath.vectorial_product(rotation_axis_debye_circle, v_out_temp),
                                        #     numpy.sin(delta_angle))
                                        # v_out_3 = ShadowMath.vector_multiply(rotation_axis_debye_circle,
                                        #                                      ShadowMath.scalar_product(
                                        #                                          rotation_axis_debye_circle,
                                        #                                          v_out_temp) * (
                                        #                                          1 - numpy.cos(delta_angle)))
                                        #
                                        # v_out = ShadowMath.vector_sum(v_out_1, ShadowMath.vector_sum(v_out_2, v_out_3))

                                        v_out = ShadowMath.vector_rotate(rotation_axis_debye_circle, delta_angle, v_out_temp)

                                        # self.out_file_2.write(str(origin_point[0] + v_out[0]*self.detector_distance) + " " + \
                                        #                      str(origin_point[1] + v_out[1]*self.detector_distance) + " " + \
                                        #                      str(origin_point[2] + v_out[2]*self.detector_distance) + "\n")

                                        reduction_factor = reflection.relative_intensity

                                        if (self.calculate_absorption == 1):
                                            reduction_factor = reduction_factor * self.calculateAbsorption(wavelength,
                                                                                                           entry_point,
                                                                                                           entry_point_out,
                                                                                                           origin_point,
                                                                                                           v_out,
                                                                                                           capillary_radius,
                                                                                                           displacement_h,
                                                                                                           displacement_v)

                                        reduction_factor = numpy.sqrt(reduction_factor)

                                        diffracted_ray_circle = numpy.zeros(18)

                                        diffracted_ray_circle[0] = origin_point[0]  # X
                                        diffracted_ray_circle[1] = origin_point[1]  # Y
                                        diffracted_ray_circle[2] = origin_point[2]  # Z
                                        diffracted_ray_circle[3] = v_out[0]  # director cos x
                                        diffracted_ray_circle[4] = v_out[1]  # director cos y
                                        diffracted_ray_circle[5] = v_out[2]  # director cos z
                                        diffracted_ray_circle[6] = Es_x * reduction_factor
                                        diffracted_ray_circle[7] = Es_y * reduction_factor
                                        diffracted_ray_circle[8] = Es_z * reduction_factor
                                        diffracted_ray_circle[9] = go_input_beam.beam.rays[ray_index, 9]  # good/lost
                                        diffracted_ray_circle[10] = k_mod  # |k|
                                        diffracted_ray_circle[11] = go_input_beam.beam.rays[ray_index, 11]  # ray index
                                        diffracted_ray_circle[12] = 1  # good only
                                        diffracted_ray_circle[13] = Es_phi
                                        diffracted_ray_circle[14] = Ep_phi
                                        diffracted_ray_circle[15] = Ep_x * reduction_factor
                                        diffracted_ray_circle[16] = Ep_y * reduction_factor
                                        diffracted_ray_circle[17] = Ep_z * reduction_factor

                                        diffracted_rays.append(diffracted_ray_circle)

                bar_value = bar_value + percentage_fraction

                if int(bar_value) % 5 == 0:
                    if not no_prog:
                        self.progressBarSet(bar_value)
                        no_prog = True
                else:
                    no_prog = False

        #self.out_file.close()
        #self.out_file_2.close()
        # self.out_file_3.close()
        # self.out_file_4.close()
        # self.out_file_5.close()

        return bar_value, diffracted_rays

    def calculateBraggAngle(self, reflection, wavelength):
        crystal = self.getMaterialXraylibCrystal(self.sample_material)
        energy = ShadowPhysics.getEnergyFromWavelength(wavelength)/1000

        return xraylib.Bragg_angle(crystal, energy, reflection.h, reflection.k, reflection.l)

    def calculateDarwinWidth(self, reflection, wavelength, bragg_angle):
        crystal = self.getMaterialXraylibCrystal(self.sample_material)
        energy = ShadowPhysics.getEnergyFromWavelength(wavelength)/1000
        debyeWaller = 1.0
        asymmetry_factor = -1.0

        fH = xraylib.Crystal_F_H_StructureFactor(crystal, energy, reflection.h, reflection.k, reflection.l, debyeWaller, 1.0)

        codata = scipy.constants.codata.physical_constants
        codata_r, tmp1, tmp2 = codata["classical electron radius"]
        volume = crystal['volume'] # volume of  unit cell in cm^3

        cte = - (codata_r*1e10) * wavelength*wavelength/(numpy.pi * volume)
        chiH = cte*fH

        return 2*numpy.absolute(chiH)/numpy.sqrt(numpy.abs(asymmetry_factor))/numpy.sin(2*bragg_angle)

    ############################################################

    def generateXRDPattern(self, bar_value, diffracted_rays, avg_wavelength, reflections):

        number_of_diffracted_rays = len(diffracted_rays)

        diffracted_beam = ShadowBeam()

        if (number_of_diffracted_rays > 0 and self.run_simulation):

            diffracted_beam.beam.rays = numpy.array(diffracted_rays)

            percentage_fraction = 50 / len(reflections)

            max_position = len(self.twotheta_angles) - 1

            twotheta_bragg = 0.0
            normalization = 1.0
            debye_waller_B = 1.0

            if self.add_lorentz_polarization_factor:
                if self.pm2k_fullprof == 0:
                    reflection_index = int(numpy.floor(len(reflections)/2))
                    twotheta_bragg = reflections[reflection_index].twotheta_bragg

                    normalization = self.calculateLPFactorPM2K(numpy.degrees(twotheta_bragg), twotheta_bragg/2)
                else:
                    normalization = self.calculateLPFactorFullProf((self.stop_angle - self.start_angle)/2)

            if self.add_debye_waller_factor:
                if self.use_default_dwf:
                    debye_waller_B = self.getDebyeWallerB(self.sample_material)
                else:
                    debye_waller_B = self.new_debye_waller_B

            statistic_factor = 1.0
            if self.normalize:
                statistic_factor = 1 / (self.number_of_origin_points * self.number_of_rotated_rays)

            if self.diffracted_arm_type == 2:
                diffracted_beam = self.traceTo2DDetector(bar_value, diffracted_beam, avg_wavelength, twotheta_bragg,
                                                         normalization, debye_waller_B, statistic_factor)
                if not diffracted_beam is None:
                    if self.area_detector_beam is None:
                        self.area_detector_beam = diffracted_beam
                    else:
                        self.area_detector_beam = ShadowBeam.mergeBeams(self.area_detector_beam, diffracted_beam)

                    # Creation of 1D pattern: weighted (with intensity) histogram of twotheta angles
                    x_coord = self.area_detector_beam.beam.rays[:, 0]
                    z_coord = self.area_detector_beam.beam.rays[:, 2]

                    r_coord = numpy.sqrt(x_coord ** 2 + z_coord ** 2)

                    twotheta_angles = numpy.degrees(numpy.arctan(r_coord / self.detector_distance))

                    intensity = self.area_detector_beam.beam.rays[:, 6] ** 2 + self.area_detector_beam.beam.rays[:, 7] ** 2 + self.area_detector_beam.beam.rays[:, 8] ** 2 + \
                                self.area_detector_beam.beam.rays[:, 15] ** 2 + self.area_detector_beam.beam.rays[:, 16] ** 2 + self.area_detector_beam.beam.rays[:, 17] ** 2

                    maximum = numpy.max(intensity)

                    weights = (intensity / maximum)

                    histogram, edges = numpy.histogram(a=twotheta_angles, bins=numpy.append(self.twotheta_angles,
                                                                                            max(self.twotheta_angles) + self.step),
                                                       weights=weights)

                    self.counts = histogram

                self.plot2DResults()
                self.plotResult(reflections=reflections)
                self.writeOutFile()
            else:
                for reflection in reflections:
                    if not self.run_simulation: break

                    twotheta_bragg = reflection.twotheta_bragg

                    theta_lim_inf = numpy.degrees(twotheta_bragg) - self.degrees_around_peak
                    theta_lim_sup = numpy.degrees(twotheta_bragg) + self.degrees_around_peak

                    if (theta_lim_inf < self.stop_angle and theta_lim_sup > self.start_angle):
                        n_steps_inf = int(numpy.floor((max(theta_lim_inf, self.start_angle) - self.start_angle) / self.step))
                        n_steps_sup = int(numpy.ceil((min(theta_lim_sup, self.stop_angle) - self.start_angle) / self.step))

                        n_steps = n_steps_sup - n_steps_inf

                        if n_steps > 0:
                            percentage_fraction_2 = percentage_fraction/n_steps

                        no_prog = False

                        for step in range(0, n_steps):
                            if not self.run_simulation: break

                            angle_index = min(n_steps_inf + step, max_position)

                            if self.diffracted_arm_type == 0:
                                out_beam = self.traceFromSlits(diffracted_beam, angle_index)
                            elif self.diffracted_arm_type == 1:
                                out_beam = self.traceFromAnalyzer(diffracted_beam, angle_index)

                            go_rays = out_beam.beam.rays[numpy.where(out_beam.beam.rays[:,9] == 1)]

                            if (len(go_rays) > 0):
                                physical_coefficent = 1.0

                                if self.add_lorentz_polarization_factor:
                                    if self.pm2k_fullprof == 0:
                                        lorentz_polarization_factor = self.calculateLPFactorPM2K(
                                            self.twotheta_angles[angle_index], twotheta_bragg / 2,
                                            normalization=normalization)
                                    else:
                                        lorentz_polarization_factor = self.calculateLPFactorFullProf(
                                            self.twotheta_angles[angle_index], normalization=normalization)

                                    physical_coefficent = physical_coefficent * lorentz_polarization_factor

                                if self.add_debye_waller_factor:
                                    physical_coefficent = physical_coefficent * self.calculateDebyeWallerFactor(
                                        self.twotheta_angles[angle_index], avg_wavelength, debye_waller_B)

                                for ray_index in range(0, len(go_rays)):
                                    if not self.run_simulation: break

                                    intensity_i = go_rays[ray_index, 6]**2 + go_rays[ray_index, 7]**2 + go_rays[ray_index, 8]**2 + \
                                                  go_rays[ray_index, 15]**2 + go_rays[ray_index, 16]**2 + go_rays[ray_index, 17]**2

                                    if not numpy.isnan(physical_coefficent*intensity_i):
                                        self.current_counts[angle_index] = self.current_counts[
                                                                               angle_index] + physical_coefficent * intensity_i * statistic_factor

                                        self.squared_counts[angle_index] = self.squared_counts[angle_index] + (
                                                                                                              physical_coefficent * intensity_i * statistic_factor) **2
                                        self.points_per_bin[angle_index] = self.points_per_bin[angle_index] + 1

                            bar_value = bar_value + percentage_fraction_2

                            if int(bar_value) % 5 == 0:
                                if not no_prog:
                                    self.progressBarSet(bar_value)
                                    no_prog = True
                            else:
                                no_prog = False

                    for index in range(0, len(self.counts)):
                        self.counts[index] = self.counts[index] + self.current_counts[index]

                self.plotResult(reflections=reflections)
                self.writeOutFile()

            return diffracted_beam

    ############################################################

    def calculateDeltaAngles(self, twotheta_reflection):

        if self.diffracted_arm_type == 0:
            width = self.slit_1_horizontal_aperture*1e-4*0.5
            delta_1 = numpy.arctan(width/self.D_1)

            width = self.slit_2_horizontal_aperture*1e-4*0.5
            delta_2 = numpy.arctan(width/self.D_2)

            delta = min(delta_1, delta_2)
        elif self.diffracted_arm_type == 1:
            width = self.acceptance_slit_horizontal_aperture*1e-4*0.5
            delta = numpy.arctan(width/self.acceptance_slit_distance)
        else:
            delta=numpy.pi

        delta_angles = []

        for index in range(0, int(self.number_of_rotated_rays)):
            delta = self.random_generator_flat.random()*delta
            random2 = self.random_generator_flat.random()

            if random2 >= 0.5:
                delta_angles.append(-delta)
            else:
                delta_angles.append(delta)

        return delta_angles

    ############################################################
        
    def calculateBackground(self, bar_value):

        percentage_fraction = 50/len(self.twotheta_angles)

        cursor = range(0, len(self.twotheta_angles))

        self.n_sigma = 0.5*(1 + self.n_sigma)

        for angle_index in cursor:
            background = 0
            if (self.add_chebyshev==1):
                coefficients = [self.cheb_coeff_0, self.cheb_coeff_1, self.cheb_coeff_2, self.cheb_coeff_3, self.cheb_coeff_4, self.cheb_coeff_5]
                
                background = background + ShadowPhysics.ChebyshevBackgroundNoised(coefficients=coefficients,
                                                                      twotheta=self.twotheta_angles[angle_index],
                                                                      n_sigma=self.n_sigma,
                                                                      random_generator=self.random_generator_flat)
                
            if (self.add_expdecay==1):
                coefficients = [self.expd_coeff_0, self.expd_coeff_1, self.expd_coeff_2, self.expd_coeff_3, self.expd_coeff_4, self.expd_coeff_5]
                decayparams = [self.expd_decayp_0, self.expd_decayp_1, self.expd_decayp_2, self.expd_decayp_3, self.expd_decayp_4, self.expd_decayp_5]
                
                background = background + ShadowPhysics.ExpDecayBackgroundNoised(coefficients=coefficients,
                                                                     decayparams=decayparams,
                                                                     twotheta=self.twotheta_angles[angle_index],
                                                                     n_sigma=self.n_sigma,
                                                                     random_generator=self.random_generator_flat)
            self.noise[angle_index] = self.noise[angle_index] + background

        bar_value = bar_value + percentage_fraction
        self.progressBarSet(bar_value)

    ############################################################

    def calculateSignal(self, angle_index):
        return round(self.counts[angle_index] + self.noise[angle_index], 2)

    ############################################################

    def calculateStatisticError(self, angle_index):
        error_on_counts = 0.0
        if self.points_per_bin[angle_index] > 0:
            error_on_counts = numpy.sqrt(max((self.counts[angle_index]**2-self.squared_counts[angle_index])/self.points_per_bin[angle_index], 0)) # RANDOM-GAUSSIAN

        error_on_noise = numpy.sqrt(self.noise[angle_index]) # POISSON

        return numpy.sqrt(error_on_counts**2 + error_on_noise**2)


    def getCagliotisData(self, reflections):
        angles = []
        data_fwhm = []
        data_shift = []

        max_position = len(self.twotheta_angles) - 1

        for reflection in reflections:
            twotheta_bragg = numpy.degrees(reflection.twotheta_bragg)

            theta_lim_inf = twotheta_bragg - self.degrees_around_peak
            theta_lim_sup = twotheta_bragg + self.degrees_around_peak

            if (theta_lim_inf < self.stop_angle and theta_lim_sup > self.start_angle):
                n_steps_inf = int(numpy.floor((max(theta_lim_inf, self.start_angle) - self.start_angle) / self.step))
                n_steps_sup = int(numpy.ceil((min(theta_lim_sup, self.stop_angle) - self.start_angle) / self.step))

                n_steps = n_steps_sup - n_steps_inf

                angles_for_fit = []
                counts_for_fit = []

                for step in range(0, n_steps):
                    angle_index = min(n_steps_inf + step, max_position)

                    angles_for_fit.append(self.twotheta_angles[angle_index])
                    counts_for_fit.append(self.counts[angle_index])

                angles.append(twotheta_bragg)

                try:
                    parameters, covariance_matrix_g = ShadowMath.gaussian_fit(angles_for_fit, counts_for_fit)

                    data_fwhm.append(numpy.abs(parameters[3]))
                    data_shift.append(twotheta_bragg-parameters[1])

                    def gaussian_function(x, A, x0, sigma):
                        return A*numpy.exp(-(x-x0)**2/(2*sigma**2))

                    for step in range(0, n_steps):
                        angle_index = min(n_steps_inf + step, max_position)

                        self.caglioti_fits[angle_index] = gaussian_function(self.twotheta_angles[angle_index], parameters[0], parameters[1], parameters[2])

                except:
                    data_fwhm.append(-1.0)
                    data_shift.append(0.0)


        return angles, data_fwhm, data_shift

    ############################################################
    # PHYSICAL CALCULATIONS
    ############################################################

    def calculateAbsorption(self, wavelength, entry_point, entry_point_out, origin_point, direction_versor, capillary_radius, displacement_h, displacement_v):

        absorption = 0

        #
        # calcolo intersezione con superficie interna ed esterna del capillare:
        #
        # x = xo + x' t
        # y = yo + y' t
        # z = zo + z' t
        #
        # (y-dh)^2 + (z-dv)^2 = (Dc/2)^2
        # (y-dh)^2 + (z-dv)^2 = ((Dc+thickness)/2)^2

        x_0 = origin_point[0]
        y_0 = origin_point[1]
        z_0 = origin_point[2]

        k_1 = direction_versor[1]/direction_versor[0]
        k_2 = direction_versor[2]/direction_versor[0]

        #
        # parametri a b c per l'equazione a(x-x0)^2 + b(x-x0) + c = 0
        #

        a = (k_1**2 + k_2**2)
        b = 2*(k_1*(y_0+displacement_h) + k_2*(z_0+displacement_v))
        c = (y_0**2 + z_0**2 + 2*displacement_h*y_0 + 2*displacement_v*z_0) - capillary_radius**2 + (displacement_h**2 + displacement_v**2)
        c_2 = (y_0**2 + z_0**2 + 2*displacement_h*y_0 + 2*displacement_v*z_0) - (capillary_radius+(self.capillary_thickness*0.1))**2 + (displacement_h**2 + displacement_v**2)

        discriminant = b**2 - 4*a*c
        discriminant_2 = b**2 - 4*a*c_2

        if (discriminant > 0):

            # equazioni risolte per x-x0
            x_1 = (-b + numpy.sqrt(discriminant))/(2*a) # (x-x0)_1
            x_2 = (-b - numpy.sqrt(discriminant))/(2*a) # (x-x0)_2

            x_1_out = (-b + numpy.sqrt(discriminant_2))/(2*a) # (x-x0)_1
            x_2_out = (-b - numpy.sqrt(discriminant_2))/(2*a) # (x-x0)_2

            x_sol = 0
            y_sol = 0
            z_sol = 0

            x_sol_out = 0
            y_sol_out = 0
            z_sol_out = 0

            # solutions only with z > 0 and
            # se y-y0 > 0 allora il versore deve avere y' > 0
            # se y-y0 < 0 allora il versore deve avere y' < 0

            z_1 = z_0 + k_2*x_1

            find_solution = False

            if (z_1 >= 0 or (z_1 < 0 and direction_versor[1] > 0)):
                if (numpy.sign((k_1*x_1))==numpy.sign(direction_versor[1])):
                    x_sol = x_1 + x_0
                    y_sol = y_0 + k_1*x_1
                    z_sol = z_1

                    x_sol_out = x_1_out + x_0
                    y_sol_out = y_0 + k_1*x_1_out
                    z_sol_out = z_0 + k_2*x_1_out

                    find_solution = True

            if not find_solution:
                z_2 = z_0 + k_2*x_2

                if (z_2 >= 0 or (z_1 < 0 and direction_versor[1] > 0)):
                    if (numpy.sign((k_1*x_2))==numpy.sign(direction_versor[1])):
                        x_sol = x_2 + x_0
                        y_sol = y_0 + k_1*x_2
                        z_sol = z_2

                        x_sol_out = x_2_out + x_0
                        y_sol_out = y_0 + k_1*x_2_out
                        z_sol_out = z_0 + k_2*x_2_out

                        find_solution = True

            if find_solution:
                exit_point = [x_sol, y_sol, z_sol]
                exit_point_out = [x_sol_out, y_sol_out, z_sol_out]

                distance = ShadowMath.point_distance(entry_point, origin_point) + ShadowMath.point_distance(origin_point, exit_point)
                distance_out = ShadowMath.point_distance(entry_point_out, entry_point) + ShadowMath.point_distance(exit_point, exit_point_out)

                absorption = self.getCapillaryTransmittance(distance_out, wavelength)*self.getTransmittance(distance, wavelength)*self.absorption_normalization_factor
            else:
                absorption = 0 # kill the ray

        return absorption

    ############################################################

    def getLinearAbsorptionCoefficient(self, wavelength):
        mu = xraylib.CS_Total_CP(self.getChemicalFormula(self.sample_material), ShadowPhysics.getEnergyFromWavelength(wavelength)/1000) # energy in KeV
        rho = self.getDensity(self.sample_material)*self.packing_factor

        return mu*rho

    def getCapillaryLinearAbsorptionCoefficient(self, wavelength):
        mu = xraylib.CS_Total_CP(self.getCapillaryChemicalFormula(self.capillary_material), ShadowPhysics.getEnergyFromWavelength(wavelength)/1000) # energy in KeV
        rho = self.getCapillaryDensity(self.capillary_material)

        return mu*rho

    def getTransmittance(self, path, wavelength):
        return numpy.exp(-self.getLinearAbsorptionCoefficient(wavelength)*path)

    def getCapillaryTransmittance(self, path, wavelength):
        return numpy.exp(-self.getCapillaryLinearAbsorptionCoefficient(wavelength)*path)

    ############################################################
    # PM2K

    def calculateLPFactorPM2K(self, twotheta_deg, bragg_angle, normalization=1.0):
        theta = numpy.radians(0.5*twotheta_deg)

        lorentz_factor = 1/(numpy.sin(theta)*numpy.sin(bragg_angle))

        if self.diffracted_arm_type == 0:
            theta_mon = numpy.radians(self.monochromator_angle)

            polarization_factor_num = (1 + self.degree_of_polarization) + ((1 - self.degree_of_polarization)*(numpy.cos(2*theta)**2)*(numpy.cos(2*theta_mon)**2))
            polarization_factor_den = 1 + numpy.cos(2*theta_mon)**2
        else:
            theta_mon = numpy.radians(self.analyzer_bragg_angle)

            polarization_factor_num = 1 + ((numpy.cos(2*theta)**2)*(numpy.cos(2*theta_mon)**2))
            polarization_factor_den = 2

        polarization_factor = polarization_factor_num/polarization_factor_den

        return lorentz_factor*polarization_factor/normalization

    ############################################################
    # FULL PROF

    def calculateLPFactorFullProf(self, twotheta_deg, normalization=1.0):
        theta_mon = numpy.radians(self.monochromator_angle)
        theta = numpy.radians(0.5*twotheta_deg)

        lorentz_factor = 1/(numpy.cos(theta)*numpy.sin(theta)**2)
        polarization_factor = ((1 - self.degree_of_polarization) + (self.degree_of_polarization*(numpy.cos(2*theta)**2)*(numpy.cos(2*theta_mon)**2)))/2

        return lorentz_factor*polarization_factor/normalization

    ############################################################

    def calculateDebyeWallerFactor(self, twotheta_deg, wavelength, B):

        theta = 0.5*numpy.radians(twotheta_deg)
        M = B*(numpy.sin(theta)/wavelength)**2

        return numpy.exp(-2*M)

    ############################################################
    # ACCESSORY METHODS
    ############################################################

    def traceFromAnalyzer(self, diffracted_beam, angle_index):

        input_beam = diffracted_beam.duplicate(history=False)

        empty_element = ShadowOpticalElement.create_empty_oe()

        empty_element.oe.T_SOURCE     = 0.0
        empty_element.oe.T_IMAGE      = self.analyzer_distance
        empty_element.oe.T_INCIDENCE  = 0.0
        empty_element.oe.T_REFLECTION = 180.0-self.twotheta_angles[angle_index]
        empty_element.oe.ALPHA        = 0.0


        empty_element.oe.FWRITE = 3
        empty_element.oe.F_ANGLE = 0

        n_screen = 1
        i_screen = numpy.array([0, 0, 0, 0, 0, 0, 0, 0, 0, 0])
        i_abs = numpy.zeros(10)
        i_slit = numpy.array([1, 0, 0, 0, 0, 0, 0, 0, 0, 0])
        i_stop = numpy.zeros(10)
        k_slit = numpy.zeros(10)
        thick = numpy.zeros(10)
        file_abs = numpy.array(['', '', '', '', '', '', '', '', '', ''])
        rx_slit = numpy.zeros(10)
        rz_slit = numpy.zeros(10)
        sl_dis = numpy.zeros(10)
        file_src_ext = numpy.array(['', '', '', '', '', '', '', '', '', ''])
        cx_slit = numpy.zeros(10)
        cz_slit = numpy.zeros(10)

        sl_dis[0] = self.acceptance_slit_distance
        rx_slit[0] = self.horizontal_acceptance_analyzer
        rz_slit[0] = self.vertical_acceptance_analyzer
        cx_slit[0] = 0.0
        cz_slit[0] = 0.0


        empty_element.oe.set_screens(n_screen,
                                    i_screen,
                                    i_abs,
                                    sl_dis,
                                    i_slit,
                                    i_stop,
                                    k_slit,
                                    thick,
                                    file_abs,
                                    rx_slit,
                                    rz_slit,
                                    cx_slit,
                                    cz_slit,
                                    file_src_ext)

        out_beam = ShadowBeam.traceFromOENoHistory(input_beam, empty_element)

        crystal = ShadowOpticalElement.create_plane_crystal()

        crystal.oe.T_SOURCE     = 0
        crystal.oe.T_IMAGE      = 1
        crystal.oe.T_INCIDENCE  = 90-self.analyzer_bragg_angle
        crystal.oe.T_REFLECTION = 90-self.analyzer_bragg_angle
        crystal.oe.ALPHA        = 180

        crystal.oe.F_REFLEC = 0
        crystal.oe.F_CRYSTAL = 1
        crystal.oe.FILE_REFL = bytes(self.rocking_curve_file, 'utf-8')
        crystal.oe.F_REFLECT = 0
        crystal.oe.F_BRAGG_A = 0
        crystal.oe.A_BRAGG = 0.0
        crystal.oe.F_REFRACT = 0


        if (self.mosaic_angle_spread_fwhm > 0):
            crystal.oe.F_MOSAIC = 1
            crystal.oe.MOSAIC_SEED = 4000000 + 1000000*self.random_generator_flat.random()
            crystal.oe.SPREAD_MOS = self.mosaic_angle_spread_fwhm
            crystal.oe.THICKNESS = 1.0

        crystal.oe.F_CENTRAL=0

        crystal.oe.FHIT_C = 1
        crystal.oe.FSHAPE = 1
        crystal.oe.RLEN1  = 2.5
        crystal.oe.RLEN2  = 2.5
        crystal.oe.RWIDX1 = 2.5
        crystal.oe.RWIDX2 = 2.5

        crystal.oe.FWRITE = 3
        crystal.oe.F_ANGLE = 0

        return ShadowBeam.traceFromOENoHistory(out_beam, crystal)

    ############################################################

    def traceFromSlits(self, diffracted_beam, angle_index):

        input_beam = diffracted_beam.duplicate(history=False)

        empty_element = ShadowOpticalElement.create_empty_oe()

        empty_element.oe.T_SOURCE     = 0.0
        empty_element.oe.T_IMAGE      = self.analyzer_distance
        empty_element.oe.T_INCIDENCE  = 0.0
        empty_element.oe.T_REFLECTION = 180.0-self.twotheta_angles[angle_index]
        empty_element.oe.ALPHA        = 0.0

        empty_element.oe.FWRITE = 3
        empty_element.oe.F_ANGLE = 0

        n_screen = 2
        i_screen = numpy.array([0, 0, 0, 0, 0, 0, 0, 0, 0, 0])
        i_abs = numpy.zeros(10)
        i_slit = numpy.array([1, 1, 0, 0, 0, 0, 0, 0, 0, 0])
        i_stop = numpy.zeros(10)
        k_slit = numpy.zeros(10)
        thick = numpy.zeros(10)
        file_abs = numpy.array(['', '', '', '', '', '', '', '', '', ''])
        rx_slit = numpy.zeros(10)
        rz_slit = numpy.zeros(10)
        sl_dis = numpy.zeros(10)
        file_src_ext = numpy.array(['', '', '', '', '', '', '', '', '', ''])
        cx_slit = numpy.zeros(10)
        cz_slit = numpy.zeros(10)

        sl_dis[0] = self.slit_1_distance
        rx_slit[0] = self.horizontal_acceptance_slit_1
        rz_slit[0] = self.vertical_acceptance_slit_1
        cx_slit[0] = 0.0 + self.slit_1_horizontal_displacement_cm
        cz_slit[0] = 0.0 + self.slit_1_vertical_displacement_cm

        sl_dis[1] = self.slit_2_distance
        rx_slit[1] = self.horizontal_acceptance_slit_2
        rz_slit[1] = self.vertical_acceptance_slit_2
        cx_slit[1] = 0.0 + self.slit_2_horizontal_displacement_cm
        cz_slit[1] = 0.0 + self.slit_2_vertical_displacement_cm

        empty_element.oe.set_screens(n_screen,
                                    i_screen,
                                    i_abs,
                                    sl_dis,
                                    i_slit,
                                    i_stop,
                                    k_slit,
                                    thick,
                                    file_abs,
                                    rx_slit,
                                    rz_slit,
                                    cx_slit,
                                    cz_slit,
                                    file_src_ext)


        return ShadowBeam.traceFromOENoHistory(input_beam, empty_element)

    def traceTo2DDetector(self, bar_value, diffracted_beam, avg_wavelength, twotheta_bragg, normalization,
                          debye_waller_B, statistic_factor):

        input_beam = diffracted_beam.duplicate(history=False)

        empty_element = ShadowOpticalElement.create_empty_oe()

        empty_element.oe.T_SOURCE     = 0.0
        empty_element.oe.T_IMAGE = self.area_detector_distance
        empty_element.oe.T_INCIDENCE  = 0.0
        empty_element.oe.T_REFLECTION = 180.0
        empty_element.oe.ALPHA        = 0.0

        empty_element.oe.FWRITE = 3
        empty_element.oe.F_ANGLE = 0

        n_screen = 1
        i_screen = numpy.array([0, 0, 0, 0, 0, 0, 0, 0, 0, 0])
        i_abs = numpy.zeros(10)
        i_slit = numpy.array([1, 0, 0, 0, 0, 0, 0, 0, 0, 0])
        i_stop = numpy.zeros(10)
        k_slit = numpy.zeros(10)
        thick = numpy.zeros(10)
        file_abs = numpy.array(['', '', '', '', '', '', '', '', '', ''])
        rx_slit = numpy.zeros(10)
        rz_slit = numpy.zeros(10)
        sl_dis = numpy.zeros(10)
        file_src_ext = numpy.array(['', '', '', '', '', '', '', '', '', ''])
        cx_slit = numpy.zeros(10)
        cz_slit = numpy.zeros(10)

        sl_dis[0] = self.area_detector_distance
        rx_slit[0] = self.area_detector_width
        rz_slit[0] = self.area_detector_height
        cx_slit[0] = 0.0
        cz_slit[0] = 0.0

        empty_element.oe.set_screens(n_screen,
                                     i_screen,
                                     i_abs,
                                     sl_dis,
                                     i_slit,
                                     i_stop,
                                     k_slit,
                                     thick,
                                     file_abs,
                                     rx_slit,
                                     rz_slit,
                                     cx_slit,
                                     cz_slit,
                                     file_src_ext)

        out_beam = ShadowBeam.traceFromOENoHistory(input_beam, empty_element)

        go_rays = copy.deepcopy(out_beam.beam.rays[numpy.where(out_beam.beam.rays[:, 9] == 1)])

        percentage_fraction = 50 / len(go_rays)
        no_prog = False

        for ray_index in range(0, len(go_rays)):

            if not self.run_simulation: break

            physical_coefficent = statistic_factor

            x_coord = go_rays[ray_index, 0]
            z_coord = go_rays[ray_index, 2]

            r_coord = numpy.sqrt(x_coord ** 2 + z_coord ** 2)

            ray_twotheta_angle = numpy.degrees(numpy.arctan(r_coord / self.detector_distance))

            if self.add_lorentz_polarization_factor:
                if self.pm2k_fullprof == 0:
                    lorentz_polarization_factor = self.calculateLPFactorPM2K(ray_twotheta_angle, twotheta_bragg / 2,
                                                                             normalization=normalization)
                else:
                    lorentz_polarization_factor = self.calculateLPFactorFullProf(ray_twotheta_angle,
                                                                                 normalization=normalization)

                physical_coefficent = physical_coefficent * lorentz_polarization_factor

            if self.add_debye_waller_factor:
                physical_coefficent = physical_coefficent * self.calculateDebyeWallerFactor(ray_twotheta_angle,
                                                                                            avg_wavelength,
                                                                                            debye_waller_B)

            physical_coefficent = numpy.sqrt(physical_coefficent)

            Es_x = go_rays[ray_index, 6]
            Es_y = go_rays[ray_index, 7]
            Es_z = go_rays[ray_index, 8]
            Ep_x = go_rays[ray_index, 15]
            Ep_y = go_rays[ray_index, 16]
            Ep_z = go_rays[ray_index, 17]

            go_rays[ray_index, 6] = Es_x * physical_coefficent
            go_rays[ray_index, 7] = Es_y * physical_coefficent
            go_rays[ray_index, 8] = Es_z * physical_coefficent
            go_rays[ray_index, 15] = Ep_x * physical_coefficent
            go_rays[ray_index, 16] = Ep_y * physical_coefficent
            go_rays[ray_index, 17] = Ep_z * physical_coefficent

            intensity_i = go_rays[ray_index, 6] ** 2 + go_rays[ray_index, 7] ** 2 + go_rays[ray_index, 8] ** 2 + \
                          go_rays[ray_index, 15] ** 2 + go_rays[ray_index, 16] ** 2 + go_rays[ray_index, 17] **2

            if numpy.isnan(intensity_i):
                go_rays[ray_index, 9] = 0

            bar_value = bar_value + percentage_fraction

            if int(bar_value) % 5 == 0:
                if not no_prog:
                    self.progressBarSet(bar_value)
                    no_prog = True
            else:
                no_prog = False


        out_beam.beam.rays = copy.deepcopy(go_rays[numpy.where(go_rays[:, 9] == 1)])

        return out_beam


    ############################################################

    def initialize(self):
        steps = range(0, int(numpy.floor((self.stop_angle_na - self.start_angle_na) / self.step)) + 1)

        self.start_angle = self.start_angle_na #+ self.shift_2theta
        self.stop_angle = self.stop_angle_na #+ self.shift_2theta

        if self.keep_result == 0 or len(self.twotheta_angles) == 0 or self.reset_button_pressed:
            self.area_detector_beam = None
            self.twotheta_angles = []
            self.counts = []
            self.caglioti_fits = []
            self.noise = []
            self.squared_counts = []
            self.points_per_bin = []
            self.absorption_coefficients = []
            self.lorentz_polarization_factors = []
            self.debye_waller_factors = []

            for step_index in steps:
                self.twotheta_angles.append(self.start_angle + step_index * self.step)
                self.counts.append(0.0)
                self.caglioti_fits.append(0.0)
                self.noise.append(0.0)
                self.squared_counts.append(0.0)
                self.points_per_bin.append(0)
                self.lorentz_polarization_factors.append(1.0)
                self.debye_waller_factors.append(1.0)

            self.twotheta_angles = numpy.array(self.twotheta_angles)
            self.counts = numpy.array(self.counts)
            self.caglioti_fits = numpy.array(self.caglioti_fits)
            self.noise = numpy.array(self.noise)
            self.squared_counts = numpy.array(self.squared_counts)
            self.points_per_bin = numpy.array(self.points_per_bin)
            self.lorentz_polarization_factors = numpy.array(self.lorentz_polarization_factors)
            self.debye_waller_factors = numpy.array(self.debye_waller_factors)

        self.reset_button_pressed = False

        self.resetCurrentCounts(steps)

        return steps

    ############################################################

    def resetCurrentCounts(self, steps):
        self.current_counts = []
        for step_index in steps:
            self.current_counts.append(0.0)

    ############################################################

    def writeOutFile(self):

        directory_out = os.getcwd() + '/Output'

        if not os.path.exists(directory_out): os.mkdir(directory_out)

        output_file_name = str(self.output_file_name).strip()
        if output_file_name == "":  output_file_name =  "XRD_Profile.xy"

        out_file = open(directory_out + '/' + output_file_name,"w")
        out_file.write("tth counts error\n")

        for angle_index in range(0, len(self.twotheta_angles)):
            out_file.write(str(self.twotheta_angles[angle_index]) + " "
                           + str(self.calculateSignal(angle_index)) + " "
                           + str(self.calculateStatisticError(angle_index))
                           + "\n")
            out_file.flush()

        out_file.close()

        caglioti_1_out_file = open(directory_out + '/' + os.path.splitext(output_file_name)[0] + "_InstrumentalBroadening.dat","w")
        caglioti_1_out_file.write("tth fwhm\n")

        for angle_index in range(0, len(self.caglioti_angles)):
            caglioti_1_out_file.write(str(self.caglioti_angles[angle_index]) + " "
                           + str(self.caglioti_fwhm[angle_index]) + "\n")
            caglioti_1_out_file.flush()

        caglioti_1_out_file.close()

        caglioti_2_out_file = open(directory_out + '/' + os.path.splitext(output_file_name)[0] + "_InstrumentalPeakShift.dat","w")
        caglioti_2_out_file.write("tth peak_shift\n")

        for angle_index in range(0, len(self.caglioti_angles)):
            caglioti_2_out_file.write(str(self.caglioti_angles[angle_index]) + " "
                           + str(self.caglioti_shift[angle_index]) + "\n")
            caglioti_2_out_file.flush()

        caglioti_2_out_file.close()

    ############################################################

    def backupOutFile(self):

        directory_out = os.getcwd() + '/Output'

        filename = str(self.output_file_name).strip()
        caglioti_1_filename = os.path.splitext(filename)[0] + "_InstrumentalBroadening.dat"
        caglioti_2_filename = os.path.splitext(filename)[0] + "_InstrumentalPeakShift.dat"

        srcfile = directory_out + '/' + filename
        srcfile_caglioti_1 = directory_out + '/' + caglioti_1_filename
        srcfile_caglioti_2 = directory_out + '/' + caglioti_2_filename

        bkpfile = directory_out + '/Last_Profile_BKP.xy'
        bkpfile_c1 = directory_out + '/Last_Profile_InstrumentalBroadening_BKP.dat'
        bkpfile_c2 = directory_out + '/Last_Profile_InstrumentalPeakShift_BKP.dat'

        if not os.path.exists(directory_out): return
        if os.path.exists(srcfile):
            if os.path.exists(bkpfile): os.remove(bkpfile)
            shutil.copyfile(srcfile, bkpfile)

        if os.path.exists(srcfile_caglioti_1):
            if os.path.exists(bkpfile_c1): os.remove(bkpfile_c1)
            shutil.copyfile(srcfile_caglioti_1, bkpfile_c1)

        if os.path.exists(srcfile_caglioti_2):
            if os.path.exists(bkpfile_c2): os.remove(bkpfile_c2)
            shutil.copyfile(srcfile_caglioti_2, bkpfile_c2)

    ############################################################
    # MATERIALS DB
    ############################################################

    def getCapillaryChemicalFormula(self, capillary_material):
        if capillary_material < len(self.capillary_materials):
            return self.capillary_materials[capillary_material].chemical_formula
        else:
            return None

    ############################################################

    def getCapillaryMaterialName(self, capillary_material):
        if capillary_material < len(self.capillary_materials):
            return self.capillary_materials[capillary_material].name
        else:
            return -1


    ############################################################

    def getCapillaryDensity(self, capillary_material):
        if capillary_material < len(self.capillary_materials):
            return self.capillary_materials[capillary_material].density
        else:
            return -1

    ############################################################

    def getChemicalFormula(self, material):
        if material < len(self.materials):
            return self.materials[material].chemical_formula
        else:
            return None

    ############################################################

    def getMaterialXraylibCrystal(self, material):
        if material < len(self.materials):
            return self.materials[material].xraylib_crystal
        else:
            return None

    ############################################################

    def getLatticeParameter(self, material):
        if material < len(self.materials):
            return self.materials[material].lattice_parameter
        else:
            return -1

    ############################################################

    def getDensity(self, material):
        if material < len(self.materials):
            return self.materials[material].density
        else:
            return -1

    ############################################################

    def getDebyeWallerB(self, material):
        if material < len(self.materials):
            return self.materials[material].debye_waller_B
        else:
            return None

    ############################################################

    def getReflections(self, material, number_of_peaks=-1, avg_wavelength=0.0):
        reflections = []

        if material < len(self.materials):
            total_reflections = self.materials[material].reflections
            added_peak = 0

            for reflection in total_reflections:
                if number_of_peaks > 0 and added_peak == number_of_peaks: break

                twotheta_bragg = 2*ShadowPhysics.calculateBraggAngle(avg_wavelength, reflection.h, reflection.k, reflection.l, self.getLatticeParameter(material))

                if numpy.degrees(twotheta_bragg) >= self.start_angle and numpy.degrees(twotheta_bragg) <= self.stop_angle:
                    reflection.twotheta_bragg = twotheta_bragg
                    reflections.append(reflection)
                    added_peak = added_peak + 1

        return reflections

    ############################################################

    def readCapillaryMaterialConfigurationFiles(self):
        self.capillary_materials = []

        foundMaterialFile = True
        materialIndex = 0

        directory_files = resources.package_dirname("orangecontrib.shadow.widgets.experimental_elements")

        try:
            while(foundMaterialFile):
                materialFileName =  directory_files + "/sample_holder_material_" + str(materialIndex) + ".dat"

                if not os.path.exists(materialFileName):
                    foundMaterialFile = False
                else:
                    materialFile = open(materialFileName, "r")

                    rows = materialFile.readlines()

                    if (len(rows) == 3):
                        name = rows[0].split('#')[0].strip()
                        chemical_formula = rows[1].split('#')[0].strip()
                        density = float(rows[2].split('#')[0].strip())

                        current_material = CapillaryMaterial(name, chemical_formula, density)

                        self.capillary_materials.append(current_material)

                    materialIndex = materialIndex + 1

        except Exception as err:
            raise Exception("Problems reading Capillary Materials Configuration file: {0}".format(err))
        except:
            raise Exception("Unexpected error reading Capillary Materials Configuration file: ", sys.exc_info()[0])

    ############################################################

    def readMaterialConfigurationFiles(self):
        self.materials = []

        foundMaterialFile = True
        materialIndex = 0

        directory_files = resources.package_dirname("orangecontrib.shadow.widgets.experimental_elements")

        try:
            while(foundMaterialFile):
                materialFileName =  directory_files + "/material_" + str(materialIndex) + ".dat"

                if not os.path.exists(materialFileName):
                    foundMaterialFile = False
                else:
                    materialFile = open(materialFileName, "r")

                    rows = materialFile.readlines()

                    if (len(rows) > 3):

                        chemical_formula = rows[0].split('#')[0].strip()
                        density = float(rows[1].split('#')[0].strip())
                        debye_waller_B = float(rows[3].split('#')[0].strip())

                        current_material = Material(chemical_formula, density, debye_waller_B)

                        for index in range(4, len(rows)):
                            if not rows[index].strip() == "" and \
                               not rows[index].strip().startswith('#'):
                                row_elements = rows[index].split(',')

                                h = int(row_elements[0].strip())
                                k = int(row_elements[1].strip())
                                l = int(row_elements[2].strip())

                                relative_intensity = 1.0
                                form_factor_2 = 1.0

                                if (len(row_elements)>3):
                                    relative_intensity = float(row_elements[3].strip())
                                if (len(row_elements)>4):
                                    form_factor_2 = float(row_elements[4].strip())

                                reflection = Reflection(h, k, l, relative_intensity=relative_intensity, form_factor_2_mult=form_factor_2)

                                material_reflection_file = directory_files + "/reflections/material_" + str(materialIndex) + "_" + str(h) + str(k)+ str(l) + ".dat"

                                if os.path.exists(material_reflection_file):
                                    reflection.material_reflection_file = material_reflection_file

                                current_material.reflections.append(reflection)

                        self.materials.append(current_material)

                    materialIndex = materialIndex + 1

        except Exception as err:
            raise Exception("Problems reading Materials Configuration file: {0}".format(err))
        except:
            raise Exception("Unexpected error reading Materials Configuration file: ", sys.exc_info()[0])

    def writeStdOut(self, text):
        cursor = self.shadow_output.textCursor()
        cursor.movePosition(QtGui.QTextCursor.End)
        cursor.insertText(text)
        self.shadow_output.setTextCursor(cursor)
        self.shadow_output.ensureCursorVisible()

############################################################
############################################################
############################################################
############################################################

class RockingCurveElement:
    delta_theta=0.0
    intensity=0.0

    def __init__(self, delta_theta, intensity):
        self.delta_theta=delta_theta
        self.intensity=intensity

class CapillaryMaterial:
    name=""
    chemical_formula=""
    density=0.0

    def __init__(self, name, chemical_formula, density):
        self.name=name
        self.chemical_formula=chemical_formula
        self.density=density

class Material:
    xraylib_crystal = None
    chemical_formula=""
    density=0.0
    lattice_parameter=0.0
    debye_waller_B=0.0

    reflections = []

    def __init__(self, chemical_formula, density, debye_waller_B):
        self.chemical_formula=chemical_formula
        self.xraylib_crystal =  xraylib.Crystal_GetCrystal(chemical_formula)
        self.density=density
        self.lattice_parameter=self.xraylib_crystal['a']
        self.debye_waller_B=debye_waller_B
        self.reflections=[]


class Reflection:
    h=0
    k=0
    l=0
    relative_intensity=1.0
    form_factor_2_mult=0.0
    twotheta_bragg=0.0
    material_reflection_file = None

    def __init__(self, h, k, l, relative_intensity=1.0, form_factor_2_mult=0.0):
        self.h=h
        self.k=k
        self.l=l
        self.relative_intensity=relative_intensity
        self.form_factor_2_mult=form_factor_2_mult

if __name__ == "__main__":
    a = QApplication(sys.argv)
    ow = XRDCapillary()
    ow.show()
    a.exec_()
    ow.saveSettings()