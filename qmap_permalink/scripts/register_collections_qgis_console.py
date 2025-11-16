"""
QGIS console helper (package location).

Place under `qmap_permalink.scripts` so it can be imported from QGIS Python Console as:

from qmap_permalink.scripts.register_collections_qgis_console import register_project_collections
register_project_collections()

This performs the same actions as the top-level script but is importable as a plugin submodule.
"""
from pathlib import Path


def register_project_collections(auto_restart: bool = False, format: str = "GeoJSON") -> bool:
    """Export current project's vector layers and register them as BBOX collections.

    Run this inside QGIS Python Console.
    """
    try:
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

        # List exported files
        try:
            exported = list(Path(mgr.exporter.output_dir).glob('*'))
        except Exception:
            exported = []

        print(f"Export completed. Exported files count: {len(exported)}")
        for p in exported:
            print(f" - {p}")

        print(f"Config saved at: {mgr.config_manager.config_path}")

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
