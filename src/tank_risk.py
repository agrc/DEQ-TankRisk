'''
Created on May 22, 2015

@author: kwalker
'''
import arcpy, os, time
from configs import *

class TankResult(object):

    
    def __init__(self, tankId):
        #Tank facility Id
        self.facilityUstId = tankId
        #In polygon feature properties
        self.isSurfaceWaterZone = None
        self.surfaceWaterSeverity = None
        self.isAquiferArea = None
        self.aquiferSeverity = None
        self.isAssessedWater = None
        self.assessedWaterSeverity = None
        self.isWetLand = None
        self.wetLandSeverity = None
        #Distance feature properties
        self.pointOfDiversionDist = None
        self.pointOfDiversionSeverity = None
        self.streamDist = None
        self.streamSeverity = None
        self.lakeDist = None
        self.lakeSeverity = None
        #Attribute feature properties
        self.shallowGroundWaterDepth = None
        self.shallowGroundWaterSeverity = None
        self.soilTexture = None
        self.soilSeverity = None
        self.censusDensity = None
        self.censusSeverity = None
        
    def populateFieldsForRiskFeature(self, featureName, value, severity):
        if featureName == "Aquifer_RechargeDischargeAreas":
            self.aquiferSeverity = severity
        
    def getResultTableRow(self):
        pass

class RiskFeature(object):
    
    def __init__(self, layerPath, layerName, outputGdb):
        self.layerPath = layerPath
        self.layerName = layerName
        self.valueAttribute = "{}_{}".format(layerName, "val")
        self.severityAttribute = "{}_{}".format(layerName, "sev")
        self.nearTable = "near_" + layerName
        self.nearTablePath = os.path.join(outputGdb, self.nearTable)
        self.nearDistField = "NEAR_DIST"
        self.nearTankIDField = "IN_FID"
        self.nearRiskIdField = "NEAR_FID"
        self.outputGdb = outputGdb
        self.tankResults = {}
        
    def createNearTable(self, tankPoints):
        inFeature = tankPoints
        nearTable = os.path.join(self.outputGdb, self.nearTable)
        nearFeature = self.layerPath
        nearTime = time.time()
        arcpy.GenerateNearTable_analysis (inFeature, nearFeature, nearTable)
        print "Near_{}: {}".format(self.layerPath.split(".")[-1], time.time() - nearTime)
        return nearTable
        
class InPolygonFeature (RiskFeature):
        
    def getTankResults(self):
        with arcpy.da.SearchCursor(in_table = self.nearTablePath, 
                           field_names = [self.nearTankIDField, self.nearDistField]) as cursor:
            for row in cursor:
                nearDistance = row[1]
                tankId = row[0]
                if nearDistance == 0:
                    self.tankResults[tankId] = 1#Tank point is in risk polygon
                else:
                    self.tankResults[tankId] = 0
        
        return self.tankResults
        
        
class DistanceFeature (RiskFeature):
        
    def getTankResults(self):
        with arcpy.da.SearchCursor(in_table = self.nearTablePath, 
                           field_names = [self.nearTankIDField, self.nearDistField]) as cursor:
            nearDistance = row[1]
            tankId = row[0]
            for row in cursor:
                self.tankResults[tankId] = nearDistance
        
        return self.tankResults

class AttributeFeature (RiskFeature):
    
    def __init__(self, featurePath, featureName, outputGdb, attributeFields):
        super(AttributeFeature, self).__init__(featurePath, featureName, outputGdb)
        self.attributeFields = attributeFields
    
    def getTankResults(self):
        arcpy.JoinField_management(self.nearTablePath, self.nearRiskIdField, 
                                   self.layerPath, arcpy.Describe(self.layerPath).OIDFieldName, self.attributeFields)
        
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
                                "ShallowGroundWater":"DEPTH", "CensusTracts2010":["POP100", "AREALAND"]}
        self.tankResults = {}
 
    def inPolygonProcessing(self, results):
        for tankId in results:
            if tankId not in self.tankResults:
                self.tankResults[tankId] = TankResult(tankId)
            
            self.tankResults[tankId]
    def censusProcessing(self, results):
        for tankId in results:
            popDensity = int(results[tankId][0])/int(results[tankId][0])
            results[tankId] = popDensity
        
        pass
    def riskFeatureFactory(self, riskFeature):
        featureName = riskFeature.split(".")[-1]
        if LayerConstants.layerNames[featureName].type == LayerConstants.IN_POLYGON:
            return InPolygonFeature(riskFeature, featureName, Outputs.outputGdb)
        elif LayerConstants.layerNames[featureName].type == LayerConstants.DISTANCE:
            return DistanceFeature(riskFeature, featureName, Outputs.outputGdb)
        elif LayerConstants.layerNames[featureName].type == LayerConstants.ATTRIBUTE:
            return AttributeFeature(riskFeature, featureName, Outputs.outputGdb, LayerConstants.layerNames[featureName].calcFields)
        else:
            print "Unkown layer error"
        pass
        
    def start(self):
        tankPoints = r"Database Connections\agrc@SGID10@gdb10.agrc.utah.sde\SGID10.ENVIRONMENT.FACILITYUST" 
        riskFeatures = MapSource().getSelectedlayers()
        print riskFeatures
        arcpy.CreateFileGDB_management(Outputs.outputDirectory, Outputs.outputGdbName)
        
        for riskFeature in riskFeatures:
            rf = self.riskFeatureFactory(riskFeature)
            print type(rf)
            rf.createNearTable(tankPoints)
            results = rf.getTankResults()
            if type(rf) == "InPolygonFeature":
                pass
                
            for r in results:
                print "{}: {}".format(r, results[r])
            break        
        

if __name__ == '__main__':

    tankRiskAssessor = TankRisk()
    tankRiskAssessor.start()
 
