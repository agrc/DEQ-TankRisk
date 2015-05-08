'''
Created on May 8, 2015

@author: kwalker
'''
import arcpy, os

class source(object):
    
    
    def __init__(self):
        pass
    
    def getSelectedlayers(self):
        mxd = arcpy.mapping.MapDocument(r"C:\Users\Administrator\My Documents\Aptana Studio 3 Workspace\DEQ-TankRisk\data\test_map.mxd")
        layerPaths = []
        for layer in arcpy.mapping.ListLayers(mxd):
            if layer.visible:
                layerPaths.append(layer.dataSource)
        del mxd
        return list(layerPaths)




if __name__ =="__main__":
    srcConfigs = source()
    srcConfigs.getSelectedlayers()
    print "done"
    