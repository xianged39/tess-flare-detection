# ==========================================
# TESS 光变曲线中值归一化脚本（改进版）
# ==========================================

import os
import pandas as pd
import numpy as np

# ======== 输入路径 ========
input_path = r"F:\AP Research\benchmark随机2000星\lightcurves"
output_path = os.path.join(input_path, "归一化数据")

os.makedirs(output_path, exist_ok=True)

# ======== 遍历文件 ========
for filename in os.listdir(input_path):

    if not filename.endswith(".csv"):
        continue

    file_path = os.path.join(input_path, filename)

    try:
        # 读取已有列名
        df = pd.read_csv(file_path)

        # 检查列
        if not {"time", "flux", "flux_err"}.issubset(df.columns):
            print(f"{filename} 列名不匹配，跳过")
            continue

        # 去除 NaN
        df = df.dropna(subset=["time", "flux", "flux_err"])

        if len(df) == 0:
            print(f"{filename} 无有效数据，跳过")
            continue

        flux = df["flux"].values
        median_flux = np.median(flux)

        if median_flux == 0:
            print(f"{filename} 中值为 0，跳过")
            continue

        # ======== 推荐归一化方式 ========
        df["fnorm"] = (flux - median_flux) / median_flux
        df["flux_err_norm"] = df["flux_err"] / median_flux

        # 保存
        out_file = os.path.join(output_path, filename)

        df[['time','fnorm','flux_err_norm']].to_csv(
            out_file,
            index=False,
            header=False
        )

        print(f"{filename} 归一化完成")

    except Exception as e:
        print(f"{filename} 处理失败: {e}")