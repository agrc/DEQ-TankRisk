#!/usr/bin/env python
# * coding: utf8 *
'''
preprocessing.py
A module that adds layers to a map
'''


import os
import pathlib
import time
import sys

from tqdm import tqdm

import arcpy

tank_layer = 'SGID10.ENVIRONMENT.FACILITYUST'
risk_layers = [
    'SGID10.ENVIRONMENT.DWQAssessedWaters',
    'SGID10.WATER.StreamsNHDHighRes',
    'SGID10.WATER.LakesNHDHighRes',
    'SGID10.DEMOGRAPHIC.CensusTracts2010',
    'SGID10.GEOSCIENCE.ShallowGroundWater',
    'SGID10.GEOSCIENCE.Soils',
    'SGID10.ENVIRONMENT.DWQAssessmentUnits',
    'SGID10.WATER.Wetlands',
    'SGID10.GEOSCIENCE.Aquifer_RechargeDischargeAreas',
]


def add_layers_to_map(project_path, workspace):
    import pdb; pdb.set_trace()

    project = arcpy.mp.ArcGISProject(project_path)
    risk_map = project.listMaps('RiskMap')[0]

    for layer_name in tqdm(risk_layers):
        risk_map.addDataFromPath(os.path.join(workspace, layer_name))

    project.save()


if __name__ == '__main__':
    project_root = pathlib.Path(__file__).resolve().parent.parent.parent

    pro_project_dir = project_root.joinpath('proproject')
    pro_project = pro_project_dir.joinpath('TankRisk', 'TankRisk.aprx')
    sde_path = pro_project_dir.joinpath('sgid.agrc.utah.gov.sde')

    if not pro_project.exists():
        print(f'could not find pro project in {pro_project}')

        sys.exit(-1)

    if not sde_path.exists():
        print(f'could not find sgid10 sde in {sde_path}')

        sys.exit(-1)

    add_layers_to_map(str(pro_project), str(sde_path))
