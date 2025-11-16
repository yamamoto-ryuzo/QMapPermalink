"""
Small helper to register current QGIS project's vector layers as BBOX collections.

Usage (in QGIS Python Console):

from qmap_permalink.scripts.register_collections_qgis_console import register_project_collections
register_project_collections(auto_restart=False, format='GeoJSON')

This script depends on the plugin modules being available in the QGIS Python environment
(`qmap_permalink.bbox`). It will:
- check the project is saved
- export vector layers to the plugin `bbox/data` directory
- update `bbox/config/bbox.toml` with [[collection]] entries
- optionally restart the BBOX server via the plugin manager
"""
from pathlib import Path
from typing import Optional


def register_project_collections(auto_restart: bool = False, format: str = "GeoJSON") -> bool:
    """Export current project's vector layers and register them as BBOX collections.

    Args:
        auto_restart: If True and BBox server is available, restart it to pick up changes.
        format: Export format for vector layers (default: "GeoJSON").

    Returns:
        True on success, False on failure.
    """
    try:
        # Import QGIS API
        from qgis.core import QgsProject

        proj_file = QgsProject.instance().fileName()
        if not proj_file:
            print("ERROR: Current QGIS project is not saved. Please save the project first.")
            return False

        # Import plugin BBox manager. If import fails, treat as error — do not
        # fall back to script-relative paths which may write config elsewhere.
        try:
            from qmap_permalink.bbox.bbox_manager import BBoxManager
        except Exception as e:
            print(f"ERROR: Failed to import BBoxManager: {e}. Ensure qmap_permalink is installed in QGIS Python environment.")
            return False

        mgr = BBoxManager()

        print(f"Project file: {proj_file}")
        print("Starting export_and_configure...")

        success = mgr.export_and_configure(format=format)
        if not success:
            print("export_and_configure failed. Check QGIS Python Console for errors.")
            return False

        # Show summary
        try:
            exported = list(Path(mgr.exporter.output_dir).glob('*'))
        except Exception:
            exported = []

        print(f"Export completed. Exported files count: {len(exported)}")
        for p in exported:
            print(f" - {p}")

        print(f"Config saved at: {mgr.config_manager.config_path}")

        # Optionally restart BBox server to pick up the new config
        if auto_restart:
            try:
                if mgr.is_bbox_available():
                    print("Restarting BBox server to apply new config...")
                    was_running = mgr.process_manager.is_running()
                    if was_running:
                        mgr.stop_bbox_server()
                    mgr.start_bbox_server(auto_export=False)
                    print("BBox server restart requested.")
                else:
                    print("BBox binary not available; cannot restart server.")
            except Exception as e:
                print(f"Failed to restart BBox server: {e}")

        return True

    except Exception as e:
        print(f"Unexpected error: {e}")
        return False
