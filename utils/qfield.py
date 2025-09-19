from pathlib import Path
import shutil
import tempfile
import zipfile

from qgis.PyQt.QtCore import QCoreApplication, Qt

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

    # 2) Save current project
    tmp_project = Path(tempfile.mkdtemp()) / f"{filename}.qgz"
    if not project.write(str(tmp_project)):
        iface.messageBar().pushMessage("Qsequoia2", "Snapshot failed.", level=Qgis.Critical, duration=10)
        raise RuntimeError("Snapshot write failed")

    # 3) tmp qfield folder
    tmp_qfield_dir = Path(tempfile.mkdtemp())
    tmp_qfield = tmp_qfield_dir / f"{filename}_qfield.qgs"

    # Tell QFieldSync to package into tmp_qgs (inside tmp_dir)
    dlg = PackageDialog(iface, project, QgsOfflineEditing())
    dlg.setAttribute(Qt.WA_DeleteOnClose, True)
    dlg.packagedProjectFileWidget.setFilePath(str(tmp_qfield))
    dlg.packagedProjectTitleLineEdit.setText(str(filename))
    dlg._validate_packaged_project_filename()
    dlg.package_project()
    dlg.close(); dlg.deleteLater(); QCoreApplication.processEvents()

    # Zip the whole tmp_dir
    zip_path = Path(outdir) / f"{filename}.zip"
    with zipfile.ZipFile(zip_path, "w", allowZip64=True) as zf:
        for fp in tmp_qfield_dir.rglob("*"):
            if fp.is_file():
                # Strip the parent so archive starts at tmp_dir/
                arc = fp.relative_to(tmp_qfield_dir)
                zf.write(fp, str(arc))

    iface.messageBar().pushInfo("QFieldSync", f"Packaged to {zip_path}")
    return zip_path