'''
Created on May 8, 2015

@author: kwalker
'''
import arcpy, os, time

class MapSource(object):
    
    
    def __init__(self, tankPoints, mapDocument):
        self.tankPoints = tankPoints#r"Database Connections\agrc@SGID10@gdb10.agrc.utah.sde\SGID10.ENVIRONMENT.FACILITYUST"
        self.mapDoc = mapDocument
        pass
    
    def getSelectedlayers(self):
        mxd = arcpy.mapping.MapDocument(self.mapDoc)
        layerPaths = []
        for layer in arcpy.mapping.ListLayers(mxd):
            if layer.visible:
                layerPaths.append(layer.dataSource)
        del mxd
        return list(layerPaths)

# class MapSource(object):
#     
#     
#     def __init__(self):
#         self.tankPoints = r"Database Connections\agrc@SGID10@gdb10.agrc.utah.sde\SGID10.ENVIRONMENT.FACILITYUST"
#         pass
#     
#     def getSelectedlayers(self):
#         mxd = arcpy.mapping.MapDocument(r"..\data\test_map.mxd")
#         layerPaths = []
#         for layer in arcpy.mapping.ListLayers(mxd):
#             if layer.visible:
#                 layerPaths.append(layer.dataSource)
#         del mxd
#         return list(layerPaths)


class Outputs(object):
    outputDirectory = r"..\data\outputs"
    uniqueTimeString = time.strftime("%Y%m%d%H%M%S")
    
    outputGdbName = "TankRisk_{}.gdb".format(uniqueTimeString)
    os.path.join(outputDirectory, outputGdbName)
    
    tempGdbName =  "nears_{}.gdb".format(uniqueTimeString)
    tempGdb = os.path.join(outputDirectory, tempGdbName)
    tempCsv = "tempCsv_{}.csv".format(uniqueTimeString)
    
class LayerAttributes(object):       
    def __init__(self, type, valAttribute, sevAttribute, valFieldName, sevFieldName, calcFields = None, valMethod = None):
        self.type = type
        self.valAttribute = valAttribute
        self.sevAttribute = sevAttribute
        self.valFieldName = valFieldName
        self.sevFieldName = sevFieldName
        self.calcFields = calcFields
        self.valMethod = valMethod
    
    



if __name__ =="__main__":
    srcConfigs = MapSource()
    srcConfigs.getSelectedlayers()
    print "done"
    