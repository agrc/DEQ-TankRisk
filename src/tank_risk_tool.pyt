#!/usr/bin/env python
# * coding: utf8 *
"""
tank_risk.py
ArcGIS script tool for evaluating tank risk based on spatial relationships to other data.
"""
import csv
import os
import time

import arcpy

VERSION = "2.1.7"


def format_time(seconds):
    """seconds: number
    returns a human-friendly string describing the amount of time
    """
    minute = 60.00
    hour = 60.00 * minute

    if seconds < 30:
        return f"{int(seconds * 1000)} ms's"

    if seconds < 90:
        return f"{round(seconds, 2)} seconds"

    if seconds < 90 * minute:
        return f"{round(seconds / minute, 2)} minutes"

    return f"{round(seconds / hour, 2)} hours"


class MapSource:
    """Class for accessing map document information."""

    def __init__(self, pro_project, map_name):
        project = arcpy.mp.ArcGISProject(pro_project)
        self.risk_map = project.listMaps(map_name)[0]

    def get_selected_layers(self, messages):
        layer_paths = []

        for layer in self.risk_map.listLayers():
            if not layer.visible:
                messages.AddWarningMessage(f"Skipping {layer.name}, reason visibility")

                continue

            if layer.supports("DATASOURCE"):
                layer_paths.append(layer)
            elif layer.supports("WORKSPACEPATH") and layer.supports("DATASETNAME"):
                layer_paths.append(layer)
            elif layer.supports("NAME"):
                messages.AddWarningMessage(f"Could not find workspace: {layer.name}")
            else:
                messages.AddWarningMessage(f"{layer.name} not supported")

        return layer_paths


class Outputs:
    """Outputs stores all the directory and file name info.
    - setOutputDirectory initializes all attribute."""

    unique_time_string = None

    output_directory = None
    output_gdb_name = None
    output_gdb = None
    output_table_name = None

    output_csv_name = None

    temp_dir = None
    temp_gdb_name = None
    temp_gdb = None

    @staticmethod
    def set_output_directory(output_dir):
        Outputs.unique_time_string = time.strftime("%Y%m%d%H%M%S")

        Outputs.output_directory = output_dir
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        Outputs.output_gdb_name = "TankRisk_{}.gdb".format(Outputs.unique_time_string)
        Outputs.output_gdb = os.path.join(
            Outputs.output_directory, Outputs.output_gdb_name
        )
        Outputs.output_table_name = "TankRiskResults_{}".format(
            Outputs.unique_time_string
        )

        Outputs.output_csv_name = "TankRiskResults_{}.csv".format(
            Outputs.unique_time_string
        )

        Outputs.temp_dir = "in_memory"
        Outputs.temp_gdb_name = "nearsTemp_{}.gdb".format(Outputs.unique_time_string)
        Outputs.temp_gdb = "in_memory"


class LayerAttributes:
    """LayerAttributes stores risk feature information in a way that
    is easy to access."""

    def __init__(
        self,
        risk_type,
        value_result_attribute,
        severity_result_attribute,
        value_field,
        severity_field,
        calc_fields=None,
        value_method=None,
    ):
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


class TankResult:
    """Stores everything that is specific to each risk feature including:
    - Literals (field names)
    - Logic for scoring results for each risk feature
    - Result data for each risk feature"""

    tank_results = {}
    IN_POLYGON = "inPolygon"
    DISTANCE = "distance"
    ATTRIBUTE = "attribute"
    OUTPUT_ID_FIELD = "facilityid"

    #: attributesForFeature associates feature names with attributes
    attributes_for_feature = {
        "aquifer_recharge_discharge_areas": LayerAttributes(
            ATTRIBUTE, "aquiferVal", "aquiferSev", "aquiferVal", "aquiferSev", ["zone"]
        ),
        "Wetlands": LayerAttributes(
            IN_POLYGON, "wetLandsVal", "wetLandsSev", "wetLandsVal", "wetLandsSev"
        ),
        "lakes_nhd": LayerAttributes(
            DISTANCE, "lakesVal", "lakeSev", "lakesVal", "lakeSev"
        ),
        "streams_nhd": LayerAttributes(
            DISTANCE, "streamsVal", "streamsSev", "streamsVal", "streamsSev"
        ),
        "dwq_assessment_units": LayerAttributes(
            ATTRIBUTE,
            "assessmentVal",
            "assessmentSev",
            "assessmentVal",
            "assessmentSev",
            ["status2006"],
        ),
        "soil": LayerAttributes(
            ATTRIBUTE, "soilVal", "soilSev", "soilVal", "soilSev", ["musurftexgrp"]
        ),
        "shallow_ground_water": LayerAttributes(
            ATTRIBUTE,
            "shallowWaterVal",
            "shallowWaterSev",
            "shallowWaterVal",
            "shallowWaterSev",
            ["depth"],
        ),
        "census_tracts_2020": LayerAttributes(
            ATTRIBUTE,
            "censusVal",
            "censusSev",
            "censusVal",
            "censusSev",
            ["pop100", "aland20"],
        ),
        "GroundWaterZones": LayerAttributes(
            ATTRIBUTE, "udwspzVal", "udwspzSev", "udwspzVal", "udwspzSev", ["protzone"]
        ),
        "SurfaceWaterZones": LayerAttributes(
            ATTRIBUTE, "udwspzVal", "udwspzSev", "udwspzVal", "udwspzSev", ["protzone"]
        ),
        "points_of_diversion": LayerAttributes(
            DISTANCE, "podVal", "podSev", "podVal", "podSev"
        ),
    }

    def __init__(self, tank_id):
        #: FacilityUST OBJECTID
        self.tank_id = tank_id
        #: Risk layer result attributes
        for layer_name in TankResult.attributes_for_feature:
            self.__dict__[
                TankResult.attributes_for_feature[layer_name].value_result_attribute
            ] = None
            self.__dict__[
                TankResult.attributes_for_feature[layer_name].severity_result_attribute
            ] = None

    def set_value_for_layer(self, layer_name, value):
        self.__dict__[
            TankResult.attributes_for_feature[layer_name].value_result_attribute
        ] = value

    def get_value_for_layer(self, layer_name):
        return self.__dict__[
            TankResult.attributes_for_feature[layer_name].value_result_attribute
        ]

    def set_severity_for_layer(self, layer_name, severity):
        self.__dict__[
            TankResult.attributes_for_feature[layer_name].severity_result_attribute
        ] = severity

    def get_severity_for_layer(self, layer_name):
        return self.__dict__[
            TankResult.attributes_for_feature[layer_name].severity_result_attribute
        ]

    @staticmethod
    def get_output_rows(feature_names):
        """Get a list that contains the rows of the output table, including header.
        - feature_names are used to order output table fields."""
        output_rows = []
        feature_name_order_header = list(feature_names)
        feature_name_order_values = []

        #: Add header
        header_list = [TankResult.OUTPUT_ID_FIELD]

        for layer_name in feature_name_order_header:
            value_field = TankResult.attributes_for_feature[layer_name].value_field
            severity_field = TankResult.attributes_for_feature[
                layer_name
            ].severity_field

            if value_field in header_list or severity_field in header_list:
                #: Two layers can share one output field and the field doesn't need to be added to twice.
                continue

            #: Make a list without shared outputs for value adding efficiency
            feature_name_order_values.append(layer_name)
            header_list.append(value_field)
            header_list.append(severity_field)

        output_rows.append(header_list)

        #: Add values
        for feature in TankResult.tank_results.values():
            temp_values = [feature.tank_id]

            for layer_name in feature_name_order_values:
                temp_values.append(feature.get_value_for_layer(layer_name))
                temp_values.append(feature.get_severity_for_layer(layer_name))

            output_rows.append(temp_values)

        return output_rows

    @staticmethod
    def update_tank_value_and_score(row, layer_name):
        """Update TankResult for the tankId contained in row parameter.
        -The items contained in a row are dependent on the particular RiskFeature layerName and type.
        """
        value = 0
        score = 0
        tank_id = row[0]

        #: Get the result object for the current tankId.
        if tank_id not in TankResult.tank_results:
            TankResult.tank_results[tank_id] = TankResult(tank_id)

        tank = TankResult.tank_results[tank_id]

        if layer_name == "aquifer_recharge_discharge_areas":
            value = str(row[1])

            if value == "Discharge":
                score = 1
            elif value == "Secondary recharge":
                score = 2
            elif value == "Primary recharge":
                score = 5
            else:
                #: 'Bedrock recharge'
                score = 0

            tank.set_value_for_layer(layer_name, value)
            tank.set_severity_for_layer(layer_name, score)

        elif layer_name == "Wetlands":
            value, score = TankResult.in_polygon_value_and_score(row[1])

            tank.set_value_for_layer(layer_name, value)
            tank.set_severity_for_layer(layer_name, score)

        elif layer_name == "lakes_nhd":
            value = row[1]
            score = TankResult.distance_score(row[1])

            tank.set_value_for_layer(layer_name, value)
            tank.set_severity_for_layer(layer_name, score)

        elif layer_name == "streams_nhd":
            value = row[1]
            score = TankResult.distance_score(row[1])

            tank.set_value_for_layer(layer_name, value)
            tank.set_severity_for_layer(layer_name, score)

        elif layer_name == "dwq_assessment_units":
            status = str(row[1])
            value = status

            if status == "Fully Supporting":
                score = 2
            elif status == "Impaired" or status == "Not Assessed":
                score = 5

            tank.set_value_for_layer(layer_name, value)
            tank.set_severity_for_layer(layer_name, score)

        elif layer_name == "soil":
            texture = row[1]
            if texture is None:
                tank.set_value_for_layer(layer_name, "No data")
                tank.set_severity_for_layer(layer_name, 5)

                return ("No data", 5)

            value = texture.casefold()

            if "gravel" in value:
                score = 5
            elif "cobb" in value:
                score = 5
            elif "ston" in value:
                score = 5
            elif "frag" in value:
                score = 5
            elif "bould" in value:
                score = 5
            elif "course" in value:
                score = 5
            elif len(value.strip()) == 0:
                score = 5
            elif "sand" in value:
                score = 4
            elif "flag" in value:
                score = 3
            elif "channer" in value:
                score = 3
            elif "varia" in value:
                score = 3
            elif value == "loam":
                score = 3
            elif "ashy" in value:
                score = 3
            elif "shaly" in value:
                score = 2
            elif "silt" in value:
                score = 2
            elif "plant" in value:
                score = 2
            elif "pea" in value:
                score = 2
            elif "clay" in value:
                score = 1
            elif "bedr" in value:
                score = 1
            else:
                score = 5

            tank.set_value_for_layer(layer_name, value)
            tank.set_severity_for_layer(layer_name, score)

        elif layer_name == "shallow_ground_water":
            depth = row[1]
            value = depth

            if value == 0:
                score = 5
            elif value == 10:
                score = 2.5
            elif value == 30:
                score = 1
            else:
                score = 0

            tank.set_value_for_layer(layer_name, value)
            tank.set_severity_for_layer(layer_name, score)

        elif layer_name == "census_tracts_2020":
            value = float(row[1]) / float(row[2])

            if value > 0.00181:
                score = 5
            elif value > 0.00108:
                score = 4
            elif value > 0.0000274:
                score = 3
            elif value > 0.00000723:
                score = 2
            elif value > 0.0:
                score = 1
            else:
                score = 0

            tank.set_value_for_layer(layer_name, value)
            tank.set_severity_for_layer(layer_name, score)

        elif layer_name == "GroundWaterZones" or layer_name == "SurfaceWaterZones":
            near_distance = row[2]
            protection_zone = row[1]
            value = protection_zone

            if near_distance != 0:
                value = 0
                score = 0
            elif protection_zone == 4:
                score = 2
            elif protection_zone == 3:
                score = 3
            elif protection_zone == 2:
                score = 4
            elif protection_zone == 1:
                score = 5
            else:
                score = 0

            if (
                not tank.get_severity_for_layer(layer_name)
                or tank.get_severity_for_layer(layer_name) < score
            ):
                tank.set_value_for_layer(layer_name, value)
                tank.set_severity_for_layer(layer_name, score)

        elif layer_name == "points_of_diversion":
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


class RiskFeature:
    """Parent class for all risk feature types."""

    def __init__(self, layer_path, layer_name, output_gdb):
        self.layer_path = layer_path
        self.layer_name = layer_name
        self.value_attribute = f"{layer_name}_val"
        self.severity_attribute = f"{layer_name}_sev"
        self.near_table = "near_" + layer_name
        self.near_table_path = os.path.join(output_gdb, self.near_table)
        self.near_dist_field = "NEAR_DIST"
        self.near_tank_id_field = "IN_FID"
        self.near_risk_id_field = "NEAR_FID"
        self.tank_id = arcpy.Describe(layer_path).OIDFieldName
        self.tank_facility_id = "facilityid"
        self.output_gdb = output_gdb

    def create_near_table(self, tank_points):
        """Near table used to determine distance between tank points and
        everything in this risk feature.
        - Point in polygon relationship determined by distance of 0"""
        in_feature = tank_points
        near_table = os.path.join(self.output_gdb, self.near_table)
        near_feature = self.layer_path

        arcpy.GenerateNearTable_analysis(in_feature, near_feature, near_table)
        tank_join_id = arcpy.Describe(tank_points).OIDFieldName
        arcpy.JoinField_management(
            near_table,
            self.near_tank_id_field,
            tank_points,
            tank_join_id,
            [self.tank_facility_id],
        )

        return near_table


class InPolygonFeature(RiskFeature):
    """Risk feature type where score is determined by a point in polygon
    relationship."""

    def update_tank_results(self):
        with arcpy.da.SearchCursor(
            in_table=self.near_table_path,
            field_names=[self.tank_facility_id, self.near_dist_field],
        ) as cursor:
            for row in cursor:
                self.tank_id = row[0]
                TankResult.update_tank_value_and_score(row, self.layer_name)


class DistanceFeature(RiskFeature):
    """Risk feature type where score is determined by a point distance to
    another feature."""

    def update_tank_results(self):
        with arcpy.da.SearchCursor(
            in_table=self.near_table_path,
            field_names=[self.tank_facility_id, self.near_dist_field],
        ) as cursor:
            for row in cursor:
                self.tank_id = row[0]
                TankResult.update_tank_value_and_score(row, self.layer_name)


class AttributeFeature(RiskFeature):
    """Risk feature type where score is determined by a combination of
    point in polygon, distance, and risk feature table attributes."""

    def __init__(self, feature_path, feature_name, output_gdb, attribute_fields):
        super(AttributeFeature, self).__init__(feature_path, feature_name, output_gdb)

        self.attribute_fields = attribute_fields

    def update_tank_results(self):
        arcpy.JoinField_management(
            self.near_table_path,
            self.near_risk_id_field,
            self.layer_path,
            arcpy.Describe(self.layer_path).OIDFieldName,
            self.attribute_fields,
        )

        fields = [self.tank_facility_id]

        #: attribute fields are specific to each risk feature.
        fields.extend(self.attribute_fields)
        fields.append(self.near_dist_field)

        with arcpy.da.SearchCursor(
            in_table=self.near_table_path, field_names=fields
        ) as cursor:
            for row in cursor:
                TankResult.update_tank_value_and_score(row, self.layer_name)


class TankRisk:
    """Primary tool class."""

    def __init__(self):
        self.risk_feature_name_order = []
        self.label = "Tank Risk Assessor"
        self.description = (
            "Evaluate tank risk based on spatial relationships to other data"
        )
        self.canRunInBackground = False

    def getParameterInfo(self):
        facility_ust_points = arcpy.Parameter(
            displayName="Petroleum Storage Tank Facilities Points",
            name="facility_ust_points",
            datatype="GPLayer",
            parameterType="Required",
            direction="Input",
        )

        map_name = arcpy.Parameter(
            displayName="Map Name",
            name="map_name",
            datatype="GPMap",
            parameterType="Required",
            direction="Input",
        )

        output_directory = arcpy.Parameter(
            displayName="Output Folder",
            name="output_directory",
            datatype="DEFolder",
            parameterType="Required",
            direction="Input",
        )

        params = [facility_ust_points, map_name, output_directory]

        return params

    def isLicensed(self):
        """Set whether tool is licensed to execute."""
        license_level = arcpy.ProductInfo()

        return license_level == "ArcInfo"

    def updateParameters(self, parameters):
        """Modify the values and properties of parameters before internal
        validation is performed.  This method is called whenever a parameter
        has been changed."""

        return

    def updateMessages(self, parameters):
        """Modify the messages created by internal validation for each tool
        parameter.  This method is called after internal validation."""
        return

    def execute(self, parameters, messages):
        facility_ust_points = parameters[0].value
        map_name = parameters[1].value
        output_directory = str(parameters[2].value)

        messages.AddMessage(f"Version {VERSION}")

        Outputs.set_output_directory(output_directory)
        arcpy.Delete_management(Outputs.temp_dir)

        start_time = time.time()

        tank_risk_assessor = TankRisk()
        completed = tank_risk_assessor.start(
            facility_ust_points, "CURRENT", map_name, messages
        )

        if completed:
            messages.AddMessage("Risk assessment results created successfully")
        else:
            messages.AddErrorMessage("Risk assessment failed")

        arcpy.Delete_management(Outputs.temp_dir)

        messages.AddMessage(
            f"Total processing time {format_time(time.time() - start_time)}"
        )

    def parse_name(self, layer):
        layer_lookup = {
            #: arcgis online services
            "https://services1.arcgis.com/99lidphwczftie9k/arcgis/rest/services/facilitypst/featureserver/0": "tanks",
            "https://services.arcgis.com/zzrwjtrez6fjioq4/arcgis/rest/services/utah_points_of_diversion/featureserver/0": "points_of_diversion",
            "https://services1.arcgis.com/99lidphwczftie9k/arcgis/rest/services/soils/featureserver/0": "soil",
            "https://services1.arcgis.com/99lidphwczftie9k/arcgis/rest/services/aquifer_rechargedischargeareas/featureserver/0": "aquifer_recharge_discharge_areas",
            "https://fwspublicservices.wim.usgs.gov/wetlandsmapservice/rest/services/wetlands/mapserver/0": "Wetlands",
            "https://services1.arcgis.com/99lidphwczftie9k/arcgis/rest/services/dwqassessmentunits/featureserver/0": "dwq_assessment_units",
            "https://services1.arcgis.com/99lidphwczftie9k/arcgis/rest/services/shallowgroundwater/featureserver/0": "shallow_ground_water",
            "https://services1.arcgis.com/99lidphwczftie9k/arcgis/rest/services/censustracts2020/featureserver/0": "census_tracts_2020",
            "https://services1.arcgis.com/99lidphwczftie9k/arcgis/rest/services/utahlakesnhd/featureserver/0": "lakes_nhd",
            "https://services1.arcgis.com/99lidphwczftie9k/arcgis/rest/services/utahstreamsnhd/featureserver/0": "streams_nhd",
            "https://services2.arcgis.com/nnxp4lz3zx8wwmp9/arcgis/rest/services/utah_ddw_groundwater_source_protection_zones/featureserver/4": "GroundWaterZones",
            #: open sgid tables
            "petroleum_storage_tank_facilities": "tanks",
            "soils": "soil",
            "aquifer_recharge_discharge_areas": "aquifer_recharge_discharge_areas",
            "dwq_assessment_units": "dwq_assessment_units",
            "shallow_ground_water": "shallow_ground_water",
            "census_tracts_2020": "census_tracts_2020",
            "lakes_nhd": "lakes_nhd",
            "streams_nhd": "streams_nhd",
            #: file gdb tables
            "ut_wetlands": "Wetlands",
            "groundwaterzones": "GroundWaterZones",
            "surfacewaterzones": "SurfaceWaterZones",
        }

        if not layer.isFeatureLayer:
            return

        if layer.isWebLayer:
            if layer.dataSource.casefold() in layer_lookup:
                return layer_lookup[layer.dataSource.casefold()]

        props = layer.connectionProperties
        if props["workspace_factory"] == "File Geodatabase":
            dataset = props["dataset"].casefold()

            if dataset in layer_lookup:
                return layer_lookup[dataset]

        if props["workspace_factory"] == "SDE":
            if (
                props["connection_info"]["db_connection_properties"]
                != "opensgid.agrc.utah.gov"
            ):
                return

            dataset = props["dataset"]
            table_name = dataset.split(".")[-1:][0].strip("%")

            if table_name in layer_lookup:
                return layer_lookup[table_name]

        return

    def parse_name_old(self, risk_feature):
        file_name = risk_feature.split(".")

        if file_name[-1].lower() == "shp":
            return file_name[-2]
        else:
            return file_name[-1]

    def risk_feature_factory(self, risk_feature):
        feature_name = self.parse_name(risk_feature)

        if (
            TankResult.attributes_for_feature[feature_name].type
            == TankResult.IN_POLYGON
        ):
            return InPolygonFeature(risk_feature, feature_name, Outputs.temp_gdb)
        elif (
            TankResult.attributes_for_feature[feature_name].type == TankResult.DISTANCE
        ):
            return DistanceFeature(risk_feature, feature_name, Outputs.temp_gdb)
        elif (
            TankResult.attributes_for_feature[feature_name].type == TankResult.ATTRIBUTE
        ):
            return AttributeFeature(
                risk_feature,
                feature_name,
                Outputs.temp_gdb,
                TankResult.attributes_for_feature[feature_name].calc_fields,
            )
        else:
            #: Feature not in TankResult.attributesForFeature.

            return None

    def create_output_table(self, result_rows):
        arcpy.CreateFileGDB_management(
            Outputs.output_directory, Outputs.output_gdb_name
        )

        with open(
            os.path.join(Outputs.output_directory, Outputs.output_csv_name),
            "w",
            newline="",
        ) as out_csv:
            csv_writer = csv.writer(out_csv, quoting=csv.QUOTE_MINIMAL)
            csv_writer.writerows(result_rows)

        arcpy.CopyRows_management(
            os.path.join(Outputs.output_directory, Outputs.output_csv_name),
            os.path.join(Outputs.output_gdb, Outputs.output_table_name),
        )

    def check_fields(self, risk_features, messages):
        for risk_feature in risk_features:
            feature_name = self.parse_name(risk_feature)

            if (
                feature_name in TankResult.attributes_for_feature
                and TankResult.attributes_for_feature[feature_name].type
                == TankResult.ATTRIBUTE
            ):
                field_names = [
                    field.name.lower() for field in arcpy.ListFields(risk_feature)
                ]
                calc_fields = TankResult.attributes_for_feature[
                    feature_name
                ].calc_fields
                missing_field = False

                for field in calc_fields:
                    if field not in field_names:
                        messages.AddError(
                            f"Field {field} not present in {feature_name}"
                        )
                        missing_field = True

                if missing_field:
                    raise ValueError("Required fields not found")

    def start(self, tank_points, pro_project, map_name, messages):
        map_doc = MapSource(pro_project, map_name)
        risk_features = map_doc.get_selected_layers(messages)

        #: Check for missing fields in attribute layers.
        try:
            self.check_fields(risk_features, messages)
        except ValueError:
            return False

        for feature in risk_features:
            single_risk = time.time()
            feature_name = self.parse_name(feature)

            if feature_name == self.parse_name(tank_points):
                #: Tank points are not a risk feature.

                continue

            if feature_name not in TankResult.attributes_for_feature:
                #: The riskFeatureFactory should not receive unknown layers.
                messages.AddWarningMessage(f"Unknown risk layer {feature}")

                continue

            messages.AddMessage(f"Calculating risks from {feature_name}")

            risk_feature = self.risk_feature_factory(feature)
            #: Keep track of name order for output field ordering.
            self.risk_feature_name_order.append(risk_feature.layer_name)

            risk_feature.create_near_table(tank_points)
            risk_feature.update_tank_results()

            messages.AddMessage(
                f"{feature_name} risks calculated in {format_time(time.time() - single_risk)}"
            )

        result_rows = TankResult.get_output_rows(self.risk_feature_name_order)
        self.create_output_table(result_rows)

        return True


class Toolbox:
    def __init__(self):
        self.label = "Tank Risk"
        self.alias = "Tank Risk"

        # List of tool classes associated with this toolbox
        self.tools = [TankRisk]
