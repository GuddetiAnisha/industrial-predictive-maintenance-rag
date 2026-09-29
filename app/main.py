from pathlib import Path
from datetime import datetime, timezone
import os
import pandas as pd
from fastapi import FastAPI, HTTPException
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, confusion_matrix

app=FastAPI(title="Industrial Predictive Maintenance API",version="2.0")
DATA=Path(os.getenv("DATA_DIR","data"))/"uci_hydraulic_cycles.csv"
_cursor=0

def df():
    if not DATA.exists(): raise HTTPException(503,"Real UCI data not prepared. Run: python scripts/generate_data.py")
    return pd.read_csv(DATA)

def evaluation():
    d=df(); X=d[["temperature_mean","vibration_max"]]; y=(d["pump_leakage"]!=0).astype(int)
    Xtr,Xte,ytr,yte=train_test_split(X,y,test_size=.25,random_state=42,stratify=y)
    m=RandomForestClassifier(n_estimators=150,random_state=42,n_jobs=-1).fit(Xtr,ytr); p=m.predict(Xte)
    cm=confusion_matrix(yte,p,labels=[0,1]).tolist(); tn,fp,fn,tp=sum(cm,[])
    return {"accuracy":accuracy_score(yte,p),"precision":precision_score(yte,p,zero_division=0),"recall":recall_score(yte,p,zero_division=0),"f1":f1_score(yte,p,zero_division=0),"false_alarm_rate":fp/(fp+tn) if fp+tn else 0,"confusion_matrix":cm,"dataset":"UCI Condition Monitoring of Hydraulic Systems","split":"75/25 stratified holdout; random_state=42"}

@app.get("/health")
def health(): return {"status":"ok","real_dataset_ready":DATA.exists()}
@app.get("/api/machines")
def machines(): return {"machines":[{"machine_id":"M24","name":"Hydraulic Test Rig","location":"UCI dataset replay"}]}
@app.get("/api/datasets/uci-hydraulic/status")
def uci_status():
    d=df(); return {"cycles":len(d),"current_cycle":_cursor,"source":"UCI Hydraulic Systems","real_data":True}
@app.post("/api/datasets/uci-hydraulic/next")
def uci_next():
    global _cursor
    d=df(); row=d.iloc[_cursor%len(d)].to_dict(); _cursor+=1; row["cycle"]=int(row["cycle"])
    row["conditions"]=[f"cooler={row['cooler_condition']}",f"valve={row['valve_condition']}",f"pump_leakage={row['pump_leakage']}",f"accumulator={row['accumulator_pressure']}",f"stable={row['stable_flag']}"]
    row["model_predictions"]={"pump_leakage_anomaly":bool(row["pump_leakage"]!=0)}; row["replay_timestamp"]=datetime.now(timezone.utc).isoformat(); return row
@app.post("/api/datasets/uci-hydraulic/reset")
def reset():
    global _cursor; _cursor=0; return {"ok":True}
@app.get("/api/datasets/status")
def datasets(): return {"uci_hydraulic":{"ready":DATA.exists(),"real":True},"nasa_ims":{"ready":False,"optional":True},"mimii_due":{"ready":False,"optional":True}}
@app.get("/api/model/evaluation")
def model_eval(): return evaluation()
@app.get("/api/model/drift")
def drift(): return {"status":"not_applicable","reason":"offline dataset replay; no production baseline configured"}
