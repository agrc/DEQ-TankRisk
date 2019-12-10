#!/usr/bin/env python
# * coding: utf8 *
'''
preprocessing.py
A module that adds layers to a map
'''


import os
import time

import arcpy

output_dir = r'C:\Users\kwalker\Documents\Aptana Studio 3 Workspace\DEQ-TankRisk\data\srcdata.gdb'
input_dir = r'Database Connections\agrc@SGID10@gdb10.agrc.utah.gov.sde'  #: Outside state network path issue

nearTablePrefix = 'Near_'
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


def add_layers_to_map(mxd_path):
    mxd = arcpy.mapping.MapDocument(mxd_path)

    for risk in risk_layers:
        riskLayer = arcpy.mapping.Layer(os.path.join(inputDir, risk))
        print(riskLayer)
        arcpy.mapping.AddLayer(arcpy.mapping.ListDataFrames(mxd)[0], riskLayer)

    mxd.save()

    del mxd


if __name__ == '__main__':
    mxdPath = r'C:\Users\Administrator\My Documents\Aptana Studio 3 Workspace\DEQ-TankRisk\data\test_map.mxd'
    add_layers_to_map(mxdPath)
