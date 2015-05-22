'''
Created on May 22, 2015

@author: kwalker
'''
import arcpy, os, time
import configs

def createNearTable(tanks, riskFeature, outputGdb):
    inFeature = tanks
    nearTablePrefix = "near_"
    nearTime = time.time()
    nearTableSuffix = riskFeature.split(".")[-1]
    nearTable = os.path.join(outputGdb, nearTablePrefix + nearTableSuffix)
    nearFeature = riskFeature
    arcpy.GenerateNearTable_analysis (inFeature, nearFeature, nearTable)
    print "Near_{}: {}".format(nearTableSuffix, time.time() - nearTime)
    return nearTable

if __name__ == '__main__':

    
    tankPoints = r"Database Connections\agrc@SGID10@gdb10.agrc.utah.gov.sde\SGID10.ENVIRONMENT.FACILITYUST" 
    riskFeatures = configs.MapSource().getSelectedlayers()
    print riskFeatures
    
    outputDirectory = r"C:\Users\Administrator\My Documents\Aptana Studio 3 Workspace\DEQ-TankRisk\data\outputs"
    outputGdb = "nears_{}.gdb".format(time.strftime("%Y%m%d%H%M%S"))
    arcpy.CreateFileGDB_management(outputDirectory, outputGdb)
    outputGdb = os.path.join(outputDirectory, outputGdb)
    
    for riskFeature in riskFeatures:
        createNearTable(tankPoints, riskFeature, outputGdb)
        break 
