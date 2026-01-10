import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import os
import gpxpy
import numpy as np
import matplotlib
matplotlib.use('Agg')

# 設定字體以支援中文 (Windows 常用微軟正黑體)
plt.rcParams['font.sans-serif'] = ['Microsoft JhengHei']
plt.rcParams['axes.unicode_minus'] = False

# 8 個坡度等級與中文簡述
SLOPE_LEVELS = [
    (3,  "#4CAF50", "0-3% 平緩路段"),
    (8,  "#8BC34A", "3-8% 緩坡爬升"),
    (15, "#CDDC39", "8-15% 有感坡度"),
    (25, "#FDD835", "15-25% 辛苦陡坡"),
    (35, "#FB8C00", "25-35% 極陡路段"),
    (45, "#E53935", "35-45% 需手腳並用"),
    (60, "#B71C1C", "45-60% 極限挑戰"),
]


def get_slope_color(slope_pct):
    abs_slope = abs(slope_pct)
    for limit, color, label in SLOPE_LEVELS:
        if abs_slope < limit:
            return color
    return "#4A148C"  # >60% 技術攀登


def generate_slope_chart(file_path, output_dir, config):
    # 讀取參數
    width_px = int(config.get("WIDTH_PX", 1024))
    height_px = int(config.get("HEIGHT_PX", 768))
    dpi = int(config.get("DPI", 100))
    interval_m = int(config.get("INTERVAL_M", 200))
    bg_color = config.get("BG_COLOR", "#F5F5F5")

    file_name = os.path.basename(file_path)

    # 像素轉英吋計算
    w_inch = width_px / dpi
    h_inch = height_px / dpi

    # 解析 GPX
    with open(file_path, 'r', encoding='utf-8') as gpx_file:
        gpx = gpxpy.parse(gpx_file)

    distances, elevations = [0.0], []
    pts = [p for track in gpx.tracks for seg in track.segments for p in seg.points]
    if not pts:
        raise ValueError("GPX 檔案內無有效路點。")

    elevations.append(pts[0].elevation)
    from gpxpy.geo import distance
    total_dist_raw = 0.0
    for i in range(1, len(pts)):
        d = distance(pts[i-1].latitude, pts[i-1].longitude,
                     None, pts[i].latitude, pts[i].longitude, None)
        total_dist_raw += d
        distances.append(total_dist_raw)
        elevations.append(pts[i].elevation)

    # 重新取樣
    resampled_dist = np.arange(0, total_dist_raw, interval_m)
    if len(resampled_dist) == 0:
        resampled_dist = np.array([0.0])
    if resampled_dist[-1] < total_dist_raw:
        resampled_dist = np.append(resampled_dist, total_dist_raw)
    resampled_alt = np.interp(resampled_dist, distances, elevations)

    # 核心數據計算
    max_elevation = np.max(resampled_alt)       # 最高海拔
    overall_distance_km = total_dist_raw / 1000.0  # 總里程

    total_ascent = 0.0
    total_descent = 0.0
    dist_ascent = 0.0
    dist_descent = 0.0

    for i in range(1, len(resampled_alt)):
        diff = resampled_alt[i] - resampled_alt[i-1]
        seg_dist_km = (resampled_dist[i] - resampled_dist[i-1]) / 1000.0
        if diff > 0:
            total_ascent += diff
            dist_ascent += seg_dist_km
        elif diff < 0:
            total_descent += abs(diff)
            dist_descent += seg_dist_km

    # 建立圖表
    fig, ax = plt.subplots(figsize=(w_inch, h_inch),
                           dpi=dpi, facecolor=bg_color)

    min_alt, max_alt = min(resampled_alt), max(resampled_alt)
    alt_range = max_alt - min_alt
    if alt_range == 0:
        alt_range = 10
    bottom_padding = max(alt_range * 0.35, 100)
    y_min = min_alt - bottom_padding
    y_max = max_alt + alt_range * 0.2

    ax.set_ylim(y_min, y_max)
    ax.set_xlim(0, overall_distance_km)

    # 天空漸層藍背景
    z = np.linspace(0, 1, 100).reshape(-1, 1)
    ax.imshow(z, interpolation='bicubic', extent=[0, overall_distance_km, y_min, y_max],
              cmap=plt.get_cmap('Blues'), aspect='auto', alpha=0.2, zorder=0)

    # 逐段填色
    for i in range(len(resampled_dist) - 1):
        d1, d2 = resampled_dist[i], resampled_dist[i+1]
        a1, a2 = resampled_alt[i], resampled_alt[i+1]
        dist_diff = d2 - d1
        slope = ((a2 - a1) / dist_diff) * 100 if dist_diff > 0 else 0

        ax.fill_between([d1/1000, d2/1000], [a1, a2], y_min,
                        color=get_slope_color(slope), alpha=0.9, zorder=2)
        ax.axvline(x=d1/1000, color='white',
                   linewidth=0.5, alpha=0.3, zorder=3)

        # 標註坡度
        mid_x = (d1 + d2) / 2 / 1000
        txt_y = min_alt - (bottom_padding * 0.8)
        t_color = "white" if abs(slope) > 30 else "black"
        ax.text(mid_x, txt_y, f"{slope:.1f}%", ha='center', va='bottom', rotation=90,
                fontsize=9, fontweight='bold', color=t_color, zorder=5, clip_on=False)

        # 標註高度
        if i % 2 == 0:
            ax.text(d1/1000, a1 + (alt_range * 0.02), f"{int(a1)}m", ha='center', va='bottom',
                    fontsize=8, color='#444444', zorder=6)

    ax.plot(resampled_dist/1000, resampled_alt,
            color='black', linewidth=2, zorder=10)

    # 設置標題
    ax.set_title(file_name, fontsize=16, fontweight='bold',
                 pad=20, color='#1A237E')

    # 圖例
    legend_elements = [mpatches.Patch(color=c, label=l)
                       for _, c, l in SLOPE_LEVELS]
    legend_elements.append(mpatches.Patch(color="#4A148C", label=">60% 技術攀登"))
    ax.legend(handles=legend_elements, loc='upper center', bbox_to_anchor=(0.5, -0.12),
              ncol=4, fontsize=10, frameon=False)

    # 底部數據顯示
    left_stats = f"總里程: {overall_distance_km:.2f} km | 最高海拔: {max_elevation:.0f} m"
    right_stats = f"總爬升: {total_ascent:.0f} m ({dist_ascent:.2f} km) | 總下降: {total_descent:.0f} m ({dist_descent:.2f} km)"

    # 左方塊 (對齊左側)
    plt.figtext(0.32, 0.05, left_stats, ha="center", fontsize=11,
                bbox={"boxstyle": "round", "facecolor": "white",
                      "edgecolor": "#CCCCCC", "alpha": 0.8},
                fontweight='bold', color='#333333')

    # 右方塊 (對齊右側)
    plt.figtext(0.68, 0.05, right_stats, ha="center", fontsize=11,
                bbox={"boxstyle": "round", "facecolor": "white",
                      "edgecolor": "#CCCCCC", "alpha": 0.8},
                fontweight='bold', color='#333333')

    ax.set_xlabel("里程 (km)", fontsize=12, fontweight='bold')
    ax.set_ylabel("海拔 (m)", fontsize=12, fontweight='bold')
    ax.grid(axis='y', color='white', linestyle='--', alpha=0.6, zorder=1)
    ax.set_facecolor('none')

    for spine in ax.spines.values():
        spine.set_visible(False)

    # 輸出調整
    plt.tight_layout()
    plt.subplots_adjust(bottom=0.25, top=0.88)

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    save_path = os.path.join(
        output_dir, file_name.replace(".gpx", "_坡度分析圖.jpg"))
    plt.savefig(save_path, dpi=dpi)
    plt.close(fig)
    return save_path
