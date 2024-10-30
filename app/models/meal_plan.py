from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class FoodDetail(BaseModel):
    foodDetail: Optional[List[str]] = []
    foodName: str
    foodCount: str
    foodDesc: str
    foodEnergy: Optional[int] = 0 
    customizedId: Optional[int] = None

class Meal(BaseModel):
    mealTypeText: str
    totalEnergy: int
    foodDetailList: List[FoodDetail]

class DayMeal(BaseModel):
    day: int
    meals: List[Meal]

class MealPlanRequest(BaseModel):
    userId: str
    customizedDate: str
    CC: Optional[List[str]] = []
    sex: Optional[str] = None
    age: Optional[int] = None
    height: Optional[str] = None
    weight: Optional[str] = None
    healthDescription: Optional[str] = None
    mealHabit: Optional[str] = None
    mealAvoid: Optional[List[str]] = []
    mealAllergy: Optional[List[str]] = []
    mealTaste: Optional[List[str]] = []
    mealStaple: Optional[List[str]] = []
    mealSpicy: Optional[str] = None
    mealSoup: Optional[str] = None

class FoodReplaceRequest(BaseModel):
    id: str
    mealTypeText: str
    CC: Optional[List[str]] = []
    sex: Optional[str] = None
    age: Optional[int] = None
    height: Optional[str] = None
    weight: Optional[str] = None
    healthDescription: Optional[str] = None
    mealHabit: Optional[str] = None
    mealAvoid: Optional[List[str]] = []
    mealAllergy: Optional[List[str]] = []
    mealTaste: Optional[List[str]] = []
    mealStaple: Optional[List[str]] = []
    mealSpicy: Optional[str] = None
    mealSoup: Optional[str] = None
    replaceFoodList: List[FoodDetail]
    remainFoodList: List[FoodDetail]

class ReplaceMealPlanData(BaseModel):
    id: str
    foodDate: str
    meals: List[Meal]

class ReplaceMealPlanResponse(BaseModel):
    code: int
    msg: str
    data: ReplaceMealPlanData

class GenerateMealPlanData(BaseModel):
    userId: str
    foodDate: str
    record: List[DayMeal]

class GenerateMealPlanResponse(BaseModel):
    code: int
    msg: str
    data: GenerateMealPlanData

class BasicResponse(BaseModel):
    code: int
    msg: str
    data: str
