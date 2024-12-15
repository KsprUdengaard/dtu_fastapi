from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import httpx
import pandas as pd
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

class ModelRequest(BaseModel):
    gamma:float
    eta:float
    colsample:float
    max_depth:int
    subsample:float
    min_child_weight:int

class ForecastRequest(BaseModel):
    coords:str
    crs:str
    parameter:str

class MultipleForecastRequests(BaseModel):
    items: List[ForecastRequest]


# Initialize FastAPI app
app = FastAPI()

@app.get("/")
def read_root():
    return {"message":"Conncetion to API established!"}


@app.get("/weather")
async def query_weather_api(request:Union[WeatherRequest, MultipleWeatherRequests]):
    dmi_climate_api_key="855fff42-4838-4bb1-91fd-8655bbd9ecd9"
    climate_url = "https://dmigw.govcloud.dk/v2/climateData/collections/countryValue/items?"
    processor = HistoricalWeatherDataProcessor()
    transformer = Transformer()
    async def fetch_weather_data(weather_request:WeatherRequest):
        print(weather_request.parameter)
        print(weather_request.time_from)
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
            else:
                return processor.process_data(json_data=response.json(), 
                                          transformer=transformer, 
                                          parameter=weather_request.parameter)

    if isinstance(request, WeatherRequest):
        return await fetch_weather_data(request)
    elif isinstance(request, MultipleWeatherRequests):
        results = []
        for item in request.items:
            result = await fetch_weather_data(item)
            results.append(result)
        return {'results': results}

@app.get("/forecast")
async def query_forecast_api(request:Union[ForecastRequest, MultipleForecastRequests]): 
    dmi_forcast_api_key = '37d18777-8ab0-44c9-bb26-113e6925338d'
    forecast_url = 'https://dmigw.govcloud.dk/v1/forecastedr/collections/harmonie_dini_sf/position'
    transformer = Transformer()
    processor = ForecastDataProcessor()
    preditor = PricePredictor('xgboost_model.json')
    async def fetch_forecast_data(forecast_request:ForecastRequest):
        print(forecast_request.parameter)
        forecast_params = {
                            'coords':forecast_request.coords,
                            'crs':forecast_request.crs,
                            'parameter-name':forecast_request.parameter,
                            'api-key':dmi_forcast_api_key
                            }
        async with httpx.AsyncClient() as client:
            full_url = client.build_request("GET", forecast_url, params=forecast_params).url
            print(full_url)
            response = await client.get(forecast_url, params=forecast_params)
            if response.status_code !=200:
                raise HTTPException(status_code=response.status_code, detail=response.text)
            else:
                return processor.process_data(json_data=response.json(),
                                                transformer=transformer,
                                                parameter=forecast_request.parameter)

    if isinstance(request, ForecastRequest):
        result = await fetch_forecast_data(request)
        return {'results':result}
    elif isinstance(request, MultipleForecastRequests):
        results = []
        for item in request.items:
            result = await fetch_forecast_data(item)
            results.append(result)

        
        spot_prices = preditor.predict_energy_prices(results)   
        return {'results': results, 'SpotPriceDKK':spot_prices}


@app.post("/model")
async def query_energy_api(request:ModelRequest):
    trainer = EnergyPriceModelTrainer()
    data = pd.read_csv('data_collection - Copy.csv') 
    print(request)
    train_model = trainer.train_model(data, 
                        request.gamma,
                        request.max_depth,
                        request.eta,
                        request.subsample,
                        request.colsample,
                        request.min_child_weight
                        )
    return train_model
    
def main():
    pass

if __name__=="__main__":
    main()