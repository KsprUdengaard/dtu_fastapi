from fastapi import FastAPI
from pydantic import BaseModel
import httpx
from datetime import datetime

class WeatherRequest(BaseModel):
    parameter:str
    limit:int
    resolution:str
    time_to:str
    time_from:str

# Initialize FastAPI app
app = FastAPI()

@app.get("/")
def read_root():
    return {"message":"Conncetion to API established!"}


@app.post("/weather")
async def query_weather_api(request:WeatherRequest):
    dmi_climate_api_key="855fff42-4838-4bb1-91fd-8655bbd9ecd9"
    climate_url = (f"https://dmigw.govcloud.dk/v2/climateData/collections/countryValue/"
                    f"items?limit={request.limit}"
                    f"&timeResolution={request.resolution}"
                    f"&datetime={request.time_from}T00:00:00Z/{request.time_to}T00:00:00Z"
                    f"&parameterId={request.parameter}"
                    f"&api-key={dmi_climate_api_key}"
                    )

    async with httpx.AsyncClient() as client:
        response = await client.get(climate_url)
        
    if response.status_code == 200:
        return {"status": "success", "data": response.json()}
    else:
        return {"status": "error", "message": f"Failed to fetch data. Status code: {response.status_code}"}