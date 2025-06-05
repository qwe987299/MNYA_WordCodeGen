import os
import ffmpeg
import subprocess
import math


def add_video_watermark(video_paths, watermark_path, output_dir):
    for video_path in video_paths:
        output_path = os.path.join(output_dir, os.path.basename(video_path))
        probe = ffmpeg.probe(video_path)
        video_stream = next(
            (stream for stream in probe['streams'] if stream['codec_type'] == 'video'), None)
        if video_stream:
            video_width = int(video_stream['width'])
        else:
            print(f"無法取得影片解析度: {video_path}")
            continue
        watermark_width = int(video_width * 0.15)
        video_input = ffmpeg.input(video_path)
        watermark_input = ffmpeg.input(watermark_path).filter(
            'scale', watermark_width, -1)
        video_overlay = ffmpeg.filter(
            [video_input, watermark_input], 'overlay', 'W-w-1', '10')
        audio_stream = next(
            (stream for stream in probe['streams'] if stream['codec_type'] == 'audio'), None)
        if audio_stream:
            audio = video_input.audio
            out = (
                ffmpeg
                .output(video_overlay, audio, output_path, vcodec="libx264", acodec="copy", preset="medium", crf=23, pix_fmt="yuv420p")
                .overwrite_output()
            )
        else:
            out = (
                ffmpeg
                .output(video_overlay, output_path, vcodec="libx264", preset="medium", crf=23, pix_fmt="yuv420p")
                .overwrite_output()
            )
        out.run()


def video_repeat_fade(
    input_file, output_dir, minute, second, fade_time, out_width, out_height
):
    total_length = minute * 60 + second

    # 產生唯一的輸出檔名
    base_name = os.path.splitext(os.path.basename(input_file))[0]
    output_file = os.path.join(output_dir, f"{base_name}_loop.mp4")
    temp_file = os.path.join(output_dir, f"{base_name}_full.mp4")

    # 取得原始影片長度
    cmd = [
        'ffprobe', '-v', 'error',
        '-show_entries', 'format=duration',
        '-of', 'default=noprint_wrappers=1:nokey=1',
        input_file
    ]
    result = subprocess.run(cmd, stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE, text=True, encoding="utf-8")
    if result.returncode != 0:
        raise RuntimeError('ffprobe 執行失敗')
    duration = float(result.stdout.strip())

    # 檢查有無音訊軌
    probe_audio = [
        'ffprobe', '-v', 'error', '-select_streams', 'a:0',
        '-show_entries', 'stream=codec_type',
        '-of', 'default=noprint_wrappers=1:nokey=1',
        input_file
    ]
    res_a = subprocess.run(probe_audio, stdout=subprocess.PIPE,
                           stderr=subprocess.PIPE, text=True, encoding="utf-8")
    has_audio = res_a.stdout.strip() == "audio"

    n_repeats = math.ceil((total_length + fade_time) / duration)
    ffmpeg_cmd = ['ffmpeg', '-y']
    for _ in range(n_repeats):
        ffmpeg_cmd += ['-i', input_file]

    # 動態產生 xfade filter
    filters = []
    for i in range(n_repeats - 1):
        in1 = '[0:v]' if i == 0 else f'[v{i}]'
        in2 = f'[{i+1}:v]'
        out = f'[v{i+1}]'
        offset = (duration - fade_time) * (i + 1)
        filters.append(
            f'{in1}{in2}xfade=transition=fade:duration={fade_time}:offset={offset}{out}')
    v_last = f'[v{n_repeats-1}]' if n_repeats > 1 else '[0:v]'
    vf_scale_crop = f'scale=w=iw*max({out_width}/iw\\,{out_height}/ih):h=ih*max({out_width}/iw\\,{out_height}/ih),crop={out_width}:{out_height}'
    filters.append(f'{v_last}{vf_scale_crop}[vout]')
    audio_inputs = ''.join(
        [f'[{i}:a]' for i in range(n_repeats)]) if has_audio else ''
    audio_filter = f'{audio_inputs}concat=n={n_repeats}:v=0:a=1[aout]' if has_audio else ''
    if audio_filter:
        filter_complex = '; '.join(filters + [audio_filter])
    else:
        filter_complex = '; '.join(filters)

    ffmpeg_cmd += [
        '-filter_complex', filter_complex,
        '-map', '[vout]'
    ]
    if has_audio:
        ffmpeg_cmd += ['-map', '[aout]', '-c:a', 'aac', '-b:a', '192k']
    else:
        ffmpeg_cmd += ['-an']
    ffmpeg_cmd += [
        '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '22',
        '-pix_fmt', 'yuv420p',
        temp_file
    ]

    run1 = subprocess.run(ffmpeg_cmd, stdout=subprocess.PIPE,
                          stderr=subprocess.PIPE, text=True, encoding="utf-8")
    if run1.returncode != 0:
        raise RuntimeError(run1.stderr)

    # 裁切至指定長度
    final_cmd = [
        'ffmpeg', '-y',
        '-i', temp_file,
        '-t', str(total_length),
        '-c:v', 'copy',
        '-c:a', 'copy',
        output_file
    ]
    run2 = subprocess.run(final_cmd, stdout=subprocess.PIPE,
                          stderr=subprocess.PIPE, text=True, encoding="utf-8")
    if run2.returncode != 0:
        raise RuntimeError(run2.stderr)

    # 清理中間檔案
    try:
        os.remove(temp_file)
    except Exception:
        pass

    return output_file
