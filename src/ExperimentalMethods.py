'''
Created on Apr 24, 2015

@author: kwalker
'''
import arcpy, os, time
startTime = time.time()

outputDir = r"C:\Users\kwalker\Documents\Aptana Studio 3 Workspace\DEQ-TankRisk\data\outputNears.gdb"
inputDir = r"Database Connections\agrc@SGID10@gdb10.agrc.utah.gov.sde"#Outside state network path issue

nearTablePrefix = "Near_"
tankLayer = "SGID10.ENVIRONMENT.FACILITYUST" 
riskLayers = ["SGID10.ENVIRONMENT.DWQAssessedWaters", "SGID10.WATER.StreamsNHDHighRes", "SGID10.WATER.LakesNHDHighRes",
           "SGID10.DEMOGRAPHIC.CensusTracts2010", "SGID10.GEOSCIENCE.ShallowGroundWater", "SGID10.GEOSCIENCE.Soils",
           "SGID10.ENVIRONMENT.DWQAssessmentUnits", "SGID10.WATER.Wetlands", "SGID10.GEOSCIENCE.Aquifer_RechargeDischargeAreas",]

inFeature = os.path.join(inputDir, tankLayer)
for riskLayer in riskLayers:
    nearTime = time.time()
    nearTableSuffix = riskLayer.split(".")[2]
    nearTable = os.path.join(outputDir, nearTablePrefix + nearTableSuffix)
    nearFeature = os.path.join(inputDir, riskLayer)
    arcpy.GenerateNearTable_analysis (inFeature, nearFeature, nearTable)
    print "Near_{}: {}".format(nearTableSuffix, time.time() - nearTime)

print "Total time: {}".format(time.time() - startTime)