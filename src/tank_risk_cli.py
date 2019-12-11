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

def test():
    project_root = pathlib.Path(__file__).resolve().parent.parent
    pro_project_dir = project_root.joinpath('proproject')
    pro_project = str(pro_project_dir.joinpath('TankRisk', 'TankRisk.aprx'))
    map_name = 'Layers'

    risk_map = arcpy.mp.ArcGISProject(pro_project).listMaps(map_name)[0]

    facility_ust_points = risk_map.listLayers('SGID10.ENVIRONMENT.FACILITYUST')[0]
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

    print(time.time() - start_time)


if __name__ == '__main__':
    test()
