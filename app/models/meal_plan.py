from pydantic import BaseModel
from typing import List, Optional

class FoodDetail(BaseModel):
    foodDetail: Optional[List[str]] = []
    foodName: str
    foodCount: str
    foodDesc: str
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