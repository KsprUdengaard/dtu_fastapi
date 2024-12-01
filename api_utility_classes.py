import pandas as pd
import xgboost as xgb
import numpy as np
from abc import ABC, abstractmethod

class Transformer:
	@staticmethod
	def transform(values:list, parameter:str)->list:
		match parameter:
			case 'temperature-2m':
				values_transformed = [round(x-273.15,1) for x in values]
				return values_transformed
			case 'pressure-surface' :
				values_transformed = [round(x/100,1) for x in values]
				return values_transformed
			case 'global-radiation-flux':
				values_transformed =  [round((values[i] - values[i - 1])/3600, 1) for i in range(1, len(values))]
				values_transformed.insert(0, 0)
				return values_transformed
			case 'total-precipitation':
				values_transformed = [round(values[i] - values[i - 1],1) for i in range(1, len(values))]
				values_transformed.insert(0, 0)
				return values_transformed
			case _:
				values_transformed = [round(x,1) for x in values]
				return values_transformed


class DataProcessor(ABC):
	@abstractmethod
	def process_data():
		pass

class HistoricalWeatherDataProcessor(DataProcessor):
	def process_data(self, json_data:dict, transformer:Transformer, parameter:str)->dict:
		timestamps = [feature['properties']['from'][:13] for feature in json_data['features']]
		values = [feature['properties']['value'] for feature in json_data['features']]
		corrected_values=transformer.transform(values=values, parameter=parameter)
		return {'parameterId': parameter,
				'timestamps':timestamps, 
				'values':corrected_values}

class ForecastDataProcessor(DataProcessor):
	def process_data(self, json_data:dict, transformer:Transformer, parameter:str)->dict:
		internal_parameter = list(json_data['parameters'].keys())[0]
		timestamps = json_data.get('domain', {}).get('axes', {}).get('t', {}).get('values', [])
		spliced_timestamps = [s[:13] for s in timestamps]
		values = json_data.get('ranges', {}).get(parameter, {}).get('values', [])
		corrected_values=transformer.transform(values=values, parameter=parameter)
		return {'parameterId': parameter,
				'timestamps':spliced_timestamps, 
				'values':corrected_values}


class PricePredictor:
	def __init__(self, model_path:str)->None:
		self.model = xgb.Booster()
		self.model.load_model(model_path)
	def predict_energy_prices(self, data:dict)->dict:
		timestamps = data[0]['timestamps']
		df_dict = {'HourUTC':timestamps}
		for entry in data:
			parameter = ''
			match entry['parameterId']:
				case 'relative-humidity-2m':
					parameter = 'mean_relative_hum'
				case 'temperature-2m':
					parameter = 'mean_temp'
				case 'wind-speed-10m':
					parameter = 'mean_wind_speed'
				case 'pressure-surface':
					parameter = 'mean_pressure'
				case 'global-radiation-flux':
					parameter = 'mean_radiation'
				case 'total-precipitation':
					parameter = 'acc_precip'
				case 'low-cloud-cover':
					parameter = 'mean_cloud_cover'

			df_dict[parameter] = entry['values']

		df = pd.DataFrame(df_dict)
		df['HourUTC'] = pd.to_datetime(df['HourUTC']).astype(int) / 10**9
		dmatrix = xgb.DMatrix(df)
		predictions = self.model.predict(dmatrix)

		price_prediction = {}
		for time, price in zip(timestamps, predictions):
			price_prediction[time] = round(float(price/1000),2)
		return price_prediction


def main():
	pass
if __name__=="__main__":
	main()