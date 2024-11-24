from fastapi import FastAPI
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import httpx
import logging
from datetime import datetime

class WeatherRequest(BaseModel):
    parameter:str
    limit:int
    resolution:str
    time_to:str
    time_from:str

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
async def query_weather_api(request:WeatherRequest):
    dmi_climate_api_key="855fff42-4838-4bb1-91fd-8655bbd9ecd9"
    climate_url = "https://dmigw.govcloud.dk/v2/climateData/collections/countryValue/items?"
    climate_params = {
                      "limit":request.limit,
                      "timeResolution":request.resolution,
                      "datetime":f"{request.time_from}T00:00:00Z/{request.time_to}T00:00:00Z",
                      "parameterId":request.parameter,
                      "api-key":dmi_climate_api_key
                    }

    async with httpx.AsyncClient() as client:
        response = await client.get(climate_url, params=climate_params)
        print(f"Status Code: {response.status_code}")  # Debugging info
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
        return response_data['features']


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

    async with httpx.AsyncClient() as client:
        response = await client.get(forecast_url, params=forecast_params)
        #logging.info(response.url)
        
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

def main():
    pass

if __name__=="__main__":
    main()