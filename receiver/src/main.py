from fastapi import FastAPI
import requests
import pydicom
import io

app = FastAPI()

ORTHANC = "http://localhost:8042"

@app.get("/")
def root():
    return {"status": "API running"}

@app.get("/studies")
def list_studies():
    r = requests.get(f"{ORTHANC}/studies")
    return r.json()

@app.get("/instances/{instance_id}")
def get_instance(instance_id: str):
    r = requests.get(f"{ORTHANC}/instances/{instance_id}/file")
    
    dicom_bytes = io.BytesIO(r.content)
    ds = pydicom.dcmread(dicom_bytes)
    
    return {
        "PatientName": str(ds.get("PatientName")),
        "Modality": str(ds.get("Modality"))
    }