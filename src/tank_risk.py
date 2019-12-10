#!/usr/bin/env python
# * coding: utf8 *
'''
tank_risk.py
ArcGIS script tool for evaluating tank risk based on spatial relationships to other data.
'''
import csv
import os
import time

import arcpy


class MapSource():
    '''Class for accessing map document information.'''

    def __init__(self, map_document):
        self.map_document = map_document

    def get_selected_layers(self):
        mxd = arcpy.mapping.MapDocument(self.map_document)
        layer_paths = []

        for layer in arcpy.mapping.ListLayers(mxd):
            if layer.visible:
                if layer.supports('DATASOURCE'):
                    layer_paths.append(layer.dataSource)
                elif layer.supports('WORKSPACEPATH') and layer.supports('DATASETNAME'):
                    layer_paths.append(os.path.join(layer.workspacePath, layer.datasetName))
                elif layer.supports('NAME'):
                    arcpy.AddWarning('Did not find workspace: {}'.format(layer.name))
                else:
                    arcpy.AddWarning('Visible layer not supported')

        del mxd

        return list(layer_paths)

    def addLayerToMap(self, layer_path):
        mxd = arcpy.mapping.MapDocument(self.map_document)
        df = arcpy.mapping.ListDataFrames(mxd, '*')[0]

        newLayer = arcpy.mapping.Layer(layer_path)

        arcpy.mapping.AddLayer(df, newLayer, 'BOTTOM')

        del mxd
        del df
        del newLayer


class Outputs():
    '''Outputs stores all the directory and file name info.
    - setOutputDirectory initializes all attribute.'''
    unique_time_string = None

    output_directory = None
    output_gdb_name = None
    output_gdb = None
    outputTableName = None

    output_csv_name = None

    temp_dir = None
    temp_gdb_name = None
    temp_gdb = None

    @staticmethod
    def set_output_directory(output_dir):
        Outputs.unique_time_string = time.strftime('%Y%m%d%H%M%S')

        Outputs.output_directory = output_dir
        Outputs.output_gdb_name = 'TankRisk_{}.gdb'.format(Outputs.unique_time_string)
        Outputs.output_gdb = os.path.join(Outputs.output_directory, Outputs.output_gdb_name)
        Outputs.outputTableName = 'TankRiskResults_{}'.format(Outputs.unique_time_string)

        Outputs.output_csv_name = 'TankRiskResults_{}.csv'.format(Outputs.unique_time_string)

        Outputs.temp_dir = 'in_memory'
        Outputs.temp_gdb_name = 'nearsTemp_{}.gdb'.format(Outputs.unique_time_string)
        Outputs.temp_gdb = 'in_memory'


class LayerAttributes():
    '''LayerAttributes stores risk feature information in a way that
    is easy to access.'''

    def __init__(self, risk_type, value_result_attribute, severity_result_attribute, value_field, severity_field, calc_fields=None, value_method=None):
        #: type of risk feature
        self.type = risk_type
        #: attribute for value result
        self.value_result_attribute = value_result_attribute
        #: attribute for severity result
        self.severity_result_attribute = severity_result_attribute
        #: Value field name in output table
        self.value_field = value_field
        #: Severity field name in output table
        self.severity_field = severity_field
        #: Fields for attribute type risk features
        self.calc_fields = calc_fields
        #: Method to produce value. Not yet used.
        self.value_method = value_method


class TankResult():
    '''Stores everything that is specific to each risk feature including:
    - Literals (field names)
    - Logic for scoring results for each risk feature
    - Result data for each risk feature'''
    tank_results = {}
    IN_POLYGON = 'inPolygon'
    DISTANCE = 'distance'
    ATTRIBUTE = 'attribute'
    OUTPUT_ID_FIELD = 'FACILITYID'

    #: attributesForFeature associates feature names with attributes
    attributes_for_feature = {
        'Aquifer_RechargeDischargeAreas': LayerAttributes(ATTRIBUTE, 'aquiferVal', 'aquiferSev', 'aquiferVal', 'aquiferSev', ['ZONE']),
        'Wetlands': LayerAttributes(IN_POLYGON, 'wetLandsVal', 'wetLandsSev', 'wetLandsVal', 'wetLandsSev'),
        'LakesNHDHighRes': LayerAttributes(DISTANCE, 'lakesVal', 'lakeSev', 'lakesVal', 'lakeSev'),
        'StreamsNHDHighRes': LayerAttributes(DISTANCE, 'streamsVal', 'streamsSev', 'streamsVal', 'streamsSev'),
        'DWQAssessmentUnits': LayerAttributes(ATTRIBUTE, 'assessmentVal', 'assessmentSev', 'assessmentVal', 'assessmentSev', ['STATUS2006']),
        'Soils': LayerAttributes(ATTRIBUTE, 'soilVal', 'soilSev', 'soilVal', 'soilSev', ['TEX_DEF']),
        'ShallowGroundWater': LayerAttributes(ATTRIBUTE, 'shallowWaterVal', 'shallowWaterSev', 'shallowWaterVal', 'shallowWaterSev', ['DEPTH']),
        'CensusTracts2010': LayerAttributes(ATTRIBUTE, 'censusVal', 'censusSev', 'censusVal', 'censusSev', ['POP100', 'AREALAND']),
        'GroundWaterZones': LayerAttributes(ATTRIBUTE, 'udwspzVal', 'udwspzSev', 'udwspzVal', 'udwspzSev', ['ProtZone']),
        'SurfaceWaterZones': LayerAttributes(ATTRIBUTE, 'udwspzVal', 'udwspzSev', 'udwspzVal', 'udwspzSev', ['ProtZone']),
        'wrpod': LayerAttributes(
            DISTANCE,  #Also known as PointsOfDiversion
            'podVal',
            'podSev',
            'podVal',
            'podSev'
        )
    }

    def __init__(self, tank_id):
        #: FacilityUST OBJECTID
        self.tank_id = tank_id
        #: Risk layer result attributes
        for layer_name in TankResult.attributes_for_feature:
            self.__dict__[TankResult.attributes_for_feature[layer_name].value_result_attribute] = None
            self.__dict__[TankResult.attributes_for_feature[layer_name].severity_result_attribute] = None

    def set_value_for_layer(self, layer_name, value):
        self.__dict__[TankResult.attributes_for_feature[layer_name].value_result_attribute] = value

    def get_value_for_layer(self, layer_name):
        return self.__dict__[TankResult.attributes_for_feature[layer_name].value_result_attribute]

    def set_severity_for_layer(self, layer_name, severity):
        self.__dict__[TankResult.attributes_for_feature[layer_name].severity_result_attribute] = severity

    def get_severity_for_layer(self, layer_name):
        return self.__dict__[TankResult.attributes_for_feature[layer_name].severity_result_attribute]

    @staticmethod
    def get_output_rows(feature_names):
        '''Get a list that contains the rows of the output table, including header.
        - feature_names are used to order output table fields.'''
        output_rows = []
        feature_name_order_header = list(feature_names)
        feature_name_order_values = []

        #: Add header
        header_list = [TankResult.OUTPUT_ID_FIELD]

        for layer_name in feature_name_order_header:
            valFieldName = TankResult.attributes_for_feature[layer_name].value_field
            sevFieldName = TankResult.attributes_for_feature[layer_name].severity_field

            if valFieldName in header_list or sevFieldName in header_list:
                #: Two layers can share one output field and the field doesn't need to be added to twice.
                continue

            #: Make a list without shared outputs for value adding efficiency
            feature_name_order_values.append(layer_name)
            header_list.append(valFieldName)
            header_list.append(sevFieldName)

        output_rows.append(header_list)

        #: Add values
        for feature in TankResult.tank_results.values():
            temp_values = [feature.tankId]

            for layer_name in feature_name_order_values:
                temp_values.append(feature.get_value_for_layer(layer_name))
                temp_values.append(feature.set_severity_for_layer(layer_name))

            output_rows.append(temp_values)

        return output_rows

    @staticmethod
    def update_tank_value_and_score(row, layer_name):
        '''Update TankResult for the tankId contained in row parameter.
        -The items contained in a row are dependent on the particular RiskFeature layerName and type.'''
        value = 0
        score = 0
        tank_id = row[0]

        #: Get the result object for the current tankId.
        if tank_id not in TankResult.tank_results:
            TankResult.tank_results[tank_id] = TankResult(tank_id)

        tank = TankResult.tank_results[tank_id]

        if layer_name == 'Aquifer_RechargeDischargeAreas':
            value = str(row[1])

            if value == 'Discharge':
                score = 1
            elif value == 'Secondary recharge':
                score = 2
            elif value == 'Primary recharge':
                score = 5
            else:
                #: 'Bedrock recharge'
                score = 0

            tank.set_value_for_layer(layer_name, value)
            tank.set_severity_for_layer(layer_name, score)

        elif layer_name == 'Wetlands':
            value, score = TankResult.in_polygon_value_and_score(row[1])

            tank.set_value_for_layer(layer_name, value)
            tank.set_severity_for_layer(layer_name, score)

        elif layer_name == 'LakesNHDHighRes':
            value = row[1]
            score = TankResult.distance_score(row[1])

            tank.set_value_for_layer(layer_name, value)
            tank.set_severity_for_layer(layer_name, score)

        elif layer_name == 'StreamsNHDHighRes':
            value = row[1]
            score = TankResult.distance_score(row[1])

            tank.set_value_for_layer(layer_name, value)
            tank.set_severity_for_layer(layer_name, score)

        elif layer_name == 'DWQAssessmentUnits':
            status = str(row[1])
            value = status

            if status == 'Fully Supporting':
                score = 2
            elif status == 'Impaired' or status == 'Not Assessed':
                score = 5

            tank.set_value_for_layer(layer_name, value)
            tank.set_severity_for_layer(layer_name, score)

        elif layer_name == 'Soils':
            texture = row[1]
            value = texture

            tank.set_value_for_layer(layer_name, value)
            tank.set_severity_for_layer(layer_name, score)

        elif layer_name == 'ShallowGroundWater':
            depth = row[1]
            value = depth

            tank.set_value_for_layer(layer_name, value)
            tank.set_severity_for_layer(layer_name, score)

        elif layer_name == 'CensusTracts2010':
            popDensity = float(row[1]) / float(row[2])
            value = popDensity

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

            tank.set_value_for_layer(layer_name, value)
            tank.set_severity_for_layer(layer_name, score)

        elif layer_name == 'GroundWaterZones' or layer_name == 'SurfaceWaterZones':
            nearDist = row[2]
            protZone = row[1]
            value = protZone

            if nearDist != 0:
                value = 0
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

            if tank.getSevForLayer(layer_name) < score:
                tank.set_value_for_layer(layer_name, value)
                tank.set_severity_for_layer(layer_name, score)

        elif layer_name == 'wrpod':
            value = row[1]
            score = TankResult.distance_score(row[1])

            tank.set_value_for_layer(layer_name, value)
            tank.set_severity_for_layer(layer_name, score)

        return (value, score)

    @staticmethod
    def in_polygon_value_and_score(distance):
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
    def distance_score(distance):
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


class RiskFeature():
    '''Parent class for all risk feature types.'''

    def __init__(self, layer_path, layer_name, output_gdb):
        self.layer_path = layer_path
        self.layer_name = layer_name
        self.value_attribute = f'{layer_name}_val'
        self.severity_attribute = f'{layer_name}_sev'
        self.near_table = 'near_' + layer_name
        self.near_table_path = os.path.join(output_gdb, self.near_table)
        self.near_dist_field = 'NEAR_DIST'
        self.near_tank_id_field = 'IN_FID'
        self.near_risk_id_field = 'NEAR_FID'
        self.tank_id = 'OBJECTID'
        self.tank_facility_id = 'FACILITYID'
        self.output_gdb = output_gdb

    def create_near_table(self, tank_points):
        '''Near table used to determine distance between tank points and
        everything in this risk feature.
        - Point in polygon relationship determined by distance of 0'''
        in_feature = tank_points
        near_table = os.path.join(self.output_gdb, self.near_table)
        nearFeature = self.layer_path
        near_time = time.time()

        arcpy.GenerateNearTable_analysis(in_feature, nearFeature, near_table)

        print(f'Near_{self.layer_path.split(".")[-1]}: {time.time() - near_time}')

        arcpy.JoinField_management(near_table, self.near_tank_id_field, tank_points, self.tank_id, [self.tank_facility_id])

        return near_table


class InPolygonFeature(RiskFeature):
    '''Risk feature type where score is determined by a point in polygon
    relationship.'''

    def update_tank_results(self):
        with arcpy.da.SearchCursor(in_table=self.near_table_path, field_names=[self.tank_facility_id, self.near_dist_field]) as cursor:
            for row in cursor:
                tank_id = row[0]
                TankResult.update_tank_value_and_score(row, self.layer_name)


class DistanceFeature(RiskFeature):
    '''Risk feature type where score is determined by a point distance to
    another feature.'''

    def update_tank_results(self):
        with arcpy.da.SearchCursor(in_table=self.near_table_path, field_names=[self.tank_facility_id, self.near_dist_field]) as cursor:
            for row in cursor:
                tank_id = row[0]
                TankResult.update_tank_value_and_score(row, self.layer_name)


class AttributeFeature(RiskFeature):
    '''Risk feature type where score is determined by a combination of
    point in polygon, distance, and risk feature table attributes.'''

    def __init__(self, feature_path, feature_name, output_gdb, attribute_fields):
        super(AttributeFeature, self).__init__(feature_path, feature_name, output_gdb)

        self.attribute_fields = attribute_fields

    def update_tank_results(self):
        arcpy.JoinField_management(self.near_table_path, self.near_risk_id_field, self.layer_path, arcpy.Describe(self.layer_path).OIDFieldName, self.attribute_fields)

        fields = [self.tank_facility_id]

        #: attribute fields are specific to each risk feature.
        fields.extend(self.attribute_fields)
        fields.append(self.near_dist_field)

        with arcpy.da.SearchCursor(in_table=self.near_table_path, field_names=fields) as cursor:
            for row in cursor:
                TankResult.update_tank_value_and_score(row, self.layer_name)


class TankRisk():
    '''Primary tool class.'''

    def __init__(self):
        self.risk_feature_name_order = []

    def parse_name(self, risk_feature):
        file_path_ending = risk_feature.split('\\')[-1]
        file_name = file_path_ending.split('.')

        if file_name[-1].lower() == 'shp':
            return file_name[-2]
        else:
            return file_name[-1]

    def risk_feature_factory(self, risk_feature):
        featureName = self.parse_name(risk_feature)

        if TankResult.attributes_for_feature[featureName].type == TankResult.IN_POLYGON:
            return InPolygonFeature(risk_feature, featureName, Outputs.temp_gdb)
        elif TankResult.attributes_for_feature[featureName].type == TankResult.DISTANCE:
            return DistanceFeature(risk_feature, featureName, Outputs.temp_gdb)
        elif TankResult.attributes_for_feature[featureName].type == TankResult.ATTRIBUTE:
            return AttributeFeature(risk_feature, featureName, Outputs.temp_gdb, TankResult.attributes_for_feature[featureName].calc_fields)
        else:  #: Feature not in TankResult.attributesForFeature.
            return None

    def create_output_table(self, result_rows):
        arcpy.CreateFileGDB_management(Outputs.output_directory, Outputs.output_gdb_name)

        with open(os.path.join(Outputs.output_directory, Outputs.output_csv_name), 'wb') as out_csv:
            csv_writer = csv.writer(out_csv)
            csv_writer.writerows(result_rows)

        arcpy.CopyRows_management(os.path.join(Outputs.output_directory, Outputs.output_csv_name), os.path.join(Outputs.output_gdb, Outputs.outputTableName))

    def check_fields(self, risk_features):
        for risk_feature in risk_features:
            feature_name = self.parse_name(risk_feature)

            if feature_name in TankResult.attributes_for_feature and TankResult.attributes_for_feature[feature_name].type == TankResult.ATTRIBUTE:
                field_names = [field.name for field in arcpy.ListFields(risk_feature)]
                calc_fields = TankResult.attributes_for_feature[feature_name].calc_fields
                missing_field = False

                for field in calc_fields:
                    if field not in field_names:
                        arcpy.AddError(f'Field {field} not present in {feature_name}')
                        missing_field = True

                if missing_field:
                    raise ValueError('Required fields not found')

    def start(self, tank_points, map_document):
        map_doc = MapSource(map_document)
        risk_features = map_doc.get_selected_layers()

        #: Check for missing fields in attribute layers.
        try:
            self.check_fields(risk_features)
        except ValueError:
            return False

        for feature in risk_features:
            start_time = time.time()
            feature_name = self.parse_name(feature)

            if feature_name == self.parse_name(tank_points):
                #: Tank points are not a risk feature.

                continue

            if feature_name not in TankResult.attributes_for_feature:
                #: The riskFeatureFactory should not receive unknown layers.
                arcpy.AddWarning(f'Unknown risk layer: {self.parse_name(feature_name)}')

                continue

            arcpy.AddMessage(f'Processing: {feature_name}')

            risk_feature = self.risk_feature_factory(feature)
            #: Keep track of name order for output field ordering.
            self.risk_feature_name_order.append(risk_feature.layer_name)

            risk_feature.create_near_table(tank_points)
            stop_time = time.time()

            risk_feature.update_tank_results()

            arcpy.AddMessage('  -Completed: {} Time: {:.2f} sec'.format(feature_name, time.time() - start_time))

            print(f'results: {time.time() - stop_time}')

        resultRows = TankResult.get_output_rows(self.risk_feature_name_order)
        self.create_output_table(resultRows)

        return True


if __name__ == '__main__':

    version = '1.0.0'
    testing = False

    if testing:
        map_document = r'..\data\test_map.mxd'
        facility_ust_points = r'..\data\FACILITYUST.gdb\FACILITYUST'
        output_directory = r'..\data\outputs'
    else:
        map_document = 'CURRENT'
        facility_ust_points = arcpy.GetParameterAsText(0)
        output_directory = arcpy.GetParameterAsText(1)

    arcpy.AddMessage(f'Version {version}')
    licLevel = arcpy.ProductInfo()

    if licLevel != 'ArcInfo':
        print('Invalid license level: ArcGIS for Desktop Advanced required')
        arcpy.AddError('Invalid license level: ArcGIS for Desktop Advanced required')

    Outputs.set_output_directory(output_directory)
    arcpy.Delete_management(Outputs.temp_dir)

    start_time = time.time()

    tank_risk_assessor = TankRisk()
    completed = tank_risk_assessor.start(facility_ust_points, map_document)

    if completed:
        arcpy.AddMessage('Risk assessment results created')
    else:
        arcpy.AddError('Risk assessment failed')

    arcpy.Delete_management(Outputs.temp_dir)

    print(time.time() - start_time)
