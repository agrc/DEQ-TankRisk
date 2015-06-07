'''
Created on Apr 24, 2015

@author: kwalker
'''
import arcpy, os, time
# startTime = time.time()
# 
# outputDir = os.path.join(r"C:\Users\Administrator\My Documents\Aptana Studio 3 Workspace\DEQ-TankRisk\data\outputs",
#                                    "ExprGdb" + time.strftime("%Y%m%d%H%M%S"))
# os.makedirs(outputDir)
# x = arcpy.CreateFileGDB_management(outputDir, "nears.gdb") 
# print x
# outputDir = os.path.join(outputDir, "nears.gdb")
# 
# inputDir = r"Database Connections\agrc@SGID10@gdb10.agrc.utah.gov.sde"#Outside state network path issue
# 
# nearTablePrefix = "Near_"
# tankLayer = "SGID10.ENVIRONMENT.FACILITYUST" 
# riskLayers = ["SGID10.ENVIRONMENT.DWQAssessedWaters", "SGID10.WATER.StreamsNHDHighRes", "SGID10.WATER.LakesNHDHighRes",
#            "SGID10.DEMOGRAPHIC.CensusTracts2010", "SGID10.GEOSCIENCE.ShallowGroundWater", "SGID10.GEOSCIENCE.Soils",
#            "SGID10.ENVIRONMENT.DWQAssessmentUnits", "SGID10.WATER.Wetlands", "SGID10.GEOSCIENCE.Aquifer_RechargeDischargeAreas",]
# 
# inFeature = os.path.join(inputDir, tankLayer)
# for riskLayer in riskLayers:
#     nearTime = time.time()
#     nearTableSuffix = riskLayer.split(".")[2]
#     nearTable = os.path.join(outputDir, nearTablePrefix + nearTableSuffix)
#     nearFeature = os.path.join(inputDir, riskLayer)
#     arcpy.GenerateNearTable_analysis (inFeature, nearFeature, nearTable)
#     print "Near_{}: {}".format(nearTableSuffix, time.time() - nearTime)
# 
# print "Total time: {}".format(time.time() - startTime)

fields = ["IN_FID"]
fields.extend(["NEAR_FID", "NEAR_DIST"])
with arcpy.da.SearchCursor(in_table = r"C:\Users\Administrator\My Documents\Aptana Studio 3 Workspace\DEQ-TankRisk\data\outputs\nears_20150529130159.gdb\near_LakesNHDHighRes", 
                   field_names = fields) as cursor:
    for row in cursor:
        x = [r for r in row[1:]]
        print x