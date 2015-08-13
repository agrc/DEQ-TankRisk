'''
Created on May 22, 2015

@author: kwalker
'''
import arcpy, os, time, csv
#from configs import *

class MapSource(object):
     
     
    def __init__(self, tankPoints, mapDocument):
        self.tankPoints = tankPoints#r"Database Connections\agrc@SGID10@gdb10.agrc.utah.sde\SGID10.ENVIRONMENT.FACILITYUST"
        self.mapDoc = mapDocument
        pass
     
    def getSelectedlayers(self):
        mxd = arcpy.mapping.MapDocument(mapDoc)
        layerPaths = []
        for layer in arcpy.mapping.ListLayers(mxd):
            if layer.visible:
                layerPaths.append(layer.dataSource)
        del mxd
        return list(layerPaths)
 
 
class Outputs(object):
    outputDirectory = r"..\data\outputs"
    uniqueTimeString = time.strftime("%Y%m%d%H%M%S")
     
    outputGdbName = "TankRisk_{}.gdb".format(uniqueTimeString)
    os.path.join(outputDirectory, outputGdbName)
     
    tempGdbName =  "nears_{}.gdb".format(uniqueTimeString)
    tempGdb = os.path.join(outputDirectory, tempGdbName)
    tempCsv = "TankRiskResults_{}.csv".format(uniqueTimeString)
     
class LayerAttributes(object):       
    def __init__(self, type, valAttribute, sevAttribute, valFieldName, sevFieldName, calcFields = None, valMethod = None):
        self.type = type
        self.valAttribute = valAttribute
        self.sevAttribute = sevAttribute
        self.valFieldName = valFieldName
        self.sevFieldName = sevFieldName
        self.calcFields = calcFields
        self.valMethod = valMethod
    


class TankResult(object):
    tankResults = {}
    IN_POLYGON = "inPolygon"
    DISTANCE = "distance"
    ATTRIBUTE = "attribute"
    OUTPUT_ID_FIELD = "TankId"
    layerNames = {"Aquifer_RechargeDischargeAreas": LayerAttributes(ATTRIBUTE, 
                                                                 "aquiferVal", "aquiferSev", 
                                                                 "aquiferVal", "aquiferSev",
                                                                 ["ZONE_"]),
                    "Wetlands": LayerAttributes(IN_POLYGON,
                                               "wetLandsVal", "wetLandsSev",
                                               "wetLandsVal", "wetLandsSev"),
                    "LakesNHDHighRes": LayerAttributes(DISTANCE ,
                                                      "lakesVal", "lakeSev",
                                                      "lakesVal", "lakeSev"), 
                    "StreamsNHDHighRes": LayerAttributes(DISTANCE ,
                                                        "streamsVal", "streamsSev",
                                                        "streamsVal", "streamsSev"),
                    "DWQAssessmentUnits": LayerAttributes(ATTRIBUTE,
                                                           "assessmentVal", "assessmentSev",
                                                           "assessmentVal", "assessmentSev",
                                                           ["STATUS2006"]), 
                    "Soils": LayerAttributes(ATTRIBUTE,
                                               "soilVal", "soilSev",
                                               "soilVal", "soilSev",
                                               ["TEX_DEF"]), 
                    "ShallowGroundWater": LayerAttributes(ATTRIBUTE,
                                                         "shallowWaterVal", "shallowWaterSev",
                                                         "shallowWaterVal", "shallowWaterSev",
                                                         ["DEPTH"]), 
                    "CensusTracts2010":LayerAttributes(ATTRIBUTE,
                                                      "censusVal", "censusSev",
                                                      "censusVal", "censusSev",
                                                      ["POP100", "AREALAND"]),
                    "GroundWaterZones":LayerAttributes(ATTRIBUTE,
                                                      "udwspzVal", "udwspzSev",
                                                      "udwspzVal", "udwspzSev",
                                                      ["ProtZone"]),
                    "SurfaceWaterZones":LayerAttributes(ATTRIBUTE,
                                                      "udwspzVal", "udwspzSev",
                                                      "udwspzVal", "udwspzSev",
                                                      ["ProtZone"])                  
                
                  }
    
    def __init__(self, tankId):
        #FacilityUST OBJECTID
        self.tankId = tankId
        #Risk layer result attributes
        self.shallowWaterVal = None
        self.shallowWaterSev = None
        self.soilVal = None
        self.soilSev = None
        self.wetLandsVal = None
        self.wetLandsSev = None
        self.aquiferVal = None
        self.aquiferSev = None
        self.surfaceWaterVal = None
        self.surfaceWaterSev = None
        self.groundWaterVal = None
        self.groundWaterSev = None
        self.assessmentVal = None
        self.assessmentSev = None
        self.censusVal = None
        self.censusSev = None
        self.streamsVal = None
        self.streamsSev = None
        self.lakesVal = None
        self.lakeSev = None
        self.udwspzVal = None
        self.udwspzSev = None

    def getOutputHeader(self):
        fieldDict = self.__dict__
        outputHeader = []
        for f in fieldDict:
            if fieldDict[f] != None:
                outputHeader.append(f)
                
        return outputHeader
    
    @staticmethod     
    def getOutputRows (featureNames):
        outputRows = []
        featureNameRowOrder = list(featureNames)
        headerList = [TankResult.OUTPUT_ID_FIELD]
        for f in featureNameRowOrder:
            valFieldName = TankResult.layerNames[f].valFieldName
            sevFieldName = TankResult.layerNames[f].sevFieldName
            if valFieldName in headerList or sevFieldName in headerList:
                featureNameRowOrder.remove(f)#Two layers can share one output field and the field doesn't need to be added to twice.
                continue
            headerList.append(valFieldName)
            headerList.append(sevFieldName)
        outputRows.append(headerList)
            
        for t in TankResult.tankResults.values():
            tempValueList = [t.tankId]
            for f in featureNameRowOrder:
                tempValueList.append(t.__getattribute__(TankResult.layerNames[f].valAttribute))
                tempValueList.append(t.__getattribute__(TankResult.layerNames[f].sevAttribute))
            outputRows.append(tempValueList)
        
        return outputRows


    @staticmethod
    def getLayerValAndScore(row, layerName):
        val = 0
        score = 0
        tankId = row[0]
        if tankId not in TankResult.tankResults:
                TankResult.tankResults[tankId] = TankResult(tankId)
        tankResultRef = TankResult.tankResults[tankId]
                
        if layerName == "Aquifer_RechargeDischargeAreas":
            val = str(row[1])
            if val == "DISCH":
                score = 1
            elif val == "SECOND":
                score = 2
            elif val == "PRIMARY":
                score = 5
            else:
                score = 0
                
            tankResultRef.aquiferVal = val
            tankResultRef.aquiferSev = score
        
        elif layerName == "Wetlands":
            val, score = TankResult.inPolygonValAndScore(row[1])
            tankResultRef.wetLandsVal = val
            tankResultRef.wetLandsSev = score
        
        elif layerName == "LakesNHDHighRes":
            val = row[1]
            score = TankResult.distanceScore(row[1])
            tankResultRef.lakesVal = val
            tankResultRef.lakeSev = score
            
        elif layerName == "StreamsNHDHighRes":
            val = row[1]
            score = TankResult.distanceScore(row[1])
            tankResultRef.streamsVal = val
            tankResultRef.streamsSev = score
                   
        elif layerName == "DWQAssessmentUnits":
            status = str(row[1])
            val = status
            if status == "Fully Supporting":
                score = 2
            elif status == "Impaired" or status == "Not Assessed":
                score = 5
            tankResultRef.assessmentVal = val
            tankResultRef.assessmentSev = score
        
        elif layerName == "Soils":
            texture = row[1]
            val = texture
            tankResultRef.soilVal = val
            tankResultRef.soilSev = score
        
        elif layerName == "ShallowGroundWater":
            depth = row[1]
            val = depth
            tankResultRef.shallowWaterVal = val
            tankResultRef.shallowWaterSev = score
        
        elif layerName == "CensusTracts2010":
            popDensity = float(row[1])/float(row[2])
            val = popDensity
            if popDensity > 0.00181:
                score = 5
            elif popDensity > 0.00108:
                score = 4
            elif popDensity > .0000274:
                score = 3
            elif popDensity > 0.00000723:
                score = 2
            elif popDensity > 0.0:
                score = 1
            else:
                score = 0
            tankResultRef.censusVal = val
            tankResultRef.censusSev = score
                            
        elif layerName == "GroundWaterZones" or layerName == "SurfaceWaterZones":
            nearDist = row[2]
            protZone = row[1]
            val = protZone
            if nearDist != 0:
                val = 0
                sev = 0
            elif protZone == 4:
                score = 2
            elif protZone == 3:
                score = 3
            elif protZone == 2:
                score = 4
            elif protZone == 1:
                score = 5
            else:
                score = 0
            
            if tankResultRef.udwspzSev < score:
                tankResultRef.udwspzVal = val
                tankResultRef.udwspzSev = score
        
        return (val, score)
    
    @staticmethod
    def inPolygonValAndScore(distance):
        val = None
        score = None
        if distance == 0:
            val = 1
            score = 5
        else:
            val = 0
            score = 0
        return (val, score)
    @staticmethod
    def distanceScore(distance):
        dist = float(distance)
        score = None
        if dist > 332:
            score = 1
        elif dist > 192:
            score = 2
        elif dist > 114:
            score = 3
        elif dist > 57:
            score = 4
        elif dist <= 56 and dist >= 0:
            score = 5
        else:
            score = 0
        
        return score

        

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
        
    def createNearTable(self, tankPoints):
        inFeature = tankPoints
        nearTable = os.path.join(self.outputGdb, self.nearTable)
        nearFeature = self.layerPath
        nearTime = time.time()
        print "Near params {}, {}, {}".format(inFeature, nearFeature, nearTable)
        arcpy.GenerateNearTable_analysis (inFeature, nearFeature, nearTable)
        print "Near_{}: {}".format(self.layerPath.split(".")[-1], time.time() - nearTime)
        return nearTable
        
class InPolygonFeature (RiskFeature):
        
    def getTankResults(self):
        with arcpy.da.SearchCursor(in_table = self.nearTablePath, 
                           field_names = [self.nearTankIDField, self.nearDistField]) as cursor:
            for row in cursor:
                tankId = row[0]
                TankResult.getLayerValAndScore(row, self.layerName)
        
#         return self.tankResults
        
        
class DistanceFeature (RiskFeature):
        
    def getTankResults(self):
        with arcpy.da.SearchCursor(in_table = self.nearTablePath, 
                           field_names = [self.nearTankIDField, self.nearDistField]) as cursor:
            for row in cursor:
                tankId = row[0]
                TankResult.getLayerValAndScore(row, self.layerName)
        
        
        #return self.tankResults

class AttributeFeature (RiskFeature):
    multiFeatureValues = {}
    def __init__(self, featurePath, featureName, outputGdb, attributeFields):
        super(AttributeFeature, self).__init__(featurePath, featureName, outputGdb)
        self.attributeFields = attributeFields
    
    def getTankResults(self):
        arcpy.JoinField_management(self.nearTablePath, self.nearRiskIdField, 
                                   self.layerPath, arcpy.Describe(self.layerPath).OIDFieldName, self.attributeFields)
        
        fields = [self.nearTankIDField]
        fields.extend(self.attributeFields)
        fields.append(self.nearDistField)
        with arcpy.da.SearchCursor(in_table = self.nearTablePath, 
                           field_names = fields) as cursor:
            for row in cursor:
                TankResult.getLayerValAndScore(row, self.layerName)




class TankRisk(object):
    def __init__(self):
        self.tankResults = {}
        self.outputFields = []
        self.riskFeatureNameOrder = []
        
    def parseName(self, riskFeature):
        filePathEnding = riskFeature.split("\\")[-1]
        fileName = filePathEnding.split(".")
        if fileName[-1].lower() == 'shp':
            return fileName[-2]
        else:
            return fileName[-1]
    
    def riskFeatureFactory(self, riskFeature):
        featureName = self.parseName(riskFeature)
        self.riskFeatureNameOrder.append(featureName)
        if TankResult.layerNames[featureName].type == TankResult.IN_POLYGON:
            return InPolygonFeature(riskFeature, featureName, Outputs.tempGdb)
        elif TankResult.layerNames[featureName].type == TankResult.DISTANCE:
            return DistanceFeature(riskFeature, featureName, Outputs.tempGdb)
        elif TankResult.layerNames[featureName].type == TankResult.ATTRIBUTE:
            return AttributeFeature(riskFeature, featureName, Outputs.tempGdb, TankResult.layerNames[featureName].calcFields)
        else:
            print "Unkown layer error"
        pass
    
    def createOutputTable(self, resultRows):
        outputDir = Outputs.outputDirectory
        arcpy.CreateFileGDB_management(Outputs.outputDirectory, Outputs.outputGdbName)
        with open(os.path.join(outputDir, Outputs.tempCsv), "wb") as outCsv:
            csvWriter = csv.writer(outCsv)
            csvWriter.writerows(resultRows)
        
    def start(self, tankPoints, mapDocument):
        mapDoc = MapSource(tankPoints, mapDocument)
        tankPoints = mapDoc.tankPoints
        self.outputFields.append("TankId") 
        riskFeatures = mapDoc.getSelectedlayers()
        print riskFeatures
        arcpy.CreateFileGDB_management(Outputs.outputDirectory, Outputs.tempGdbName)
        
        for riskFeature in riskFeatures:
            print riskFeature
            rf = self.riskFeatureFactory(riskFeature)
            print "factory"
            rf.createNearTable(tankPoints)
            print "near"
            resultTime = time.time()
            rf.getTankResults()
            print "results: {}".format(time.time() - resultTime)
            
        resultRows = TankResult.getOutputRows(self.riskFeatureNameOrder)
        self.createOutputTable(resultRows)
        

if __name__ == '__main__':
    testing = False

    if testing:
        mapDoc = r"..\data\test_map.mxd"
        facilityUstTankPoints = r"C:\GIS\Work\DEQ_TankRisk\FACILITYUST.gdb\FACILITYUST"
        outputDir = r"..\data\outputs"
    else:
        mapDoc = "CURRENT"
        facilityUstTankPoints = arcpy.GetParameterAsText(0)
        outputDir = arcpy.GetParameterAsText(1)
        
#     outputFileName = "mapservGeocodeResults_" + time.strftime("%Y%m%d%H%M%S") + ".csv"
    
    startTime = time.time()
    tankRiskAssessor = TankRisk()
    tankRiskAssessor.start(facilityUstTankPoints, mapDoc)
    print time.time() - startTime
 
