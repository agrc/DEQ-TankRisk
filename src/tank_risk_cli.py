#!/usr/bin/env python
# * coding: utf8 *
"""
tank_risk_cli.py
A module that runs the tank risk tool from the terminal
"""

import pathlib
from tank_risk import VERSION, Outputs, TankRisk


import arcpy


class Logger:
    def AddMessage(self, string):
        print(string)

    def AddWarningMessage(self, string):
        print(string)

    def AddErrorMessage(self, string):
        print(string)

    def AddError(self, string):
        print(string)


layer_lookup = {
    "https://services1.arcgis.com/99lidphwczftie9k/arcgis/rest/services/facilitypst/featureserver/0": "tanks",
    "https://services.arcgis.com/zzrwjtrez6fjioq4/arcgis/rest/services/podview/featureserver/0": "points_of_diversion",
    "https://services1.arcgis.com/99lidphwczftie9k/arcgis/rest/services/soils/featureserver/0": "soil",
    "https://services1.arcgis.com/99lidphwczftie9k/arcgis/rest/services/aquifer_rechargedischargeareas/featureserver/0": "aquifer_recharge_discharge_areas",
    "https://fwspublicservices.wim.usgs.gov/wetlandsmapservice/rest/services/wetlands/mapserver/0": "Wetlands",
    "https://services1.arcgis.com/99lidphwczftie9k/arcgis/rest/services/dwqassessmentunits/featureserver/0": "dwq_assessment_units",
    "https://services1.arcgis.com/99lidphwczftie9k/arcgis/rest/services/shallowgroundwater/featureserver/0": "shallow_ground_water",
    "https://services1.arcgis.com/99lidphwczftie9k/arcgis/rest/services/censustracts2020/featureserver/0": "census_tracts_2020",
    "https://services1.arcgis.com/99lidphwczftie9k/arcgis/rest/services/utahlakesnhd/featureserver/0": "lakes_nhd",
    "https://services1.arcgis.com/99lidphwczftie9k/arcgis/rest/services/utahstreamsnhd/featureserver/0": "streams_nhd",
    "https://services2.arcgis.com/nnxp4lz3zx8wwmp9/arcgis/rest/services/utah_ddw_groundwater_source_protection_zones/featureserver/0": "GroundWaterZones",
    "petroleum_storage_tank_facilities": "tanks",
    "soils": "soil",
    "aquifer_recharge_discharge_areas": "aquifer_recharge_discharge_areas",
    "dwq_assessment_units": "dwq_assessment_units",
    "shallow_ground_water": "shallow_ground_water",
    "census_tracts_2020": "census_tracts_2020",
    "lakes_nhd": "lakes_nhd",
    "streams_nhd": "streams_nhd",
    "ut_wetlands": "Wetlands"
}


def find_tank_layer(layers):
    layer_links = {}

    for layer in layers:
        print(f"""{layer.name} props:
  feature layer: {layer.isFeatureLayer}
  web layer: {layer.isWebLayer}
  SDE: {layer.connectionProperties['workspace_factory']}
  SDE table: {layer.connectionProperties['dataset']}
  data source: {layer.dataSource}
""")

        if not layer.isFeatureLayer:
            continue

        if layer.isWebLayer:
            data_source = layer.dataSource.lower()

            if data_source in layer_lookup:
                print(f'including {layer.name}')
                layer_links[layer_lookup[data_source]] = layer

            continue

        props = layer.connectionProperties
        workspace = props['workspace_factory']

        if workspace == 'File Geodatabase':
            table_name = props['dataset'].casefold()

            if table_name in layer_lookup:
                print(f'including {layer.name}')
                layer_links[layer_lookup[table_name]] = layer

            continue

        if props["workspace_factory"] != "SDE":
            continue

        if (
            props["connection_info"]["db_connection_properties"]
            != "opensgid.agrc.utah.gov"
        ):
            continue

        dataset = props["dataset"]
        table_name = dataset.split(".")[-1:][0].strip("%").lower()

        if table_name in layer_lookup:
            print(f'including {layer.name}')
            layer_links[layer_lookup[table_name]] = layer

    return layer_links


def test():
    project_root = pathlib.Path(__file__).resolve().parent.parent
    pro_project_dir = project_root.joinpath("proproject")
    pro_project = str(pro_project_dir.joinpath("TankRisk", "TankRisk.aprx"))
    map_name = "RiskMap"

    risk_project = arcpy.mp.ArcGISProject(pro_project)
    risk_map = risk_project.listMaps(map_name)[0]
    layers = find_tank_layer(risk_map.listLayers())
    facility_ust_points = layers["tanks"]
    output_directory = str(pro_project_dir.joinpath("outputs"))

    print(f"Version {VERSION}")

    Outputs.set_output_directory(output_directory)
    arcpy.Delete_management(Outputs.temp_dir)

    messages = Logger()
    tank_risk_assessor = TankRisk()
    completed = tank_risk_assessor.start(
        facility_ust_points, pro_project, map_name, messages
    )

    if completed:
        print("Risk assessment results created")
    else:
        print("Risk assessment failed")

    arcpy.Delete_management(Outputs.temp_dir)


if __name__ == "__main__":
    test()
