from pathlib import Path
import io, zipfile, urllib.request
import pandas as pd

URL="https://archive.ics.uci.edu/static/public/447/condition+monitoring+of+hydraulic+systems.zip"
OUT=Path("data/uci_hydraulic_cycles.csv"); RAW=Path("data/uci_raw")

def read_profile(root):
    return pd.read_csv(next(root.rglob("profile.txt")),sep="\t",header=None,names=["cooler_condition","valve_condition","pump_leakage","accumulator_pressure","stable_flag"])
def main():
    OUT.parent.mkdir(parents=True,exist_ok=True)
    if not RAW.exists() or not list(RAW.rglob("profile.txt")):
        print("Downloading official UCI Hydraulic Systems archive...")
        with urllib.request.urlopen(URL,timeout=120) as r: blob=r.read()
        RAW.mkdir(parents=True,exist_ok=True)
        with zipfile.ZipFile(io.BytesIO(blob)) as z: z.extractall(RAW)
    y=read_profile(RAW); y.insert(0,"cycle",range(1,len(y)+1))
    y["temperature_mean"]=pd.read_csv(next(RAW.rglob("TS1.txt")),sep="\t",header=None).mean(axis=1)
    y["vibration_max"]=pd.read_csv(next(RAW.rglob("VS1.txt")),sep="\t",header=None).max(axis=1)
    y.to_csv(OUT,index=False); print(f"Wrote {len(y)} real UCI cycles to {OUT}")
if __name__=="__main__": main()
