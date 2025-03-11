# Headwaters Hydrology Project API

An API to deliver streamflow predictions from the Headwaters Hydrology Project ML model for ungaged basins across the contiguous USA.  

## License
The HHP is licensed under the [Creative Commons Attribution-NonCommercial 4.0 International License](https://creativecommons.org/licenses/by-nc/4.0/).

## Contact  
- **Name:** Zachary Hoylman, Colin Brust
- **Organization:** Montana Climate Office, University of Montana
- **Website:** [https://climate.umt.edu](https://climate.umt.edu/)  
- **Email:** [zachary.hoylman@mso.umt.edu](mailto:zachary.hoylman@mso.umt.edu), [colin.brust@mso.umt.edu](mailto:colin.brust@mso.umt.edu)

## Base URL  
[https://data.climate.umt.edu/streamflow-api](https://data.climate.umt.edu/streamflow-api)

## Endpoints  

### **1. Get Predictions**  
**Endpoint:** `/predictions`  
**Description:** Get streamflow predictions for a given location and date range. Data is aggregated across all 10 k-fold models using median as the default aggregation function. Other aggregation functions can be specified using the `aggregations` query parameter.

#### Query Parameters  
- `aggregations` _(optional)_: Aggregation function(s) (e.g., `min`, `max`, `mean`, `median`, `stddev`, `iqr`).  
- `locations` _(optional)_: HUC10 ID(s) for data retrieval.  
- `latitude` _(optional)_: Latitude(s) of the region of interest.  
- `longitude` _(optional)_: Longitude(s) of the region of interest.  
- `date_start` _(optional, default: `1980-01-01`)_: Start date for predictions.  
- `date_end` _(optional, default: `2100-01-01`)_: End date for predictions.  
- `units` _(optional, default: `cfs`)_: Streamflow units (`cfs` or `mm`).  
- `version` _(optional, default: `vPUB2025`)_: Model version.  
- `as_csv` _(optional, default: `false`)_: Return data as CSV (`true` or `false`).  

#### Responses  
- **200:** Successful response with JSON data.  
- **422:** Validation error.  

---

### **2. Get Raw Predictions**  
**Endpoint:** `/predictions/raw`  
**Description:** Get streamflow predictions for a given location and date range. This endpoint returns the raw predictions from the 10 k-fold models without any aggregation.

#### Query Parameters  
(Same as `/predictions`, excluding `aggregations`.)  

#### Responses  
- **200:** Successful response with raw JSON data.  
- **422:** Validation error.  

---

### **3. Get Latest Predictions**  
**Endpoint:** `/predictions/latest`  
**Description:** Get the latest streamflow predictions for all locations. Data is aggregated across all 10 k-fold models using median as the default aggregation function. Other aggregation functions can be specified using the `aggregations` query parameter.

#### Query Parameters  
- `aggregations` _(optional)_: Aggregation function(s) (e.g., `min`, `max`, `mean`, `median`, `stddev`, `iqr`).  
- `as_csv` _(optional, default: `false`)_: Return data as CSV (`true` or `false`).  

#### Responses  
- **200:** Successful response with JSON data.  
- **422:** Validation error.  


## Data Models  

### **ReturnPredictions**  
- `location` _(array of strings)_: Locations of predictions.  
- `date` _(array of dates)_: Dates of predictions.  
- `version` _(array of strings)_: Model version used.  
- `metric` _(array of strings)_: Aggregation metric applied.  
- `value` _(array of numbers)_: Predicted streamflow values.  

### **RawReturnPredictions**  
- `location` _(array of strings)_: Locations of predictions.  
- `date` _(array of dates)_: Dates of predictions.  
- `version` _(array of strings)_: Model version used.  
- `model_no` _(array of integers)_: Model number identifier.  
- `value` _(array of numbers)_: Predicted streamflow values.  

### **Streamflow Units**  
- `mm` _(millimeters)_  
- `cfs` _(cubic feet per second)_  

### **Versions**  
- `v1.0`  
- `vPUB2025`  
