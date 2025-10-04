import sys
import os
import json
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QFileDialog, QLabel, QListWidget, QListWidgetItem, QSlider, QComboBox,
    QLineEdit, QGridLayout, QSplitter, QGroupBox, QFormLayout, QCheckBox,
    QFrame, QInputDialog, QMessageBox, QAction, QMenu, QMenuBar
)
from PyQt5.QtGui import QPixmap, QPainter, QColor, QFont, QIcon, QBrush, QPen
from PyQt5.QtCore import Qt, QPoint, QSize
from PIL import Image, ImageDraw, ImageFont
import sys
from PyQt5.QtGui import QImage

class WatermarkApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.load_last_settings()
        
    def init_ui(self):
        # 设置窗口标题和大小
        self.setWindowTitle("图片水印工具")
        self.setGeometry(100, 100, 1200, 800)
        
        # 创建中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 创建主布局
        main_layout = QHBoxLayout(central_widget)
        
        # 创建左侧面板（文件列表）
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_panel.setMaximumWidth(250)
        
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
        self.file_list.setIconSize(QSize(120, 120))
        self.file_list.setResizeMode(QListWidget.Adjust)
        self.file_list.setMovement(QListWidget.Static)
        self.file_list.itemClicked.connect(self.on_file_selected)
        
        # 导出按钮
        self.export_btn = QPushButton("导出图片")
        self.export_btn.clicked.connect(self.export_images)
        self.export_btn.setEnabled(False)
        
        left_layout.addLayout(file_ops_layout)
        left_layout.addWidget(QLabel("已导入图片:"))
        left_layout.addWidget(self.file_list)
        left_layout.addWidget(self.export_btn)
        
        # 创建中间面板（预览）
        center_panel = QWidget()
        center_layout = QVBoxLayout(center_panel)
        
        # 预览窗口
        self.preview_label = QLabel("预览窗口")
        self.preview_label.setAlignment(Qt.AlignCenter)
        self.preview_label.setMinimumSize(400, 400)
        self.preview_label.setStyleSheet("background-color: #f0f0f0; border: 1px solid #ccc;")
        self.preview_label.mousePressEvent = self.on_preview_mouse_press
        self.preview_label.mouseMoveEvent = self.on_preview_mouse_move
        self.preview_label.mouseReleaseEvent = self.on_preview_mouse_release
        
        center_layout.addWidget(QLabel("预览:"))
        center_layout.addWidget(self.preview_label)
        
        # 创建右侧面板（水印设置）
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_panel.setMaximumWidth(300)
        
        # 文本水印设置
        text_watermark_group = QGroupBox("文本水印设置")
        text_watermark_layout = QFormLayout()
        
        self.watermark_text = QLineEdit("水印文字")
        self.watermark_text.textChanged.connect(self.update_preview)
        
        self.font_size = QComboBox()
        for size in range(10, 72, 2):
            self.font_size.addItem(str(size))
        self.font_size.setCurrentText("24")
        self.font_size.currentTextChanged.connect(self.update_preview)
        
        self.transparency = QSlider(Qt.Horizontal)
        self.transparency.setRange(0, 100)
        self.transparency.setValue(50)
        self.transparency.setTickPosition(QSlider.TicksBelow)
        self.transparency.setTickInterval(10)
        self.transparency.valueChanged.connect(self.update_preview)
        
        self.transparency_label = QLabel("透明度: 50%")
        self.transparency.valueChanged.connect(lambda value: self.transparency_label.setText(f"透明度: {value}%"))
        
        # 字体颜色
        self.font_color = QComboBox()
        colors = {"黑色": "#000000", "白色": "#FFFFFF", "红色": "#FF0000", "蓝色": "#0000FF", "绿色": "#00FF00"}
        for name, code in colors.items():
            self.font_color.addItem(name, code)
        self.font_color.currentIndexChanged.connect(self.update_preview)
        
        text_watermark_layout.addRow("水印文本:", self.watermark_text)
        text_watermark_layout.addRow("字体大小:", self.font_size)
        text_watermark_layout.addRow(self.transparency_label, self.transparency)
        text_watermark_layout.addRow("字体颜色:", self.font_color)
        text_watermark_group.setLayout(text_watermark_layout)
        
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
        
        # 尺寸调整设置
        resize_group = QGroupBox("尺寸调整")
        resize_layout = QFormLayout()
        
        self.resize_method = QComboBox()
        self.resize_method.addItem("原始尺寸")
        self.resize_method.addItem("按宽度")
        self.resize_method.addItem("按高度")
        self.resize_method.addItem("按百分比")
        self.resize_method.currentIndexChanged.connect(self.toggle_resize_options)
        resize_layout.addRow("调整方式:", self.resize_method)
        
        self.width_input = QLineEdit()
        self.width_input.setPlaceholderText("输入宽度")
        self.width_input.setEnabled(False)
        resize_layout.addRow("宽度 (像素):", self.width_input)
        
        self.height_input = QLineEdit()
        self.height_input.setPlaceholderText("输入高度")
        self.height_input.setEnabled(False)
        resize_layout.addRow("高度 (像素):", self.height_input)
        
        self.percent_slider = QSlider(Qt.Horizontal)
        self.percent_slider.setRange(10, 200)
        self.percent_slider.setValue(100)
        self.percent_slider.setTickPosition(QSlider.TicksBelow)
        self.percent_slider.setTickInterval(10)
        self.percent_slider.setEnabled(False)
        
        self.percent_label = QLabel("缩放比例: 100%")
        self.percent_slider.valueChanged.connect(lambda value: self.percent_label.setText(f"缩放比例: {value}%"))
        
        resize_layout.addRow(self.percent_label, self.percent_slider)
        resize_group.setLayout(resize_layout)
        
        # 导出设置
        export_group = QGroupBox("导出设置")
        export_layout = QFormLayout()
        
        self.output_format = QComboBox()
        self.output_format.addItem("JPEG")
        self.output_format.addItem("PNG")
        self.output_format.currentIndexChanged.connect(self.toggle_quality_settings)
        export_layout.addRow("输出格式:", self.output_format)
        
        self.quality_slider = QSlider(Qt.Horizontal)
        self.quality_slider.setRange(0, 100)
        self.quality_slider.setValue(90)
        self.quality_slider.setTickPosition(QSlider.TicksBelow)
        self.quality_slider.setTickInterval(10)
        
        self.quality_label = QLabel("JPEG质量: 90%")
        self.quality_slider.valueChanged.connect(lambda value: self.quality_label.setText(f"JPEG质量: {value}%"))
        
        export_layout.addRow(self.quality_label, self.quality_slider)
        
        self.output_folder = QLineEdit()
        self.output_folder.setReadOnly(True)
        browse_btn = QPushButton("浏览...")
        browse_btn.clicked.connect(self.select_output_folder)
        
        folder_layout = QHBoxLayout()
        folder_layout.addWidget(self.output_folder)
        folder_layout.addWidget(browse_btn)
        export_layout.addRow("输出文件夹:", folder_layout)
        
        self.preserve_filename = QCheckBox("保留原文件名")
        self.preserve_filename.setChecked(True)
        self.preserve_filename.stateChanged.connect(self.toggle_filename_options)
        export_layout.addRow(self.preserve_filename)
        
        self.prefix = QLineEdit("wm_")
        self.prefix.setEnabled(False)
        self.prefix.textChanged.connect(self.toggle_prefix_suffix)
        export_layout.addRow("前缀:", self.prefix)
        
        self.suffix = QLineEdit("_watermarked")
        self.suffix.setEnabled(False)
        self.suffix.textChanged.connect(self.toggle_prefix_suffix)
        export_layout.addRow("后缀:", self.suffix)
        
        export_group.setLayout(export_layout)
        
        # 模板管理
        template_group = QGroupBox("模板管理")
        template_layout = QVBoxLayout()
        
        self.template_list = QComboBox()
        self.load_templates()
        
        template_buttons_layout = QHBoxLayout()
        save_template_btn = QPushButton("保存模板")
        save_template_btn.clicked.connect(self.save_template)
        load_template_btn = QPushButton("加载模板")
        load_template_btn.clicked.connect(self.load_template)
        delete_template_btn = QPushButton("删除模板")
        delete_template_btn.clicked.connect(self.delete_template)
        
        template_buttons_layout.addWidget(save_template_btn)
        template_buttons_layout.addWidget(load_template_btn)
        template_buttons_layout.addWidget(delete_template_btn)
        
        template_layout.addWidget(QLabel("可用模板:"))
        template_layout.addWidget(self.template_list)
        template_layout.addLayout(template_buttons_layout)
        
        template_group.setLayout(template_layout)
        
        # 添加所有组件到右侧布局
        right_layout.addWidget(text_watermark_group)
        right_layout.addWidget(position_group)
        right_layout.addWidget(resize_group)
        right_layout.addWidget(export_group)
        right_layout.addWidget(template_group)
        right_layout.addStretch()
        
        # 将所有面板添加到主布局
        main_layout.addWidget(left_panel)
        main_layout.addWidget(center_panel, 1)
        main_layout.addWidget(right_panel)
        
        # 初始化变量
        self.images = []
        self.current_image_index = -1
        self.watermark_pos = QPoint(100, 100)
        self.dragging = False
        self.drag_start = QPoint()
        self.output_folder_path = ""
        self.use_prefix = False
        self.use_suffix = False
        
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
                thumbnail.thumbnail((120, 120))
                
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
        
        # 调整预览大小以适应窗口
        preview_size = self.preview_label.size()
        preview_size = QSize(preview_size.width() - 20, preview_size.height() - 20)  # 留出边距
        
        # 计算合适的显示大小
        img_width, img_height = watermarked_img.size
        scale = min(preview_size.width() / img_width, preview_size.height() / img_height, 1.0)
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
    
    def add_watermark_to_image(self, img):
        # 确保图片支持透明度
        if img.mode != 'RGBA':
            img = img.convert('RGBA')
        
        # 创建一个可绘制的副本
        watermark_img = Image.new('RGBA', img.size, (255, 255, 255, 0))
        draw = ImageDraw.Draw(watermark_img)
        
        # 获取水印文本和设置
        text = self.watermark_text.text()
        if not text:
            return img
        
        font_size = int(self.font_size.currentText())
        transparency = self.transparency.value()
        color_code = self.font_color.currentData()
        
        # 解析颜色
        r = int(color_code[1:3], 16)
        g = int(color_code[3:5], 16)
        b = int(color_code[5:7], 16)
        
        # 创建字体
        font = None
        
        # 尝试使用系统中支持中文的字体
        # 1. 首先尝试Windows系统字体目录中的中文字体
        if os.name == 'nt':  # Windows系统
            windows_font_dir = r"C:\Windows\Fonts"
            chinese_fonts = [
                os.path.join(windows_font_dir, "simhei.ttf"),  # 黑体
                os.path.join(windows_font_dir, "msyh.ttc"),    # 微软雅黑
                os.path.join(windows_font_dir, "simsun.ttc"),  # 宋体
                os.path.join(windows_font_dir, "msyhbd.ttc")   # 微软雅黑粗体
            ]
            
            for font_path in chinese_fonts:
                try:
                    if os.path.exists(font_path):
                        font = ImageFont.truetype(font_path, font_size)
                        break
                except:
                    continue
        
        # 2. 如果没找到或不是Windows系统，尝试使用字体名称
        if font is None:
            font_names = [
                "SimHei", "WenQuanYi Micro Hei", "Heiti TC", 
                "Microsoft YaHei", "SimSun", "Arial Unicode MS"
            ]
            
            for font_name in font_names:
                try:
                    font = ImageFont.truetype(font_name, font_size)
                    break
                except:
                    continue
        
        # 3. 如果还是找不到，使用默认字体并记录警告
        if font is None:
            print("警告: 无法加载支持中文的字体，可能导致中文显示异常")
            font = ImageFont.load_default()
        
        # 获取文本尺寸
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        
        # 调整水印位置到图片坐标系
        img_width, img_height = img.size
        pos_x = int(self.watermark_pos.x() * img_width / (self.preview_label.width() - 20))
        pos_y = int(self.watermark_pos.y() * img_height / (self.preview_label.height() - 20))
        
        # 绘制水印
        draw.text((pos_x, pos_y), text, font=font, fill=(r, g, b, int(255 * (100 - transparency) / 100)))
        
        # 合并图片
        result = Image.alpha_composite(img, watermark_img)
        
        return result
    
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
            
            # 保存模板设置，包括新添加的质量和尺寸调整设置
            template = {
                'text': self.watermark_text.text(),
                'font_size': self.font_size.currentText(),
                'transparency': self.transparency.value(),
                'font_color': self.font_color.currentIndex(),
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
            self.font_color.setCurrentIndex(template.get('font_color', 0))
            
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