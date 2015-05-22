'''
Created on May 22, 2015

@author: kwalker
'''
import arcpy, os, time
import configs

class Result(object):
    
    def __init__(self):
        self.facilityUstId = None
        
        self.isSurfaceWaterZone = None
        self.isAquiferArea = None
        self.isAssessedWater = None
        self.isWetLand = None
        
        self.distPointOfDiversion = None
        self.distStream = None
        self.distLake = None
        
        self.shallowGroundWaterDepth = None
        self.soilTexture = None
        self.censusDensity = None



class TankRisk(object):
    def __init__(self):
        self.inPolygonLayers = []
        self.distanceLayers = []
        self.attributeLayers = {}
        

    def createNearTable(self, tanks, riskFeature, outputGdb):
        inFeature = tanks
        nearTablePrefix = "near_"
        nearTime = time.time()
        nearTableSuffix = riskFeature.split(".")[-1]
        nearTable = os.path.join(outputGdb, nearTablePrefix + nearTableSuffix)
        nearFeature = riskFeature
        arcpy.GenerateNearTable_analysis (inFeature, nearFeature, nearTable)
        print "Near_{}: {}".format(nearTableSuffix, time.time() - nearTime)
        return nearTable
    
    def getResults(self):
        
        for layer in self.inPolygonLayers:
            pass
    
    def start(self):
        tankPoints = r"Database Connections\agrc@SGID10@gdb10.agrc.utah.gov.sde\SGID10.ENVIRONMENT.FACILITYUST" 
        riskFeatures = configs.MapSource().getSelectedlayers()
        print riskFeatures
        
        outputDirectory = r"C:\Users\Administrator\My Documents\Aptana Studio 3 Workspace\DEQ-TankRisk\data\outputs"
        outputGdb = "nears_{}.gdb".format(time.strftime("%Y%m%d%H%M%S"))
        arcpy.CreateFileGDB_management(outputDirectory, outputGdb)
        outputGdb = os.path.join(outputDirectory, outputGdb)
        
        for riskFeature in riskFeatures:
            self.createNearTable(tankPoints, riskFeature, outputGdb)
            break        
        

if __name__ == '__main__':

    tankRiskAssessor = TankRisk()
    tankRiskAssessor.start()
 
