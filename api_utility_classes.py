import pandas as pd
from abc import ABC, abstractmethod

class Transformer:
	@staticmethod
	def transform(df:pd.DataFrame, parameter:str)->pd.DataFrame:
		match parameter:
			case 'temperature-2m':
				df_transformed = round(df-273.15,1)
				return df_transformed
			case 'pressure-surface' :
				df_transformed = round(df/100,1)
				return df_transformed
			case 'global-radiation-flux':
				df_transformed =  round(df.diff()/3600, 1)
				return df_transformed
			case 'total-precipitation':
				df_transformed = round(df.diff(), 1)
				return df_transformed
			case _:
				df_transformed = round(df, 1)
				return df_transformed


class DataProcessor(ABC):
	@abstractmethod
	def process_data():
		pass

class HistoricalWeatherDataProcessor(DataProcessor):
	def process_data(self, jsonData:dict, transformer:Transformer, parameter:str)->dict:
		timestamps = [feature['properties']['from'][:13] for feature in jsonData['features']]
		values = [feature['properties']['value'] for feature in jsonData['features']]
		return {'parameterId': parameter,
				'timestamps':timestamps, 
				'values':values}

class ForecastDataProcessor(DataProcessor):
	def process_data(self, jsonData:dict, transformer:Transformer)->pd.DataFrame:
		if not jsonData:
			print("Error: Missing json data")
			return pd.DataFrame()
		try:
			parameter = list(jsonData['parameters'].keys())[0]
			timestamps = jsonData.get('domain', {}).get('axes', {}).get('t', {}).get('values', [])
			if not parameter or not timestamps:
				raise KeyError('Missing parameter or timestamps in jsonData')
			spliced_timestamps = [s[:13] for s in timestamps]
			values = jsonData.get('ranges', {}).get(parameter, {}).get('values', [])
			if not values:
				raise KeyError(f'Missing or empty values for parameter "{parameter}"')
		except KeyError as e:
			raise KeyError(f'Missing expected key in jsonData: {e}')
		# Create a DataFrame for the JSON dataset
		df = pd.DataFrame({parameter: values}, index=spliced_timestamps)
		df.index.name = "HourUTC"
		df_transformed = transformer.transform(df, parameter)
		return df_transformed


#class DataContainer:
#	def __init__(self, url:str=None, payload:str=None, apiFetcher:ApiFetcher=None, dataProcessor:DataProcessor=None, transformer:Transformer=None):
#		self.url:str = url
#		self.payload:dict = payload
#		self.transformer = transformer
#		self.apiFetcher = apiFetcher
#		self.dataProcessor= dataProcessor
#		self.df:pd.DataFrame=None
#
#	def create_data(self):
#		json_data = self.apiFetcher.fetch_data(self.url, self.payload)
#		if json_data is None:
#			print(json_data)
#			print("No data available")
#		else:
#			self.df = self.dataProcessor.process_data(json_data, self.transformer)


def main():

	test_params = {'items':[

	]}

if __name__=="__main__":
	main()