import sys
import os
import json
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QFileDialog, QLabel, QListWidget, QListWidgetItem, QSlider, QComboBox,
    QLineEdit, QGridLayout, QSplitter, QGroupBox, QFormLayout, QCheckBox,
    QFrame, QInputDialog, QMessageBox, QAction, QMenu, QMenuBar, QColorDialog, QSizePolicy, QScrollArea
)
from PyQt5.QtGui import QPixmap, QPainter, QColor, QFont, QIcon, QBrush, QPen, QFontDatabase, QImage
from PyQt5.QtCore import Qt, QPoint, QSize
from PIL import Image, ImageDraw, ImageFont

class WatermarkApp(QMainWindow):
    def __init__(self):
        super().__init__()
        # 初始化实例变量
        self.current_image_index = -1
        self.images = []
        self.watermark_pos = QPoint(100, 100)
        self.dragging = False
        self.drag_start = QPoint()
        self.output_folder_path = ""
        self.current_color = "#000000"
        self.current_stroke_color = "#FFFFFF"
        self.use_prefix = False
        self.use_suffix = False
        
        # 新增图片水印相关变量
        self.watermark_type = "text"  # text 或 image
        self.image_watermark_path = ""
        self.image_watermark = None
        self.image_watermark_scale = 100  # 百分比
        self.image_watermark_width = 100
        self.image_watermark_height = 100
        self.image_watermark_resize_method = "按百分比"
        
        self.init_ui()
        self.load_last_settings()
        
    def init_ui(self):
        # 设置窗口标题和大小，增大初始尺寸以便更好地显示预览
        self.setWindowTitle("图片水印工具")
        self.setGeometry(100, 100, 1600, 900)  # 增加窗口宽度，确保右侧菜单栏可以完整显示
        
        # 创建中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 创建主布局 - 使用QSplitter实现可调整大小的三面板布局
        main_splitter = QSplitter(Qt.Horizontal)
        main_layout = QHBoxLayout(central_widget)
        main_layout.addWidget(main_splitter)
        
        # 创建左侧面板（文件列表）
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_panel.setMaximumWidth(280)
        
        # 文件操作按钮
        file_ops_layout = QHBoxLayout()
        self.import_btn = QPushButton("导入图片")
        self.import_btn.clicked.connect(self.import_images)
        self.import_folder_btn = QPushButton("导入文件夹")
        self.import_folder_btn.clicked.connect(self.import_folder)
        file_ops_layout.addWidget(self.import_btn)
        file_ops_layout.addWidget(self.import_folder_btn)
        
        # 文件列表
        self.file_list = QListWidget()
        self.file_list.setViewMode(QListWidget.IconMode)
        self.file_list.setIconSize(QSize(200, 200))
        self.file_list.setResizeMode(QListWidget.Adjust)
        self.file_list.setMovement(QListWidget.Static)
        self.file_list.itemClicked.connect(self.on_file_selected)
        self.file_list.setSpacing(10)  # 增加缩略图之间的间距
        
        # 导出按钮
        self.export_btn = QPushButton("导出图片")
        self.export_btn.clicked.connect(self.export_images)
        self.export_btn.setEnabled(False)
        
        # 输出文件夹选择
        self.output_folder = QLineEdit()
        self.output_folder.setReadOnly(True)
        self.output_folder.setPlaceholderText("未选择输出文件夹")
        
        self.select_folder_btn = QPushButton("选择文件夹")
        self.select_folder_btn.clicked.connect(self.select_output_folder)
        
        folder_layout = QHBoxLayout()
        folder_layout.addWidget(self.output_folder)
        folder_layout.addWidget(self.select_folder_btn)
        
        left_layout.addLayout(file_ops_layout)
        left_layout.addWidget(QLabel("已导入图片:"))
        left_layout.addWidget(self.file_list)
        left_layout.addWidget(QLabel("输出文件夹:"))
        left_layout.addLayout(folder_layout)
        left_layout.addWidget(self.export_btn)
        
        # 创建中间面板（预览）- 大幅增加预览区域
        center_panel = QWidget()
        center_layout = QVBoxLayout(center_panel)
        
        # 预览窗口，大幅增加最小尺寸以更好地显示水印效果
        self.preview_label = QLabel("预览窗口")
        self.preview_label.setAlignment(Qt.AlignCenter)
        self.preview_label.setMinimumSize(800, 700)  # 大幅增加预览窗口最小尺寸
        self.preview_label.setStyleSheet("background-color: #f0f0f0; border: 1px solid #ccc;")
        self.preview_label.mousePressEvent = self.on_preview_mouse_press
        self.preview_label.mouseMoveEvent = self.on_preview_mouse_move
        self.preview_label.mouseReleaseEvent = self.on_preview_mouse_release
        
        center_layout.addWidget(QLabel("预览:"))
        center_layout.addWidget(self.preview_label)
        
        # 创建右侧面板（设置）
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_panel.setMaximumWidth(500)  # 增加最大宽度以完整显示所有选项
        
        # 创建滚动区域，放置所有设置项
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)
        scroll_area.setWidget(scroll_widget)
        
        # 水印类型选择
        watermark_type_group = QGroupBox("水印类型")
        watermark_type_layout = QHBoxLayout()
        
        self.text_watermark_radio = QCheckBox("文本水印")
        self.text_watermark_radio.setChecked(True)
        self.text_watermark_radio.stateChanged.connect(self.set_watermark_type)
        
        self.image_watermark_radio = QCheckBox("图片水印")
        self.image_watermark_radio.stateChanged.connect(self.set_watermark_type)
        
        watermark_type_layout.addWidget(self.text_watermark_radio)
        watermark_type_layout.addWidget(self.image_watermark_radio)
        watermark_type_group.setLayout(watermark_type_layout)
        scroll_layout.addWidget(watermark_type_group)
        
        # 文本水印设置
        self.text_watermark_group = QGroupBox("文本水印设置")
        text_watermark_layout = QFormLayout()
        
        self.watermark_text = QLineEdit("水印文字")
        self.watermark_text.textChanged.connect(self.update_preview)
        
        # 字体大小选择器
        self.font_size = QComboBox()
        # 允许用户输入任意大小，并提供常用选项
        self.font_size.setEditable(True)
        for size in range(8, 120, 2):
            self.font_size.addItem(str(size))
        self.font_size.setCurrentText("24")
        self.font_size.currentTextChanged.connect(self.update_preview)
        
        # 粗体选项
        style_layout = QHBoxLayout()
        self.bold_checkbox = QCheckBox("粗体")
        self.bold_checkbox.stateChanged.connect(self.update_preview)
        style_layout.addWidget(self.bold_checkbox)
        
        self.transparency = QSlider(Qt.Horizontal)
        self.transparency.setRange(0, 100)
        self.transparency.setValue(50)
        self.transparency.setTickPosition(QSlider.TicksBelow)
        self.transparency.setTickInterval(10)
        self.transparency.valueChanged.connect(self.update_preview)
        
        self.transparency_label = QLabel("透明度: 50%")
        self.transparency.valueChanged.connect(lambda value: self.transparency_label.setText(f"透明度: {value}%"))
        
        # 高级颜色选择器
        color_layout = QHBoxLayout()
        self.color_preview = QLabel()
        self.color_preview.setMinimumWidth(30)
        self.color_preview.setStyleSheet("background-color: #000000; border: 1px solid #ccc;")
        self.color_button = QPushButton("选择颜色")
        self.color_button.clicked.connect(self.select_color)
        self.current_color = "#000000"
        color_layout.addWidget(self.color_preview)
        color_layout.addWidget(self.color_button)
        
        # 文本效果
        effects_group = QGroupBox("文本效果")
        effects_layout = QFormLayout()
        
        # 阴影效果
        self.shadow_checkbox = QCheckBox("添加阴影")
        self.shadow_checkbox.stateChanged.connect(self.toggle_shadow_options)
        effects_layout.addRow(self.shadow_checkbox)
        
        self.shadow_distance = QSlider(Qt.Horizontal)
        self.shadow_distance.setRange(1, 10)
        self.shadow_distance.setValue(2)
        self.shadow_distance.setEnabled(False)
        self.shadow_distance.valueChanged.connect(self.update_preview)
        effects_layout.addRow("阴影距离:", self.shadow_distance)
        
        # 描边效果
        self.stroke_checkbox = QCheckBox("添加描边")
        self.stroke_checkbox.stateChanged.connect(self.toggle_stroke_options)
        effects_layout.addRow(self.stroke_checkbox)
        
        self.stroke_width = QSlider(Qt.Horizontal)
        self.stroke_width.setRange(1, 5)
        self.stroke_width.setValue(1)
        self.stroke_width.setEnabled(False)
        self.stroke_width.valueChanged.connect(self.update_preview)
        effects_layout.addRow("描边宽度:", self.stroke_width)
        
        self.stroke_color_button = QPushButton("描边颜色")
        self.stroke_color_button.setEnabled(False)
        self.stroke_color_button.clicked.connect(self.select_stroke_color)
        self.stroke_color_preview = QLabel()
        self.stroke_color_preview.setMinimumWidth(30)
        self.stroke_color_preview.setStyleSheet("background-color: #FFFFFF; border: 1px solid #ccc;")
        self.current_stroke_color = "#FFFFFF"
        
        stroke_color_layout = QHBoxLayout()
        stroke_color_layout.addWidget(self.stroke_color_preview)
        stroke_color_layout.addWidget(self.stroke_color_button)
        effects_layout.addRow("描边颜色:", stroke_color_layout)
        effects_group.setLayout(effects_layout)
        
        text_watermark_layout.addRow("水印文本:", self.watermark_text)
        text_watermark_layout.addRow("字体大小:", self.font_size)
        text_watermark_layout.addRow("字体样式:", style_layout)
        text_watermark_layout.addRow(self.transparency_label, self.transparency)
        text_watermark_layout.addRow("字体颜色:", color_layout)
        text_watermark_layout.addRow(effects_group)
        self.text_watermark_group.setLayout(text_watermark_layout)
        scroll_layout.addWidget(self.text_watermark_group)
        
        # 图片水印设置
        self.image_watermark_group = QGroupBox("图片水印设置")
        image_watermark_layout = QFormLayout()
        
        # 选择图片按钮
        self.select_image_btn = QPushButton("选择图片水印")
        self.select_image_btn.clicked.connect(self.select_image_watermark)
        image_watermark_layout.addRow(self.select_image_btn)
        
        # 显示已选择的图片路径
        self.image_path_label = QLabel("未选择图片")
        self.image_path_label.setWordWrap(True)
        self.image_path_label.setMaximumHeight(40)
        image_watermark_layout.addRow(self.image_path_label)
        
        # 图片水印透明度
        self.image_transparency = QSlider(Qt.Horizontal)
        self.image_transparency.setRange(0, 100)
        self.image_transparency.setValue(50)
        self.image_transparency.setTickPosition(QSlider.TicksBelow)
        self.image_transparency.setTickInterval(10)
        self.image_transparency.valueChanged.connect(self.update_preview)
        
        self.image_transparency_label = QLabel("透明度: 50%")
        self.image_transparency.valueChanged.connect(lambda value: self.image_transparency_label.setText(f"透明度: {value}%"))
        image_watermark_layout.addRow(self.image_transparency_label, self.image_transparency)
        
        # 图片大小调整
        self.image_resize_method = QComboBox()
        self.image_resize_method.addItem("按百分比")
        self.image_resize_method.addItem("按宽度")
        self.image_resize_method.addItem("按高度")
        self.image_resize_method.currentIndexChanged.connect(self.toggle_image_resize_options)
        image_watermark_layout.addRow("调整方式:", self.image_resize_method)
        
        self.image_percent_slider = QSlider(Qt.Horizontal)
        self.image_percent_slider.setRange(10, 300)
        self.image_percent_slider.setValue(100)
        self.image_percent_slider.setTickPosition(QSlider.TicksBelow)
        self.image_percent_slider.setTickInterval(10)
        self.image_percent_slider.valueChanged.connect(self.update_image_watermark_scale)
        self.image_percent_slider.valueChanged.connect(self.update_preview)
        
        self.image_percent_label = QLabel("大小: 100%")
        image_watermark_layout.addRow(self.image_percent_label, self.image_percent_slider)
        
        self.image_width_input = QLineEdit()
        self.image_width_input.setPlaceholderText("输入宽度")
        self.image_width_input.setEnabled(False)
        self.image_width_input.editingFinished.connect(self.update_image_size_from_input)
        image_watermark_layout.addRow("宽度 (像素):", self.image_width_input)
        
        self.image_height_input = QLineEdit()
        self.image_height_input.setPlaceholderText("输入高度")
        self.image_height_input.setEnabled(False)
        self.image_height_input.editingFinished.connect(self.update_image_size_from_input)
        image_watermark_layout.addRow("高度 (像素):", self.image_height_input)
        
        self.image_watermark_group.setLayout(image_watermark_layout)
        scroll_layout.addWidget(self.image_watermark_group)
        self.image_watermark_group.hide()  # 默认隐藏图片水印设置
        
        # 位置设置
        position_group = QGroupBox("水印位置")
        position_layout = QGridLayout()
        
        positions = [
            ("左上", 0, 0), ("中上", 0, 1), ("右上", 0, 2),
            ("左中", 1, 0), ("中心", 1, 1), ("右中", 1, 2),
            ("左下", 2, 0), ("中下", 2, 1), ("右下", 2, 2)
        ]
        
        self.position_buttons = []
        for name, row, col in positions:
            btn = QPushButton(name)
            btn.setFixedSize(60, 30)
            btn.clicked.connect(lambda checked, pos=name: self.set_watermark_position(pos))
            position_layout.addWidget(btn, row, col)
            self.position_buttons.append(btn)
        
        position_group.setLayout(position_layout)
        scroll_layout.addWidget(position_group)
        
        # 导出设置
        export_group = QGroupBox("导出设置")
        export_layout = QFormLayout()
        
        # 输出格式
        self.output_format = QComboBox()
        self.output_format.addItem("JPEG")
        self.output_format.addItem("PNG")
        self.output_format.currentTextChanged.connect(self.toggle_quality_settings)
        export_layout.addRow("输出格式:", self.output_format)
        
        # JPEG质量设置
        self.quality_slider = QSlider(Qt.Horizontal)
        self.quality_slider.setRange(1, 100)
        self.quality_slider.setValue(90)
        self.quality_slider.setTickPosition(QSlider.TicksBelow)
        self.quality_slider.setTickInterval(10)
        
        self.quality_label = QLabel("质量: 90%")
        self.quality_slider.valueChanged.connect(lambda value: self.quality_label.setText(f"质量: {value}%"))
        export_layout.addRow(self.quality_label, self.quality_slider)
        
        # 图片尺寸调整
        self.resize_method = QComboBox()
        self.resize_method.addItem("原始尺寸")
        self.resize_method.addItem("按宽度")
        self.resize_method.addItem("按高度")
        self.resize_method.addItem("按百分比")
        self.resize_method.currentTextChanged.connect(self.toggle_resize_options)
        export_layout.addRow("尺寸调整:", self.resize_method)
        
        # 宽度输入
        self.width_input = QLineEdit()
        self.width_input.setPlaceholderText("输入宽度")
        self.width_input.setEnabled(False)
        export_layout.addRow("宽度 (像素):", self.width_input)
        
        # 高度输入
        self.height_input = QLineEdit()
        self.height_input.setPlaceholderText("输入高度")
        self.height_input.setEnabled(False)
        export_layout.addRow("高度 (像素):", self.height_input)
        
        # 百分比调整
        self.percent_slider = QSlider(Qt.Horizontal)
        self.percent_slider.setRange(10, 300)
        self.percent_slider.setValue(100)
        self.percent_slider.setTickPosition(QSlider.TicksBelow)
        self.percent_slider.setTickInterval(10)
        self.percent_slider.setEnabled(False)
        
        self.percent_label = QLabel("大小: 100%")
        self.percent_slider.valueChanged.connect(lambda value: self.percent_label.setText(f"大小: {value}%"))
        export_layout.addRow(self.percent_label, self.percent_slider)
        
        # 文件命名选项
        self.preserve_filename = QCheckBox("保留原始文件名")
        self.preserve_filename.setChecked(True)
        self.preserve_filename.stateChanged.connect(lambda state: self.toggle_filename_options(state))
        export_layout.addRow(self.preserve_filename)
        
        # 文件前缀和后缀
        self.prefix = QLineEdit()
        self.prefix.setPlaceholderText("文件前缀")
        self.prefix.setEnabled(False)
        self.prefix.textChanged.connect(self.toggle_prefix_suffix)
        
        self.suffix = QLineEdit()
        self.suffix.setPlaceholderText("文件后缀")
        self.suffix.setEnabled(False)
        self.suffix.textChanged.connect(self.toggle_prefix_suffix)
        
        export_layout.addRow("文件前缀:", self.prefix)
        export_layout.addRow("文件后缀:", self.suffix)
        
        export_group.setLayout(export_layout)
        scroll_layout.addWidget(export_group)
        
        # 模板设置
        template_group = QGroupBox("模板管理")
        template_layout = QFormLayout()
        
        # 模板选择下拉框
        self.template_list = QComboBox()
        template_layout.addRow("选择模板:", self.template_list)
        
        # 模板操作按钮
        template_buttons_layout = QHBoxLayout()
        self.save_template_btn = QPushButton("保存模板")
        self.save_template_btn.clicked.connect(self.save_template)
        self.load_template_btn = QPushButton("加载模板")
        self.load_template_btn.clicked.connect(self.load_template)
        self.delete_template_btn = QPushButton("删除模板")
        self.delete_template_btn.clicked.connect(self.delete_template)
        
        template_buttons_layout.addWidget(self.save_template_btn)
        template_buttons_layout.addWidget(self.load_template_btn)
        template_buttons_layout.addWidget(self.delete_template_btn)
        template_layout.addRow(template_buttons_layout)
        
        template_group.setLayout(template_layout)
        scroll_layout.addWidget(template_group)
        scroll_layout.addStretch()
        
        # 将滚动区域添加到右侧布局
        right_layout.addWidget(scroll_area)
        
        # 使用Splitter替代固定宽度的布局
        main_splitter = QSplitter(Qt.Horizontal)
        main_splitter.addWidget(left_panel)
        main_splitter.addWidget(center_panel)
        main_splitter.addWidget(right_panel)
        
        # 设置初始大小比例，给预览区域更多空间，右侧面板初始宽度也增加到500
        main_splitter.setSizes([300, 800, 500])
        
        # 将Splitter添加到主布局
        main_layout.addWidget(main_splitter)
        
        # 初始化变量
        self.images = []
        self.current_image_index = -1
        self.watermark_pos = QPoint(100, 100)
        self.dragging = False
        self.drag_start = QPoint()
        self.output_folder_path = ""
        self.use_prefix = False
        self.use_suffix = False
        self.watermark_type = "text"  # 默认使用文本水印
        
        # 图片水印相关变量初始化
        self.image_watermark = None
        self.image_watermark_path = ""
        self.image_watermark_width = 0
        self.image_watermark_height = 0
        self.image_watermark_scale = 100  # 默认100%
        
        # 初始化质量设置显示
        self.toggle_quality_settings()
        
        # 创建菜单
        self.create_menu()
    
    def create_menu(self):
        menubar = self.menuBar()
        
        # 文件菜单
        file_menu = menubar.addMenu("文件")
        
        import_action = QAction("导入图片", self)
        import_action.triggered.connect(self.import_images)
        file_menu.addAction(import_action)
        
        import_folder_action = QAction("导入文件夹", self)
        import_folder_action.triggered.connect(self.import_folder)
        file_menu.addAction(import_folder_action)
        
        file_menu.addSeparator()
        
        export_action = QAction("导出图片", self)
        export_action.triggered.connect(self.export_images)
        file_menu.addAction(export_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction("退出", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # 帮助菜单
        help_menu = menubar.addMenu("帮助")
        
        about_action = QAction("关于", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
    
    def import_images(self):
        file_paths, _ = QFileDialog.getOpenFileNames(
            self, "选择图片文件", "", "图片文件 (*.jpg *.jpeg *.png *.bmp *.tiff *.tif)"
        )
        
        if file_paths:
            self.add_images(file_paths)
    
    def import_folder(self):
        folder_path = QFileDialog.getExistingDirectory(self, "选择文件夹", "")
        
        if folder_path:
            valid_extensions = ['.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.tif']
            file_paths = []
            
            for root, _, files in os.walk(folder_path):
                for file in files:
                    if any(file.lower().endswith(ext) for ext in valid_extensions):
                        file_paths.append(os.path.join(root, file))
            
            if file_paths:
                self.add_images(file_paths)
            else:
                QMessageBox.warning(self, "警告", "所选文件夹中没有支持的图片文件")
    
    def add_images(self, file_paths):
        for file_path in file_paths:
            # 检查文件是否已存在
            if any(os.path.abspath(img['path']) == os.path.abspath(file_path) for img in self.images):
                continue
            
            try:
                # 打开图片并创建缩略图
                img = Image.open(file_path)
                
                # 保存图片信息
                self.images.append({
                    'path': file_path,
                    'image': img,
                    'original_path': file_path
                })
                
                # 创建列表项
                item = QListWidgetItem(os.path.basename(file_path))
                
                # 创建缩略图用于显示
                thumbnail = img.copy()
                thumbnail.thumbnail((200, 200))
                
                # 转换为QPixmap
                try:
                    # 尝试直接使用PyQt5的QImage转换
                    if thumbnail.mode == 'RGBA':
                        data = thumbnail.tobytes("raw", "RGBA")
                        q_image = QImage(data, thumbnail.width, thumbnail.height, QImage.Format_RGBA8888)
                    else:
                        data = thumbnail.tobytes("raw", "RGBX")
                        q_image = QImage(data, thumbnail.width, thumbnail.height, QImage.Format_RGBX8888)
                    pixmap = QPixmap.fromImage(q_image)
                    item.setIcon(QIcon(pixmap))
                    self.file_list.addItem(item)
                except Exception as e:
                    QMessageBox.warning(self, "错误", f"无法创建缩略图: {str(e)}")
                    # 如果无法创建缩略图，仍添加文件但不显示缩略图
                    self.file_list.addItem(item)
                
            except Exception as e:
                QMessageBox.warning(self, "错误", f"无法打开文件 {os.path.basename(file_path)}: {str(e)}")
        
        # 如果是第一次导入图片，自动选择第一张
        if len(self.images) > 0 and self.current_image_index == -1:
            self.current_image_index = 0
            self.file_list.setCurrentRow(0)
            self.update_preview()
        
        # 启用导出按钮
        self.export_btn.setEnabled(len(self.images) > 0)
    
    def on_file_selected(self, item):
        index = self.file_list.row(item)
        if 0 <= index < len(self.images):
            self.current_image_index = index
            self.update_preview()
    
    def update_preview(self):
        if self.current_image_index < 0 or self.current_image_index >= len(self.images):
            return
        
        img_info = self.images[self.current_image_index]
        img = img_info['image'].copy()
        
        # 添加水印
        watermarked_img = self.add_watermark_to_image(img)
        
        # 调整预览大小以适应窗口，完全利用可用空间
        preview_size = self.preview_label.size()
        
        # 计算合适的显示大小，移除最大缩放限制，让图片尽可能大
        img_width, img_height = watermarked_img.size
        scale = min(preview_size.width() / img_width, preview_size.height() / img_height)  # 移除最大缩放限制，让图片完全填充预览区域
        new_width = int(img_width * scale)
        new_height = int(img_height * scale)
        
        # 调整图片大小
        resized_img = watermarked_img.resize((new_width, new_height))
        
        # 转换为QPixmap并显示
        try:
            # 尝试直接使用PyQt5的QImage转换
            if resized_img.mode == 'RGBA':
                data = resized_img.tobytes("raw", "RGBA")
                q_image = QImage(data, resized_img.width, resized_img.height, QImage.Format_RGBA8888)
            else:
                data = resized_img.tobytes("raw", "RGBX")
                q_image = QImage(data, resized_img.width, resized_img.height, QImage.Format_RGBX8888)
            pixmap = QPixmap.fromImage(q_image)
        except Exception as e:
            print(f"转换图像失败: {str(e)}")
            return
        self.preview_label.setPixmap(pixmap)
    
    def set_watermark_type(self, state):
        # 初始化按钮组（如果尚未初始化）
        if not hasattr(self, 'watermark_type_buttons'):
            self.watermark_type_buttons = [self.text_watermark_radio, self.image_watermark_radio]
        
        # 判断哪个复选框被触发
        if self.sender() == self.text_watermark_radio:
            if state == Qt.Checked:
                self.watermark_type = "text"
                self.image_watermark_radio.setChecked(False)
                self.text_watermark_group.show()
                self.image_watermark_group.hide()
        elif self.sender() == self.image_watermark_radio:
            if state == Qt.Checked:
                self.watermark_type = "image"
                self.text_watermark_radio.setChecked(False)
                self.text_watermark_group.hide()
                self.image_watermark_group.show()
        
        # 更新预览
        self.update_preview()
    
    def select_image_watermark(self):
        # 打开文件选择对话框，仅允许选择图片文件
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择图片水印", "", "图片文件 (*.png *.jpg *.jpeg *.bmp *.gif)"
        )
        
        if file_path:
            try:
                # 尝试打开图片
                img = Image.open(file_path).convert('RGBA')
                
                # 保存图片水印信息
                self.image_watermark_path = file_path
                self.image_watermark = img
                self.image_watermark_width, self.image_watermark_height = img.size
                
                # 更新UI显示
                self.image_path_label.setText(os.path.basename(file_path))
                self.image_width_input.setText(str(self.image_watermark_width))
                self.image_height_input.setText(str(self.image_watermark_height))
                
                # 更新预览
                self.update_preview()
                
            except Exception as e:
                QMessageBox.warning(self, "错误", f"无法打开图片: {str(e)}")
    
    def toggle_image_resize_options(self):
        method = self.image_resize_method.currentText()
        
        # 根据选择的调整方式启用对应的输入控件
        self.image_percent_slider.setEnabled(method == "按百分比")
        self.image_percent_label.setEnabled(method == "按百分比")
        self.image_width_input.setEnabled(method == "按宽度")
        self.image_height_input.setEnabled(method == "按高度")
    
    def update_image_watermark_scale(self, value):
        self.image_watermark_scale = value
        self.image_percent_label.setText(f"大小: {value}%")
    
    def update_image_size_from_input(self):
        try:
            if self.image_resize_method.currentText() == "按宽度":
                new_width = int(self.image_width_input.text())
                # 保持宽高比
                scale = new_width / self.image_watermark_width
                new_height = int(self.image_watermark_height * scale)
                self.image_height_input.setText(str(new_height))
            elif self.image_resize_method.currentText() == "按高度":
                new_height = int(self.image_height_input.text())
                # 保持宽高比
                scale = new_height / self.image_watermark_height
                new_width = int(self.image_watermark_width * scale)
                self.image_width_input.setText(str(new_width))
            
            # 更新预览
            self.update_preview()
        except ValueError:
            pass  # 忽略无效输入
    
    def add_watermark_to_image(self, img):
        # 确保图片支持透明度
        if img.mode != 'RGBA':
            img = img.convert('RGBA')
        
        # 创建一个可绘制的副本
        watermark_img = Image.new('RGBA', img.size, (255, 255, 255, 0))
        
        # 根据水印类型添加水印
        if self.watermark_type == "text":
            draw = ImageDraw.Draw(watermark_img)
            
            # 获取水印文本和设置
            text = self.watermark_text.text()
            if not text:
                return img
            
            font_size = int(self.font_size.currentText())
            transparency = self.transparency.value()
            
            # 解析颜色（从新的颜色选择器获取）
            color_code = self.current_color
            r = int(color_code[1:3], 16)
            g = int(color_code[3:5], 16)
            b = int(color_code[5:7], 16)
            
            # 创建字体（使用默认字体）
            font = None
            font_family = "SimHei"  # 使用默认中文字体
            bold = self.bold_checkbox.isChecked()
            italic = False  # 斜体功能已移除
            
            print(f"使用字体: {font_family}, 粗体: {bold}")
            
            try:
                # 验证字体大小是有效的数字
                try:
                    font_size = int(font_size) if isinstance(font_size, str) else font_size
                    # 限制字体大小范围，防止过大或过小的字体导致问题
                    font_size = max(4, min(font_size, 500))
                except ValueError:
                    print(f"无效的字体大小: {font_size}，使用默认大小24")
                    font_size = 24
                
                # 构建常见中文字体的映射表
                chinese_fonts_map = {
                    'Microsoft YaHei': ['msyh.ttc', 'msyhbd.ttc', 'msyhl.ttc'],
                    'SimHei': ['simhei.ttf'],
                    'SimSun': ['simsun.ttc'],
                    'KaiTi': ['simkai.ttf'],
                    'FangSong': ['simfang.ttf'],
                    'LiSu': ['lisu.ttf'],    # 隶书
                    'YouYuan': ['youyuan.ttf'],  # 幼圆
                    'DengXian': ['dengxian.ttc', 'dengxianbd.ttc']  # 等线
                }
                
                # 初始化Windows字体目录路径（如果适用）
                windows_font_dir = r"C:\Windows\Fonts" if os.name == 'nt' else None
                
                # 改进的字体加载策略
                # 1. 首先尝试使用PIL的ImageFont.truetype直接加载字体
                # 构建可能的字体变体名称
                font_variants = []
                if bold and italic:
                    font_variants.extend([
                        f"{font_family} Bold Italic",
                        f"{font_family}-BoldItalic",
                        f"{font_family} Bold-Italic",
                        f"{font_family} BI"
                    ])
                elif bold:
                    font_variants.extend([
                        f"{font_family} Bold",
                        f"{font_family}-Bold",
                        f"{font_family}bd"
                    ])
                elif italic:
                    font_variants.extend([
                        f"{font_family} Italic",
                        f"{font_family}-Italic",
                        f"{font_family}i"
                    ])
                font_variants.append(font_family)
                
                print(f"尝试的字体变体: {font_variants}")
                
                # 尝试加载字体变体
                for variant in font_variants:
                    try:
                        font = ImageFont.truetype(variant, font_size)
                        print(f"成功加载字体变体: {variant}")
                        break
                    except Exception as e:
                        print(f"无法加载字体变体 {variant}: {str(e)}")
                        # 继续尝试下一个变体，不中断程序
                        continue
                
                # 2. 如果直接使用字体名称失败且是Windows系统，尝试查找字体文件
                if font is None and windows_font_dir and os.path.exists(windows_font_dir):
                    print(f"在Windows字体目录中查找: {windows_font_dir}")
                    
                    # 构建搜索的字体文件列表
                    font_files = []
                    
                    # 先检查是否是常见中文字体
                    if font_family in chinese_fonts_map:
                        # 根据粗体和斜体选择合适的字体文件
                        if bold and italic and len(chinese_fonts_map[font_family]) > 3:
                            font_files = [os.path.join(windows_font_dir, chinese_fonts_map[font_family][2])]
                        elif bold and len(chinese_fonts_map[font_family]) > 1:
                            font_files = [os.path.join(windows_font_dir, chinese_fonts_map[font_family][1])]
                        else:
                            font_files = [os.path.join(windows_font_dir, chinese_fonts_map[font_family][0])]
                        print(f"添加常见中文字体文件路径: {font_files}")
                    
                    # 根据粗体和斜体设置构建可能的字体文件名
                    if not font_files:
                        base_name = font_family.lower().replace(' ', '')
                        extensions = ['.ttf', '.ttc', '.otf', '.fon']
                        
                        # 构建可能的文件基础名称变体
                        file_basenames = []
                        if bold and italic:
                            file_basenames.extend([base_name, base_name+'bi', base_name+'bdit', base_name+'bolditalic'])
                        elif bold:
                            file_basenames.extend([base_name, base_name+'bd', base_name+'bold'])
                        elif italic:
                            file_basenames.extend([base_name, base_name+'i', base_name+'italic'])
                        else:
                            file_basenames.append(base_name)
                        
                        # 去重
                        file_basenames = list(set(file_basenames))
                        print(f"尝试的字体文件基础名称: {file_basenames}")
                        
                        # 生成完整的文件路径
                        for bn in file_basenames:
                            for ext in extensions:
                                font_files.append(os.path.join(windows_font_dir, bn + ext))
                    
                    # 尝试加载字体文件
                    for font_file in font_files:
                        try:
                            if os.path.exists(font_file):
                                print(f"尝试加载字体文件: {font_file}")
                                font = ImageFont.truetype(font_file, font_size)
                                print(f"成功加载字体文件: {font_file}")
                                break
                        except Exception as e:
                            print(f"无法加载字体文件 {font_file}: {str(e)}")
                            # 继续尝试下一个文件，不中断程序
                            continue
                
                # 3. 如果以上方法都失败，尝试通用的中文字体回退列表
                if font is None:
                    print("尝试加载通用中文字体")
                    fallback_fonts = ["SimHei", "WenQuanYi Micro Hei", "Heiti TC", "Microsoft YaHei", "SimSun", "Arial Unicode MS"]
                    
                    for fallback_font in fallback_fonts:
                        try:
                            font = ImageFont.truetype(fallback_font, font_size)
                            print(f"成功加载回退字体: {fallback_font}")
                            break
                        except Exception as e:
                            print(f"无法加载回退字体 {fallback_font}: {str(e)}")
                            # 继续尝试下一个回退字体，不中断程序
                            continue
                
                # 4. 最终回退：使用PIL自带的默认字体
                if font is None:
                    print("无法加载任何指定字体，使用PIL默认字体作为最终回退")
                    font = ImageFont.load_default()
                    # 打印默认字体的信息
                    print(f"使用默认字体: {font.getname() if hasattr(font, 'getname') else 'Default Font'}")
            except Exception as e:
                print(f"字体加载过程中发生严重错误: {str(e)}")
                # 发生任何异常时，使用默认字体作为最后的保障
                try:
                    font = ImageFont.load_default()
                    print("已回退到默认字体")
                except:
                    # 如果连默认字体都加载失败，创建一个简单的字体对象
                    # 这是最后的安全保障，确保程序不会因字体问题而崩溃
                    print("警告: 无法加载默认字体，程序可能无法正确显示文本")
                    # 创建一个功能更完整的DummyFont对象，支持中文文本处理
                    class DummyFont:
                        def __init__(self, size=font_size):
                            self.size = size
                        def getsize(self, text):
                            # 估算文本尺寸，确保中文能被正确处理
                            try:
                                # 对于中文，每个字符大约占一个半英文字符宽度
                                width = len(text) * self.size // 2
                                for char in text:
                                    if ord(char) > 127:  # 非ASCII字符（如中文）
                                        width += self.size // 4
                                return (width, self.size)
                            except:
                                return (len(text) * self.size // 2, self.size)
                        def getname(self):
                            return ("DummyFont", "Regular")
                        def getbbox(self, text, *args, **kwargs):
                            # 实现getbbox方法以避免在处理中文时出错
                            width, height = self.getsize(text)
                            return (0, -height // 2, width, height // 2)
                    font = DummyFont(font_size)
            
            # 应用斜体效果（如果需要）
            if italic:
                try:
                    # 首先尝试加载专门的斜体字体文件
                    italic_font = None
                    if os.name == 'nt' and font_family in chinese_fonts_map and len(chinese_fonts_map[font_family]) > 2:
                        italic_font_path = os.path.join(windows_font_dir, chinese_fonts_map[font_family][2])
                        if os.path.exists(italic_font_path):
                            italic_font = ImageFont.truetype(italic_font_path, font_size)
                            font = italic_font
                            print(f"已加载专门的斜体字体文件: {italic_font_path}")
                    
                    # 如果没有专门的斜体字体文件，尝试使用字体变换创建伪斜体效果
                    if italic_font is None:
                        # 使用PIL的ImageDraw方法实现伪斜体
                        # 我们会在绘制文本时应用斜体变换
                        print("无法加载专门的斜体字体文件，将在绘制时应用伪斜体效果")
                except Exception as e:
                    print(f"无法应用斜体效果: {str(e)}")
                    # 如果变换失败，保持原字体
                    pass
            
            # 获取文本尺寸
            # 对于斜体文本，我们需要调整计算方式
            try:
                if italic:
                    # 创建一个临时的图像来测量斜体文本的尺寸
                    temp_img = Image.new('RGBA', (1000, 1000), (255, 255, 255, 0))
                    temp_draw = ImageDraw.Draw(temp_img)
                    # 正常文本的尺寸
                    try:
                        bbox = temp_draw.textbbox((0, 0), text, font=font)
                        text_width = bbox[2] - bbox[0]
                        text_height = bbox[3] - bbox[1]
                    except UnicodeEncodeError:
                        print(f"计算斜体文本尺寸时出现编码错误")
                        # 使用简化方法估算文本尺寸
                        width_ratio = 1.5 if any(ord(char) > 127 for char in text) else 1.0
                        text_width = int(len(text) * font_size * 0.5 * width_ratio)
                        text_height = font_size
                    except Exception as e:
                        print(f"计算斜体文本尺寸时出错: {str(e)}")
                        # 使用简化方法估算文本尺寸
                        text_width = len(text) * font_size // 2
                        text_height = font_size
                    # 斜体文本通常比正常文本宽10-15%
                    text_width = int(text_width * 1.15)
                else:
                    try:
                        bbox = draw.textbbox((0, 0), text, font=font)
                        text_width = bbox[2] - bbox[0]
                        text_height = bbox[3] - bbox[1]
                    except UnicodeEncodeError:
                        print(f"计算文本尺寸时出现编码错误")
                        # 使用简化方法估算文本尺寸
                        width_ratio = 1.5 if any(ord(char) > 127 for char in text) else 1.0
                        text_width = int(len(text) * font_size * 0.5 * width_ratio)
                        text_height = font_size
                    except Exception as e:
                        print(f"计算文本尺寸时出错: {str(e)}")
                        # 使用简化方法估算文本尺寸
                        text_width = len(text) * font_size // 2
                        text_height = font_size
            except Exception as e:
                print(f"获取文本尺寸时发生严重错误: {str(e)}")
                # 使用安全的默认值
                text_width = len(text) * font_size // 2
                text_height = font_size
            
            # 调整水印位置到图片坐标系
            img_width, img_height = img.size
            pos_x = int(self.watermark_pos.x() * img_width / (self.preview_label.width() - 20))
            pos_y = int(self.watermark_pos.y() * img_height / (self.preview_label.height() - 20))
            
            # 准备填充颜色
            fill_color = (r, g, b, int(255 * (100 - transparency) / 100))
            
            # 如果启用了描边效果
            if self.stroke_checkbox.isChecked():
                # 解析描边颜色
                stroke_color_code = self.current_stroke_color
                stroke_r = int(stroke_color_code[1:3], 16)
                stroke_g = int(stroke_color_code[3:5], 16)
                stroke_b = int(stroke_color_code[5:7], 16)
                stroke_width = self.stroke_width.value()
                
                # 绘制描边（在文本周围绘制多个偏移的文本）
                for x_offset in range(-stroke_width, stroke_width + 1):
                    for y_offset in range(-stroke_width, stroke_width + 1):
                        if x_offset != 0 or y_offset != 0:  # 避免重复绘制中心文本
                            draw.text((pos_x + x_offset, pos_y + y_offset), text, font=font, 
                                     fill=(stroke_r, stroke_g, stroke_b, int(255 * (100 - transparency) / 100)))
            
            # 如果启用了阴影效果
            if self.shadow_checkbox.isChecked():
                shadow_distance = self.shadow_distance.value()
                # 绘制阴影
                draw.text((pos_x + shadow_distance, pos_y + shadow_distance), text, font=font, 
                         fill=(0, 0, 0, int(128 * (100 - transparency) / 100)))
            
            # 绘制主文本
            try:
                # 如果需要粗体效果但没有加载到粗体字体文件，手动模拟粗体
                if bold and self.stroke_checkbox.isChecked() == False:
                    # 通过在文本周围绘制多个偏移的文本实现伪粗体效果
                    # 绘制伪粗体（四个方向的偏移文本）
                    bold_offset = 1
                    for x_offset in range(-bold_offset, bold_offset + 1):
                        for y_offset in range(-bold_offset, bold_offset + 1):
                            if x_offset != 0 or y_offset != 0:  # 避免重复绘制中心文本
                                try:
                                    draw.text((pos_x + x_offset, pos_y + y_offset), text, font=font, fill=fill_color)
                                except:
                                    pass
                
                if italic:
                    # 应用伪斜体效果（通过变换坐标）
                    # 使用一个简单的剪切变换来创建斜体效果
                    try:
                        # 保存原始文本的边界框
                        original_bbox = draw.textbbox((pos_x, pos_y), text, font=font)
                        original_center = ((original_bbox[0] + original_bbox[2]) // 2, 
                                           (original_bbox[1] + original_bbox[3]) // 2)
                    except Exception as e:
                        print(f"计算原始文本边界框时出错: {str(e)}")
                        # 使用估算的位置
                        original_center = (pos_x + text_width // 2, pos_y + text_height // 2)
                    
                    # 计算斜体变换的系数 (倾斜程度)
                    shear_factor = 0.2  # 控制斜体倾斜度
                    
                    # 创建一个带有alpha通道的新层来绘制斜体文本
                    italic_layer = Image.new('RGBA', watermark_img.size, (255, 255, 255, 0))
                    italic_draw = ImageDraw.Draw(italic_layer)
                    
                    # 尝试绘制文本，如果失败则处理编码问题
                    try:
                        italic_draw.text((pos_x, pos_y), text, font=font, fill=fill_color)
                    except UnicodeEncodeError:
                        print(f"绘制斜体文本时出现编码错误，尝试处理文本")
                        # 尝试处理文本：替换非ASCII字符或使用简化文本
                        processed_text = "".join([char if ord(char) < 128 else "?" for char in text])
                        if processed_text:
                            italic_draw.text((pos_x, pos_y), processed_text, font=font, fill=fill_color)
                    except Exception as e:
                        print(f"绘制斜体文本时出错: {str(e)}")
                        # 如果无法绘制斜体，继续执行
                        pass
                    
                    # 应用剪切变换
                    # 计算新的尺寸，考虑到剪切后的扩展
                    new_width = watermark_img.width + int(watermark_img.height * abs(shear_factor))
                    
                    # 应用Affine变换来实现斜体效果
                    try:
                        italic_layer = italic_layer.transform(
                            (new_width, watermark_img.height),
                            Image.AFFINE,
                            (1, shear_factor, 0, 0, 1, 0),
                            Image.BICUBIC
                        )
                        
                        # 计算偏移量以保持文本居中
                        offset_x = int((original_center[0] * shear_factor))
                        
                        # 将斜体层粘贴回主图像
                        watermark_img.paste(
                            italic_layer, 
                            (offset_x, 0), 
                            italic_layer.split()[3]  # 使用alpha通道作为掩码
                        )
                    except Exception as e:
                        print(f"应用斜体变换时出错: {str(e)}")
                        # 如果变换失败，尝试直接绘制文本作为回退
                        try:
                            draw.text((pos_x, pos_y), text, font=font, fill=fill_color)
                        except:
                            pass
                else:
                    # 正常绘制文本
                    try:
                        draw.text((pos_x, pos_y), text, font=font, fill=fill_color)
                    except UnicodeEncodeError:
                        print(f"绘制文本时出现编码错误，尝试处理文本")
                        # 尝试处理文本：替换非ASCII字符或使用简化文本
                        processed_text = "".join([char if ord(char) < 128 else "?" for char in text])
                        if processed_text:
                            draw.text((pos_x, pos_y), processed_text, font=font, fill=fill_color)
                    except Exception as e:
                        print(f"绘制文本时出错: {str(e)}")
                        # 如果无法绘制，继续执行
                        pass
            except Exception as e:
                print(f"绘制主文本时发生严重错误: {str(e)}")
                # 忽略错误，继续执行
            
            # 合并图片
            result = Image.alpha_composite(img, watermark_img)
            
            return result
        elif self.watermark_type == "image" and self.image_watermark:
            # 调整水印图片大小
            img_width, img_height = img.size
            
            # 根据选择的调整方式调整水印图片大小
            resize_method = self.image_resize_method.currentText()
            new_width = self.image_watermark_width
            new_height = self.image_watermark_height
            
            if resize_method == "按百分比":
                scale = self.image_watermark_scale / 100
                new_width = int(self.image_watermark_width * scale)
                new_height = int(self.image_watermark_height * scale)
            elif resize_method == "按宽度" and self.image_width_input.text().strip():
                try:
                    new_width = int(self.image_width_input.text())
                    # 保持宽高比
                    scale = new_width / self.image_watermark_width
                    new_height = int(self.image_watermark_height * scale)
                except ValueError:
                    pass
            elif resize_method == "按高度" and self.image_height_input.text().strip():
                try:
                    new_height = int(self.image_height_input.text())
                    # 保持宽高比
                    scale = new_height / self.image_watermark_height
                    new_width = int(self.image_watermark_width * scale)
                except ValueError:
                    pass
            
            # 调整水印图片大小
            resized_watermark = self.image_watermark.resize((new_width, new_height), Image.LANCZOS)
            
            # 调整水印透明度
            transparency = self.image_transparency.value()
            if transparency < 100:
                # 使用更高效的方法调整透明度
                # 首先确保水印图片是RGBA模式
                if resized_watermark.mode != 'RGBA':
                    resized_watermark = resized_watermark.convert('RGBA')
                
                # 分解图像通道
                r, g, b, a = resized_watermark.split()
                # 计算新的透明度
                new_transparency = int(255 * (100 - transparency) / 100)
                # 应用新的透明度
                a = a.point(lambda p: int(p * new_transparency / 255))
                # 合并通道
                resized_watermark = Image.merge('RGBA', (r, g, b, a))
            
            # 调整水印位置到图片坐标系
            pos_x = int(self.watermark_pos.x() * img_width / (self.preview_label.width()))
            pos_y = int(self.watermark_pos.y() * img_height / (self.preview_label.height()))
            
            # 确保水印在图片范围内
            pos_x = max(0, min(pos_x, img_width - new_width))
            pos_y = max(0, min(pos_y, img_height - new_height))
            
            # 将水印粘贴到目标图像上
            watermark_img.paste(resized_watermark, (pos_x, pos_y), resized_watermark)
            
            # 合并图片
            result = Image.alpha_composite(img, watermark_img)
            
            return result
        
        # 如果没有水印（文本为空或没有选择图片水印），直接返回原图
        return img
    
    def on_preview_mouse_press(self, event):
        if event.button() == Qt.LeftButton and self.current_image_index >= 0:
            self.dragging = True
            self.drag_start = event.pos()
    
    def on_preview_mouse_move(self, event):
        if self.dragging:
            # 计算鼠标移动的距离
            delta = event.pos() - self.drag_start
            
            # 更新水印位置
            self.watermark_pos += delta
            
            # 确保水印位置在预览窗口内
            self.watermark_pos.setX(max(0, min(self.watermark_pos.x(), self.preview_label.width() - 20)))
            self.watermark_pos.setY(max(0, min(self.watermark_pos.y(), self.preview_label.height() - 20)))
            
            # 更新拖动起点
            self.drag_start = event.pos()
            
            # 更新预览
            self.update_preview()
    
    def on_preview_mouse_release(self, event):
        if event.button() == Qt.LeftButton:
            self.dragging = False
    
    def set_watermark_position(self, position):
        if self.current_image_index < 0:
            return
        
        # 计算预览窗口内的位置
        width = self.preview_label.width() - 20
        height = self.preview_label.height() - 20
        
        positions = {
            "左上": (10, 10),
            "中上": (width // 2 - 50, 10),
            "右上": (width - 110, 10),
            "左中": (10, height // 2 - 20),
            "中心": (width // 2 - 50, height // 2 - 20),
            "右中": (width - 110, height // 2 - 20),
            "左下": (10, height - 40),
            "中下": (width // 2 - 50, height - 40),
            "右下": (width - 110, height - 40)
        }
        
        if position in positions:
            self.watermark_pos = QPoint(*positions[position])
            self.update_preview()
    
    def select_output_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "选择输出文件夹", "")
        if folder:
            # 检查是否是原文件夹
            original_folders = set()
            for img_info in self.images:
                original_folders.add(os.path.dirname(os.path.abspath(img_info['original_path'])))
            
            if folder in original_folders:
                QMessageBox.warning(self, "警告", "为防止覆盖原图，禁止导出到原文件夹")
                return
            
            self.output_folder_path = folder
            self.output_folder.setText(folder)
    
    def toggle_shadow_options(self):
        # 根据是否启用阴影效果来控制相关控件的可用性
        self.shadow_distance.setEnabled(self.shadow_checkbox.isChecked())
        self.update_preview()
        
    def toggle_stroke_options(self):
        # 根据是否启用描边效果来控制相关控件的可用性
        self.stroke_width.setEnabled(self.stroke_checkbox.isChecked())
        self.stroke_color_button.setEnabled(self.stroke_checkbox.isChecked())
        self.update_preview()
        
    def select_color(self):
        # 打开颜色选择对话框
        color = QColorDialog.getColor(QColor(self.current_color), self, "选择字体颜色")
        if color.isValid():
            self.current_color = color.name()
            self.color_preview.setStyleSheet(f"background-color: {self.current_color}; border: 1px solid #ccc;")
            self.update_preview()
            
    def select_stroke_color(self):
        # 打开描边颜色选择对话框
        color = QColorDialog.getColor(QColor(self.current_stroke_color), self, "选择描边颜色")
        if color.isValid():
            self.current_stroke_color = color.name()
            self.stroke_color_preview.setStyleSheet(f"background-color: {self.current_stroke_color}; border: 1px solid #ccc;")
            self.update_preview()
            
    def toggle_filename_options(self, state):
        self.prefix.setEnabled(not state)
        self.suffix.setEnabled(not state)
        
        if state:
            self.use_prefix = False
            self.use_suffix = False
        else:
            self.use_prefix = not self.prefix.text().strip() == ""
            self.use_suffix = not self.suffix.text().strip() == ""
    
    def toggle_prefix_suffix(self):
        self.use_prefix = not self.prefix.text().strip() == ""
        self.use_suffix = not self.suffix.text().strip() == ""
    
    def toggle_quality_settings(self):
        # 仅当选择JPEG格式时启用质量设置
        is_jpeg = self.output_format.currentText() == "JPEG"
        self.quality_slider.setEnabled(is_jpeg)
        self.quality_label.setEnabled(is_jpeg)
    
    def toggle_resize_options(self):
        method = self.resize_method.currentText()
        
        # 根据选择的调整方式启用对应的输入控件
        self.width_input.setEnabled(method == "按宽度")
        self.height_input.setEnabled(method == "按高度")
        self.percent_slider.setEnabled(method == "按百分比")
        self.percent_label.setEnabled(method == "按百分比")
    
    def export_images(self):
        if not self.images:
            return
        
        # 检查输出文件夹
        if not self.output_folder_path:
            self.select_output_folder()
            if not self.output_folder_path:
                return
        
        # 确保输出文件夹存在
        os.makedirs(self.output_folder_path, exist_ok=True)
        
        # 导出每张图片
        for img_info in self.images:
            try:
                # 添加水印
                img = img_info['image'].copy()
                watermarked_img = self.add_watermark_to_image(img)
                
                # 调整图片尺寸
                resize_method = self.resize_method.currentText()
                if resize_method != "原始尺寸":
                    width, height = watermarked_img.size
                    
                    if resize_method == "按宽度":
                        try:
                            new_width = int(self.width_input.text())
                            # 保持宽高比
                            scale = new_width / width
                            new_height = int(height * scale)
                            watermarked_img = watermarked_img.resize((new_width, new_height), Image.LANCZOS)
                        except ValueError:
                            # 如果输入无效，跳过尺寸调整
                            pass
                    elif resize_method == "按高度":
                        try:
                            new_height = int(self.height_input.text())
                            # 保持宽高比
                            scale = new_height / height
                            new_width = int(width * scale)
                            watermarked_img = watermarked_img.resize((new_width, new_height), Image.LANCZOS)
                        except ValueError:
                            # 如果输入无效，跳过尺寸调整
                            pass
                    elif resize_method == "按百分比":
                        scale = self.percent_slider.value() / 100
                        new_width = int(width * scale)
                        new_height = int(height * scale)
                        watermarked_img = watermarked_img.resize((new_width, new_height), Image.LANCZOS)
                
                # 确定输出文件名
                original_filename = os.path.basename(img_info['original_path'])
                base_name, ext = os.path.splitext(original_filename)
                
                if self.preserve_filename.isChecked():
                    output_filename = original_filename
                else:
                    prefix = self.prefix.text() if self.use_prefix else ""
                    suffix = self.suffix.text() if self.use_suffix else ""
                    output_filename = f"{prefix}{base_name}{suffix}.{self.output_format.currentText().lower()}"
                
                # 保存图片
                output_path = os.path.join(self.output_folder_path, output_filename)
                
                # 根据输出格式和设置保存
                if self.output_format.currentText() == "JPEG":
                    if watermarked_img.mode == 'RGBA':
                        watermarked_img = watermarked_img.convert('RGB')
                    # 使用指定的JPEG质量
                    quality = self.quality_slider.value()
                    watermarked_img.save(output_path, quality=quality)
                else:
                    # PNG格式直接保存
                    watermarked_img.save(output_path)
                
            except Exception as e:
                QMessageBox.warning(self, "错误", f"无法导出文件 {original_filename}: {str(e)}")
                continue
        
        QMessageBox.information(self, "完成", f"所有图片已成功导出到 {self.output_folder_path}")
    
    def save_template(self):
        # 获取当前设置
        template_name, ok = QInputDialog.getText(self, "保存模板", "请输入模板名称:")
        
        if ok and template_name:
            # 确保模板目录存在
            template_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "templates")
            os.makedirs(template_dir, exist_ok=True)
            
            # 保存模板设置，包括新添加的高级文本水印设置
            template = {
                'text': self.watermark_text.text(),
                'font_size': self.font_size.currentText(),
                'transparency': self.transparency.value(),
                'font_color': self.current_color,  # 使用新的颜色选择器值
                'font_family': self.font_family.currentText(),
                'bold': self.bold_checkbox.isChecked(),
                'italic': self.italic_checkbox.isChecked(),
                'shadow_enabled': self.shadow_checkbox.isChecked(),
                'shadow_distance': self.shadow_distance.value(),
                'stroke_enabled': self.stroke_checkbox.isChecked(),
                'stroke_width': self.stroke_width.value(),
                'stroke_color': self.current_stroke_color,
                'position': (self.watermark_pos.x(), self.watermark_pos.y()),
                'output_format': self.output_format.currentIndex(),
                'quality': self.quality_slider.value(),  # JPEG质量
                'resize_method': self.resize_method.currentIndex(),  # 尺寸调整方式
                'width_input': self.width_input.text(),  # 宽度输入
                'height_input': self.height_input.text(),  # 高度输入
                'percent_value': self.percent_slider.value(),  # 百分比值
                'preserve_filename': self.preserve_filename.isChecked(),
                'prefix': self.prefix.text(),
                'suffix': self.suffix.text()
            }
            
            template_path = os.path.join(template_dir, f"{template_name}.json")
            
            try:
                with open(template_path, 'w', encoding='utf-8') as f:
                    json.dump(template, f, ensure_ascii=False, indent=4)
                
                # 更新模板列表
                self.load_templates()
                self.template_list.setCurrentText(template_name)
                
            except Exception as e:
                QMessageBox.warning(self, "错误", f"无法保存模板: {str(e)}")
    
    def load_templates(self):
        # 清空模板列表
        self.template_list.clear()
        
        # 检查模板目录
        template_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "templates")
        if not os.path.exists(template_dir):
            return
        
        # 加载所有模板
        try:
            for filename in os.listdir(template_dir):
                if filename.endswith(".json"):
                    template_name = os.path.splitext(filename)[0]
                    self.template_list.addItem(template_name)
        except Exception as e:
            QMessageBox.warning(self, "错误", f"无法加载模板: {str(e)}")
    
    def load_template(self):
        template_name = self.template_list.currentText()
        if not template_name:
            return
        
        # 读取模板文件
        template_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "templates")
        template_path = os.path.join(template_dir, f"{template_name}.json")
        
        try:
            with open(template_path, 'r', encoding='utf-8') as f:
                template = json.load(f)
            
            # 应用模板设置
            self.watermark_text.setText(template.get('text', "水印文字"))
            self.font_size.setCurrentText(template.get('font_size', "24"))
            self.transparency.setValue(template.get('transparency', 50))
            
            # 应用新的高级文本设置
            self.current_color = template.get('font_color', "#000000")
            self.color_preview.setStyleSheet(f"background-color: {self.current_color}; border: 1px solid #ccc;")
            
            # 字体选择器已移除，使用默认字体
            
            self.bold_checkbox.setChecked(template.get('bold', False))
            # 斜体功能已移除
            
            # 应用文本效果设置
            self.shadow_checkbox.setChecked(template.get('shadow_enabled', False))
            self.shadow_distance.setValue(template.get('shadow_distance', 2))
            self.toggle_shadow_options()
            
            self.stroke_checkbox.setChecked(template.get('stroke_enabled', False))
            self.stroke_width.setValue(template.get('stroke_width', 1))
            self.current_stroke_color = template.get('stroke_color', "#FFFFFF")
            self.stroke_color_preview.setStyleSheet(f"background-color: {self.current_stroke_color}; border: 1px solid #ccc;")
            self.toggle_stroke_options()
            
            pos = template.get('position', (100, 100))
            self.watermark_pos = QPoint(*pos)
            
            self.output_format.setCurrentIndex(template.get('output_format', 0))
            self.quality_slider.setValue(template.get('quality', 90))  # 加载JPEG质量设置
            self.resize_method.setCurrentIndex(template.get('resize_method', 0))  # 加载尺寸调整方式
            self.width_input.setText(template.get('width_input', ""))  # 加载宽度输入
            self.height_input.setText(template.get('height_input', ""))  # 加载高度输入
            self.percent_slider.setValue(template.get('percent_value', 100))  # 加载百分比值
            
            self.preserve_filename.setChecked(template.get('preserve_filename', True))
            self.prefix.setText(template.get('prefix', "wm_"))
            self.suffix.setText(template.get('suffix', "_watermarked"))
            
            # 更新相关设置
            self.toggle_filename_options(self.preserve_filename.isChecked())
            self.toggle_quality_settings()
            self.toggle_resize_options()
            self.update_preview()
            
        except Exception as e:
            QMessageBox.warning(self, "错误", f"无法加载模板: {str(e)}")
    
    def delete_template(self):
        template_name = self.template_list.currentText()
        if not template_name:
            return
        
        # 确认删除
        reply = QMessageBox.question(
            self, "确认删除", f"确定要删除模板 '{template_name}' 吗？",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            # 删除模板文件
            template_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "templates")
            template_path = os.path.join(template_dir, f"{template_name}.json")
            
            try:
                if os.path.exists(template_path):
                    os.remove(template_path)
                
                # 更新模板列表
                self.load_templates()
                
            except Exception as e:
                QMessageBox.warning(self, "错误", f"无法删除模板: {str(e)}")
    
    def load_last_settings(self):
        # 检查设置文件
        settings_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "settings.json")
        
        if os.path.exists(settings_path):
            try:
                with open(settings_path, 'r', encoding='utf-8') as f:
                    settings = json.load(f)
                
                # 加载设置
                if 'last_template' in settings and settings['last_template']:
                    # 先加载模板列表
                    self.load_templates()
                    
                    # 查找并加载最后使用的模板
                    index = self.template_list.findText(settings['last_template'])
                    if index >= 0:
                        self.template_list.setCurrentIndex(index)
                        self.load_template()
                
            except Exception as e:
                print(f"无法加载上次设置: {str(e)}")
    
    def save_last_settings(self):
        # 保存设置
        settings_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "settings.json")
        
        try:
            settings = {
                'last_template': self.template_list.currentText()
            }
            
            with open(settings_path, 'w', encoding='utf-8') as f:
                json.dump(settings, f, ensure_ascii=False, indent=4)
                
        except Exception as e:
            print(f"无法保存设置: {str(e)}")
    
    def show_about(self):
        QMessageBox.about(
            self, "关于图片水印工具",
            "图片水印工具 v1.0\n\n"+
            "这是一个用于给图片添加水印的工具，可以批量处理图片并添加自定义文本水印。\n"+
            "支持调整水印的位置、大小、颜色和透明度等参数。"
        )
    
    def closeEvent(self, event):
        # 保存最后设置
        self.save_last_settings()
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = WatermarkApp()
    window.show()
    sys.exit(app.exec_())