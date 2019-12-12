# DEQ Tank Risk Assessment Tool

This project is for an ArcGIS Pro python tool that calculates a relationship between facilities with underground storage tanks with a variety of statewide environmental features.

## Usage

1. Go to releases tab and download `tank_risk_tool.*.zip` from the assets
1. Unzip the tool and add it to your pro project from the catalog pane
1. Add the following layers to your map. **Feature names must be exact.** Layers that are **not visible** will **not** be included in the analysis.
   - Aquifer_RechargeDischargeAreas
   - ShallowGroundWater
   - SurfaceWaterZones
   - StreamsNHDHighRes
   - DWQAssessmentUnits
   - Wetlands
   - CensusTracts2010
   - GroundWaterZones
   - wrpod
   - Soils
   - LakesNHDHighRes
1. Run the tool with the parameters
   - Select the Facility UST layer
   - Select the map name that has the risk factor layers
   - Choose the output folder where the risk values are stored

### Prerequisites

1. An advanced license level
