'''
ArcGIS script tool for evaluating tank risk based on spatial relationships to other data.

Created on May 22, 2015
@author: kwalker
'''
import arcpy, os, time, csv


class MapSource(object):
    """Class for accessing map document information.""" 
    def __init__(self, mapDocument):
        self.mapDoc = mapDocument
        pass
     
    def getSelectedlayers(self):
        mxd = arcpy.mapping.MapDocument(self.mapDoc)
        layerPaths = []
        for layer in arcpy.mapping.ListLayers(mxd):
            if layer.visible:
                if layer.supports('DATASOURCE'):
                    layerPaths.append(layer.dataSource)
                elif layer.supports('WORKSPACEPATH') and layer.supports('DATASETNAME'):
                    layerPaths.append(os.path.join(layer.workspacePath, layer.datasetName))
                elif layer.supports('NAME'):
                    arcpy.AddWarning('Did not find workspace: {}'.format(layer.name))
                else:
                    arcpy.AddWarning('Visble layer not supported')
        del mxd
        return list(layerPaths)
    
                
    def addLayerToMap(self, layerPath):
        mxd = arcpy.mapping.MapDocument(self.mapDoc)
        df = arcpy.mapping.ListDataFrames(mxd,"*")[0]
        newLayer = arcpy.mapping.Layer(layerPath)
        arcpy.mapping.AddLayer(df, newLayer,"BOTTOM")
        del mxd
        del df
        del newLayer                  

 
class Outputs(object):
    """Outputs stores all the directory and file name info.
    - setOutputDirectory initializes all attribute."""
    uniqueTimeString = None
    
    outputDirectory = None
    outputGdbName = None
    outputGdb = None
    outputTableName = None
    
    outputCsvName = None
    
    tempDir = None
    tempGdbName =  None
    tempGdb = None
    
    @staticmethod
    def setOutputDirectory(outputDir):
        Outputs.uniqueTimeString = time.strftime("%Y%m%d%H%M%S")
        
        Outputs.outputDirectory = outputDir
        Outputs.outputGdbName = "TankRisk_{}.gdb".format(Outputs.uniqueTimeString)
        Outputs.outputGdb = os.path.join(Outputs.outputDirectory, Outputs.outputGdbName)
        Outputs.outputTableName = "TankRiskResults_{}".format(Outputs.uniqueTimeString)
        
        Outputs.outputCsvName = "TankRiskResults_{}.csv".format(Outputs.uniqueTimeString)
        
        Outputs.tempDir = "in_memory"
        Outputs.tempGdbName =  "nearsTemp_{}.gdb".format(Outputs.uniqueTimeString)
        Outputs.tempGdb = "in_memory" #os.path.join(tempDir, tempGdbName)

     
class LayerAttributes(object):
    """LayerAttributes stores risk feature information in a way that 
    is easy to access."""       
    def __init__(self, type, valAttribute, sevAttribute, valFieldName, sevFieldName, calcFields = None, valMethod = None):
        self.type = type #type of risk feature
        self.valAttribute = valAttribute #attribute for value result
        self.sevAttribute = sevAttribute #attribute for severity result
        self.valFieldName = valFieldName #Value field name in output table
        self.sevFieldName = sevFieldName #Severity field name in output table
        self.calcFields = calcFields #Fields for attribute type risk features
        self.valMethod = valMethod #Method to produce value. Not yet used.
    

class TankResult(object):
    """Stores everything that is specific to each risk feature including:
    - Litterals (field names) 
    - Logic for scoring results for each risk feature
    - Result data for each risk feature"""
    tankResults = {}
    IN_POLYGON = "inPolygon"
    DISTANCE = "distance"
    ATTRIBUTE = "attribute"
    OUTPUT_ID_FIELD = "FACILITYID"
    #attributesForFeature associates feature names with attributes
    attributesForFeature = {"Aquifer_RechargeDischargeAreas": LayerAttributes(ATTRIBUTE, 
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
                                                      ["ProtZone"]),
                  "wrpod": LayerAttributes(DISTANCE,                #Also known as PointsOfDiversion
                                                 "podVal", "podSev", 
                                                 "podVal", "podSev")
                  }
    
    def __init__(self, tankId):
        #FacilityUST OBJECTID
        self.tankId = tankId
        #Risk layer result attributes
        for f in TankResult.attributesForFeature:
            self.__dict__[TankResult.attributesForFeature[f].valAttribute] = None
            self.__dict__[TankResult.attributesForFeature[f].sevAttribute] = None

    def setValForLayer(self, layerName, val):
        self.__dict__[TankResult.attributesForFeature[layerName].valAttribute] = val
        
    def getValForLayer(self, layerName):
        return self.__dict__[TankResult.attributesForFeature[layerName].valAttribute]
    
    def setSevForLayer(self, layerName, sev):
        self.__dict__[TankResult.attributesForFeature[layerName].sevAttribute] = sev
        
    def getSevForLayer(self, layerName):
        return self.__dict__[TankResult.attributesForFeature[layerName].sevAttribute]
    
    @staticmethod     
    def getOutputRows (featureNames):
        """Get a list that contains the rows of the output table, including header.
        - featureNames are used to order output table fields."""
        outputRows = []
        featureNameOrder_Header = list(featureNames)
        featureNamesOrder_Values = []
        #Add header
        headerList = [TankResult.OUTPUT_ID_FIELD]
        for f in featureNameOrder_Header:
            valFieldName = TankResult.attributesForFeature[f].valFieldName
            sevFieldName = TankResult.attributesForFeature[f].sevFieldName
            if valFieldName in headerList or sevFieldName in headerList:
                continue#Two layers can share one output field and the field doesn't need to be added to twice.
            featureNamesOrder_Values.append(f)#Make a list without shared outputs for value adding efficiency
            headerList.append(valFieldName)
            headerList.append(sevFieldName)

        outputRows.append(headerList)
        #Add values          
        for t in TankResult.tankResults.values():
            tempValueList = [t.tankId]
            for f in featureNamesOrder_Values:
                tempValueList.append(t.getValForLayer(f))
                tempValueList.append(t.getSevForLayer(f))
            outputRows.append(tempValueList)
        
        return outputRows

    @staticmethod
    def updateTankValAndScore(row, layerName):
        """Update TankResult for the tankId contained in row parameter.
        -The items contained in a row are dependent on the particular RiskFeautre layerName and type."""
        val = 0
        score = 0
        tankId = row[0]
        #Get the result object for the current tankId.
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
            tankResultRef.setValForLayer(layerName, val)
            tankResultRef.setSevForLayer(layerName, score)
        
        elif layerName == "Wetlands":
            val, score = TankResult.inPolygonValAndScore(row[1])
            tankResultRef.setValForLayer(layerName, val)
            tankResultRef.setSevForLayer(layerName, score)
        
        elif layerName == "LakesNHDHighRes":
            val = row[1]
            score = TankResult.distanceScore(row[1])
            tankResultRef.setValForLayer(layerName, val)
            tankResultRef.setSevForLayer(layerName, score)
            
        elif layerName == "StreamsNHDHighRes":
            val = row[1]
            score = TankResult.distanceScore(row[1])
            tankResultRef.setValForLayer(layerName, val)
            tankResultRef.setSevForLayer(layerName, score)
                   
        elif layerName == "DWQAssessmentUnits":
            status = str(row[1])
            val = status
            if status == "Fully Supporting":
                score = 2
            elif status == "Impaired" or status == "Not Assessed":
                score = 5
            tankResultRef.setValForLayer(layerName, val)
            tankResultRef.setSevForLayer(layerName, score)
        
        elif layerName == "Soils":
            texture = row[1]
            val = texture
            tankResultRef.setValForLayer(layerName, val)
            tankResultRef.setSevForLayer(layerName, score)
        
        elif layerName == "ShallowGroundWater":
            depth = row[1]
            val = depth
            tankResultRef.setValForLayer(layerName, val)
            tankResultRef.setSevForLayer(layerName, score)
        
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
            tankResultRef.setValForLayer(layerName, val)
            tankResultRef.setSevForLayer(layerName, score)
                            
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
            
            if tankResultRef.getSevForLayer(layerName) < score:
                tankResultRef.setValForLayer(layerName, val)
                tankResultRef.setSevForLayer(layerName, score)           
        elif layerName == "wrpod":
            val = row[1]
            score = TankResult.distanceScore(row[1])
            tankResultRef.setValForLayer(layerName, val)
            tankResultRef.setSevForLayer(layerName, score)
            
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
    """Parent class for all risk feature types."""
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
        self.tankObjectID = "OBJECTID"
        self.tankFacilityID = "FACILITYID"
        self.outputGdb = outputGdb
        
    def createNearTable(self, tankPoints):
        """Near table used to determine distance between tank points and
        everything in this risk feature.
        - Point in polygon relationship determined by distance of 0"""
        inFeature = tankPoints
        nearTable = os.path.join(self.outputGdb, self.nearTable)
        nearFeature = self.layerPath
        nearTime = time.time()
        arcpy.GenerateNearTable_analysis (inFeature, nearFeature, nearTable)
        print "Near_{}: {}".format(self.layerPath.split(".")[-1], time.time() - nearTime)
        arcpy.JoinField_management(nearTable, self.nearTankIDField, tankPoints, self.tankObjectID, [self.tankFacilityID])
        
        
        return nearTable

        
class InPolygonFeature (RiskFeature):
    """Risk feature type where score is determined by a point in polygon
    relationship."""
    def updateTankResults(self):
        with arcpy.da.SearchCursor(in_table = self.nearTablePath, 
                           field_names = [self.tankFacilityID, self.nearDistField]) as cursor:
            for row in cursor:
                tankId = row[0]
                TankResult.updateTankValAndScore(row, self.layerName)
        
        
class DistanceFeature (RiskFeature):
    """Risk feature type where score is determined by a point distance to
    another feature."""        
    def updateTankResults(self):
        with arcpy.da.SearchCursor(in_table = self.nearTablePath, 
                           field_names = [self.tankFacilityID, self.nearDistField]) as cursor:
            for row in cursor:
                tankId = row[0]
                TankResult.updateTankValAndScore(row, self.layerName)
        

class AttributeFeature (RiskFeature):
    """Risk feature type where score is determined by a combination of 
    point in polygon, distance, and risk feature table attributes."""
    def __init__(self, featurePath, featureName, outputGdb, attributeFields):
        super(AttributeFeature, self).__init__(featurePath, featureName, outputGdb)
        self.attributeFields = attributeFields
    
    def updateTankResults(self):
        arcpy.JoinField_management(self.nearTablePath, self.nearRiskIdField, 
                                   self.layerPath, arcpy.Describe(self.layerPath).OIDFieldName, self.attributeFields)
        
        fields = [self.tankFacilityID]
        fields.extend(self.attributeFields)#attribute fields are specific to each risk feature.
        fields.append(self.nearDistField)
        with arcpy.da.SearchCursor(in_table = self.nearTablePath, 
                           field_names = fields) as cursor:
            for row in cursor:
                TankResult.updateTankValAndScore(row, self.layerName)


class TankRisk(object):
    """Primary tool class."""
    def __init__(self):
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
        if TankResult.attributesForFeature[featureName].type == TankResult.IN_POLYGON:
            return InPolygonFeature(riskFeature, featureName, Outputs.tempGdb)
        elif TankResult.attributesForFeature[featureName].type == TankResult.DISTANCE:
            return DistanceFeature(riskFeature, featureName, Outputs.tempGdb)
        elif TankResult.attributesForFeature[featureName].type == TankResult.ATTRIBUTE:
            return AttributeFeature(riskFeature, featureName, Outputs.tempGdb, 
                                    TankResult.attributesForFeature[featureName].calcFields)
        else:# Feature not in TankResult.attributesForFeature.
            return None
    
    def createOutputTable(self, resultRows):
        arcpy.CreateFileGDB_management(Outputs.outputDirectory, Outputs.outputGdbName)
        with open(os.path.join(Outputs.outputDirectory, Outputs.outputCsvName), "wb") as outCsv:
            csvWriter = csv.writer(outCsv)
            csvWriter.writerows(resultRows)
        
        arcpy.CopyRows_management(os.path.join(Outputs.outputDirectory, Outputs.outputCsvName), 
                                  os.path.join(Outputs.outputGdb, Outputs.outputTableName))
               
    def start(self, tankPnts, mapDocument):
        mapDoc = MapSource(mapDocument)
        tankPoints = tankPnts
        riskFeatures = mapDoc.getSelectedlayers()
        
        for riskFeature in riskFeatures:
            rfStartTime = time.time()
            featureName = self.parseName(riskFeature)
            if featureName == self.parseName(tankPnts):#Tank points are not a risk feature.
                continue
            if featureName not in TankResult.attributesForFeature:#The riskFeatureFactory should not receive unkown layers.
                arcpy.AddWarning("Unkown risk layer: {}".format(self.parseName(featureName)))
                continue
                    
            arcpy.AddMessage("Processing: {}".format(featureName))
            rf = self.riskFeatureFactory(riskFeature)
            self.riskFeatureNameOrder.append(rf.layerName)#Keep track of name order for output field ordering.
                
            rf.createNearTable(tankPnts)
            resultTime = time.time()
            rf.updateTankResults()
            arcpy.AddMessage("  -Completed: {} Time: {:.2f} sec".format(featureName, time.time() - rfStartTime))
            print "results: {}".format(time.time() - resultTime)
            
        resultRows = TankResult.getOutputRows(self.riskFeatureNameOrder)
        self.createOutputTable(resultRows)
        

if __name__ == '__main__':
    
    version = "0.7.1"
    testing = False
    if testing:
        mapDoc = r"..\data\test_map.mxd"
        facilityUstTankPoints = r"..\data\FACILITYUST.gdb\FACILITYUST"
        outputDir = r"..\data\outputs"
    else:
        mapDoc = "CURRENT"
        facilityUstTankPoints = arcpy.GetParameterAsText(0)
        outputDir = arcpy.GetParameterAsText(1)
    
    arcpy.AddMessage("Version {}".format(version))
    licLevel = arcpy.ProductInfo()
    if licLevel != "ArcInfo":
        print "Invalid license level: ArcGIS for Desktop Advanced required"
        arcpy.AddError("Invalid license level: ArcGIS for Desktop Advanced required")
        
    Outputs.setOutputDirectory(outputDir)
    arcpy.Delete_management(Outputs.tempDir)
    startTime = time.time()
    tankRiskAssessor = TankRisk()
    tankRiskAssessor.start(facilityUstTankPoints, mapDoc)
    arcpy.Delete_management(Outputs.tempDir)
    print time.time() - startTime
 
