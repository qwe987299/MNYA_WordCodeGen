import os
import ffmpeg


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
