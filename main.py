from fastapi import FastAPI, Path, HTTPException, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel ,Field , computed_field
from typing import Annotated , Literal , Optional
import json


app = FastAPI()

class Patient(BaseModel):
    id : Annotated[str, Field(..., description="The ID of the patient in the DB", example="P001")]  
    name : Annotated[str, Field(..., description="The name of the patient", example="John Doe")]
    city : Annotated[str, Field(..., description="The city where the patient lives", example="New York")]
    age : Annotated[int, Field(..., gt=0, lt=150, description="The age of the patient", example=30)]
    gender : Annotated[Literal["Male", "Female", "Other"], Field(..., description="The gender of the patient", example="Male")]
    height : Annotated[float, Field(..., gt=0, description="The height of the patient in meters", example=1.75)]
    weight : Annotated[float, Field(..., gt=0, description="The weight of the patient in kilograms", example=70.0)]

    @computed_field
    @property
    def bmi(self) -> float:
        return round(self.weight / (self.height ** 2), 2)
    
    @computed_field
    @property
    def health_status(self) -> str: 

        if self.bmi < 18.5:
            return "Underweight" 
        elif 18.5 <= self.bmi < 24.9:
            return "Normal weight"  
        elif 25 <= self.bmi < 29.9:
            return "Overweight"
        
class PatientUpdate(BaseModel): 
    name : Annotated[Optional[str], Field(default=None, description="The name of the patient", example="John Doe")]
    city : Annotated[Optional[str], Field(default=None, description="The city where the patient lives", example="New York")]
    age : Annotated[Optional[int], Field(default=None, gt=0, lt=150, description="The age of the patient", example=30)]
    gender : Annotated[Optional[Literal["Male", "Female", "Other"]], Field(default=None, description="The gender of the patient", example="Male")]
    height : Annotated[Optional[float], Field(default=None, gt=0, description="The height of the patient in meters", example=1.75)]
    weight : Annotated[Optional[float], Field(default=None, gt=0, description="The weight of the patient in kilograms", example=70.0)]

def load_data():
    with open("patient.json", "r") as f:    
        data = json.load(f)
    return data

def save_data(data):
    with open("patient.json", "w") as f:
        json.dump(data, f)

@app.get("/")
def hello():
    return {"Message": "Patient Management System API is running!"}

@app.get("/about")
def about():
    return {"Message": "This API is designed to manage patient records, appointments, and medical history for healthcare providers."}

@app.get("/view")
def view ():
    data=load_data()
    return data 

@app.get('/patient/{patient_id}')
def view_patient(patient_id: str= Path(..., description="The ID of the patient in the DB",example="P001")):
    data = load_data()
    if patient_id in data:
            return data[patient_id]
    raise HTTPException(status_code=404, detail='Patient not found')    

@app.get('/sort')
def sort_patients(sort_by: str = Query(..., description='Sort on the basis of height, weight or bmi'), order: str = Query('asc', description='sort in asc or desc order')):

    valid_fields = ['height', 'weight', 'bmi']

    if sort_by not in valid_fields:
        raise HTTPException(status_code=400, detail=f'Invalid field select from {valid_fields}')
    
    if order not in ['asc', 'desc']:
        raise HTTPException(status_code=400, detail='Invalid order select between asc and desc')
    
    data = load_data()

    sort_order = True if order=='desc' else False

    sorted_data = sorted(data.values(), key=lambda x: x.get(sort_by, 0), reverse=sort_order)

    return sorted_data

@app.post('/create')
def create_patient(patient: Patient):
    #loading the existing data from the json file
    data = load_data()
    #checking if the patient ID already exists in the data
    if patient.id in data:
        raise HTTPException(status_code=400, detail='Patient with this ID already exists')
    
    data[patient.id] = patient.model_dump(exclude=['id'])
    
    with open("patient.json", "w") as f:
        json.dump(data, f, indent=4)

    save_data(data)
     
    return JSONResponse(status_code=201, content={"message": "Patient created successfully", "patient_id": patient.id})

@app.put('/update/{patient_id}')
def update_patient(patient_id: str, patient_update: PatientUpdate):

    data = load_data()
    if patient_id not in data:
        raise HTTPException(status_code=404, detail='Patient not found')
    
    data_patient_info = data[patient_id] 

    patient_update_info = patient_update.model_dump(exclude_unset=True)
    existing_patient_info['id'] = patient_id
    Patient_pydantic_obj =patient(**existing_patient_info)

    existing_patient_info=patient_pydantic_obj.model_dump(exclude='id')
     
    for key, value in patient_update_info.items():
        existing_patient_info[key] = value

    data[patient_id] = existing_patient_info

    save_data(data)

    return JSONResponse(status_code=200, content={"message": "Patient updated successfully"})

@app.delete('/delete/{patient_id}')
def delete_patient(patient_id: str):    
    data = load_data()
    if patient_id not in data:
        raise HTTPException(status_code=404, detail='Patient not found')
    
    del data[patient_id]
    save_data(data)

    return JSONResponse(status_code=200, content={"message": "Patient deleted successfully"})   