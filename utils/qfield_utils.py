from pathlib import Path
import zipfile

import shutil
import tempfile
import zipfile
from pathlib import Path

from qgis.PyQt.QtCore import QCoreApplication
from qgis.core import QgsOfflineEditing
from qfieldsync.gui.package_dialog import PackageDialog

def package_for_qfield(iface, project, outdir, filename):
    """
    Packages a QField‐ready project and zips it.

    :param iface:        qgis.utils.iface
    :param project:      QgsProject.instance() (or your project reference)
    :param outdir:       Path to an existing output directory
    :param filename:     Base name (no extension) for .qgs and .zip
    :param parent:       Optional parent widget for any dialogs
    :return:             Path to the .zip file, or None if it was aborted
    """
    # 1) Validate output folder
    if not outdir.exists():
        iface.messageBar().pushCritical("Qsequoia2", f"Output folder not found:\n{outdir}")
        return None

    # 2) Build temp workspace
    tmp_dir = tempfile.mkdtemp()
    tmp_path = Path(tmp_dir)
    qgs_path = tmp_path / f"{filename}.qgs"

    try:
        # 3) Run QGIS packaging
        dlg = PackageDialog(iface, project, QgsOfflineEditing())
        dlg.packagedProjectFileWidget.setFilePath(str(qgs_path))
        dlg.packagedProjectTitleLineEdit.setText(project.baseName())
        dlg._validate_packaged_project_filename()
        dlg.package_project()
        dlg.close()
        dlg.deleteLater()
        QCoreApplication.processEvents()

        # 4) Zip up the folder if you still want a .zip
        zip_path = outdir / f"{filename}.zip"
        try:
            zip_folder_contents(tmp_path, zip_path)
        except PermissionError:
            # swallow any locked‐file errors, since the .zip itself is valid
            pass

    finally:
        # 5) Manually remove the temp dir, ignoring any leftover lock errors
        shutil.rmtree(tmp_path, ignore_errors=True)

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
