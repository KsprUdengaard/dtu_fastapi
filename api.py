from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import httpx
import logging
from datetime import datetime
from typing import List, Union
from api_utility_classes import *

class WeatherRequest(BaseModel):
    parameter:str
    limit:int
    resolution:str
    time_to:str
    time_from:str

class MultipleWeatherRequests(BaseModel):
    items: List[WeatherRequest]

class EnergyRequest(BaseModel):
    pass

class ForecastRequest(BaseModel):
    coords:str
    crs:str
    parameter:str


# Initialize FastAPI app
app = FastAPI()

@app.get("/")
def read_root():
    return {"message":"Conncetion to API established!"}


@app.post("/weather")
async def query_weather_api(request:Union[WeatherRequest, MultipleWeatherRequests]):
    dmi_climate_api_key="855fff42-4838-4bb1-91fd-8655bbd9ecd9"
    climate_url = "https://dmigw.govcloud.dk/v2/climateData/collections/countryValue/items?"
    async def fetch_weather_data(weather_request:WeatherRequest):
        climate_params = {
                      "limit":weather_request.limit,
                      "timeResolution":weather_request.resolution,
                      "datetime":f"{weather_request.time_from}T00:00:00Z/{weather_request.time_to}T00:00:00Z",
                      "parameterId":weather_request.parameter,
                      "api-key":dmi_climate_api_key
                    }        
        async with httpx.AsyncClient() as client:
            response = await client.get(climate_url, params=climate_params)
            if response.status_code !=200:
                raise HTTPException(status_code=response.status_code, detail=response.text)
            response_data = response.json()
            timestamps = [feature['properties']['from'][:13] for feature in response_data['features']]
            values = [feature['properties']['value'] for feature in response_data['features']]
            return {'parameterId': weather_request.parameter,
                    'timestamps':timestamps, 
                    'values':values}

    if isinstance(request, WeatherRequest):
        return await fetch_weather_data(request)
    elif isinstance(request, MultipleWeatherRequests):
        results = []
        for item in request.items:
            result = await fetch_weather_data(item)
            print(result)
            results.append(result)
        return {'results': results}


@app.post("/energy")
async def query_energy_api(request:EnergyRequest):
    pass


@app.post("/forecast")
async def query_forecast_api(request:ForecastRequest): 
    dmi_forcast_api_key = '37d18777-8ab0-44c9-bb26-113e6925338d'
    forecast_url = 'https://dmigw.govcloud.dk/v1/forecastedr/collections/harmonie_dini_sf/position'
    forecast_params = {
                        'coords':request.coords,
                        'crs':request.crs,
                        'parameter-name':request.parameter,
                        'api-key':dmi_forcast_api_key
                        }
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(forecast_url, params=forecast_params)
            logging.info(f"Status Code: {response.status_code}")  # Debugging info
        if response.status_code !=200:
            return JSONResponse({
                "status": "error",
                "message": f"Failed to fetch data. HTTP Status Code: {response.status_code}",
                "response": response.text,  # Include raw response for debugging
            },
            status_code=response.status_code
            ) 
        else:
            response_data = response.json()
            return response_data

    except httpx.RequestError as e:
        # Handle network-related errors
        raise HTTPException(status_code=503, detail=f"Network error occurred: {str(e)}")
    except KeyError as e:
        # Handle missing keys in the response
        raise HTTPException(status_code=500, detail=f"Malformed response from API: {str(e)}")
    except Exception as e:
        # Catch-all for unexpected errors
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")

def main():
    pass

if __name__=="__main__":
    main()