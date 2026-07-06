import sys

import pathlib

from dataclasses import dataclass
from typing import Any

from PyQt6.QtCore import Qt, QDateTime, QLocale, QSize, QTimer, QUrl
from PyQt6.QtGui import QAction, QDesktopServices, QDoubleValidator, QPalette
from PyQt6.QtWidgets import QAbstractItemView, QApplication, QComboBox, QDateTimeEdit, QFileDialog, QHBoxLayout, QHeaderView, QLabel, QLineEdit, QListWidget, QListWidgetItem, QMainWindow, QPushButton, QSizePolicy, QSlider, QSplitter, QTableWidget, QTableWidgetItem, QTreeWidget, QTreeWidgetItem, QVBoxLayout, QWidget
from PyQt6.QtWebEngineWidgets import QWebEngineView


import numpy as np

from datetime import datetime

import matplotlib
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qtagg import NavigationToolbar2QT as NavigationToolbar

import seaborn as sns


@dataclass
class GPXElements:
    track_segment_tree: QTreeWidget
    waypoint_list: Any

@dataclass
class ElevationCanvas:
    canvas: FigureCanvas
    toolbar: NavigationToolbar
    figure: matplotlib.figure.Figure
    axis: matplotlib.axes.Axes
    
    colormap: Any
    has_continuous_colormap: bool
    colorbar: Any
    
    highlight_point: Any

@dataclass
class ControlsPanel:
    filter_selector: QComboBox
    filter_selector_debounce_timer: QTimer
    filter_width_slider: QSlider
    filter_width_label: QLabel
    start_time_selector: QDateTimeEdit
    speed_model_selector: QComboBox
    speed_model_parameters_panel: QWidget
    speed_model_parameter_inputs: dict
    fit_speed_model_button: QPushButton

@dataclass
class MenuActions:
    open_file: QAction
    export_file: QAction
    show_settings: QAction
    exit_app: QAction
    show_canvas_toolbar: QAction
    show_data_table: QAction
    show_map: QAction

class GPXView(QMainWindow):
    def __init__(self, viewmodel):
        super().__init__()
        
        self.viewmodel = viewmodel
        
        self.map_window = MapView(viewmodel)
        
        
        self._style_window()
        
        self.gpx_elements = self._create_gpx_elements()
        self.elevation_canvas = self._create_elevation_canvas()
        self.controls = self._create_controls()
        self._set_controls_values()
        self._create_speed_model_parameter_panel()
        
        self.data_table = self._create_data_table()
        
        self.menu_actions = self._create_menu_actions()
        
        self._assemble_window_layout(dimensions=(1200, 700))
        self._create_menu_bar()
        
        
        
        
        self.viewmodel.track_loaded.connect(self._on_track_loaded)
        self.viewmodel.profile_changed.connect(self._on_profile_changed)
        self.viewmodel.point_selected.connect(self._on_point_selected)
    
    def closeEvent(self, event):
        self.viewmodel.settings.save()
        
        self.map_window.close()
        
        super().closeEvent(event)
    
    def _create_gpx_elements(self):
        track_segment_tree = QTreeWidget()
        track_segment_tree.setHeaderHidden(True)
        track_segment_tree.itemSelectionChanged.connect(self._on_track_segment_selection_changed)
        
        waypoint_list = QListWidget()
        
        return GPXElements(track_segment_tree=track_segment_tree, waypoint_list=waypoint_list)
    
    def _create_elevation_canvas(self):
        
        has_continuous_colormap = True
        
        
        figure, axis = plt.subplots(figsize=(6,4), layout='constrained')
        canvas = FigureCanvas(figure)
        toolbar = NavigationToolbar(canvas, self)
        
        toolbar.setIconSize(QSize(16, 16))
        for action in toolbar.actions():
            if action.text() in ['Back', 'Forward' ,'Subplots', 'Customize']:
                toolbar.removeAction(action)
        
        toolbar.set_message = lambda _: None
        
        toolbar.setVisible(False)
        
        
        canvas.setStyleSheet('background-color: transparent;')
        
        figure.patch.set_alpha(0.0)
        axis.patch.set_alpha(0.0)
        
        
        _cmap = matplotlib.colors.LinearSegmentedColormap.from_list('quäldich', [(R/255, G/255, B/255) for R, G, B in [(180,212,142), (193,219,142), (254,254,141), (247,203,124), (240,146,109), (215,98,94), (144,83,81), (117,76,75), (90,72,71)]])
        
        if has_continuous_colormap:
            colormap = plt.cm.ScalarMappable(cmap=_cmap, norm=matplotlib.colors.Normalize(vmin=0, vmax=0.2, clip=True))
            colorbar = figure.colorbar(colormap, ax=axis, pad=0.02, orientation='vertical', extend='max')
        else:
            _cmap_bins = [0.00, 0.03, 0.05, 0.08, 0.10, 0.15, 1]
            
            colormap = plt.cm.ScalarMappable(cmap=matplotlib.colors.ListedColormap([(*_cmap(i / (len(_cmap_bins)-2))[:3],1.0) for i in range(len(_cmap_bins)-1)]), norm=matplotlib.colors.BoundaryNorm(_cmap_bins, ncolors=len(_cmap_bins)-1))
            colorbar = figure.colorbar(colormap, ax=axis, pad=0.02, spacing='proportional', orientation='vertical', extend='max')
            
        
        colorbar.set_label(f'{self.viewmodel.localization['label_absolute_slope']} (%)')
        colorbar.ax.yaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda x, _: f"{x * 100:.0f}"))
        colorbar.ax.set_ylim(0,0.2)
        
        colorbar.ax.set_visible(False)
        
        
        highlight_point, = axis.plot([], [], marker='.', markersize=15, zorder=10, clip_on=False)
        
        
        axis.set_axis_off()
        
        
        canvas.mpl_connect('button_press_event', self._on_elevation_canvas_clicked)
        
        
        return ElevationCanvas(canvas=canvas, toolbar=toolbar, figure=figure, axis=axis, colormap=colormap, has_continuous_colormap=has_continuous_colormap, colorbar=colorbar, highlight_point=highlight_point)

    def _create_controls(self):
        
        filter_selector = QComboBox()
        filter_selector.setFixedWidth(200)
        filter_selector.currentIndexChanged.connect(self._on_filter_changed)
        
        filter_selector_debounce_timer = QTimer()
        filter_selector_debounce_timer.setSingleShot(True)
        filter_selector_debounce_timer.setInterval(500)
        filter_selector_debounce_timer.timeout.connect(self._on_filter_changed)
        
        filter_width_slider = QSlider(Qt.Orientation.Horizontal)
        filter_width_slider.setRange(0, 2000)
        filter_width_slider.setFixedWidth(140)
        filter_width_slider.valueChanged.connect(self._on_filter_slider_changed)
        
        filter_width_label = QLabel()
        filter_width_label.setFixedWidth(40)
        
        start_time_selector = QDateTimeEdit()
        start_time_selector.setFixedWidth(200)
        start_time_selector.setDisplayFormat('dd.MM.yyyy HH:mm')
        start_time_selector.setDateTime(QDateTime.currentDateTime())
        start_time_selector.dateTimeChanged.connect(self._on_start_time_changed)
        
        speed_model_selector = QComboBox()
        speed_model_selector.setFixedWidth(200)
        speed_model_selector.currentIndexChanged.connect(self._on_speed_model_selected)

        speed_model_parameters_panel = QWidget()
        speed_model_parameters_layout = QVBoxLayout(speed_model_parameters_panel)
        speed_model_parameters_layout.setContentsMargins(0, 0, 0, 0)
        speed_model_parameters_layout.setSpacing(2)
        
        fit_speed_model_button = QPushButton()
        fit_speed_model_button.setEnabled(False)
        #fit_speed_model_button.clicked.connect(self._on_fit_speed_clicked)
        
        
        return ControlsPanel(filter_selector=filter_selector, filter_selector_debounce_timer=filter_selector_debounce_timer, filter_width_slider=filter_width_slider, filter_width_label=filter_width_label, start_time_selector=start_time_selector, speed_model_selector=speed_model_selector, speed_model_parameters_panel=speed_model_parameters_panel, speed_model_parameter_inputs={}, fit_speed_model_button=fit_speed_model_button)

    def _create_speed_model_parameter_panel(self):
        
        layout = self.controls.speed_model_parameters_panel.layout()
        
        while layout.count():
            item = layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        self.controls.speed_model_parameter_inputs.clear()
        
        
        _QDoubleValidator = QDoubleValidator()
        _QDoubleValidator.setLocale(QLocale(QLocale.Language.C))
        _QDoubleValidator.setNotation(QDoubleValidator.Notation.StandardNotation)
        
        for parameter, parameter_attributes in self.viewmodel.speed_model.parameters.items():
            
            row = QWidget()
            #row.setFixedHeight(24)
            row_layout = QHBoxLayout(row)
            row_layout.setContentsMargins(0, 0, 0, 0)
            row_layout.addWidget(QLabel(f'{parameter_attributes["label"].get(self.viewmodel.language_code, parameter_attributes["label"]["en"])}:'))
            
            parameter_input = QLineEdit()
            parameter_input.setValidator(_QDoubleValidator)
            parameter_input.setText(str(getattr(self.viewmodel.speed_model, parameter)))
            parameter_input.setMinimumWidth(60)
            parameter_input.setMaximumWidth(80)
            parameter_input.setAlignment(Qt.AlignmentFlag.AlignRight)
            parameter_input.editingFinished.connect(self._on_speed_model_parameter_changed)
            row_layout.addWidget(parameter_input)
            
            layout.addWidget(row)
            self.controls.speed_model_parameter_inputs[parameter] = parameter_input
        
        #layout.addWidget(self.controls.fit_speed_model_button)
        layout.addStretch()

    def _create_data_table(self):
        data_table = QTableWidget()
        data_table.setEditTriggers(QAbstractItemView.EditTrigger.DoubleClicked)
        data_table.setColumnCount(7)
        data_table.setHorizontalHeaderLabels([f'{self.viewmodel.localization['label_distance']} (km)', f'{self.viewmodel.localization['label_coordinates']}', f'{self.viewmodel.localization['label_elevation']} (m)', f'{self.viewmodel.localization['label_slope']} (%)', f'{self.viewmodel.localization['label_ascent']} (m)', f'{self.viewmodel.localization['label_descent']} (m)', f'{self.viewmodel.localization['label_time']} (h)'])
        data_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        data_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        data_table.itemSelectionChanged.connect(self._on_data_table_clicked)
        
        return data_table
    
    def _create_menu_actions(self):
        
        open_file = QAction(self.viewmodel.localization['menu_file_open'], self)
        open_file.setEnabled(True)
        open_file.triggered.connect(self._open_file_dialog)
        
        export_file = QAction(self.viewmodel.localization['menu_file_export'], self)
        export_file.setEnabled(False)
        export_file.triggered.connect(self._export_file_dialog)
        
        show_settings = QAction(self.viewmodel.localization['menu_file_show_settings'], self)
        show_settings.setEnabled(True)
        show_settings.triggered.connect(self._open_settings_directory)
        
        exit_app = QAction(self.viewmodel.localization['menu_file_exit'], self)
        exit_app.setEnabled(True)
        exit_app.setMenuRole(QAction.MenuRole.NoRole)
        exit_app.triggered.connect(self.close)
        
        show_canvas_toolbar = QAction(self.viewmodel.localization['menu_view_show_canvas_toolbar'], self, checkable=True)
        show_canvas_toolbar.setChecked(False)
        show_canvas_toolbar.triggered.connect(self._on_show_canvas_toolbar_toggled)
        
        show_data_table = QAction(self.viewmodel.localization['menu_view_show_table'], self, checkable=True)
        show_data_table.setChecked(True)
        show_data_table.triggered.connect(self._on_show_data_table_toggled)
        
        show_map = QAction(self.viewmodel.localization['menu_view_show_map'], self)
        show_map.setEnabled(False)
        show_map.triggered.connect(self._on_show_map_window_clicked)
        
        return MenuActions(open_file=open_file, export_file=export_file, show_settings=show_settings, exit_app=exit_app, show_canvas_toolbar=show_canvas_toolbar, show_data_table=show_data_table, show_map=show_map)
    
    def _assemble_window_layout(self, dimensions):
        
        self.resize(*dimensions)
        
        left_splitter = QSplitter(Qt.Orientation.Vertical)
        left_splitter.addWidget(self.gpx_elements.track_segment_tree)
        left_splitter.addWidget(self.gpx_elements.waypoint_list)
        
        right_top_panel = QWidget()
        right_top_layout = QVBoxLayout(right_top_panel)
        right_top_layout.setContentsMargins(0, 0, 0, 0)
        
        
        controls_panel = QWidget()
        controls_panel.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        controls_panel_layout = QHBoxLayout(controls_panel)
        controls_panel_layout.setContentsMargins(0, 0, 0, 0)

        controls_panel_layout.addStretch()
        controls_panel_layout.addStretch()

        filter_panel = QWidget()
        filter_panel_layout = QVBoxLayout(filter_panel)
        filter_panel_layout.setContentsMargins(0, 0, 0, 0)
        
        
        _row = QWidget()
        _row.setFixedHeight(28)
        _row_layout = QHBoxLayout(_row)
        _row_layout.setContentsMargins(0, 0, 0, 0)
        _row_layout.addWidget(QLabel(f'<b>{self.viewmodel.localization['label_filter']}:</b>'))
        _row_layout.addWidget(self.controls.filter_selector)
        
        filter_panel_layout.addWidget(_row)
        
        _row = QWidget()
        _row.setFixedHeight(28)
        _row_layout = QHBoxLayout(_row)
        _row_layout.setContentsMargins(0, 0, 0, 0)
        _row_layout.addWidget(QLabel(f'{self.viewmodel.localization['label_filter_width']} (m):'))
        _row_layout.addWidget(self.controls.filter_width_slider)
        _row_layout.addWidget(self.controls.filter_width_label)
        
        filter_panel_layout.addWidget(_row)
        
        
        
        filter_panel_layout.addStretch()
        
        controls_panel_layout.addWidget(filter_panel)
        
        
        
        speed_model_panel = QWidget()
        speed_model_panel_layout = QVBoxLayout(speed_model_panel)
        speed_model_panel_layout.setContentsMargins(0, 0, 0, 0)
        speed_model_panel_layout.setSpacing(2)
        
        
        _row = QWidget()
        _row.setFixedHeight(28)
        _row_layout = QHBoxLayout(_row)
        _row_layout.setContentsMargins(0, 0, 0, 0)
        _row_layout.addWidget(QLabel(f'<b>{self.viewmodel.localization["label_start_time"]}:</b>'))
        _row_layout.addWidget(self.controls.start_time_selector)
        
        speed_model_panel_layout.addWidget(_row)
        
        
        
        _row = QWidget()
        _row.setFixedHeight(28)
        _row_layout = QHBoxLayout(_row)
        _row_layout.setContentsMargins(0, 0, 0, 0)
        _row_layout.addWidget(QLabel(f'<b>{self.viewmodel.localization["label_speed_model"]}:</b>'))
        _row_layout.addWidget(self.controls.speed_model_selector)

        speed_model_panel_layout.addWidget(_row)

        #self.controls.fit_speed_model_button.setText(f'{self.viewmodel.localization["label_fit_speed_model"]}')

        speed_model_panel_layout.addWidget(self.controls.speed_model_parameters_panel)

        controls_panel_layout.addWidget(speed_model_panel)
        
        
        
        right_top_layout.addWidget(self.elevation_canvas.toolbar)
        right_top_layout.addWidget(self.elevation_canvas.canvas)
        right_top_layout.addWidget(controls_panel)
        
        
        right_splitter = QSplitter(Qt.Orientation.Vertical)
        right_splitter.addWidget(right_top_panel)
        right_splitter.addWidget(self.data_table)
        
        
        
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QVBoxLayout(central_widget)
        
        main_splitter = QSplitter(Qt.Orientation.Horizontal)
        main_splitter.addWidget(left_splitter)
        main_splitter.addWidget(right_splitter)
        
        main_layout.addWidget(main_splitter)
        
        
        
        main_splitter.setSizes([int(dimensions[0] * 0.25), int(dimensions[0] * 0.75)])
        left_splitter.setSizes([int(dimensions[1] * 0.6), int(dimensions[1] * 0.4)])
        right_splitter.setSizes([int(dimensions[1] * 0.7), int(dimensions[1] * 0.3)])

    def _style_window(self):
        app = QApplication.instance()
        
        system_font_family = app.font().family()
        
        if sys.platform == 'darwin':
            system_font_family = 'Helvetica Neue'
        if sys.platform == 'win32':
            system_font_family = 'Segoe UI'
        
        system_font_size = 10
        
        system_font_color = app.palette().color(QPalette.ColorRole.WindowText).name()

        plt.rcParams['font.family'] = system_font_family
        plt.rcParams['font.size'] = system_font_size
        plt.rcParams['text.color'] = system_font_color
        plt.rcParams['axes.labelcolor'] = system_font_color
        plt.rcParams['axes.edgecolor'] = system_font_color
        plt.rcParams['xtick.color'] = system_font_color
        plt.rcParams['ytick.color'] = system_font_color
        
        plt.rcParams['lines.color'] = system_font_color
        plt.rcParams['grid.color'] = system_font_color
        plt.rcParams['axes.prop_cycle'] = plt.cycler(color=[system_font_color])

    def _create_menu_bar(self):
        menu_bar = self.menuBar()

        file_menu = menu_bar.addMenu(self.viewmodel.localization['menu_file'])
        file_menu.addAction(self.menu_actions.open_file)
        file_menu.addAction(self.menu_actions.export_file)
        file_menu.addSeparator()
        settings_submenu = file_menu.addMenu(self.viewmodel.localization['menu_settings'])
        settings_submenu.menuAction().setMenuRole(QAction.MenuRole.NoRole)
        settings_submenu.addAction(self.menu_actions.show_settings)
        file_menu.addSeparator()
        file_menu.addAction(self.menu_actions.exit_app)
        
        view_menu = menu_bar.addMenu(self.viewmodel.localization['menu_view'])
        view_menu.addAction(self.menu_actions.show_canvas_toolbar)
        view_menu.addAction(self.menu_actions.show_data_table)
        view_menu.addSeparator()
        view_menu.addAction(self.menu_actions.show_map)

    def _set_controls_values(self):
        
        self.controls.filter_selector.blockSignals(True)
        self.controls.filter_width_slider.blockSignals(True)
        
        for filter_name, filter in self.viewmodel.plugins.filters.items():
            self.controls.filter_selector.addItem(filter.name, filter_name)
        
        for i in range(self.controls.filter_selector.count()):
            if self.controls.filter_selector.itemData(i) == type(self.viewmodel.filter).__name__:
                self.controls.filter_selector.setCurrentIndex(i)
                break
        
        self.controls.filter_width_slider.setValue(self.viewmodel.filter.width)
        self.controls.filter_width_label.setText(str(self.viewmodel.filter.width))
        
        self.controls.filter_selector.blockSignals(False)
        self.controls.filter_width_slider.blockSignals(False)
        
        
        
        self.controls.speed_model_selector.blockSignals(True)
        
        for speed_model_name, speed_model in self.viewmodel.plugins.speed_models.items():
            self.controls.speed_model_selector.addItem(speed_model.name, speed_model_name)
        
        for i in range(self.controls.speed_model_selector.count()):
            if self.controls.speed_model_selector.itemData(i) == type(self.viewmodel.speed_model).__name__:
                self.controls.speed_model_selector.setCurrentIndex(i)
                break
        
        self.controls.speed_model_selector.blockSignals(False)


    def _open_file_dialog(self):
        file_path, _ = QFileDialog.getOpenFileName(self, f'{self.viewmodel.localization['menu_file_open']}:', str(self.viewmodel.settings.last_os_path), f'{self.viewmodel.localization['menu_file_open_filter']}')

        if file_path:
            self.viewmodel.settings.last_os_path = pathlib.Path(file_path).parent
            
            self.viewmodel.load_gpx_file(file_path)
    
    def _export_file_dialog(self):
        
        _exporter_collection = {exporter.file_filter: name for name, exporter in self.viewmodel.plugins.exporters.items()}
        
        file_path, file_filter = QFileDialog.getSaveFileName(self, f'{self.viewmodel.localization['menu_file_export']}:', str(self.viewmodel.settings.last_os_path), ';;'.join(_exporter_collection.keys()))
        
        
        if file_path:
            self.viewmodel.export_file(file_path, _exporter_collection[file_filter])

    def _open_settings_directory(self):
        
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(self.viewmodel.settings.base_path)))

    def _on_show_canvas_toolbar_toggled(self, state):
        self.elevation_canvas.toolbar.setVisible(state)

    def _on_show_data_table_toggled(self, state):
        self.data_table.setVisible(state)

    def _on_show_map_window_clicked(self):
        
        if self.viewmodel.profile is not None:
            self.map_window._initialize_map_view()
            self.map_window.show()
            
            self.map_window.raise_()
            self.map_window.activateWindow()


    def _on_track_loaded(self):
        
        self.gpx_elements.track_segment_tree.clear()
        self.gpx_elements.waypoint_list.clear()
        
        for i, track in enumerate(self.viewmodel.gpx.tracks):
            track_item = QTreeWidgetItem(self.gpx_elements.track_segment_tree, [f'Track: {track.name}'])
            for j, segment in enumerate(track.segments):
                segment_item = QTreeWidgetItem(track_item, [f'Segment {j+1}'])
                segment_item.setData(0, Qt.ItemDataRole.UserRole, (i,j))

        self.gpx_elements.track_segment_tree.expandAll()
        

        try:
            self.gpx_elements.track_segment_tree.setCurrentItem(self.gpx_elements.track_segment_tree.topLevelItem(0).child(0))
        except Exception:
            pass
        
        
        for i, waypoint in enumerate(self.viewmodel.gpx.waypoints):
            item = QListWidgetItem(f'{waypoint.name}')
            item.setData(Qt.ItemDataRole.UserRole, i)
            item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEnabled)
            item.setToolTip(f'{waypoint.latitude:.6f}, {waypoint.longitude:.6f}')
            self.gpx_elements.waypoint_list.addItem(item)
        
        
        if len(self.viewmodel.plugins.exporters) > 0:
            self.menu_actions.export_file.setEnabled(True)
        self.menu_actions.show_map.setEnabled(True) 

    def _on_profile_changed(self):
        
        self._draw_elevation_profile()
        self._fill_data_table()
        self._get_control_values()

    def _on_point_selected(self):
        
        idx = self.viewmodel.selected_point
        
        self.elevation_canvas.highlight_point.set_data([self.viewmodel.profile.distance[idx]/1000], [self.viewmodel.profile.elevation[idx]])
        self.elevation_canvas.canvas.draw_idle()
        
        self.data_table.blockSignals(True)
        self.data_table.selectRow(idx)
        self.data_table.scrollToItem(self.data_table.item(idx, 0))
        self.data_table.blockSignals(False)
        
    def _on_track_segment_selection_changed(self):
        
        selected_items = self.gpx_elements.track_segment_tree.selectedItems()
        
        if selected_items:
            data_keys = selected_items[0].data(0, Qt.ItemDataRole.UserRole)
            
            if data_keys is not None:
                track_idx, segment_idx = data_keys
                self.viewmodel.select_track_segment(track_idx, segment_idx)
    
    def _on_filter_slider_changed(self):
        self.controls.filter_width_label.setText(str(self.controls.filter_width_slider.value()))
        self.controls.filter_selector_debounce_timer.start()
    
    def _on_filter_changed(self):
        
        self.viewmodel.set_filter(name=self.controls.filter_selector.currentData(), width=self.controls.filter_width_slider.value())
    
    def _on_start_time_changed(self):
        self.viewmodel.set_start_time(self.controls.start_time_selector.dateTime().toPyDateTime().replace(second=0, microsecond=0))
    
    def _on_speed_model_selected(self):
        _speed_model_name = self.controls.speed_model_selector.currentData()
        self.viewmodel.set_speed_model(name=_speed_model_name)
        
        self._create_speed_model_parameter_panel()
    
    def _on_speed_model_parameter_changed(self):
        _speed_model_name = self.controls.speed_model_selector.currentData()
        _speed_model_parameters = {parameter: float(parameter_input.text() or '0') for parameter, parameter_input in self.controls.speed_model_parameter_inputs.items()}
        
        self.viewmodel.set_speed_model(name=_speed_model_name, parameters=_speed_model_parameters)
    
    def _on_elevation_canvas_clicked(self, event):
        
        if self.viewmodel.profile is not None:
            if event.inaxes == self.elevation_canvas.axis and event.xdata is not None:
                
                idx = int((np.abs(self.viewmodel.profile.distance / 1000 - event.xdata)).argmin())
                self.viewmodel.set_selected_point(idx)
    
    def _on_data_table_clicked(self):
        rows = [item.row() for item in self.data_table.selectedItems()]

        if rows:
            self.viewmodel.set_selected_point(rows[0])
    
    def _get_control_values(self):
        self.controls.start_time_selector.blockSignals(True)
        self.controls.start_time_selector.setDateTime(QDateTime(self.viewmodel.track_segment_start_time or datetime.now().replace(second=0, microsecond=0)))
        self.controls.start_time_selector.blockSignals(False)
    
    def _draw_elevation_profile(self):
        
        ax = self.elevation_canvas.axis
        
        ax.clear()
        ax.patch.set_alpha(0)
        
        self.elevation_canvas.highlight_point, = ax.plot([], [], marker='.', markersize=15, zorder=10, clip_on=False)
        
        _elevation_range = (self.viewmodel.profile.elevation.min(), self.viewmodel.profile.elevation.max())
        _elevation_range = (_elevation_range[0] - 0.05 * (_elevation_range[1] - _elevation_range[0]), _elevation_range[1] + 0.05 * (_elevation_range[1] - _elevation_range[0]))
        
        if not self.elevation_canvas.has_continuous_colormap:
            slope_bin_boundaries = self.elevation_canvas.colormap.norm.boundaries
        else:
            slope_bin_boundaries = np.hstack((np.linspace(0,0.2,41), 1))
        
        for i, slope_bin in enumerate(zip(slope_bin_boundaries[:-1], slope_bin_boundaries[1:])):
            I = self.viewmodel.profile.where_slope(slope_bin=slope_bin)
            ax.fill_between(self.viewmodel.profile.distance / 1000, np.where(I, self.viewmodel.profile.elevation, np.nan), 0, edgecolor=None, facecolor=self.elevation_canvas.colormap.to_rgba(sum(slope_bin)/2), zorder=0)
        
        ax.plot(self.viewmodel.profile.distance / 1000, self.viewmodel.profile.elevation, linewidth=1, zorder=2, label=f'{self.viewmodel.profile.ascent[-1]:.1f}m / {self.viewmodel.profile.descent[-1]:.1f}m')
        
        ax.grid(True, axis='y', which='major', linestyle='--', linewidth=0.5, zorder=-1)

        ax.set_xlim(0, self.viewmodel.profile.distance.max() / 1000)
        ax.set_ylim(*_elevation_range)
        
        ax.set_xlabel(f'{self.viewmodel.localization['label_distance']} (km)')
        ax.set_ylabel(f'{self.viewmodel.localization['label_elevation']} (m)')

        sns.despine(ax=ax, offset=10)
        
        self.elevation_canvas.colorbar.ax.set_visible(True)
        
        
        self.elevation_canvas.highlight_point.set_data([self.viewmodel.profile.distance[self.viewmodel.selected_point] / 1000], [self.viewmodel.profile.elevation[self.viewmodel.selected_point]])
        
        
        self.elevation_canvas.canvas.draw()
    
    def _fill_data_table(self):
        def seconds_to_hhmm(s):
            try:
                hh, r = divmod(int(s), 3600)
                mm, _ = divmod(r, 60)
                return f'{hh:d}:{mm:02d}'
            except Exception:
                return 'nan'
        
        def seconds_to_timestamp(s):
            try:
                return (_start_time + datetime.timedelta(seconds=self.viewmodel.profile.time[i])).strftime(r'%d.%m.%Y %H:%M')
            except Exception:
                return 'nan'
        
        _start_time = self.viewmodel.track_segment_start_time
        
        if _start_time is None:
            seconds_to_ = seconds_to_hhmm
        else:
            seconds_to_ = seconds_to_timestamp
        
        
        self.data_table.clearContents()
        self.data_table.setRowCount(len(self.viewmodel.profile.distance))
        
        for i in range(len(self.viewmodel.profile.distance)):
            self.data_table.setItem(i, 1, QTableWidgetItem(f'{self.viewmodel.profile.coordinates[i][0]:.6f}, {self.viewmodel.profile.coordinates[i][1]:.6f}'))
            self.data_table.setItem(i, 0, QTableWidgetItem(f'{self.viewmodel.profile.distance[i] / 1000:.3f}'))
            
            self.data_table.setItem(i, 2, QTableWidgetItem(f'{self.viewmodel.profile.elevation[i]:.1f}'))
            self.data_table.setItem(i, 3, QTableWidgetItem(f'{100 * self.viewmodel.profile.slope[i]:.1f}'))
            self.data_table.setItem(i, 4, QTableWidgetItem(f'{self.viewmodel.profile.ascent[i]:.0f}'))
            self.data_table.setItem(i, 5, QTableWidgetItem(f'{self.viewmodel.profile.descent[i]:.0f}'))
            
            self.data_table.setItem(i, 6, QTableWidgetItem(seconds_to_(self.viewmodel.profile.time[i])))
                
        self.data_table.resizeColumnsToContents()
        for j in range(self.data_table.columnCount()):
            self.data_table.setColumnWidth(j, self.data_table.columnWidth(j) + 10)
        
    
class MapView(QWidget):
    def __init__(self, viewmodel):
        super().__init__()
    
        self.viewmodel = viewmodel
        
        self.map_view = QWebEngineView()
        self.map_view.setContextMenuPolicy(Qt.ContextMenuPolicy.NoContextMenu)
        
        self._assemble_window_layout()
        
        self._map_view_initialized = False
        
        
        
        self.viewmodel.track_segment_selected.connect(self._on_track_changed)
        self.viewmodel.point_selected.connect(self._on_point_selected)
        
    
    def _assemble_window_layout(self):
        
        self.setWindowTitle(self.viewmodel.localization['mapview_title'])
        self.resize(400, 400)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0,0,0,0)

        layout.addWidget(self.map_view)
    
    def _initialize_map_view(self):
        
        _coordinates = [list(_) for _ in self.viewmodel.profile.coordinates]
        _selected_coordinate = _coordinates[self.viewmodel.selected_point]
        
        self.map_view.setHtml(f'''
            <!DOCTYPE html>
            <html>
            <head>
                <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
                <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
                <style>
                    body {{ margin: 0; padding: 0; }}
                    #map {{ width: 100vw; height: 100vh; }}
                </style>
            </head>
            <body>
                <div id="map"></div>
                <script>
                    var map = L.map('map').setView({_selected_coordinate}, 14);
                    map.attributionControl.setPrefix('Leaflet');
                    L.tileLayer('https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png', {{
                        attribution: '&copy; OpenStreetMap contributors'
                    }}).addTo(map);
                    L.polyline({_coordinates}, {{color: \'gray\', weight: 4}}).addTo(map);
                    var marker = L.marker({_selected_coordinate}).addTo(map);
                </script>
            </body>
            </html>
        ''')
        
        self._map_view_initialized = True

    def _on_point_selected(self):
        
        if self.isVisible():
        
            if not self._map_view_initialized:
                self._initialize_map_view()
            else:
                _selected_coordinate = list(self.viewmodel.profile.coordinates[self.viewmodel.selected_point])
                
                js = f'''
                    var latlng = L.latLng({_selected_coordinate[0]}, {_selected_coordinate[1]});
                    marker.setLatLng(latlng);
                    map.panTo(latlng);
                '''
                self.map_view.page().runJavaScript(js)
            
    def _on_track_changed(self):
        self._map_view_initialized = False
        
        self._on_point_selected()
    
