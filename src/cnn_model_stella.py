import pandas as pd
import numpy as np
import os
import glob
import sys
import time
import contextlib
from tqdm import tqdm

# ========================
# 0. 强制静音 TensorFlow + 消音器
# ========================
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'

@contextlib.contextmanager
def suppress_output():
    with open(os.devnull, "w") as devnull:
        old_stdout = sys.stdout
        old_stderr = sys.stderr
        try:
            sys.stdout = devnull
            sys.stderr = devnull
            yield
        finally:
            sys.stdout = old_stdout
            sys.stderr = old_stderr

# ========================
# 1. 路径设置
# ========================
INPUT_DIR = "/Users/guiliangzheng/Desktop/向/flare_sample"
OUT_DIR = "/Users/guiliangzheng/Desktop/向/stella_results"
os.makedirs(OUT_DIR, exist_ok=True)

sys.path.insert(1, '********************')
import stella

# ========================
# 2. 加载 10 个模型 (Ensemble)
# ========================
print("正在初始化模型组...")
available_models = []

with suppress_output():
    try:
        ds = stella.DownloadSets()
        if hasattr(ds, "download_models"):
            ds.download_models()
        if hasattr(ds, "models"):
            available_models = ds.models
        elif hasattr(ds, "get_models"):
            available_models = ds.get_models()
    except:
        pass

if len(available_models) == 0:
    models_dir = r"/Users/guiliangzheng/.stella/models"
    if os.path.isdir(models_dir):
        available_models = [
            os.path.join(models_dir, f)
            for f in os.listdir(models_dir)
            if f.endswith(".h5")
        ]

if len(available_models) == 0:
    raise RuntimeError("❌ 未找到模型。")

ENSEMBLE_MODELS = available_models[:10]
print(f"✅ 已加载 {len(ENSEMBLE_MODELS)} 个模型。")

with suppress_output():
    cnn = stella.ConvNN(output_dir=OUT_DIR)

# ========================
# 3. 处理所有文件
# ========================
csv_files = sorted(glob.glob(os.path.join(INPUT_DIR, "*.csv")))
print(f"📂 待处理文件数: {len(csv_files)}")
print("开始处理，请勿合盖/睡眠...")

all_flares = []
error_log = []

for file_path in tqdm(csv_files, desc="Ensemble Processing", unit="file"):
    t0 = time.time()
    tess_id = "Unknown"

    try:
        # --- A. 获取 TESSID ---
        filename = os.path.basename(file_path)
        tess_id = os.path.splitext(filename)[0]

        # --- B. 读取数据 ---
        df = pd.read_csv(file_path)
        times = df['time'].values
        fluxes = df['flux'].values
        errs = df['flux_err'].values

        # --- C. 去 NaN + 归一化 ---
        mask = (~np.isnan(times)) & (~np.isnan(fluxes)) & (~np.isnan(errs))
        times = times[mask]
        fluxes = fluxes[mask]
        errs = errs[mask]

        if len(fluxes) == 0:
            continue

        median_flux = np.nanmedian(fluxes)

        #未归一化
        if median_flux > 0:
            fluxes_norm = fluxes
            errs_norm = errs
        #归一化    
        # if median_flux > 0:
        #     fluxes_norm = fluxes / median_flux
        #     errs_norm = errs / median_flux
        else:
            fluxes_norm = fluxes
            errs_norm = errs

        # --- D. Ensemble 预测 (10个模型) ---
        with suppress_output():
            try:
                cnn.predict(modelname=ENSEMBLE_MODELS[0], times=times, fluxes=fluxes_norm, errs=errs_norm)
            except:
                cnn.predict(modelname=ENSEMBLE_MODELS[0], times=[times], fluxes=[fluxes_norm], errs=[errs_norm])

        base_pred = cnn.predictions[0]
        pred_times = cnn.predict_time[0]
        pred_fluxes = cnn.predict_flux[0]

        preds_matrix = np.zeros((len(ENSEMBLE_MODELS), len(base_pred)))
        preds_matrix[0] = base_pred

        for i, model in enumerate(ENSEMBLE_MODELS[1:], start=1):
            with suppress_output():
                try:
                    cnn.predict(modelname=model, times=times, fluxes=fluxes_norm, errs=errs_norm)
                    preds_matrix[i] = cnn.predictions[0]
                except:
                    preds_matrix[i] = np.zeros_like(base_pred)

        avg_pred = np.nanmedian(preds_matrix, axis=0)
        compute_time = round(time.time() - t0, 4)

        # --- E. 识别耀发 ---
        i = 0
        n = len(avg_pred)
        THRESHOLD = 0.5

        while i < n:
            if avg_pred[i] > THRESHOLD:
                start_idx = i
                j = i
                while j < n and avg_pred[j] > THRESHOLD:
                    j += 1
                end_idx = j

                if (end_idx - start_idx) >= 4:
                    t_start = pred_times[start_idx]
                    t_end = pred_times[end_idx - 1]

                    segment_flux = pred_fluxes[start_idx:end_idx]
                    # 取耀发开始前的一小段作为局部基线（例如前 20 个点），注意边界
                    pre = max(0, start_idx - 20)
                    baseline = np.median(pred_fluxes[pre:start_idx]) if start_idx > pre else np.median(pred_fluxes)

                    segment_time = pred_times[start_idx:end_idx]
                    local_peak_idx = np.argmax(segment_flux)
                    t_peak = segment_time[local_peak_idx]

                    duration = t_end - t_start
                    amplitude = np.max(segment_flux) / baseline - 1

                    all_flares.append({
                        'TESSID': tess_id,
                        'starttime': t_start,
                        'peaktime': t_peak,
                        'end': t_end,
                        'amplitude': amplitude,
                        'duration_days': duration,
                        'computing_time': compute_time
                    })
                i = j
            else:
                i += 1

    except Exception as e:
        error_log.append(f"{tess_id}: {str(e)}")
        continue

# ========================
# 4. 保存结果
# ========================
if len(all_flares) > 0:
    final_df = pd.DataFrame(all_flares)
    cols = ['TESSID', 'starttime', 'peaktime', 'end', 'amplitude', 'duration_days', 'computing_time']
    final_df = final_df[cols]

    output_path = os.path.join(OUT_DIR, "ensemble_sample_flares_result.csv")
    final_df.to_csv(output_path, index=False)

    print(f"\n✅ 全部完成！共处理 {len(csv_files)} 个文件。")
    print(f"📊 发现 {len(final_df)} 个耀发事件。")
    print(f"💾 已保存至: {output_path}")
    print(final_df.head())
else:
    print("\n⚠️ 未检测到耀发。")

if error_log:
    print(f"\n⚠️ 有 {len(error_log)} 个文件出错。")