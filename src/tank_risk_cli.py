#!/usr/bin/env python
# * coding: utf8 *
'''
tank_risk_cli.py
A module that runs the tank risk tool from the terminal
'''

import pathlib
import time
from tank_risk import VERSION, Outputs, TankRisk


import arcpy


class Logger():
    def AddMessage(self, string):
        print(string)

    def AddWarningMessage(self, string):
        print(string)

    def AddErrorMessage(self, string):
        print(string)

    def AddError(self, string):
        print(string)

layer_lookup = {
    'https://services1.arcgis.com/99lidPhWCzftIe9K/ArcGIS/rest/services/FacilityPST/FeatureServer/0': 'tanks',
    'petroleum_storage_tank_facilities': 'tanks',
    'https://services.arcgis.com/ZzrwjTRez6FJiOq4/arcgis/rest/services/PODView/FeatureServer/0': 'points_of_diversion',
    'https://services1.arcgis.com/99lidPhWCzftIe9K/arcgis/rest/services/Soils/FeatureServer/0': 'soil',
    'aquifer_recharge_discharge_areas': 'aquifer_recharge_discharge_areas',
    'wetlands': 'wetlands',
    'dwq_assessment_units': 'dwq_assessment_units',
    'shallow_ground_water': 'shallow_ground_water',
    'census_tracts_2010': 'census_tracts_2010',
    'lakes_nhd': 'lakes_nhd',
    'streams_nhd': 'streams_nhd',
    'dwq_assessment_units': 'dwq_assessment_units'
}

def find_tank_layer(layers):
    layer_links = {

    }

    for layer in layers:
        if not layer.isFeatureLayer:
            continue

        if layer.isWebLayer:
            if(layer.dataSource in layer_lookup):
                layer_links[layer_lookup[layer.dataSource]] = layer

            continue

        props = layer.connectionProperties
        if props['workspace_factory'] != 'SDE':
            continue

        if props['connection_info']['db_connection_properties'] != 'opensgid.agrc.utah.gov':
            continue

        dataset = props['dataset']
        table_name = dataset.split('.')[-1:][0].strip('%')

        if(table_name in layer_lookup):
            layer_links[layer_lookup[table_name]] = layer

    return layer_links

def test():
    project_root = pathlib.Path(__file__).resolve().parent.parent
    pro_project_dir = project_root.joinpath('proproject')
    pro_project = str(pro_project_dir.joinpath('TankRisk', 'TankRisk.aprx'))
    map_name = 'RiskMap'

    risk_project = arcpy.mp.ArcGISProject(pro_project)
    risk_map = risk_project.listMaps(map_name)[0]
    layers = find_tank_layer(risk_map.listLayers())
    facility_ust_points = layers['tanks']
    output_directory = str(pro_project_dir.joinpath('outputs'))

    print(f'Version {VERSION}')

    Outputs.set_output_directory(output_directory)
    arcpy.Delete_management(Outputs.temp_dir)

    start_time = time.time()

    messages = Logger()
    tank_risk_assessor = TankRisk()
    completed = tank_risk_assessor.start(facility_ust_points, pro_project, map_name, messages)

    if completed:
        print('Risk assessment results created')
    else:
        print('Risk assessment failed')

    arcpy.Delete_management(Outputs.temp_dir)


if __name__ == '__main__':
    test()
