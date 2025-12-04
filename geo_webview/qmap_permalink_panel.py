# -*- coding: utf-8 -*-
"""
/***************************************************************************
 GeoWebViewPanel
                                 A QGIS plugin
 Navigate QGIS map views through external permalink system - Panel Version
                             -------------------
        begin                : 2025-10-05
        git sha              : $Format:%H$
        copyright            : (C) 2025 by yamamoto-ryuzo
        email                : 
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""

import os

from qgis.PyQt import uic
from qgis.PyQt.QtWidgets import QDockWidget, QWidget
from qgis.PyQt.QtCore import Qt

# Qt6 enum compatibility: some enums are scoped in Qt6 (e.g. DockWidgetArea).
# Ensure older attribute style (Qt.LeftDockWidgetArea) exists for code that
# expects it so the plugin works on both Qt5 and Qt6 via qgis.PyQt.
try:
    if not hasattr(Qt, 'LeftDockWidgetArea'):
        # Qt6: enums are namespaced (Qt.DockWidgetArea.LeftDockWidgetArea)
        try:
            Qt.LeftDockWidgetArea = Qt.DockWidgetArea.LeftDockWidgetArea
            Qt.RightDockWidgetArea = Qt.DockWidgetArea.RightDockWidgetArea
        except Exception:
            # best-effort fallback: leave as-is
            pass
except Exception:
    pass
try:
    # Provide legacy enum names on QDockWidget for Qt6 where enums may be scoped.
    if not hasattr(QDockWidget, 'DockWidgetMovable'):
        feat = getattr(QDockWidget, 'DockWidgetFeature', None) or getattr(QDockWidget, 'Feature', None)
        if feat is not None:
            # map common names if present
            if hasattr(feat, 'DockWidgetMovable'):
                QDockWidget.DockWidgetMovable = getattr(feat, 'DockWidgetMovable')
            elif hasattr(feat, 'Movable'):
                QDockWidget.DockWidgetMovable = getattr(feat, 'Movable')

            if hasattr(feat, 'DockWidgetFloatable'):
                QDockWidget.DockWidgetFloatable = getattr(feat, 'DockWidgetFloatable')
            elif hasattr(feat, 'Floatable'):
                QDockWidget.DockWidgetFloatable = getattr(feat, 'Floatable')

            if hasattr(feat, 'DockWidgetClosable'):
                QDockWidget.DockWidgetClosable = getattr(feat, 'DockWidgetClosable')
            elif hasattr(feat, 'Closable'):
                QDockWidget.DockWidgetClosable = getattr(feat, 'Closable')
except Exception:
    pass
from qgis.PyQt.QtGui import QGuiApplication

# UIファイルのパスを指定
FORM_CLASS = None
try:
    FORM_CLASS, _ = uic.loadUiType(os.path.join(
        os.path.dirname(__file__), 'qmap_permalink_panel_base.ui'))
except Exception:
    # Defer UI loading errors to runtime. Keep FORM_CLASS as None so the
    # module can be imported in environments where Qt/PyQt or uic is not
    # available (for example when running static analysis or tests).
    FORM_CLASS = None


class GeoWebViewPanel(QDockWidget):
    """geo_webviewのパネルクラス
    
    Qt Designerで作成されたUIファイルを読み込んでドッキング可能なパネルとして表示
    """
    
    def __init__(self, parent=None):
        """コンストラクタ
        
        Args:
            parent: 親ウィジェット
        """
        super(GeoWebViewPanel, self).__init__(parent)
        
        # パネルのタイトルを設定
        self.setWindowTitle("GeoWebView")
        
        # ドッキングエリアを設定（左側を優先、右側も可能）
        self.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)

        # 内部ウィジェットを作成
        self.widget = QWidget()
        # If FORM_CLASS could not be loaded (e.g. uic unavailable), create a
        # minimal fallback UI so the plugin can still import and display a
        # helpful message instead of failing entirely.
        if FORM_CLASS is None:
            self.ui = None
            try:
                # Create a minimal placeholder UI
                from qgis.PyQt.QtWidgets import QLabel, QVBoxLayout
                layout = QVBoxLayout()
                label = QLabel(self.tr("UI ファイルを読み込めませんでした。プラグインの再インストールを検討してください。"))
                layout.addWidget(label)
                self.widget.setLayout(layout)
            except Exception:
                # If even Qt widgets are not available, leave widget empty
                pass
        else:
            self.ui = FORM_CLASS()
            self.ui.setupUi(self.widget)

        # 直接アクセス用のプロパティを追加（ui が None の場合は None を代入）
        self.pushButton_generate = getattr(self.ui, 'pushButton_generate', None)
        self.pushButton_navigate = getattr(self.ui, 'pushButton_navigate', None)
        self.pushButton_copy = getattr(self.ui, 'pushButton_copy', None)
        # newly added UI elements
        self.pushButton_clipboard = getattr(self.ui, 'pushButton_clipboard', None)
        self.pushButton_paste = getattr(self.ui, 'pushButton_paste', None)
        self.pushButton_open = getattr(self.ui, 'pushButton_open', None)
        # MapLibre button (added in UI)
        self.pushButton_maplibre = getattr(self.ui, 'pushButton_maplibre', None)
        self.lineEdit_permalink = getattr(self.ui, 'lineEdit_permalink', None)
        self.lineEdit_navigate = getattr(self.ui, 'lineEdit_navigate', None)
        self.label_server_status = getattr(self.ui, 'label_server_status', None)
        self.comboBox_themes = getattr(self.ui, 'comboBox_themes', None)
        
        # Google Maps/Earth用のUI要素
        self.pushButton_google_maps = getattr(self.ui, 'pushButton_google_maps', None)
        self.pushButton_google_earth = getattr(self.ui, 'pushButton_google_earth', None)
        # HTTP server toggle checkbox (added to UI)
        self.checkBox_server_toggle = getattr(self.ui, 'checkBox_server_toggle', None)
        # External control checkbox (new in UI)
        self.checkBox_external_control = getattr(self.ui, 'checkBox_external_control', None)
        # Port number spinbox (new in UI)
        self.spinBox_port = getattr(self.ui, 'spinBox_port', None)
        # Check access button (new in UI)
        self.pushButton_check_access = getattr(self.ui, 'pushButton_check_access', None)
        # Standard port buttons (new in UI)
        self.pushButton_port_80 = getattr(self.ui, 'pushButton_port_80', None)
        self.pushButton_port_443 = getattr(self.ui, 'pushButton_port_443', None)
        
        # ウィジェットを設定
        self.setWidget(self.widget)
        
        # パネルのサイズを設定（左側パネルに適したサイズ）
        self.setMinimumWidth(250)
        self.setMaximumWidth(400)
        
        # パネルの特徴を設定
        self.setFeatures(QDockWidget.DockWidgetMovable | 
                        QDockWidget.DockWidgetFloatable | 
                        QDockWidget.DockWidgetClosable)
        
        # UI要素を翻訳
        self.translate_ui()

        # クリップボード関連のシグナルを接続
        try:
            clipboard = QGuiApplication.clipboard()
            if self.pushButton_clipboard is not None:
                # コピー: 現在の permalink テキストをクリップボードへ
                self.pushButton_clipboard.clicked.connect(self._on_copy_permalink_to_clipboard)
            if self.pushButton_paste is not None:
                # 貼り付け: クリップボードから navigate テキストボックスへ
                self.pushButton_paste.clicked.connect(self._on_paste_from_clipboard)
            if self.pushButton_maplibre is not None:
                # Open permalink in a MapLibre-based viewer
                try:
                    from . import qmap_maplibre as maplibre_gen

                    def _open_maplibre():
                        """Open MapLibre viewer from the current permalink (robust).

                        Fallback order for permalink text: current permalink field,
                        navigate field, system clipboard. Any error is shown to the user
                        instead of being silently swallowed so debugging is easier.
                        """
                        try:
                            permalink_text = ''
                            # prefer generated permalink
                            if hasattr(self, 'lineEdit_permalink') and self.lineEdit_permalink is not None:
                                permalink_text = self.lineEdit_permalink.text() or ''

                            # fallback to navigate input
                            if not permalink_text and hasattr(self, 'lineEdit_navigate') and self.lineEdit_navigate is not None:
                                permalink_text = self.lineEdit_navigate.text() or ''

                            # finally try clipboard
                            if not permalink_text:
                                try:
                                    cb = QGuiApplication.clipboard()
                                    if cb is not None:
                                        permalink_text = cb.text() or ''
                                except Exception:
                                    pass

                            # Parse the permalink to extract x, y, scale, crs, rotation parameters
                            # and construct a /maplibre URL with these direct parameters instead of
                            # passing the full permalink string.
                            try:
                                import webbrowser
                                import re
                                from urllib.parse import parse_qs, urlparse
                                
                                # default port
                                port = 8089
                                try:
                                    if hasattr(self, 'label_server_status') and self.label_server_status is not None:
                                        text = self.label_server_status.text() or ''
                                        m = re.search(r'localhost:(\d+)', text)
                                        if m:
                                            port = int(m.group(1))
                                except Exception:
                                    pass

                                # Parse permalink parameters
                                params = {}
                                if permalink_text:
                                    try:
                                        parsed = urlparse(permalink_text)
                                        query_params = parse_qs(parsed.query)
                                        # Extract x, y, scale, crs, rotation from query parameters
                                        for key in ['x', 'y', 'scale', 'crs', 'rotation']:
                                            if key in query_params and query_params[key]:
                                                params[key] = query_params[key][0]
                                    except Exception:
                                        pass

                                # Build MapLibre URL with x/y/scale/crs/rotation format
                                base = f'http://localhost:{port}/maplibre'
                                if params:
                                    # Use x/y/scale/crs/rotation format
                                    param_parts = []
                                    for key in ['x', 'y', 'scale', 'crs', 'rotation']:
                                        if key in params:
                                            param_parts.append(f'{key}={params[key]}')
                                    if param_parts:
                                        url = base + '?' + '&'.join(param_parts)
                                    else:
                                        url = base
                                else:
                                    url = base

                                webbrowser.open(url)
                            except Exception:
                                # fallback to original generator if webbrowser/URL fails
                                maplibre_gen.open_maplibre_from_permalink(permalink_text)
                        except Exception as e:
                            try:
                                from qgis.PyQt.QtWidgets import QMessageBox
                                if isinstance(e, ValueError) or 'Cannot parse permalink' in str(e):
                                    QMessageBox.information(
                                        self,
                                        "MapLibre",
                                        "有効なパーマリンクが見つかりませんでした。\n" \
                                        "'Current Permalink' または 'Navigate' 欄に有効なパーマリンクを入力するか、\n" \
                                        "クリップボードを確認してください。"
                                    )
                                else:
                                    QMessageBox.warning(self, "MapLibre", f"Failed to open MapLibre: {e}")
                            except Exception:
                                # if even QMessageBox fails, silently ignore to avoid breaking plugin
                                pass

                    self.pushButton_maplibre.clicked.connect(_open_maplibre)
                except Exception as e:
                    # If the generator cannot be imported, disable the button so
                    # users see that MapLibre functionality is unavailable and
                    # can inspect the tooltip for the cause.
                    try:
                        self.pushButton_maplibre.setEnabled(False)
                        # set tooltip with brief error message (avoid long traces)
                        self.pushButton_maplibre.setToolTip(f"MapLibre generator unavailable: {e}")
                    except Exception:
                        # ignore any errors while attempting to update the widget
                        pass
        except Exception:
            # Qt 環境が利用できない場合は無視
            pass
        
    def translate_ui(self):
        """UI要素のテキストを翻訳"""
        from qgis.PyQt.QtCore import QCoreApplication
        
        def tr(text):
            return QCoreApplication.translate('QMapPermalink', text)
        # グループボックスのタイトル
        if hasattr(self.ui, 'groupBox_server'):
            self.ui.groupBox_server.setTitle(tr("HTTP Server Status"))
        if hasattr(self.ui, 'groupBox_generate'):
            self.ui.groupBox_generate.setTitle(tr("Generate Permalink"))
        if hasattr(self.ui, 'groupBox_permalink'):
            self.ui.groupBox_permalink.setTitle(tr("Current Permalink"))
        if hasattr(self.ui, 'groupBox_navigate'):
            self.ui.groupBox_navigate.setTitle(tr("Navigate to Location"))

        # ラベル
        if hasattr(self.ui, 'label_generate_info'):
            self.ui.label_generate_info.setText(tr("Generate a permalink for the current map view"))
        if hasattr(self.ui, 'label_theme_selection'):
            self.ui.label_theme_selection.setText(tr("Theme/Layer State:"))
        if hasattr(self.ui, 'label_navigate_info'):
            self.ui.label_navigate_info.setText(tr("Enter a permalink to navigate"))

        # Buttons now include the icon/label together; set button texts instead
        if hasattr(self.ui, 'pushButton_google_maps'):
            self.ui.pushButton_google_maps.setText(tr("🗺️ Google Maps"))
        if hasattr(self.ui, 'pushButton_google_earth'):
            self.ui.pushButton_google_earth.setText(tr("🌍 Google Earth"))

        # ボタン
        if hasattr(self.ui, 'pushButton_generate'):
            self.ui.pushButton_generate.setText(tr("Generate Permalink"))
        if hasattr(self.ui, 'pushButton_copy'):
            self.ui.pushButton_copy.setText(tr("URLCopy"))
        if hasattr(self.ui, 'pushButton_open'):
            self.ui.pushButton_open.setText(tr("OpenLayers"))
        if hasattr(self.ui, 'pushButton_navigate'):
            self.ui.pushButton_navigate.setText(tr("Navigate"))

        # プレースホルダーテキスト
        if hasattr(self.ui, 'lineEdit_permalink'):
            self.ui.lineEdit_permalink.setPlaceholderText(tr("Generated permalink will appear here"))
        if hasattr(self.ui, 'lineEdit_navigate'):
            self.ui.lineEdit_navigate.setPlaceholderText(tr("Paste permalink here"))

        # コンボボックスの項目
        if hasattr(self.ui, 'comboBox_themes'):
            # 既存の項目をクリアして翻訳済みの項目を追加
            self.ui.comboBox_themes.clear()
            self.ui.comboBox_themes.addItem(tr("-- No Theme (Position Only) --"))
            # ツールチップも翻訳
            self.ui.comboBox_themes.setToolTip(tr("Select theme option: no theme (position only) or specific theme"))
        # External control checkbox
        if hasattr(self.ui, 'checkBox_external_control'):
            self.ui.checkBox_external_control.setText(tr("External Control"))
            self.ui.checkBox_external_control.setToolTip(tr("When enabled, map view can be updated by external URLs"))
    
    def update_server_status(self, port, running):
        """サーバーステータスを更新
        
        Args:
            port: サーバーポート番号
            running: サーバーが実行中かどうか
        """
        if running:
            status_text = f"HTTP Server: Running on http://localhost:{port}"
            style = "color: green; font-weight: bold;"
        else:
            status_text = "HTTP Server: Stopped"
            style = "color: red; font-weight: bold;"
            
        self.label_server_status.setText(status_text)
        self.label_server_status.setStyleSheet(style)
        
        # Update spinBox_port to reflect current port
        try:
            if self.spinBox_port is not None:
                self.spinBox_port.blockSignals(True)
                self.spinBox_port.setValue(int(port))
                self.spinBox_port.blockSignals(False)
        except Exception:
            pass
        
        # Keep checkbox in sync if present
        try:
            if self.checkBox_server_toggle is not None:
                # block signals to avoid recursive calls
                self.checkBox_server_toggle.blockSignals(True)
                self.checkBox_server_toggle.setChecked(bool(running))
                self.checkBox_server_toggle.blockSignals(False)
        except Exception:
            pass
        # keep external control checkbox untouched here (no server relation)
        try:
            if self.checkBox_external_control is not None:
                # ensure it's boolean
                self.checkBox_external_control.blockSignals(True)
                self.checkBox_external_control.setChecked(bool(getattr(self.checkBox_external_control, 'isChecked', lambda: False)()))
                self.checkBox_external_control.blockSignals(False)
        except Exception:
            pass

    def set_server_toggle_handler(self, handler):
        """外部からトグルのハンドラを設定する

        handler: function(checked: bool) -> None
        """
        if self.checkBox_server_toggle is None:
            return
        try:
            # connect stateChanged -> handler
            self.checkBox_server_toggle.stateChanged.connect(lambda state: handler(bool(state)))
        except Exception:
            pass

    def set_external_control_handler(self, handler):
        """外部制御トグルのハンドラを設定する

        handler: function(checked: bool) -> None
        """
        if self.checkBox_external_control is None:
            return
        try:
            self.checkBox_external_control.stateChanged.connect(lambda state: handler(bool(state)))
        except Exception:
            pass
    
    def set_port_change_handler(self, handler):
        """ポート番号変更のハンドラを設定する

        handler: function(port: int) -> None
        """
        if self.spinBox_port is None:
            return
        try:
            self.spinBox_port.valueChanged.connect(lambda value: handler(int(value)))
        except Exception:
            pass
    
    def update_google_buttons_state(self, enabled=True):
        """Google Maps/Earthボタンの状態を更新
        
        Args:
            enabled: ボタンを有効にするかどうか
        """
        if hasattr(self, 'pushButton_google_maps'):
            self.pushButton_google_maps.setEnabled(enabled)
        if hasattr(self, 'pushButton_google_earth'):
            self.pushButton_google_earth.setEnabled(enabled)

    # --- Clipboard handlers ---
    def _on_copy_permalink_to_clipboard(self):
        """lineEdit_permalink の内容をシステムクリップボードにコピーする"""
        try:
            text = ''
            if hasattr(self, 'lineEdit_permalink') and self.lineEdit_permalink is not None:
                text = self.lineEdit_permalink.text() or ''
            QGuiApplication.clipboard().setText(text)
        except Exception:
            pass

    def _on_paste_from_clipboard(self):
        """クリップボードからテキストを取得して lineEdit_navigate に貼り付ける"""
        try:
            cb = QGuiApplication.clipboard()
            text = cb.text() if cb is not None else ''
            if hasattr(self, 'lineEdit_navigate') and self.lineEdit_navigate is not None:
                self.lineEdit_navigate.setText(text)
        except Exception:
            pass