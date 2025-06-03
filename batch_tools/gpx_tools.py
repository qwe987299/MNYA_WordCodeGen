import os
import gpxpy
import pyproj


def convert_coordinate(org, to, lon, lat, is_int):
    transformer = pyproj.Transformer.from_crs(org, to, always_xy=True)
    lon, lat = transformer.transform(lon, lat)
    if is_int:
        return int(lon), int(lat)
    else:
        return lon, lat


def convert_gpx_files(file_paths, output_dir):
    twd67_longlat = pyproj.CRS(
        "+proj=longlat +ellps=aust_SA +towgs84=-752,-358,-179,-.0000011698,.0000018398,.0000009822,.00002329 +no_defs"
    )
    twd67_tm2 = pyproj.CRS(
        "+proj=tmerc +lat_0=0 +lon_0=121 +k=0.9999 +x_0=250000 +y_0=0 "
        "+ellps=aust_SA +towgs84=-752,-358,-179,-0.0000011698,0.0000018398,0.0000009822,0.00002329 +units=m +no_defs"
    )
    twd97_longlat = pyproj.CRS(
        "+proj=longlat +ellps=WGS84 +datum=WGS84 +no_defs"
    )
    twd97_tm2 = pyproj.CRS(
        "+proj=tmerc +lat_0=0 +lon_0=121 +k=0.9999 +x_0=250000 +y_0=0 +ellps=GRS80 +units=m +no_defs"
    )
    for file_path in file_paths:
        with open(file_path, "r", encoding="utf-8") as gpx_file:
            gpx = gpxpy.parse(gpx_file)
        wpt_info = []
        for wpt in gpx.waypoints:
            name = wpt.name
            lon = wpt.longitude
            lat = wpt.latitude
            lon_twd67_longlat, lat_twd67_longlat = convert_coordinate(
                twd97_longlat, twd67_longlat, lon, lat, False)
            lon_twd67_tm2_T, lat_twd67_tm2_T = convert_coordinate(
                twd97_longlat, twd67_tm2, lon, lat, True)
            lon_twd67_tm2_F, lat_twd67_tm2_F = convert_coordinate(
                twd97_longlat, twd67_tm2, lon, lat, False)
            lon_twd97_tm2_T, lat_twd97_tm2_T = convert_coordinate(
                twd97_longlat, twd97_tm2, lon, lat, True)
            lon_twd97_tm2_F, lat_twd97_tm2_F = convert_coordinate(
                twd97_longlat, twd97_tm2, lon, lat, False)
            wpt_info.append(
                f"{name}\n▶️ TWD67 經緯度座標值: {lon_twd67_longlat}, {lat_twd67_longlat} \
                \n▶️ TWD67 二度分帶座標值: {lon_twd67_tm2_T}, {lat_twd67_tm2_T} ({lon_twd67_tm2_F}, {lat_twd67_tm2_F}) \
                \n▶️ TWD97(WGS84) 經緯度座標值: {wpt.longitude}, {wpt.latitude} \
                \n▶️ TWD97 二度分帶座標值: {lon_twd97_tm2_T}, {lat_twd97_tm2_T} ({lon_twd97_tm2_F}, {lat_twd97_tm2_F}) \
                \n\n"
            )
        output_file_path = os.path.join(output_dir, os.path.splitext(
            os.path.basename(file_path))[0] + ".txt")
        with open(output_file_path, "w", encoding="utf-8") as output_file:
            output_file.writelines(wpt_info)
