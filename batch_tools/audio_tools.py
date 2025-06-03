import os
import pydub


def merge_audio(files, output_dir):
    if len(files) < 2:
        return None
    audio_files = [pydub.AudioSegment.from_file(file) for file in files]
    combined_audio = pydub.AudioSegment.empty()
    for audio in audio_files:
        combined_audio += audio
    output_file = os.path.join(output_dir, os.path.splitext(
        os.path.basename(files[0]))[0] + "_merge.mp3")
    combined_audio.export(output_file, format="mp3", bitrate="320k")
    return output_file
