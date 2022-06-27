#!/usr/bin/env python
# * coding: utf8 *
'''
preprocessing.py
A module that adds layers to a map
'''


import os
from pathlib import Path
import sys

from tqdm import tqdm

import arcpy

TANK_LAYER = 'https://services1.arcgis.com/99lidPhWCzftIe9K/ArcGIS/rest/services/FacilityPST/FeatureServer/0'  #: facility pst
RISK_LAYERS = [
    'opensgid.environment.dwq_assessment_units',
    'opensgid.water.streams_nhd',
    'opensgid.water.lakes_nhd',
    'opensgid.demographic.census_tracts_2020',
    'opensgid.geoscience.shallow_ground_water',
    'https://services1.arcgis.com/99lidPhWCzftIe9K/arcgis/rest/services/Soils/FeatureServer/0',  #: soils
    'opensgid.environment.dwq_assessment_units',
    'opensgid.water.wetlands',
    'opensgid.geoscience.aquifer_recharge_discharge_areas',
    'https://services.arcgis.com/ZzrwjTRez6FJiOq4/arcgis/rest/services/PODView/FeatureServer/0',  #: points of diversion
    'https://services2.arcgis.com/NnxP4LZ3zX8wWmP9/ArcGIS/rest/services/Utah_DDW_Groundwater_Source_Protection_Zones/FeatureServer/0'  #: ground water zones
]


def add_layers_to_map(project_path, workspace):
    project = arcpy.mp.ArcGISProject(project_path)
    try:
        risk_map = project.listMaps('RiskMap')[0]
    except IndexError:
        print('Create a map called RiskMap')
        return
    RISK_LAYERS.append(TANK_LAYER)
    for layer_name in tqdm(RISK_LAYERS):
        if layer_name.startswith('opensgid'):
            risk_map.addDataFromPath(os.path.join(workspace, layer_name))
            continue
        if layer_name.startswith('http'):
            risk_map.addDataFromPath(layer_name)
            continue

        data_file = Path(layer_name)
        try:
            path = data_file.resolve(strict=True)
        except FileNotFoundError:
            print(f'{layer_name} was not found')
            return

        risk_map.addDataFromPath(str(path))

    project.save()


if __name__ == '__main__':
    project_root = Path(__file__).resolve().parent.parent.parent

    pro_project_dir = project_root.joinpath('proproject')
    pro_project = pro_project_dir.joinpath('TankRisk', 'TankRisk.aprx')
    sde_path = pro_project_dir.joinpath('opensgid.agrc.utah.gov.sde')

    if not pro_project.exists():
        print(f'could not find pro project in {pro_project}')

        sys.exit(-1)

    if not sde_path.exists():
        print(f'could not find sgid sde in {sde_path}')

        sys.exit(-1)

    add_layers_to_map(str(pro_project), str(sde_path))
