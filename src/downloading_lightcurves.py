# ==========================================
# TESS 并行下载 —— 终极稳定版
# ==========================================

import os
import re
import time
import numpy as np
import pandas as pd
import lightkurve as lk
import concurrent.futures

INPUT_CSV = r'F:\AP Research\benchmark随机2000星\tic_sector_2263.csv'
OUT_DIR = r'F:\AP Research\benchmark随机2000星\lightcurves'
LOG_FILE = r'F:\AP Research\benchmark随机2000星\download_log_2263.csv'

MISSION = "TESS"
AUTHOR = "SPOC"
CADENCE = 120

MAX_WORKERS = 3      # ⭐ 降低并发，避免被 MAST 限流
MAX_RETRY = 3
RETRY_WAIT = 5

os.makedirs(OUT_DIR, exist_ok=True)


def parse_sectors(x):
    return sorted(set(int(n) for n in re.findall(r"\d+", str(x))))


def read_input(path):
    df = pd.read_csv(path, dtype=str)
    df = df.iloc[:, :2]
    df.columns = ["tic", "sector"]
    return df


def load_log(path):
    if not os.path.exists(path):
        return set()
    df = pd.read_csv(path, dtype=str)
    return set(zip(df["tic"], df["sector"]))


def append_log(path, tic, sector):
    header = not os.path.exists(path)
    with open(path, "a", encoding="utf-8") as f:
        if header:
            f.write("tic,sector\n")
        f.write(f"{tic},{sector}\n")


def convert_native(x):
    return np.array(x).astype(np.float64)


def download_one(tic_raw, sec):

    query = f"TIC {tic_raw}"

    for attempt in range(MAX_RETRY):

        try:
            sr = lk.search_lightcurve(
                query,
                mission=MISSION,
                author=AUTHOR,
                sector=sec,
                exptime=CADENCE
            )

            if len(sr) == 0:
                return False

            lc = sr.download(quality_bitmask="default")

            if hasattr(lc, "pdcsap_flux"):
                flux = lc.pdcsap_flux
                flux_err = lc.pdcsap_flux_err
            else:
                flux = lc.flux
                flux_err = lc.flux_err

            df = pd.DataFrame({
                "time": convert_native(lc.time.value),
                "flux": convert_native(flux.value),
                "flux_err": convert_native(flux_err.value)
            }).dropna()

            outname = f"{tic_raw}_sector{sec}.csv"
            df.to_csv(os.path.join(OUT_DIR, outname), index=False)

            append_log(LOG_FILE, tic_raw, sec)

            return True

        except Exception:
            time.sleep(RETRY_WAIT)

    return False


# ================= 主程序 =================

df = read_input(INPUT_CSV)
done = load_log(LOG_FILE)

tasks = []

for _, row in df.iterrows():
    tic = row["tic"].strip()
    for sec in parse_sectors(row["sector"]):
        if (tic, str(sec)) not in done:
            tasks.append((tic, sec))

print("待下载:", len(tasks))

success = 0
failed = 0

with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:

    futures = [executor.submit(download_one, tic, sec) for tic, sec in tasks]

    for future in concurrent.futures.as_completed(futures):
        try:
            if future.result():
                success += 1
            else:
                failed += 1
        except:
            failed += 1

print("完成")
print("成功:", success)
print("失败:", failed)