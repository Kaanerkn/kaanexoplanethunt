from fastapi import FastAPI
from pydantic import BaseModel
from pipeline import run_pipeline
import pandas as pd

app = FastAPI(title="Exoplanet Candidate API")

class InputData(BaseModel):
    file_path: str

@app.post("/run")
def run_pipeline_api(data: InputData):
    df: pd.DataFrame = run_pipeline(data.file_path)

    class_counts = df["class"].value_counts().to_dict() if "class" in df.columns else {}

    return {
        "file_path": data.file_path,
        "total_rows": len(df),
        "class_counts": class_counts
    }
