import pandas as pd
import xgboost as xgb
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
import numpy as np
from datetime import datetime, timedelta
from abc import ABC, abstractmethod

class Transformer:
	@staticmethod
	def transform(values:list, parameter:str)->list:
		if values is None:  # Explicitly check for None
			raise TypeError("The 'values' input cannot be None.")
		if not values:
			return []
		if not all(isinstance(x, (int, float)) for x in values):
			raise TypeError("All elements in the 'values' list must be numbers.")
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
	def process_data(self, json_data: dict, transformer: Transformer, parameter: str) -> dict:
		timestamps = []
		values = []
		for feature in json_data.get("features", []):
			props = feature.get("properties", {})
			# Only include features with both 'from' and 'value' keys
			if "from" in props and "value" in props:
				timestamps.append(props["from"][:13])
				values.append(props["value"])

		if not values:  # Handle empty values
			return {'parameterId': parameter, 'timestamps': [], 'values': []}

		corrected_values = transformer.transform(values=values, parameter=parameter)
		return {'parameterId': parameter, 'timestamps': timestamps, 'values': corrected_values}


class ForecastDataProcessor(DataProcessor):
	def process_data(self, json_data: dict, transformer: Transformer, parameter: str) -> dict:
		# Get internal parameter if present
		internal_parameter = next(iter(json_data.get("parameters", {}).keys()), None)

		# Get timestamps and values with defaults
		timestamps = json_data.get("domain", {}).get("axes", {}).get("t", {}).get("values", [])
		spliced_timestamps = [s[:13] for s in timestamps]
		values = json_data.get("ranges", {}).get(parameter, {}).get("values", [])

		if not values:  # Handle empty values
			return {'parameterId': parameter, 'timestamps': [], 'values': []}
		
		corrected_values = transformer.transform(values=values, parameter=parameter)
		return {'parameterId': parameter, 'timestamps': spliced_timestamps, 'values': corrected_values}


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
				case _:
					parameter = entry['parameterId']
					df_dict[parameter] = entry['values']

			df_dict[parameter] = entry['values']

		df = pd.DataFrame(df_dict)
		df['HourUTC'] = pd.to_datetime(df['HourUTC']).astype(int) / 10**9
		dmatrix = xgb.DMatrix(df)
		predictions = self.model.predict(dmatrix)

		price_prediction = {}
		for time, price in zip(timestamps, predictions):
			price_prediction[time] = round(float(price/1000),2)
		return price_prediction

class EnergyPriceModelTrainer:
	@staticmethod
	def train_model(data:pd.DataFrame, 
					gamma:float, 
					max_depth:int, 
					eta:float, 
					subsample:float, 
					colsample_bytree:float, 
					min_child_weight:int,
					num_rounds:int=1000):

		if data.empty:
			raise ValueError("Input DataFrame is empty.")
		if 'SpotPriceDKK' not in data.columns:
			raise KeyError("'SpotPriceDKK' column is missing in the input DataFrame.")

		x = data.drop(columns=['SpotPriceDKK'])
		y = data['SpotPriceDKK']

		x_train, x_test, y_train, y_test = train_test_split(x, y, test_size=0.2, random_state=42)

		dtrain = xgb.DMatrix(x_train, label=y_train)
		dtest = xgb.DMatrix(x_test, label=y_test)

		params = {
			'gamma':gamma,
			'objective': 'reg:squarederror',
			'max_depth': max_depth,
			'eta': eta,
			'subsample': subsample,
			'colsample_bytree': colsample_bytree,
			'min_child_weight': min_child_weight,
			'eval_metric': 'rmse'  # Set RMSE as the evaluation metric
			}
		rounds = num_rounds

		evals = [(dtrain, 'train'), (dtest, 'test')]

		model = xgb.train(
			params,
			dtrain,
			num_rounds,
			evals=evals,
			early_stopping_rounds=10,
			verbose_eval=50
			)
		y_pred = model.predict(dtest)
		model.save_model('xgboost_model_test.json')
		
		mse = mean_squared_error(y_test, y_pred)
		rmse = np.sqrt(mse)
		mae = mean_absolute_error(y_test, y_pred)
		r2 = r2_score(y_test, y_pred)

		mean_actual = np.mean(y_test)
		rmse_percentage = (rmse / mean_actual) * 100
		return {
        		'rmse': round(rmse, 2),
        		'mea': round(mae, 2),
        		'r2': round(r2, 4),
        		'rsd': round(rmse_percentage, 2)
    			}

def main():
	pass

if __name__=="__main__":
	main()