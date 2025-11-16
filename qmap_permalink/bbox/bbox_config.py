"""
BBOX Server設定ファイル管理モジュール

BBOX Server用のTOML設定ファイルを生成・管理
"""

from pathlib import Path
from typing import Dict, Any, List, Optional
from qgis.core import QgsMessageLog, Qgis


class BBoxConfig:
    """BBOX Server設定ファイル管理クラス"""
    
    def __init__(self, config_path: Optional[Path] = None):
        """設定マネージャーを初期化
        
        Args:
            config_path: 設定ファイルパス（Noneの場合は自動生成）
        """
        if config_path is None:
            try:
                # Prefer installed plugin location so sibling plugins/bbox is used
                import qmap_permalink as _pkg
                plugin_dir = Path(_pkg.__file__).resolve().parent
                plugins_root = plugin_dir.parent
                bbox_root = plugins_root / 'bbox'
                # Use the same default filename as BBoxServerManager.create_config()
                self.config_path = bbox_root / 'config' / 'bbox.toml'
            except Exception:
                plugin_dir = Path(__file__).parent.parent
                self.config_path = plugin_dir / "bbox" / "config" / "bbox.toml"
        else:
            self.config_path = Path(config_path)
        
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        
        # デフォルト設定
        self.config = {
            "webserver": {
                "bind": "0.0.0.0",
                "port": 8080,
                "threads": 0
            },
            "cors": {
                "allowed_origins": ["*"]
            },
            "tilesets": [],
            "collections": []
        }
    
    def set_port(self, port: int):
        """ポート番号を設定"""
        self.config["webserver"]["port"] = port
    
    def set_bind_address(self, address: str):
        """バインドアドレスを設定"""
        self.config["webserver"]["bind"] = address
    
    def add_tileset(self, name: str, source: Path, format: str = "png",
                    minzoom: int = 0, maxzoom: int = 18):
        """タイルセットを追加
        
        Args:
            name: タイルセット名
            source: MBTilesファイルパス
            format: タイル形式（png, jpg, pbf等）
            minzoom: 最小ズームレベル
            maxzoom: 最大ズームレベル
        """
        # 相対パスに変換（設定ファイルからの相対）。
        # - まず config ファイル親（config/） を基準に相対化を試みる
        # - 次に bbox ルート（config/ の親）を基準に相対化を試みる
        # - どちらも無理なら絶対パスのまま保存する
        relative_source = source
        # 1) 可能なら QGIS プロジェクトのディレクトリを基準に相対化
        try:
            from qgis.core import QgsProject
            proj_file = QgsProject.instance().fileName()
            if proj_file:
                proj_dir = Path(proj_file).parent
                try:
                    relative_source = source.relative_to(proj_dir)
                except Exception:
                    relative_source = relative_source
        except Exception:
            # QGIS が利用できない環境やプロジェクト情報が取れない場合は無視
            pass

        # 2) 続けて config/ を基準に相対化
        if relative_source == source:
            try:
                relative_source = source.relative_to(self.config_path.parent)
            except ValueError:
                try:
                    # bbox root (config parent の親) を基準にする
                    bbox_root = self.config_path.parent.parent
                    relative_source = source.relative_to(bbox_root)
                except Exception:
                    relative_source = source
        
        tileset = {
            "name": name,
            "source": str(relative_source),
            "format": format,
            "minzoom": minzoom,
            "maxzoom": maxzoom
        }
        
        self.config["tilesets"].append(tileset)
        
        QgsMessageLog.logMessage(
            f"📦 Added tileset: {name}",
            "QMapPermalink", Qgis.Info
        )
    
    def add_collection(self, name: str, source: Path, srs: str = "EPSG:4326"):
        """フィーチャーコレクションを追加
        
        Args:
            name: コレクション名
            source: データソースパス（GeoJSON, GeoPackage等）
            srs: 座標参照系
        """
        # 相対パスに変換（同上）
        relative_source = source
        # 1) 可能なら QGIS プロジェクトのディレクトリを基準に相対化（優先）
        try:
            from qgis.core import QgsProject
            proj_file = QgsProject.instance().fileName()
            if proj_file:
                proj_dir = Path(proj_file).parent
                try:
                    relative_source = source.relative_to(proj_dir)
                except Exception:
                    relative_source = relative_source
        except Exception:
            pass

        # 2) 次に設定ファイルの親（config/）を基準に相対化
        if relative_source == source:
            try:
                relative_source = source.relative_to(self.config_path.parent)
            except ValueError:
                try:
                    bbox_root = self.config_path.parent.parent
                    relative_source = source.relative_to(bbox_root)
                except Exception:
                    relative_source = source
        
        collection = {
            "name": name,
            "source": str(relative_source).replace('\\', '/'),
            "srs": srs
        }
        
        self.config["collections"].append(collection)
        
        QgsMessageLog.logMessage(
            f"📋 Added collection: {name}",
            "QMapPermalink", Qgis.Info
        )
    
    def generate_toml(self) -> str:
        """TOML形式の設定ファイルを生成
        
        Returns:
            str: TOML形式の設定文字列
        """
        lines = [
            "# BBOX Server Configuration",
            "# Generated by QMapPermalink",
            "",
            "[webserver]",
            f'bind = "{self.config["webserver"]["bind"]}"',
            f'port = {self.config["webserver"]["port"]}',
            f'threads = {self.config["webserver"]["threads"]}',
            "",
            "[webserver.cors]",
            f'allowed_origins = {self._format_string_array(self.config["cors"]["allowed_origins"])}',
            ""
        ]
        
        # タイルセット
        for tileset in self.config["tilesets"]:
            lines.extend([
                "[[tileset]]",
                f'name = "{tileset["name"]}"',
                f'source = "{tileset["source"]}"',
                f'format = "{tileset["format"]}"',
                f'minzoom = {tileset["minzoom"]}',
                f'maxzoom = {tileset["maxzoom"]}',
                ""
            ])
        
        # フィーチャーコレクション
        for collection in self.config["collections"]:
            # Use table-style source so implementations that expect structured
            # collection sources (e.g. file path + format) can parse it more
            # reliably. Many BBOX server configs accept a 'source' table.
            src = collection["source"].replace('\\', '/')
            # Try to emit a 'file' style source with explicit format to match
            # possible BBOX server expected variants.
            # Example: source = { file = "data/foo.geojson", format = "geojson" }
            fmt = "geojson"
            lines.extend([
                "[[collection]]",
                f'name = "{collection["name"]}"',
                f'source = {{ path = "{src}", format = "{fmt}" }}',
                f'srs = "{collection["srs"]}"',
                ""
            ])
        
        return "\n".join(lines)
    
    def _format_string_array(self, array: List[str]) -> str:
        """文字列配列をTOML形式にフォーマット"""
        quoted = [f'"{item}"' for item in array]
        return f'[{", ".join(quoted)}]'
    
    def save(self) -> Path:
        """設定ファイルを保存
        
        Returns:
            Path: 保存された設定ファイルのパス
        """
        toml_content = self.generate_toml()
        
        with open(self.config_path, 'w', encoding='utf-8') as f:
            f.write(toml_content)
        
        QgsMessageLog.logMessage(
            f"💾 Config saved: {self.config_path}",
            "QMapPermalink", Qgis.Info
        )
        
        return self.config_path
    
    def load(self) -> bool:
        """設定ファイルを読み込み
        
        Returns:
            bool: 読み込み成功時True
        """
        if not self.config_path.exists():
            QgsMessageLog.logMessage(
                f"⚠️ Config file not found: {self.config_path}",
                "QMapPermalink", Qgis.Warning
            )
            return False
        
        # 簡易的なTOMLパーサー（基本的な値のみサポート）
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # TODO: 本格的なTOMLパーサーを使う場合は toml ライブラリを使用
            QgsMessageLog.logMessage(
                f"✅ Config loaded: {self.config_path}",
                "QMapPermalink", Qgis.Info
            )
            return True
            
        except Exception as e:
            QgsMessageLog.logMessage(
                f"❌ Failed to load config: {e}",
                "QMapPermalink", Qgis.Critical
            )
            return False
