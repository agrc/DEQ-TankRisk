# DEQ-TankRisk

## DEQ Tank Risk Assessment Tool

ArcMap tool that calculates a relationship between facilities with underground storage tanks and a variety of statewide environmental features.

**Requires ArcGIS for Desktop Advanced license level.**

tank_risk.py

- Implements the Risk Assessment tool.
- Must be imported into the Risk Assessment script tool through ArcCatalog before being distributed.

### ArcGIS toolbox

Tank Risk Tools.tbx

- Contains the Risk Assessment tool.
- Result table will be created in output directory in Geodatabase table and CSV format.

### Recognized Features

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

**Feature names must be exact.**
