import os
import numpy as np
from PIL import Image
import cv2


def webp_to_mp4(webp_files, output_dir):
    for webp_path in webp_files:
        try:
            im = Image.open(webp_path)
        except Exception as e:
            print(f"無法開啟 {os.path.basename(webp_path)}：{e}")
            continue

        frames = []
        durations = []
        try:
            while True:
                frame = im.copy().convert("RGB")
                frames.append(np.array(frame))
                durations.append(im.info.get("duration", 100))
                im.seek(im.tell() + 1)
        except EOFError:
            pass  # 幀讀取結束

        if len(frames) == 0:
            print(f"{os.path.basename(webp_path)} 中沒有讀取到任何幀")
            continue

        # 以第一個幀的 duration 計算 fps
        fps = 1000.0 / durations[0] if durations[0] else 10
        height, width, _ = frames[0].shape
        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        output_filename = os.path.splitext(
            os.path.basename(webp_path))[0] + ".mp4"
        output_path = os.path.join(output_dir, output_filename)
        video_writer = cv2.VideoWriter(
            output_path, fourcc, fps, (width, height))

        for frame in frames:
            frame_bgr = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
            video_writer.write(frame_bgr)

        video_writer.release()
