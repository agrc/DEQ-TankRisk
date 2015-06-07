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

class RiskFeature(object):
    
    def __init__(self, layerName, outputGdb):
        self.layerName = layerName
        self.nearTable = "near_" + layerName.split(".")[-1]
        self.nearTablePath = os.path.join(outputGdb, self.nearTable)
        self.nearDistField = "NEAR_DIST"
        self.nearTankIDField = "IN_FID"
        self.nearRiskIdField = "NEAR_FID"
        self.tankResults = {}
        
    def createNearTable(self, tankPoints):
        inFeature = tankPoints
        nearTable = os.path.join(self.outputGdb, self.nearTable)
        nearFeature = self.layerName
        nearTime = time.time()
        arcpy.GenerateNearTable_analysis (inFeature, nearFeature, nearTable)
        print "Near_{}: {}".format(self.layerName.split(".")[-1], time.time() - nearTime)
        return nearTable
        
class InPolygonFeature (RiskFeature):
    
    def __init__(self, layerName):
        super(InPolygonFeature, self).__init__(layerName)
        
    def getTankResults(self):
        with arcpy.SearchCursor(in_table = self.nearTablePath, 
                           where_clause = """{} = 0""".format(self.nearDistField), 
                           field_names = [self.nearTankIDField, self.nearDistField]) as cursor:
            for row in cursor:
                self.tankResults[row[0]] = row[1]#change this to yes value, 1 maybe
        
        return self.tankResults
        
        
class DistanceFeature (RiskFeature):
    
    def __init__(self, layerName):
        super(DistanceFeature, self).__init__(layerName)
        
    def getTankResults(self):
        with arcpy.SearchCursor(in_table = self.nearTablePath, 
                           field_names = [self.nearTankIDField, self.nearDistField]) as cursor:
            for row in cursor:
                self.tankResults[row[0]] = row[1]
        
        return self.tankResults

class AttributeFeature (RiskFeature):
    
    def __init__(self, layerName, attributeFields):
        super(AttributeFeature, self).__init__(layerName)
        self.attributeFields = attributeFields
    
    def getTankResults(self):
        arcpy.JoinField_management(self.nearTablePath, self.nearRiskIdField, self.layerName, self.attributeFields)
        
        fields = [self.nearTankIDField]
        fields.extend(self.attributeFields)
        with arcpy.da.SearchCursor(in_table = self.nearTablePath, 
                           field_names = fields) as cursor:
            for row in cursor:
                self.tankResults[row[0]] = [value for value in row[1:]]
        
        return self.tankResults
    



class TankRisk(object):
    def __init__(self):
        self.inPolygonLayers = ["Aquifer_RechargeDischargeAreas", "Wetlands",]
        self.distanceLayers = ["LakesNHDHighRes", "StreamsNHDHighRes", ]
        self.attributeLayers = {"DWQAssessmentUnits":"STATUS2006", "Soils":"TEX_DEF", 
                                "ShallowGroundWater":"DEPTH", "CensusTracts2010":["AREALAND", "TotalPopulation"]}
        

#     def createNearTable(self, tanks, riskFeature, outputGdb):
#         inFeature = tanks
#         nearTablePrefix = "near_"
#         nearTime = time.time()
#         nearTableSuffix = riskFeature.split(".")[-1]
#         nearTable = os.path.join(outputGdb, nearTablePrefix + nearTableSuffix)
#         nearFeature = riskFeature
#         arcpy.GenerateNearTable_analysis (inFeature, nearFeature, nearTable)
#         print "Near_{}: {}".format(nearTableSuffix, time.time() - nearTime)
#         return nearTable
#     
#     def getResults(self):
#         
#         for layer in self.inPolygonLayers:
#             pass
#     
    def censusProcessing(self):
    def riskFeatureFactory(self, riskFeature):
        
    def start(self):
        tankPoints = r"Database Connections\agrc@SGID10@gdb10.agrc.utah.gov.sde\SGID10.ENVIRONMENT.FACILITYUST" 
        riskFeatures = configs.MapSource().getSelectedlayers()
        print riskFeatures
        
        outputDirectory = r"C:\Users\Administrator\My Documents\Aptana Studio 3 Workspace\DEQ-TankRisk\data\outputs"
        outputGdb = "nears_{}.gdb".format(time.strftime("%Y%m%d%H%M%S"))
        arcpy.CreateFileGDB_management(outputDirectory, outputGdb)
        outputGdb = os.path.join(outputDirectory, outputGdb)
        
        for riskFeature in riskFeatures:
            rf = RiskFeature(riskFeature, outputGdb)
            rf.createNearTable(tankPoints)
            break        
        

if __name__ == '__main__':

    tankRiskAssessor = TankRisk()
    tankRiskAssessor.start()
 
