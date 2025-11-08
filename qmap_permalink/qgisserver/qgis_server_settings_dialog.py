# -*- coding: utf-8 -*-
"""
QGIS Server Settings Dialog
QGIS Serverの自動起動設定ダイアログ
"""
from qgis.PyQt.QtCore import Qt, QSettings
from qgis.PyQt.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
    QCheckBox, QSpinBox, QPushButton, QGroupBox, QMessageBox
)


class QGISServerSettingsDialog(QDialog):
    """QGIS Server設定ダイアログ"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("QGIS Server Settings")
        self.setMinimumWidth(400)
        
        self.init_ui()
        self.load_settings()
    
    def init_ui(self):
        """UIを初期化"""
        layout = QVBoxLayout()
        
        # QGIS Server設定グループ
        server_group = QGroupBox("QGIS Server Auto-Start")
        server_layout = QVBoxLayout()
        
        # 自動起動チェックボックス
        self.auto_start_check = QCheckBox("Automatically start QGIS Server when plugin loads")
        server_layout.addWidget(self.auto_start_check)
        
        # ポート設定
        port_layout = QHBoxLayout()
        port_layout.addWidget(QLabel("Port:"))
        self.port_spin = QSpinBox()
        self.port_spin.setRange(1024, 65535)
        self.port_spin.setValue(8090)
        port_layout.addWidget(self.port_spin)
        port_layout.addStretch()
        server_layout.addLayout(port_layout)
        
        # 説明文
        info_label = QLabel(
            "QGIS Server provides high-performance WMS service.\n"
            "• Plugin HTTP Server (port 8089): Development/Preview\n"
            "• QGIS Server (port 8090): Production/High-load\n\n"
            "Note: QGIS Server must be installed separately."
        )
        info_label.setWordWrap(True)
        info_label.setStyleSheet("color: #666; font-size: 9pt;")
        server_layout.addWidget(info_label)
        
        server_group.setLayout(server_layout)
        layout.addWidget(server_group)
        
        # ボタン
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        self.ok_button = QPushButton("OK")
        self.ok_button.clicked.connect(self.accept)
        button_layout.addWidget(self.ok_button)
        
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_button)
        
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
    
    def load_settings(self):
        """設定を読み込む"""
        settings = QSettings()
        auto_start = settings.value('QMapPermalink/qgis_server_auto_start', False, type=bool)
        port = settings.value('QMapPermalink/qgis_server_port', 8090, type=int)
        
        self.auto_start_check.setChecked(auto_start)
        self.port_spin.setValue(port)
    
    def save_settings(self):
        """設定を保存"""
        settings = QSettings()
        settings.setValue('QMapPermalink/qgis_server_auto_start', self.auto_start_check.isChecked())
        settings.setValue('QMapPermalink/qgis_server_port', self.port_spin.value())
    
    def accept(self):
        """OKボタンが押されたときの処理"""
        self.save_settings()
        super().accept()
