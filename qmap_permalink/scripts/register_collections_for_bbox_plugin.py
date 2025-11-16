"""
Export current QGIS project vector layers into the actual `bbox` plugin directory
and generate `bbox/config/bbox.toml` so the running BBOX server (sibling plugin)
can pick up the collections.

Usage (QGIS Python Console):
from qmap_permalink.scripts.register_collections_for_bbox_plugin import register_project_collections_to_bbox_plugin
register_project_collections_to_bbox_plugin(auto_restart=False, format='GeoJSON')
"""
from pathlib import Path


def register_project_collections_to_bbox_plugin(auto_restart: bool = False, format: str = "GeoJSON") -> bool:
    """Export project vector layers into sibling 'bbox' plugin and create config.

    This function attempts to locate the sibling 'bbox' plugin directory by
    instantiating BBoxServerManager with this plugin's directory. It then
    exports vector layers to that plugin's `data/` and calls
    `BBoxServerManager.create_config()` to generate `bbox.toml`.
    """
    try:
        from qgis.core import QgsProject

        proj_file = QgsProject.instance().fileName()
        if not proj_file:
            print("ERROR: Current QGIS project is not saved. Please save the project first.")
            return False

        # Determine this plugin directory (qmap_permalink package location).
        # Prefer the installed package location; if import fails, treat as error
        # because falling back to script-relative paths can write config to
        # unexpected locations.
        try:
            import qmap_permalink as _pkg
            plugin_dir = Path(_pkg.__file__).resolve().parent
        except Exception as e:
            print("ERROR: qmap_permalink package is not importable. Ensure the plugin is installed in QGIS Python environment.")
            raise

        try:
            from qmap_permalink.bbox.bbox_server_manager import BBoxServerManager
        except Exception as e:
            print(f"Failed to import BBoxServerManager: {e}")
            return False

        # Instantiate with qmap_permalink plugin_dir so it computes sibling bbox dir
        mgr = BBoxServerManager(str(plugin_dir))

        bbox_root = Path(mgr.bbox_root)
        data_dir = Path(mgr.data_dir)
        config_path = Path(mgr.config_dir) / 'bbox.toml'

        print(f"Detected bbox root: {bbox_root}")
        print(f"Target data dir: {data_dir}")
        print(f"Target config path: {config_path}")

        # Ensure data dir exists
        data_dir.mkdir(parents=True, exist_ok=True)

        # Note: automatic exporter was removed from the plugin to avoid
        # unintended data duplication. This script now generates the
        # BBOX config by scanning the current QGIS project directory for
        # pre-prepared GeoJSON/GPKG/MBTiles files and writes the config
        # into the sibling bbox plugin config (same behavior as the
        # plugin's BBoxManager).
        try:
            from qmap_permalink.bbox.bbox_manager import BBoxManager
            from pathlib import Path

            bm = BBoxManager()

            # If we have a saved project, prefer to set the project_basedir
            # so generated config uses project-relative paths where possible.
            try:
                proj_dir = Path(proj_file).resolve().parent
                bm.config_manager.project_basedir = proj_dir
            except Exception:
                pass

            success = bm.export_and_configure(format=format)
            if not success:
                print("export_and_configure failed. Check QGIS Python Console for messages.")
                return False

            cfg = bm.config_manager.config_path
            print(f"Config created at: {cfg}")

            if auto_restart:
                try:
                    pm = bm.process_manager
                    if pm.is_running():
                        print("Restarting BBox server to pick up new config...")
                        pm.stop()
                    print("Starting BBox server...")
                    pm.start(config_file=cfg, cwd=bm.config_manager.project_basedir)
                    print("BBox server started via process_manager.")
                except Exception as e:
                    print(f"Failed to restart/start BBox server via process_manager: {e}")

            return True
        except Exception as e:
            print(f"Unexpected error while generating config via BBoxManager: {e}")
            return False

    except Exception as e:
        print(f"Unexpected error: {e}")
        return False
