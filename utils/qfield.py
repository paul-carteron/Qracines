from pathlib import Path
import shutil
import tempfile
import zipfile

from qgis.PyQt.QtCore import QCoreApplication, Qt
from qgis.PyQt.QtWidgets import QMessageBox
from qgis.core import QgsProject
from qgis.core import QgsOfflineEditing
from qfieldsync.gui.package_dialog import PackageDialog

def package_for_qfield(iface, project, outdir, filename):
    """
    Packages a QField‐ready project and zips it, without ever
    overwriting or mutating the “live” project on disk.

    Returns the .zip path or None if aborted.
    """
    # 1) Validate output folder
    if not outdir.exists():
        iface.messageBar().pushCritical("Qsequoia2", f"Output folder not found:\n{outdir}")
        return None

    # 2) Prepare a temp workspace
    base_tmp = Path(tempfile.mkdtemp())
    src_dir = base_tmp / "src" ; src_dir.mkdir()
    qfield_dir = base_tmp / "qfield" ; qfield_dir.mkdir()

    src_qgs = src_dir / f"{filename}_src.qgs"
    packaged_qgs = qfield_dir / f"{filename}.qgs"
    zip_path  = outdir / f"{filename}.zip"

    try:
        # ─── 3) Dump your live project into src_dir ────────────────────
        project.write(str(src_qgs))

        # ─── 4) Load staging copy into a fresh QgsProject ─────────────
        temp_project = QgsProject()
        if not temp_project.read(str(src_qgs)):
            raise RuntimeError(f"Failed to load staging project at {src_qgs}")

        # ─── 5) Run QFieldSync, targeting qfield_dir ──────────────────
        dlg = PackageDialog(iface, temp_project, QgsOfflineEditing())
        dlg.setAttribute(Qt.WA_DeleteOnClose, True)
        dlg.packagedProjectFileWidget.setFilePath(str(packaged_qgs))
        dlg.packagedProjectTitleLineEdit.setText(temp_project.baseName())
        dlg._validate_packaged_project_filename()
        dlg.package_project()
        dlg.close(); dlg.deleteLater(); QCoreApplication.processEvents()

        # ─── 6) Zip *only* the qfield_dir ─────────────────────────────
        with zipfile.ZipFile(zip_path, "w", allowZip64=True) as zf:
            for fp in qfield_dir.rglob("*"):
                if fp.is_file():
                    # preserve the top-level folder name in the archive
                    arc = fp.relative_to(qfield_dir)
                    zf.write(fp, str(arc))

        iface.messageBar().pushInfo("QFieldSync", f"Packaged to {zip_path}")
        return zip_path

    finally:
        # ─── 7) Clean up both temp dirs and the temp project ───────────
        try:
            temp_project.clear()
        except Exception:
            pass
        shutil.rmtree(base_tmp, ignore_errors=True)


def zip_folder_contents(folder_path, output_zip_path):
    """
    Zips all contents (files and subfolders) of folder_path
    into a zip archive at output_zip_path.

    The contents will be stored in the zip archive without the top-level folder.
    """
    folder_path = Path(folder_path)
    output_zip_path = Path(output_zip_path)

    with zipfile.ZipFile(output_zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        # Recursively iterate over all files under folder_path
        for file_path in folder_path.rglob('*'):
            if file_path.is_file():
                # Make arcname relative to the root folder so top-level folder is omitted
                arcname = file_path.relative_to(folder_path)
                zipf.write(file_path, arcname)

    print(f"Created zip archive at {output_zip_path}")