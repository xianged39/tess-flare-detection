# matching_with_fwhm.py
# 假定 pandas 已导入
import pandas as pd
import numpy as np
import os

def to_minutes_from_days(series):
    s = pd.to_numeric(series, errors='coerce')
    return s * 24.0 * 60.0

def prepare_benchmark_from_fwhm(bench_df, peak_col='peak time', fwhm_col='time scale'):
    """
    bench_df contains:
      - peak_col: epoch in days (TJD/BTJD)
      - fwhm_col: FWHM in minutes (template half-width * 2)
    Returns DataFrame with columns:
      'tic', 'sector', 'bench_peak_min', 'bench_fwhm_min', 'bench_start_min', 'bench_end_min'
    """
    df = bench_df.copy()
    # canonical tic, sector names assumed 'tic id' and 'sector' (adjust if different)
    if 'tic id' in df.columns:
        df['tic'] = pd.to_numeric(df['tic id'], errors='coerce').astype('Int64')
    elif 'tic' in df.columns:
        df['tic'] = pd.to_numeric(df['tic'], errors='coerce').astype('Int64')
    else:
        raise KeyError("benchmark must have tic id or tic column")
    df['sector'] = pd.to_numeric(df['sector'], errors='coerce').astype('Int64')

    # peak in days -> minutes
    df['bench_peak_min'] = to_minutes_from_days(df[peak_col])

    # fwhm_col is in minutes already (you stated so) -> numeric
    df['bench_fwhm_min'] = pd.to_numeric(df[fwhm_col], errors='coerce')

    # if any fwhm NaN: set small fallback (e.g., 10 min) and warn
    n_missing = df['bench_fwhm_min'].isna().sum()
    if n_missing > 0:
        print(f"[WARN] {n_missing} bench rows missing FWHM -> filling with 10 min fallback")
        df['bench_fwhm_min'] = df['bench_fwhm_min'].fillna(10.0)

    # construct interval: use FWHM as interval length
    df['bench_start_min'] = df['bench_peak_min'] - 0.5 * df['bench_fwhm_min']
    df['bench_end_min']   = df['bench_peak_min'] + 0.5 * df['bench_fwhm_min']
    # ensure numeric and valid
    df[['bench_peak_min','bench_fwhm_min','bench_start_min','bench_end_min']] = df[['bench_peak_min','bench_fwhm_min','bench_start_min','bench_end_min']].astype(float)
    return df[['tic','sector','bench_peak_min','bench_fwhm_min','bench_start_min','bench_end_min']]

def prepare_detection_df(det_df, tic_col_candidates=None, sector_col='sector', start_col_candidates=None, peak_col_candidates=None, end_col_candidates=None, time_unit='days'):
    """
    Normalize detection dataframe to minutes. Assumes detection start/peak/end (in days) exist.
    time_unit: unit of detection time columns (default 'days').
    Returns dataframe with columns: 'tic','sector','det_start_min','det_peak_min','det_end_min','det_idx'
    """
    df = det_df.copy()
    # guess tic col
    if tic_col_candidates is None:
        tic_candidates = [c for c in df.columns if 'tic' in c.lower() or 'tess' in c.lower()]
    else:
        tic_candidates = tic_col_candidates
    tic_col = None
    for c in tic_candidates:
        if c in df.columns:
            tic_col = c; break
    if tic_col is None:
        raise KeyError("No TIC column found in detection df")
    df['tic'] = pd.to_numeric(df[tic_col], errors='coerce').astype('Int64')
    # sector
    if sector_col in df.columns:
        df['sector'] = pd.to_numeric(df[sector_col], errors='coerce').astype('Int64')
    else:
        raise KeyError("Detection df missing sector column")
    # pick peak,start,end columns
    if peak_col_candidates is None:
        peak_col_candidates = [c for c in df.columns if 'peak' in c.lower()]
    if start_col_candidates is None:
        start_col_candidates = [c for c in df.columns if 'begin' in c.lower() or 'start' in c.lower()]
    if end_col_candidates is None:
        end_col_candidates = [c for c in df.columns if c.lower()=='end' or 'end' in c.lower()]

    peak_col = next((c for c in peak_col_candidates if c in df.columns), None)
    start_col = next((c for c in start_col_candidates if c in df.columns), None)
    end_col = next((c for c in end_col_candidates if c in df.columns), None)

    if peak_col is None:
        raise KeyError("No peak column detected in detection df")
    # convert to numeric
    df['_peak_raw'] = pd.to_numeric(df[peak_col], errors='coerce')
    df['det_peak_min'] = to_minutes_from_days(df['_peak_raw']) if time_unit == 'days' else pd.to_numeric(df[peak_col], errors='coerce')

    # start and end
    if start_col is not None:
        df['_start_raw'] = pd.to_numeric(df[start_col], errors='coerce')
        df['det_start_min'] = to_minutes_from_days(df['_start_raw']) if time_unit == 'days' else pd.to_numeric(df[start_col], errors='coerce')
    if end_col is not None:
        df['_end_raw'] = pd.to_numeric(df[end_col], errors='coerce')
        df['det_end_min'] = to_minutes_from_days(df['_end_raw']) if time_unit == 'days' else pd.to_numeric(df[end_col], errors='coerce')

    # if start/end missing, use peak +/- 0.5*duration if duration column exists
    if ('det_start_min' not in df.columns or df['det_start_min'].isna().all()):
        # try duration column
        if 'duration' in df.columns:
            dur = pd.to_numeric(df['duration'], errors='coerce')
            # if duration in days, convert to minutes
            # Heuristic: if median duration < 2, probably in days? but user said detection durations are TJD (days)
            df['det_duration_min'] = to_minutes_from_days(dur)
            df['det_start_min'] = df['det_peak_min'] - 0.5 * df['det_duration_min']
            df['det_end_min']   = df['det_peak_min'] + 0.5 * df['det_duration_min']
        else:
            # fallback +/- 10 minutes
            df['det_start_min'] = df['det_peak_min'] - 10.0
            df['det_end_min']   = df['det_peak_min'] + 10.0
    else:
        # ensure det_end exists
        if 'det_end_min' not in df.columns or df['det_end_min'].isna().all():
            if 'det_duration_min' in df.columns:
                df['det_end_min'] = df['det_start_min'] + df['det_duration_min']
            else:
                df['det_end_min'] = df['det_peak_min'] + 10.0

    # finalize
    df['det_start_min'] = pd.to_numeric(df['det_start_min'], errors='coerce').astype(float)
    df['det_peak_min']  = pd.to_numeric(df['det_peak_min'], errors='coerce').astype(float)
    df['det_end_min']   = pd.to_numeric(df['det_end_min'], errors='coerce').astype(float)

    # keep only needed columns and original index as det_idx
    out = df[['tic','sector','det_start_min','det_peak_min','det_end_min']].copy()
    out['det_idx'] = df.index
    return out

def match_using_bench_fwhm(bench_prepared, det_prepared, overlap_thresh=0.05, min_peak_tol_min=10.0, require_sector=True):
    """
    Greedy one-to-one match between bench_prepared and det_prepared.
    bench_prepared columns: tic, sector, bench_peak_min, bench_fwhm_min, bench_start_min, bench_end_min
    det_prepared columns: tic, sector, det_start_min, det_peak_min, det_end_min, det_idx
    Returns:
      matches: list of tuples (tic, sector, true_index, det_idx, overlap_frac, peak_diff_min)
      unmatched_true_indices, unmatched_det_indices  (indices refer to original bench / det_prepared indices)
    """
    matches = []
    unmatched_true = set()
    unmatched_det = set()

    # set index references (true: bench_prepared.index, det: det_prepared.index)
    bench = bench_prepared.copy()
    det = det_prepared.copy()

    # group by (tic,sector)
    if require_sector:
        bench_groups = bench.groupby(['tic','sector'])
        det_groups = det.groupby(['tic','sector'])
        for key, tgroup in bench_groups:
            tic, sector = key
            try:
                dgroup = det_groups.get_group(key)
            except Exception:
                # no detections for this key => all tgroup true are unmatched
                for t_idx in tgroup.index:
                    unmatched_true.add(('true', t_idx))
                continue
            # build lists
            tlist = [{'idx': idx,
                      'start': float(row['bench_start_min']),
                      'end':   float(row['bench_end_min']),
                      'peak':  float(row['bench_peak_min']),
                      'fwhm':  float(row['bench_fwhm_min'])}
                     for idx,row in tgroup.iterrows()]
            dlist = [{'idx': idx,
                      'start': float(row['det_start_min']),
                      'end':   float(row['det_end_min']),
                      'peak':  float(row['det_peak_min'])}
                     for idx,row in dgroup.iterrows()]
            # matched flags
            t_matched = {t['idx']: False for t in tlist}
            # iterate detections greedily
            for drow in dlist:
                best = None; best_overlap = -1.0; best_peakdiff = None
                for trow in tlist:
                    if t_matched[trow['idx']]:
                        continue
                    overlap = min(trow['end'], drow['end']) - max(trow['start'], drow['start'])
                    overlap = max(0.0, overlap)
                    overlap_frac = overlap / max(1e-9, trow['fwhm'])
                    peak_diff = abs(trow['peak'] - drow['peak'])
                    if overlap_frac > best_overlap:
                        best = (trow, drow, overlap_frac, peak_diff)
                        best_overlap = overlap_frac
                        best_peakdiff = peak_diff
                    elif overlap_frac == best_overlap and best is not None and peak_diff < best_peakdiff:
                        best = (trow, drow, overlap_frac, peak_diff)
                        best_peakdiff = peak_diff
                if best is not None:
                    trow, drow, overlap_frac, peak_diff = best
                    tol = max(0.5 * trow['fwhm'], min_peak_tol_min)
                    if overlap_frac >= overlap_thresh or peak_diff <= tol:
                        matches.append((tic, sector, trow['idx'], drow['idx'], overlap_frac, peak_diff))
                        t_matched[trow['idx']] = True
                    else:
                        # detection remains unmatched for now
                        pass
            # any unmatched true in this tgroup
            for trow in tlist:
                if not t_matched[trow['idx']]:
                    unmatched_true.add(('true', trow['idx']))
        # collect unmatched det indices
        matched_det_idxs = set([m[3] for m in matches])
        all_det_idxs = set(det.index)
        for di in all_det_idxs - matched_det_idxs:
            unmatched_det.add(('det', di))
    else:
        # similar grouping by tic only (not implemented here, conceptually same)
        raise NotImplementedError("Non-sector matching not implemented in this helper")

    return matches, unmatched_true, unmatched_det

# ---------------------------
# 调用示例（将路径改为你文件位置）
# ---------------------------
if __name__ == "__main__":
    bench_path = r"F:\AP Research\benchmark随机2000星\事件配对\benchmarks_real_flares_2263.csv"
    stella_path = r"F:\AP Research\benchmark随机2000星\事件配对\stella_final_result.csv"
    yang_path = r"F:\AP Research\benchmark随机2000星\事件配对\Yang's_result_new.csv"

    bench_raw = pd.read_csv(bench_path)
    stella_raw = pd.read_csv(stella_path)
    yang_raw = pd.read_csv(yang_path)

    # prepare
    bench_p = prepare_benchmark_from_fwhm(bench_raw, peak_col='peak time', fwhm_col='time scale')  # fwhm in minutes
    stella_p = prepare_detection_df(stella_raw, time_unit='days')  # detection times in days (TJD)
    yang_p   = prepare_detection_df(yang_raw, time_unit='days')

    # match
    matches_s, unmatched_true_s, unmatched_det_s = match_using_bench_fwhm(bench_p, stella_p, overlap_thresh=0.20, min_peak_tol_min=10.0, require_sector=True)
    matches_y, unmatched_true_y, unmatched_det_y = match_using_bench_fwhm(bench_p, yang_p, overlap_thresh=0.20, min_peak_tol_min=10.0, require_sector=True)

    TP_s = len(matches_s)
    FN_s = len([x for x in unmatched_true_s if x[0]=='true'])
    FP_s = len([x for x in unmatched_det_s if x[0]=='det'])
    recall_s = TP_s / (TP_s + FN_s) if (TP_s + FN_s) > 0 else 0.0

    print("STELLA: TP=",TP_s,"FN=",FN_s,"FP=",FP_s,"Recall=",recall_s)

    TP_y = len(matches_y)
    FN_y = len([x for x in unmatched_true_y if x[0]=='true'])
    FP_y = len([x for x in unmatched_det_y if x[0]=='det'])
    recall_y = TP_y / (TP_y + FN_y) if (TP_y + FN_y) > 0 else 0.0

    print("YANG:   TP=",TP_y,"FN=",FN_y,"FP=",FP_y,"Recall=",recall_y)

    #print("YANG:   TP=",len(matches_y),"FN=",len(unmatched_true_y),"FP=",len(unmatched_det_y))


    # save matches for inspection
    # create DataFrames from matches
    # def matches_to_df(matches, bench_df, det_df):
    #     rows=[]
    #     for (tic, sector, true_idx, det_idx, overlap_frac, peak_diff) in matches:
    #         t = bench_df.loc[true_idx] if true_idx in bench_df.index else {}
    #         d = det_df.loc[det_idx] if det_idx in det_df.index else {}
    #         rows.append({
    #             'tic': tic, 'sector': sector, 'true_idx': true_idx, 'det_idx': det_idx,
    #             'overlap_frac': overlap_frac, 'peak_diff_min': peak_diff,
    #             'bench_peak_min': t.get('bench_peak_min', np.nan),
    #             'bench_fwhm_min': t.get('bench_fwhm_min', np.nan),
    #             'bench_start_min': t.get('bench_start_min', np.nan),
    #             'bench_end_min': t.get('bench_end_min', np.nan),
    #             'det_start_min': d.get('det_start_min', np.nan),
    #             'det_peak_min': d.get('det_peak_min', np.nan),
    #             'det_end_min': d.get('det_end_min', np.nan)
    #         })
    #     return pd.DataFrame(rows)

    def matches_to_df(matches):
        return pd.DataFrame(matches, columns=[
            "tic",
            "sector",
            "true_idx",
            "det_idx",
            "overlap_frac",
            "peak_diff_min"
        ])

matches_to_df(matches_s).to_csv("matches_stella.csv", index=False)
matches_to_df(matches_y).to_csv("matches_yang.csv", index=False)

    # pd.DataFrame(matches_s).to_csv("matches_stella.csv", index=False)
    # pd.DataFrame(matches_y).to_csv("matches_yang.csv", index=False)