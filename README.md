# DEQ Tank Risk Assessment Tool

This project is for an ArcGIS Pro python tool that calculates a relationship between facilities with underground storage tanks with a variety of statewide environmental features.

## Usage

1. Go to releases tab and download `tank_risk_tool.*.zip` from the assets
1. Unzip the tool and add it to your pro project from the catalog pane
1. Add the following layers to your map from the Open SGID or ArcGIS Online. Layers that are **not visible** will **not** be included in the analysis.
   - Facility PST
   - Aquifer Recharge Discharge Areas
   - Shallow Ground Water
   - SurfaceWaterZones **Feature name must be exact and available in a local file geodatabase.**
   - Streams NHD
   - DWQ Assessment Units
   - Wetlands
   - Census Tracts 2020
   - GroundWaterZones
   - Points of Diversion
   - Soils
   - Lakes NHD
1. Run the tool with the parameters
   - Select the Facility PST layer
   - Select the map name that has the risk factor layers
   - Choose the output folder where the risk values are stored

### Prerequisites

1. An advanced license level

## Development

1. Create a conda environment
   - `conda create -n tank arcpy-base && activate tank`
1. Add some packages
   - `pip install -r requirements.txt`
1. Create a TaskRisk ProProject (or use the one provided) and have a blank RiskMap
1. With the aprx closed, add data to the map
   - `python src\preprocess\preprocessing.py`
1. Assert that the risk map coordinate system is UTM Zone 12 North
   - ![image](https://user-images.githubusercontent.com/325813/230181252-cd362df2-f0b3-4ff5-9af8-e1819a430deb.png)
1. Either symlinkn or duplicate the `tank_risk_tool.pyt` `to tank_risk.py` so the cli can import it
1. Run the cli

