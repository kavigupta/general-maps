import os
import sys

from qgis.core import QgsProject, QgsLayoutExporter, QgsApplication


_, layout_name, title, path = sys.argv

dpi = 400
layout_name = layout_name
dpi = int(dpi)

QgsApplication.setPrefixPath("/usr", True)

gui_flag = False
app = QgsApplication([], gui_flag)

app.initQgis()

project_path = os.path.abspath("main.qgz")

project_instance = QgsProject.instance()
project_instance.setFileName(project_path)
project_instance.read()
project_instance.setTitle(title)
project_instance.setCustomVariables(dict(title=title))

manager = QgsProject.instance().layoutManager()
layout = manager.layoutByName(layout_name)

exporter = QgsLayoutExporter(layout)
settings = QgsLayoutExporter.ImageExportSettings()
settings.dpi = dpi
exporter.exportToImage(os.path.abspath(path), settings)
app.exitQgis()
