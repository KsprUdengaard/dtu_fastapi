import pandas as pd
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
	def process_data(self, jsonData:dict, transformer:Transformer, parameter:str)->dict:
		timestamps = [feature['properties']['from'][:13] for feature in jsonData['features']]
		values = [feature['properties']['value'] for feature in jsonData['features']]
		corrected_values=transformer.transform(values=values, parameter=parameter)
		return {'parameterId': parameter,
				'timestamps':timestamps, 
				'values':corrected_values}

class ForecastDataProcessor(DataProcessor):
	def process_data(self, jsonData:dict, transformer:Transformer, parameter:str)->dict:
		internal_parameter = list(jsonData['parameters'].keys())[0]
		timestamps = jsonData.get('domain', {}).get('axes', {}).get('t', {}).get('values', [])
		spliced_timestamps = [s[:13] for s in timestamps]
		values = jsonData.get('ranges', {}).get(parameter, {}).get('values', [])
		corrected_values=transformer.transform(values=values, parameter=parameter)
		return {'parameterId': parameter,
				'timestamps':spliced_timestamps, 
				'values':corrected_values}

def main():
	pass
if __name__=="__main__":
	main()