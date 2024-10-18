import csv
import json
from datetime import datetime
from typing import Any, Dict, List, Union

class CSVLogger:
    def __init__(self, file_path: str):
        self.file_path = file_path
        self.headers = ["Timestamp", "Module", "Type", "Day", "Meal", "Calories", "Dishes"]
        self._initialize_csv()

    def _initialize_csv(self):
        with open(self.file_path, 'w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            writer.writerow(self.headers)

    def _format_data(self, data: Any) -> str:
        if isinstance(data, (dict, list)):
            return json.dumps(data, ensure_ascii=False, indent=2)
        return str(data)

    def _write_row(self, row: List[str]):
        with open(self.file_path, 'a', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            writer.writerow(row)

    def log(self, module: str, data_type: str, data: Any, execution_time: float = None):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        if module in ["FrameModule_MealPlanGeneration", "FinalMealPlan"] and data_type == "Output":
            self._log_meal_plan(timestamp, module, data_type, data)
        else:
            formatted_data = self._format_data(data)
            self._write_row([timestamp, module, data_type, formatted_data, '', '', ''])
        
        if execution_time is not None:
            self._write_row([timestamp, module, 'Execution Time', f"{execution_time:.2f} seconds", '', '', ''])
        
        self._write_row([])  # 空行分隔不同的日志条目

    def _log_meal_plan(self, timestamp: str, module: str, data_type: str, meal_plan: List[Dict]):
        for meal in meal_plan:
            day = meal.get('day', '')
            meal_type = meal.get('meal', '')
            menu = meal.get('menu', {})
            calories = menu.get('total_calories', '')
            dishes = '; '.join([f"{dish['name']} ({dish['quantity']})" for dish in menu.get('dishes', [])])
            
            self._write_row([timestamp, module, data_type, day, meal_type, calories, dishes])

def log_module_io(csv_logger: CSVLogger, module_name: str, input_data: Dict[str, Any], output_data: Any, execution_time: float):
    csv_logger.log(module_name, "Input", input_data)
    csv_logger.log(module_name, "Output", output_data)
    csv_logger.log(module_name, "Execution Time", execution_time)