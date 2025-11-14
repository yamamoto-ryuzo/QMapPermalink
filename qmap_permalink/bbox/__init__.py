"""
BBOX Server連携モジュール

QMapPermalinkとBBOX Serverを統合し、以下の機能を提供:
- BBOX Serverプロセスの管理（起動・停止）
- QGISプロジェクトのBBOX形式エクスポート
- データ同期とリアルタイム更新
- 設定ファイルの自動生成
"""

__version__ = "1.0.0"
__all__ = [
    "BBoxManager",
    "BBoxExporter", 
    "BBoxConfig",
    "BBoxProcessManager",
    "BBoxServerManager"
]

from .bbox_manager import BBoxManager
from .bbox_exporter import BBoxExporter
from .bbox_config import BBoxConfig
from .bbox_process import BBoxProcessManager
from .bbox_server_manager import BBoxServerManager
