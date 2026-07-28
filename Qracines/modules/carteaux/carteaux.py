import re
from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLineEdit,
    QMessageBox,
    QApplication
)
from qgis.core import QgsProject, QgsVectorLayer
from qgis.gui import QgsAuthConfigSelect


WFS_URL = "https://datacarto.atlasante.fr/wfs"

WFS_LAYERS = (
    {
        "name": "PPI - Protection immédiate",
        "typename": "ms:dgs_carteaux_ppi_partenaire_j",
        "service": "a0163ef4-1f0e-4b7e-94d0-56098abbf72e",
    },
    {
        "name": "PPR - Protection rapprochée",
        "typename": "ms:dgs_carteaux_ppr_partenaire_j",
        "service": "1f8000de-8432-4eb8-b171-2833a4212f55",
    },
    {
        "name": "PPE - Protection éloignée",
        "typename": "ms:dgs_carteaux_ppe_partenaire_j",
        "service": "00e41bf2-57c5-4f6b-8161-0b5c24479a7a",
    },
)


def normalize_department(value):
    value = value.strip().upper()

    if not re.fullmatch(r"\d{1,3}|2[AB]", value):
        raise ValueError("Code département invalide.")

    return value.zfill(3)


def ask_wfs_config(parent=None):
    dialog = QDialog(parent)
    dialog.setWindowTitle("Configuration WFS")

    auth_input = QgsAuthConfigSelect(dialog, "wfs")

    department_input = QLineEdit(dialog)
    department_input.setPlaceholderText("Ex. 08, 51, 2A ou 971")
    department_input.setMaxLength(3)

    buttons = QDialogButtonBox(
        QDialogButtonBox.Ok | QDialogButtonBox.Cancel,
        parent=dialog,
    )
    buttons.accepted.connect(dialog.accept)
    buttons.rejected.connect(dialog.reject)

    layout = QFormLayout(dialog)
    layout.addRow("Authentification :", auth_input)
    layout.addRow("Département :", department_input)
    layout.addRow(buttons)

    if dialog.exec() != QDialog.Accepted:
        return None

    authcfg = auth_input.configId()

    try:
        department = normalize_department(department_input.text())
    except ValueError as error:
        QMessageBox.warning(parent, "Configuration WFS", str(error))
        return None

    if not authcfg:
        QMessageBox.warning(
            parent,
            "Configuration WFS",
            "Sélectionnez une configuration d'authentification.",
        )
        return None

    return authcfg, department


def create_wfs_layer(config, authcfg, department):
    typename = config["typename"]
    sql = (
        f'SELECT * FROM "{typename}" '
        f'WHERE "code_pp" LIKE \'{department}%\''
    )

    uri = (
        f"authcfg={authcfg} "
        "pagingEnabled='default' "
        "preferCoordinatesForWfsT11='false' "
        "restrictToRequestBBOX='1' "
        "srsname='EPSG:2154' "
        f"typename='{typename}' "
        f"url='{WFS_URL}/{config['service']}' "
        "version='auto' "
        f"sql={sql}"
    )

    return QgsVectorLayer(uri, config["name"], "WFS")


def add_carteaux(parent=None):
    selection = ask_wfs_config(parent)

    if not selection:
        return []

    authcfg, department = selection
    valid_layers = []
    invalid_layers = []

    QApplication.setOverrideCursor(Qt.WaitCursor)
    QApplication.processEvents()

    try:
        for config in WFS_LAYERS:
            layer = create_wfs_layer(
                config,
                authcfg,
                department,
            )

            if not layer.isValid():
                invalid_layers.append(layer.name())
                continue

            valid_layers.append(layer)

        if valid_layers:
            project = QgsProject.instance()
            root = project.layerTreeRoot()

            group = root.findGroup("CARTEAUX")
            if group is None:
                group = root.addGroup("CARTEAUX")

            # Enregistre les couches sans les placer à la racine.
            project.addMapLayers(valid_layers, False)

            for layer in valid_layers:
                group.addLayer(layer)

    finally:
        QApplication.restoreOverrideCursor()

    if invalid_layers:
        QMessageBox.warning(
            parent,
            "Chargement WFS",
            "Couches non chargées :\n"
            + "\n".join(invalid_layers),
        )

    return valid_layers