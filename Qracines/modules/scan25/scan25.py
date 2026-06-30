from qgis.PyQt.QtWidgets import QDialog, QVBoxLayout, QLabel, QDialogButtonBox, QMessageBox
from qgis.core import QgsDataSourceUri, QgsProject, QgsRasterLayer
from qgis.gui import QgsAuthConfigSelect


def ask_authcfg(parent=None):
    dlg = QDialog(parent)
    dlg.setWindowTitle("Authentification WMTS")

    layout = QVBoxLayout(dlg)
    layout.addWidget(QLabel(
        "Sélectionnez une configuration d'authentification QGIS,\n"
        "ou créez-en une avec le bouton +."
    ))

    auth_widget = QgsAuthConfigSelect(dlg, "wms")
    layout.addWidget(auth_widget)

    buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, parent=dlg)
    buttons.accepted.connect(dlg.accept)
    buttons.rejected.connect(dlg.reject)
    layout.addWidget(buttons)

    if dlg.exec() != QDialog.Accepted:
        return None

    return auth_widget.configId() or None


def qbytearray_to_str(value):
    # QgsDataSourceUri.encodedUri() peut renvoyer QByteArray selon la version QGIS
    if isinstance(value, bytes):
        return value.decode("utf-8")
    return bytes(value).decode("utf-8")


def add_scan25(parent=None):
    authcfg = ask_authcfg(parent)

    if not authcfg:
        QMessageBox.warning(parent, "WMTS", "Aucune authentification sélectionnée.")
        return None

    quri = QgsDataSourceUri()
    quri.setParam("authcfg", authcfg)
    quri.setParam("crs", "EPSG:3857")
    quri.setParam("format", "image/jpeg")
    quri.setParam("layers", "GEOGRAPHICALGRIDSYSTEMS.MAPS.SCAN25TOUR")
    quri.setParam("styles", "normal")
    quri.setParam("tileMatrixSet", "PM_6_16")
    quri.setParam(
        "url",
        "https://data.geopf.fr/private/wmts/?service=WMTS&version=1.0.0&request=GetCapabilities"
    )

    uri = qbytearray_to_str(quri.encodedUri())

    layer = QgsRasterLayer(
        uri,
        "©IGN - SCAN 25®",
        "wms",
    )

    if not layer.isValid():
        QMessageBox.critical(
            parent,
            "Erreur WMTS",
            layer.error().summary() or "La couche WMTS est invalide."
        )
        print("URI utilisée :", uri)
        return None

    QgsProject.instance().addMapLayer(layer)
    return layer
