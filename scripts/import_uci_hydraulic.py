import sys
from pathlib import Path
import pandas as pd
def main(root):
    root=Path(root); out=Path("data/uci_hydraulic_cycles.csv"); out.parent.mkdir(exist_ok=True)
    y=pd.read_csv(next(root.rglob("profile.txt")),sep="\t",header=None,names=["cooler_condition","valve_condition","pump_leakage","accumulator_pressure","stable_flag"])
    y.insert(0,"cycle",range(1,len(y)+1))
    y["temperature_mean"]=pd.read_csv(next(root.rglob("TS1.txt")),sep="\t",header=None).mean(axis=1)
    y["vibration_max"]=pd.read_csv(next(root.rglob("VS1.txt")),sep="\t",header=None).max(axis=1)
    y.to_csv(out,index=False); print(f"Imported {len(y)} cycles -> {out}")
if __name__=="__main__":
    if len(sys.argv)!=2: raise SystemExit("Usage: python scripts/import_uci_hydraulic.py PATH_TO_EXTRACTED_UCI")
    main(sys.argv[1])
