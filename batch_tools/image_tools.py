import os
from PIL import Image, ImageEnhance, ImageDraw, ImageFilter
import subprocess


def add_watermark(image_paths, watermark_path, output_dir):
    watermark = Image.open(watermark_path).convert("RGBA")
    watermark_alpha = watermark.split()[-1]
    watermark_alpha = ImageEnhance.Brightness(watermark_alpha).enhance(0.7)
    watermark.putalpha(watermark_alpha)

    for image_path in image_paths:
        image = Image.open(image_path)
        if image.size[0] < 100 or image.size[1] < 50:
            ratio = max(100 / image.size[0], 50 / image.size[1])
            new_size = (int(image.size[0] * ratio), int(image.size[1] * ratio))
            image = image.resize(new_size)
        new_image = Image.new("RGBA", image.size, (0, 0, 0, 0))
        new_image.paste(image, (0, 0))
        watermark_position = (
            image.size[0] - watermark.size[0] - 3,
            image.size[1] - watermark.size[1] - 1
        )
        new_image.alpha_composite(watermark, watermark_position)
        filename = os.path.basename(image_path)
        output_path = os.path.join(
            output_dir, os.path.splitext(filename)[0] + ".jpg")
        new_image.convert("RGB").save(output_path)


def merge_images(image_paths, output_dir):
    # 單數時最後一張不處理
    if len(image_paths) % 2 == 1:
        image_paths = image_paths[:-1]
    for i in range(0, len(image_paths), 2):
        image1 = Image.open(image_paths[i])
        image2 = Image.open(image_paths[i+1])
        width = image1.width + image2.width
        height = image1.height
        new_image = Image.new('RGB', (width, height))
        new_image.paste(image1, (0, 0))
        new_image.paste(image2, (image1.width, 0))
        output_path = os.path.join(output_dir, f'merge_{i//2}.jpg')
        new_image.save(output_path)


def split_and_merge_image(file_path, output_dir):
    image = Image.open(file_path)
    width, height = image.size
    left = image.crop((0, 0, width/2, height))
    right = image.crop((width/2, 0, width, height))
    new_image = Image.new(
        'RGB', (int(width/2), int(height*2)), (255, 255, 255))
    new_image.paste(left, (0, 0))
    new_image.paste(right, (0, height))
    output_path = os.path.join(output_dir, os.path.splitext(
        os.path.basename(file_path))[0] + '.jpg')
    new_image.save(output_path)


def center_process_images(image_paths, output_dir, target_size=(1024, 768)):
    for image_path in image_paths:
        filename = os.path.basename(image_path)
        output_path = os.path.join(
            output_dir, os.path.splitext(filename)[0] + '.jpg')
        try:
            original_img = Image.open(image_path)
            orig_w, orig_h = original_img.size
            scale_w = target_size[0] / orig_w
            scale_h = target_size[1] / orig_h
            scale_factor = max(scale_w, scale_h)
            bg_w = int(orig_w * scale_factor)
            bg_h = int(orig_h * scale_factor)
            background = original_img.resize(
                (bg_w, bg_h), Image.Resampling.LANCZOS)
            background = background.filter(ImageFilter.GaussianBlur(20))
            final_bg = Image.new('RGB', target_size, (0, 0, 0))
            offset_x = (target_size[0] - bg_w) // 2
            offset_y = (target_size[1] - bg_h) // 2
            final_bg.paste(background, (offset_x, offset_y))

            scale_factor2 = min(scale_w, scale_h)
            new_w = int(orig_w * scale_factor2)
            new_h = int(orig_h * scale_factor2)
            scaled_img = original_img.resize(
                (new_w, new_h), Image.Resampling.LANCZOS)
            pos_x = (target_size[0] - new_w) // 2
            pos_y = (target_size[1] - new_h) // 2

            blur_radius = 5
            shadow_opacity = 200
            shadow_w = new_w + 2 * blur_radius
            shadow_h = new_h + 2 * blur_radius
            shadow_img = Image.new(
                'RGBA', (shadow_w, shadow_h), (255, 255, 255, 0))
            draw = ImageDraw.Draw(shadow_img)
            draw.rectangle([blur_radius, blur_radius, blur_radius+new_w, blur_radius+new_h],
                           fill=(255, 255, 255, shadow_opacity))
            shadow_img = shadow_img.filter(
                ImageFilter.GaussianBlur(blur_radius))
            final_bg.paste(shadow_img, (pos_x-blur_radius,
                           pos_y-blur_radius), shadow_img)
            final_bg.paste(scaled_img, (pos_x, pos_y))
            final_bg.save(output_path, format="JPEG", quality=90)
        except Exception as e:
            print(f"處理 {filename} 時發生錯誤: {e}")


def compress_images_by_cjpeg(
    image_paths, cjpeg_path="cjpeg.exe",
    quality=85, progressive=True, overwrite=True
):
    output_files = []
    failed_files = []
    for src_path in image_paths:
        if not os.path.isfile(src_path):
            continue
        filename = os.path.basename(src_path)
        src_dir = os.path.dirname(src_path)
        # 覆蓋模式：先輸出到暫存檔
        if overwrite:
            dest_path = os.path.join(src_dir, filename + ".tmp.jpg")
        else:
            out_dir = os.path.join(src_dir, "output")
            os.makedirs(out_dir, exist_ok=True)
            dest_path = os.path.join(out_dir, filename)
        # 組合參數
        cmd = [
            cjpeg_path,
            "-quality", str(quality),
            "-optimize",
        ]
        if progressive:
            cmd.append("-progressive")
        else:
            cmd.append("-baseline")
        cmd += [
            "-outfile", dest_path,
            src_path
        ]
        # 執行 cjpeg.exe
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            if overwrite:
                try:
                    os.replace(dest_path, src_path)
                    output_files.append(src_path)
                except Exception as e:
                    failed_files.append((src_path, str(e)))
            else:
                output_files.append(dest_path)
        else:
            failed_files.append((src_path, result.stderr))
    return output_files, failed_files
