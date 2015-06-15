'''
Created on May 8, 2015

@author: kwalker
'''
import arcpy, os, time

class MapSource(object):
    
    
    def __init__(self):
        pass
    
    def getSelectedlayers(self):
        mxd = arcpy.mapping.MapDocument(r"..\data\test_map.mxd")
        layerPaths = []
        for layer in arcpy.mapping.ListLayers(mxd):
            if layer.visible:
                layerPaths.append(layer.dataSource)
        del mxd
        return list(layerPaths)


class Outputs(object):
    outputDirectory = r"..\data\ouputs"
    outputGdbName =  "nears_{}.gdb".format(time.strftime("%Y%m%d%H%M%S"))
    outputGdb = os.path.join(outputDirectory, outputGdbName)
    
class LayerAttributes(object):       
    def __init__(self, type, valAttribute, sevAttribute, valFieldName, sevFieldName, calcFields = None):
        self.type = type
        self.valAttribute = valAttribute
        self.sevAttribute = sevAttribute
        self.valFieldName = valFieldName
        self.sevFieldName = sevFieldName
        self.calcFields = calcFields
    
        
class LayerConstants(object):
    IN_POLYGON = "inPolygon"
    DISTANCE = "distance"
    ATTRIBUTE = "attribute"
    layerNames = {"Aquifer_RechargeDischargeAreas": LayerAttributes(IN_POLYGON, 
                                                                 "aquiferVal", "aquiferSev", 
                                                                 "aquiferVal", "aquiferSev"),
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
                                                           "STATUS2006"), 
                    "Soils": LayerAttributes(ATTRIBUTE,
                                               "soilVal", "soilSev",
                                               "soilVal", "soilSev",
                                               "TEX_DEF"), 
                    "ShallowGroundWater": LayerAttributes(ATTRIBUTE,
                                                         "shallowWaterVal", "shallowWaterSev",
                                                         "shallowWaterVal", "shallowWaterSev",
                                                         "DEPTH"), 
                    "CensusTracts2010":LayerAttributes(ATTRIBUTE,
                                                      "censusVal", "censusSev",
                                                      "censusVal", "censusSev",
                                                      ["POP100", "AREALAND"])
                  }
    






if __name__ =="__main__":
    srcConfigs = MapSource()
    srcConfigs.getSelectedlayers()
    print "done"
    