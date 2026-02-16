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

    # 標記航點
    if config.get("MARK_WAYPOINTS", False) and gpx.waypoints:
        waypoints_to_plot = []
        
        # 1. 收集所有航點資訊
        for wp in gpx.waypoints:
            nearest_idx = -1
            
            # 優先嘗試時間匹配
            if wp.time:
                min_time_diff = float('inf')
                for i, p in enumerate(pts):
                    if p.time:
                        diff = abs((wp.time - p.time).total_seconds())
                        if diff < min_time_diff:
                            min_time_diff = diff
                            nearest_idx = i
            
            # 回退到距離匹配
            if nearest_idx == -1:
                min_dist = float('inf')
                for i, p in enumerate(pts):
                    d_val = distance(wp.latitude, wp.longitude, None, p.latitude, p.longitude, None)
                    if d_val < min_dist:
                        min_dist = d_val
                        nearest_idx = i
            
            if nearest_idx != -1:
                wp_dist_km = distances[nearest_idx] / 1000.0
                wp_ele = elevations[nearest_idx]
                waypoints_to_plot.append({
                    "name": wp.name,
                    "x": wp_dist_km,
                    "y_base": wp_ele,
                    "y_top": wp_ele  # 初始化
                })
        
        # 2. 排序與計算高度 (避免重疊)
        # 依據 X 軸 (里程) 排序
        waypoints_to_plot.sort(key=lambda w: w["x"])
        
        # 設定基礎高度偏移
        base_offset = alt_range * 0.15          # 基礎旗竿高度
        
        # 估算「一個文字寬度」在 X 軸上的距離 (Km)
        # 假設字體大小為 9pt，DPI 為 100，則字寬約為 9/72 * 100 = 12.5 px
        # 總寬度 width_px 對應 overall_distance_km
        # 所以 1 px 對應 overall_distance_km / width_px (km)
        # 這裡估算一個中文字寬約 14px (稍微寬一點以策安全)
        # 則 safe_distance_km = 14 * (overall_distance_km / width_px)
        
        # 為避免除以零，先做檢查
        if width_px > 0:
            char_width_px = 16  # 估算字寬 (含間距)
            safe_distance_km = char_width_px * (overall_distance_km / width_px)
        else:
            safe_distance_km = overall_distance_km * 0.02 # fallback

        # 重疊時 Y 軸墊高量 (讓文字錯開的距離)
        # 這裡改為動態計算，不再依賴固定步長
        y_padding = alt_range * 0.05 # 文字間的緩衝距離
        
        last_x = -999
        last_text_top = -999 # 記錄上一個點的「文字頂端」高度 (而不只是文字起始點)
        
        max_label_top = y_max # 記錄所有標籤最高點，用於擴展 Y 軸
        
        for wp in waypoints_to_plot:
            current_base_top = wp["y_base"] + base_offset
            
            # 估算當前這個點的文字高度 (每個字元估算高度)
            # 垂直文字高度約 = 字數 * (範圍 * 0.04)
            text_height_est = len(wp["name"]) * (alt_range * 0.04)
            
            # 如果與前一個點距離小於「一個文字寬度」
            # 若發生碰撞，則起始點 (y_top) 必須高於前一個點的文字頂端 + padding
            # 我們稍微放寬 safe_distance_km 的判斷 (乘 1.25 倍) 以抓到更多邊緣重疊
            if abs(wp["x"] - last_x) < (safe_distance_km * 1.25):
                wp["y_top"] = max(current_base_top, last_text_top + y_padding)
            else:
                wp["y_top"] = current_base_top
            
            # 計算該點文字的絕對頂端
            current_text_top = wp["y_top"] + text_height_est
            
            last_x = wp["x"]
            last_text_top = current_text_top
            
            # 標籤總高 = 旗竿頂 + 文字高
            if current_text_top > max_label_top:
                max_label_top = current_text_top

        # 3. 如果標籤超出邊界，擴展 Y 軸
        # 為了避免碰到標題，再多加一點緩衝
        final_y_max = max(y_max, max_label_top + (alt_range * 0.1))
        ax.set_ylim(y_min, final_y_max)
        
        # 4. 繪製
        for wp in waypoints_to_plot:
            # 畫虛線：從地面 (y_base) 到 旗竿頂 (y_top)
            ax.plot([wp["x"], wp["x"]], [wp["y_base"], wp["y_top"]], 
                    color='#E91E63', linestyle='--', linewidth=1, alpha=0.7, zorder=20)
            
            # 垂直文字處理 (插入換行符)
            vertical_name = "\n".join(list(wp["name"]))
            
            # 標註名稱
            ax.text(wp["x"], wp["y_top"] + (alt_range * 0.01), vertical_name, 
                    ha='center', va='bottom', 
                    fontsize=9, color='#C2185B', fontweight='bold', zorder=20,
                    linespacing=1.0) # 緊湊行距

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
