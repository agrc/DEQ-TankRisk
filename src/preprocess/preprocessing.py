import arcpy, os, time
outputDir = r"C:\Users\kwalker\Documents\Aptana Studio 3 Workspace\DEQ-TankRisk\data\srcdata.gdb"
inputDir = r"Database Connections\agrc@SGID10@gdb10.agrc.utah.gov.sde"#Outside state network path issue

nearTablePrefix = "Near_"
tankLayer = "SGID10.ENVIRONMENT.FACILITYUST" 
riskLayers = ["SGID10.ENVIRONMENT.DWQAssessedWaters", "SGID10.WATER.StreamsNHDHighRes", "SGID10.WATER.LakesNHDHighRes",
           "SGID10.DEMOGRAPHIC.CensusTracts2010", "SGID10.GEOSCIENCE.ShallowGroundWater", "SGID10.GEOSCIENCE.Soils",
           "SGID10.ENVIRONMENT.DWQAssessmentUnits", "SGID10.WATER.Wetlands", "SGID10.GEOSCIENCE.Aquifer_RechargeDischargeAreas"]

# for riskLayer in riskLayers:
#     lStart = time.time()
#     outputFeature = os.path.join(outputDir, riskLayer.split(".")[2])
#     arcpy.CopyFeatures_management(os.path.join(inputDir, riskLayer))
#     print "{}: {}".format(riskLayer, time.time() - lStart)

def addLayersToMap(mxdPath):
    mxd = arcpy.mapping.MapDocument(mxdPath)
    for risk in riskLayers:
        riskLayer = arcpy.mapping.Layer(os.path.join(inputDir, risk))
        print riskLayer
        arcpy.mapping.AddLayer(arcpy.mapping.ListDataFrames(mxd)[0], riskLayer)
    mxd.save()
    del mxd
        
if __name__ == "__main__":
    mxdPath = r"C:\Users\Administrator\My Documents\Aptana Studio 3 Workspace\DEQ-TankRisk\data\test_map.mxd"
    addLayersToMap(mxdPath)