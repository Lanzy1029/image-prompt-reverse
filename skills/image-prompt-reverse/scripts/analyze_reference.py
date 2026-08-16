#!/usr/bin/env python3
"""Preserve a reference image and create deterministic color evidence."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import shutil
import struct
import subprocess
import zlib
from datetime import datetime, timezone
from pathlib import Path

MAX_EDGE = 256
TARGET_COLORS = 5
ANALYSIS_SCHEMA_VERSION = "1.2"
DISTRIBUTION_GRID_LONG_EDGE = 24
DISTRIBUTION_OUTPUT_LONG_EDGE = 1024
DISTRIBUTION_BLUR_PASSES = 2

FONT = {
    "0": ["01110", "10001", "10011", "10101", "11001", "10001", "01110"],
    "1": ["00100", "01100", "00100", "00100", "00100", "00100", "01110"],
    "2": ["01110", "10001", "00001", "00010", "00100", "01000", "11111"],
    "3": ["11110", "00001", "00001", "01110", "00001", "00001", "11110"],
    "4": ["00010", "00110", "01010", "10010", "11111", "00010", "00010"],
    "5": ["11111", "10000", "10000", "11110", "00001", "00001", "11110"],
    "6": ["01110", "10000", "10000", "11110", "10001", "10001", "01110"],
    "7": ["11111", "00001", "00010", "00100", "01000", "01000", "01000"],
    "8": ["01110", "10001", "10001", "01110", "10001", "10001", "01110"],
    "9": ["01110", "10001", "10001", "01111", "00001", "00001", "01110"],
    "A": ["01110", "10001", "10001", "11111", "10001", "10001", "10001"],
    "B": ["11110", "10001", "10001", "11110", "10001", "10001", "11110"],
    "C": ["01111", "10000", "10000", "10000", "10000", "10000", "01111"],
    "D": ["11110", "10001", "10001", "10001", "10001", "10001", "11110"],
    "E": ["11111", "10000", "10000", "11110", "10000", "10000", "11111"],
    "F": ["11111", "10000", "10000", "11110", "10000", "10000", "10000"],
    "#": ["01010", "11111", "01010", "01010", "11111", "01010", "00000"],
    ".": ["00000", "00000", "00000", "00000", "00000", "00110", "00110"],
    "%": ["11001", "11010", "00100", "01000", "10110", "00110", "00000"],
    "-": ["00000", "00000", "00000", "11111", "00000", "00000", "00000"],
    " ": ["00000"] * 7,
}

COLOR_NAMES = {
    "Black": (18, 18, 18),
    "Charcoal": (55, 58, 62),
    "Slate": (91, 101, 115),
    "White": (245, 245, 242),
    "Cream": (239, 227, 197),
    "Beige": (205, 185, 150),
    "Brown": (118, 79, 55),
    "Red": (190, 45, 45),
    "Orange": (222, 112, 39),
    "Yellow": (229, 192, 55),
    "Olive": (116, 117, 62),
    "Green": (54, 135, 80),
    "Teal": (42, 137, 137),
    "Blue": (54, 102, 190),
    "Navy": (33, 52, 92),
    "Purple": (113, 77, 151),
    "Pink": (211, 121, 154),
    "Gray": (145, 145, 145),
}


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def infer_suffix(path: Path) -> str:
    head = path.read_bytes()[:32]
    if head.startswith(b"\x89PNG\r\n\x1a\n"):
        return ".png"
    if head.startswith(b"\xff\xd8\xff"):
        return ".jpg"
    if head.startswith((b"GIF87a", b"GIF89a")):
        return ".gif"
    if head.startswith(b"RIFF") and head[8:12] == b"WEBP":
        return ".webp"
    if head.startswith(b"BM"):
        return ".bmp"
    if head.startswith((b"II*\x00", b"MM\x00*")):
        return ".tif"
    if len(head) >= 12 and head[4:8] == b"ftyp":
        brand = head[8:12]
        if brand in {b"heic", b"heix", b"hevc", b"mif1"}:
            return ".heic"
        if brand in {b"avif", b"avis"}:
            return ".avif"
    suffix = path.suffix.lower()
    if suffix in {".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp", ".tif", ".tiff", ".heic", ".avif"}:
        return {".jpeg": ".jpg", ".tiff": ".tif"}.get(suffix, suffix)
    raise ValueError("unsupported image signature")


def parse_jpeg_dimensions(data: bytes) -> tuple[int, int] | None:
    position = 2
    sof = {0xC0, 0xC1, 0xC2, 0xC3, 0xC5, 0xC6, 0xC7, 0xC9, 0xCA, 0xCB, 0xCD, 0xCE, 0xCF}
    while position + 9 < len(data):
        if data[position] != 0xFF:
            position += 1
            continue
        marker = data[position + 1]
        position += 2
        if marker in {0xD8, 0xD9}:
            continue
        if position + 2 > len(data):
            break
        length = int.from_bytes(data[position:position + 2], "big")
        if marker in sof and position + 7 <= len(data):
            height = int.from_bytes(data[position + 3:position + 5], "big")
            width = int.from_bytes(data[position + 5:position + 7], "big")
            return width, height
        if length < 2:
            break
        position += length
    return None


def ffprobe_dimensions(path: Path) -> tuple[int, int] | None:
    probe = shutil.which("ffprobe")
    if not probe:
        return None
    process = subprocess.run(
        [probe, "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width,height", "-of", "json", str(path)],
        check=False,
        capture_output=True,
        text=True,
    )
    if process.returncode:
        return None
    try:
        stream = json.loads(process.stdout)["streams"][0]
        return int(stream["width"]), int(stream["height"])
    except (KeyError, IndexError, TypeError, ValueError, json.JSONDecodeError):
        return None


def image_dimensions(path: Path) -> tuple[int, int]:
    data = path.read_bytes()
    if data.startswith(b"\x89PNG\r\n\x1a\n") and len(data) >= 24:
        return struct.unpack(">II", data[16:24])
    if data.startswith((b"GIF87a", b"GIF89a")) and len(data) >= 10:
        return struct.unpack("<HH", data[6:10])
    if data.startswith(b"BM") and len(data) >= 26:
        return abs(struct.unpack("<i", data[18:22])[0]), abs(struct.unpack("<i", data[22:26])[0])
    if data.startswith(b"\xff\xd8\xff"):
        dimensions = parse_jpeg_dimensions(data)
        if dimensions:
            return dimensions
    dimensions = ffprobe_dimensions(path)
    if dimensions:
        return dimensions
    raise ValueError("could not determine image dimensions; install ffprobe for this format")


def parse_ppm(data: bytes) -> tuple[int, int, list[tuple[int, int, int]]]:
    position = 0

    def token() -> bytes:
        nonlocal position
        while position < len(data):
            if data[position:position + 1] == b"#":
                position = data.find(b"\n", position)
                if position < 0:
                    raise ValueError("invalid PPM comment")
            elif chr(data[position]).isspace():
                position += 1
            else:
                break
        start = position
        while position < len(data) and not chr(data[position]).isspace():
            position += 1
        return data[start:position]

    if token() != b"P6":
        raise ValueError("decoder did not return binary PPM")
    width, height, maximum = int(token()), int(token()), int(token())
    if maximum != 255 or width <= 0 or height <= 0:
        raise ValueError("unsupported PPM output")
    if position < len(data) and chr(data[position]).isspace():
        position += 1
    raw = data[position:position + width * height * 3]
    if len(raw) != width * height * 3:
        raise ValueError("decoder returned incomplete pixel data")
    pixels = [(raw[i], raw[i + 1], raw[i + 2]) for i in range(0, len(raw), 3)]
    return width, height, pixels


def decode_pixels(path: Path) -> tuple[int, int, list[tuple[int, int, int]], str]:
    try:
        from PIL import Image  # type: ignore

        with Image.open(path) as image:
            image = image.convert("RGB")
            image.thumbnail((MAX_EDGE, MAX_EDGE))
            return image.width, image.height, list(image.getdata()), "Pillow"
    except ImportError:
        pass
    except Exception:
        pass

    ffmpeg = shutil.which("ffmpeg")
    if ffmpeg:
        process = subprocess.run(
            [
                ffmpeg,
                "-nostdin",
                "-v", "error",
                "-i", str(path),
                "-frames:v", "1",
                "-vf", f"scale={MAX_EDGE}:{MAX_EDGE}:force_original_aspect_ratio=decrease:flags=lanczos",
                "-f", "image2pipe",
                "-vcodec", "ppm",
                "pipe:1",
            ],
            check=False,
            capture_output=True,
        )
        if process.returncode == 0:
            width, height, pixels = parse_ppm(process.stdout)
            return width, height, pixels, "ffmpeg"

    magick = shutil.which("magick")
    if magick:
        process = subprocess.run(
            [magick, str(path), "-thumbnail", f"{MAX_EDGE}x{MAX_EDGE}", "ppm:-"],
            check=False,
            capture_output=True,
        )
        if process.returncode == 0:
            width, height, pixels = parse_ppm(process.stdout)
            return width, height, pixels, "ImageMagick"

    raise RuntimeError("no usable image decoder found; install Pillow, ffmpeg, or ImageMagick")


def srgb_to_linear(value: float) -> float:
    value /= 255.0
    return value / 12.92 if value <= 0.04045 else ((value + 0.055) / 1.055) ** 2.4


def rgb_to_lab(rgb: tuple[float, float, float]) -> tuple[float, float, float]:
    r, g, b = (srgb_to_linear(channel) for channel in rgb)
    x = (r * 0.4124 + g * 0.3576 + b * 0.1805) / 0.95047
    y = (r * 0.2126 + g * 0.7152 + b * 0.0722)
    z = (r * 0.0193 + g * 0.1192 + b * 0.9505) / 1.08883

    def pivot(value: float) -> float:
        return value ** (1 / 3) if value > 0.008856 else 7.787 * value + 16 / 116

    fx, fy, fz = pivot(x), pivot(y), pivot(z)
    return 116 * fy - 16, 500 * (fx - fy), 200 * (fy - fz)


def distance(a: tuple[float, float, float], b: tuple[float, float, float]) -> float:
    return math.sqrt(sum((a[i] - b[i]) ** 2 for i in range(3)))


def representative(group: list[tuple[int, int, int]]) -> tuple[float, float, float]:
    size = len(group)
    return tuple(sum(pixel[i] for pixel in group) / size for i in range(3))


def median_cut(pixels: list[tuple[int, int, int]], target: int = 16) -> list[list[tuple[int, int, int]]]:
    groups = [pixels]
    while len(groups) < target:
        candidates = []
        for index, group in enumerate(groups):
            if len(group) < 2:
                continue
            ranges = [max(pixel[c] for pixel in group) - min(pixel[c] for pixel in group) for c in range(3)]
            candidates.append((max(ranges) * math.sqrt(len(group)), index, ranges.index(max(ranges))))
        if not candidates:
            break
        _, index, channel = max(candidates)
        group = sorted(groups.pop(index), key=lambda pixel: pixel[channel])
        middle = len(group) // 2
        groups.extend((group[:middle], group[middle:]))
    return groups


def extract_palette(pixels: list[tuple[int, int, int]], target: int = TARGET_COLORS) -> list[dict[str, object]]:
    accepted = [pixel for pixel in pixels if 7 <= pixel[0] * 0.2126 + pixel[1] * 0.7152 + pixel[2] * 0.0722 <= 248]
    working = accepted if len(accepted) >= 24 else pixels
    pixel_labs = [rgb_to_lab(pixel) for pixel in working]
    buckets = sorted(median_cut(working), key=len, reverse=True)
    centers_rgb: list[tuple[float, float, float]] = []
    for bucket in buckets:
        candidate = representative(bucket)
        if not centers_rgb or min(distance(rgb_to_lab(candidate), rgb_to_lab(center)) for center in centers_rgb) > 5:
            centers_rgb.append(candidate)
        if len(centers_rgb) == target:
            break
    if not centers_rgb:
        raise ValueError("image has no analyzable pixels")
    centers = [rgb_to_lab(center) for center in centers_rgb]

    assignments = [0] * len(working)
    for _ in range(10):
        for index, lab in enumerate(pixel_labs):
            assignments[index] = min(range(len(centers)), key=lambda item: distance(lab, centers[item]))
        sums = [[0.0, 0.0, 0.0, 0] for _ in centers]
        for lab, assignment in zip(pixel_labs, assignments):
            for channel in range(3):
                sums[assignment][channel] += lab[channel]
            sums[assignment][3] += 1
        centers = [
            tuple(sums[index][channel] / sums[index][3] for channel in range(3)) if sums[index][3] else center
            for index, center in enumerate(centers)
        ]

    rgb_sums = [[0.0, 0.0, 0.0, 0] for _ in centers]
    for pixel, lab in zip(working, pixel_labs):
        assignment = min(range(len(centers)), key=lambda item: distance(lab, centers[item]))
        for channel in range(3):
            rgb_sums[assignment][channel] += pixel[channel]
        rgb_sums[assignment][3] += 1

    colors = []
    for item in rgb_sums:
        if not item[3]:
            continue
        rgb = tuple(round(item[channel] / item[3]) for channel in range(3))
        colors.append({"rgb": rgb, "count": item[3]})
    colors.sort(key=lambda item: int(item["count"]), reverse=True)
    total = sum(int(item["count"]) for item in colors)

    roles = ["support"] * len(colors)
    roles[0] = "dominant"
    remaining = set(range(1, len(colors)))
    if remaining:
        shadow = min(remaining, key=lambda i: sum(colors[i]["rgb"]))  # type: ignore[arg-type]
        roles[shadow] = "shadow"
        remaining.remove(shadow)
    if remaining:
        highlight = max(remaining, key=lambda i: sum(colors[i]["rgb"]))  # type: ignore[arg-type]
        roles[highlight] = "highlight"
        remaining.remove(highlight)
    if remaining:
        def chroma(index: int) -> int:
            rgb = colors[index]["rgb"]  # type: ignore[assignment]
            return max(rgb) - min(rgb)
        accent = max(remaining, key=chroma)
        roles[accent] = "accent"

    result = []
    for index, item in enumerate(colors):
        rgb = item["rgb"]  # type: ignore[assignment]
        nearest = min(COLOR_NAMES, key=lambda name: distance(rgb, COLOR_NAMES[name]))
        result.append({
            "hex": "#" + "".join(f"{channel:02X}" for channel in rgb),
            "rgb": list(rgb),
            "ratio": round(int(item["count"]) * 100 / total, 1),
            "role": roles[index],
            "name_en": nearest,
        })
    return result


def tonal_profile(pixels: list[tuple[int, int, int]]) -> dict[str, str]:
    lumas = [pixel[0] * 0.2126 + pixel[1] * 0.7152 + pixel[2] * 0.0722 for pixel in pixels]
    average = sum(lumas) / len(lumas)
    deviation = math.sqrt(sum((value - average) ** 2 for value in lumas) / len(lumas))
    saturations = []
    for pixel in pixels:
        maximum, minimum = max(pixel), min(pixel)
        saturations.append(0 if maximum == 0 else (maximum - minimum) / maximum)
    saturation = sum(saturations) / len(saturations)
    warmth = sum(pixel[0] - pixel[2] for pixel in pixels) / len(pixels)
    return {
        "temperature": "warm" if warmth > 14 else "cool" if warmth < -14 else "balanced",
        "contrast": "low" if deviation < 32 else "medium" if deviation < 62 else "high",
        "saturation": "muted" if saturation < 0.24 else "moderate" if saturation < 0.5 else "vivid",
    }


def set_pixel(canvas: bytearray, width: int, height: int, x: int, y: int, rgb: tuple[int, int, int]) -> None:
    if 0 <= x < width and 0 <= y < height:
        offset = (y * width + x) * 3
        canvas[offset:offset + 3] = bytes(rgb)


def fill_rect(canvas: bytearray, width: int, height: int, x: int, y: int, w: int, h: int, rgb: tuple[int, int, int]) -> None:
    x0, y0, x1, y1 = max(0, x), max(0, y), min(width, x + w), min(height, y + h)
    row = bytes(rgb) * max(0, x1 - x0)
    for row_y in range(y0, y1):
        offset = (row_y * width + x0) * 3
        canvas[offset:offset + len(row)] = row


def draw_text(canvas: bytearray, width: int, height: int, x: int, y: int, text: str, rgb: tuple[int, int, int], scale: int = 2) -> None:
    cursor = x
    for character in text.upper():
        glyph = FONT.get(character, FONT[" "])
        for row, bits in enumerate(glyph):
            for column, enabled in enumerate(bits):
                if enabled == "1":
                    fill_rect(canvas, width, height, cursor + column * scale, y + row * scale, scale, scale, rgb)
        cursor += 6 * scale


def png_chunk(kind: bytes, payload: bytes) -> bytes:
    return struct.pack(">I", len(payload)) + kind + payload + struct.pack(">I", zlib.crc32(kind + payload) & 0xFFFFFFFF)


def write_palette_png(path: Path, colors: list[dict[str, object]]) -> None:
    width, height = 1000, 240
    canvas = bytearray(bytes((247, 244, 237)) * width * height)
    count = len(colors)
    for index, color in enumerate(colors):
        x0 = round(index * width / count)
        x1 = round((index + 1) * width / count)
        rgb = tuple(color["rgb"])  # type: ignore[arg-type]
        fill_rect(canvas, width, height, x0, 0, x1 - x0, 168, rgb)
        draw_text(canvas, width, height, x0 + 14, 184, str(color["hex"]), (28, 29, 32), 2)
        draw_text(canvas, width, height, x0 + 14, 210, f"{float(color['ratio']):.1f}%", (88, 89, 94), 2)
    raw = b"".join(b"\x00" + bytes(canvas[row * width * 3:(row + 1) * width * 3]) for row in range(height))
    png = (
        b"\x89PNG\r\n\x1a\n"
        + png_chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0))
        + png_chunk(b"IDAT", zlib.compress(raw, 9))
        + png_chunk(b"IEND", b"")
    )
    path.write_bytes(png)


def downsample_spatial_grid(
    pixels: list[tuple[int, int, int]],
    width: int,
    height: int,
    target_width: int,
    target_height: int,
) -> list[tuple[int, int, int]]:
    """Average rectangular source regions into a coarse spatial color grid."""
    result = []
    for target_y in range(target_height):
        source_y0 = target_y * height // target_height
        source_y1 = max(source_y0 + 1, (target_y + 1) * height // target_height)
        for target_x in range(target_width):
            source_x0 = target_x * width // target_width
            source_x1 = max(source_x0 + 1, (target_x + 1) * width // target_width)
            red = green = blue = count = 0
            for source_y in range(source_y0, min(source_y1, height)):
                row = source_y * width
                for source_x in range(source_x0, min(source_x1, width)):
                    pixel = pixels[row + source_x]
                    red += pixel[0]
                    green += pixel[1]
                    blue += pixel[2]
                    count += 1
            result.append((round(red / count), round(green / count), round(blue / count)))
    return result


def box_blur_grid(
    pixels: list[tuple[int, int, int]],
    width: int,
    height: int,
    passes: int = DISTRIBUTION_BLUR_PASSES,
) -> list[tuple[int, int, int]]:
    """Blur a small RGB grid while retaining large-scale color placement."""
    current = pixels
    for _ in range(passes):
        blurred = []
        for y in range(height):
            for x in range(width):
                red = green = blue = count = 0
                for neighbor_y in range(max(0, y - 1), min(height, y + 2)):
                    row = neighbor_y * width
                    for neighbor_x in range(max(0, x - 1), min(width, x + 2)):
                        pixel = current[row + neighbor_x]
                        red += pixel[0]
                        green += pixel[1]
                        blue += pixel[2]
                        count += 1
                blurred.append((round(red / count), round(green / count), round(blue / count)))
        current = blurred
    return current


def bilinear_upscale(
    pixels: list[tuple[int, int, int]],
    width: int,
    height: int,
    target_width: int,
    target_height: int,
) -> bytearray:
    """Render a coarse color grid as a smooth RGB raster."""
    x_samples = []
    for target_x in range(target_width):
        source_x = (target_x + 0.5) * width / target_width - 0.5
        x0 = max(0, min(width - 1, math.floor(source_x)))
        x1 = max(0, min(width - 1, x0 + 1))
        x_samples.append((x0, x1, max(0.0, min(1.0, source_x - x0))))

    canvas = bytearray(target_width * target_height * 3)
    for target_y in range(target_height):
        source_y = (target_y + 0.5) * height / target_height - 0.5
        y0 = max(0, min(height - 1, math.floor(source_y)))
        y1 = max(0, min(height - 1, y0 + 1))
        y_weight = max(0.0, min(1.0, source_y - y0))
        for target_x, (x0, x1, x_weight) in enumerate(x_samples):
            top_left = pixels[y0 * width + x0]
            top_right = pixels[y0 * width + x1]
            bottom_left = pixels[y1 * width + x0]
            bottom_right = pixels[y1 * width + x1]
            offset = (target_y * target_width + target_x) * 3
            for channel in range(3):
                top = top_left[channel] * (1 - x_weight) + top_right[channel] * x_weight
                bottom = bottom_left[channel] * (1 - x_weight) + bottom_right[channel] * x_weight
                canvas[offset + channel] = round(top * (1 - y_weight) + bottom * y_weight)
    return canvas


def write_rgb_png(path: Path, width: int, height: int, pixels: bytes | bytearray) -> None:
    raw = b"".join(b"\x00" + bytes(pixels[row * width * 3:(row + 1) * width * 3]) for row in range(height))
    png = (
        b"\x89PNG\r\n\x1a\n"
        + png_chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0))
        + png_chunk(b"IDAT", zlib.compress(raw, 9))
        + png_chunk(b"IEND", b"")
    )
    path.write_bytes(png)


def write_color_distribution_png(
    path: Path,
    original_width: int,
    original_height: int,
    sample_width: int,
    sample_height: int,
    sample_pixels: list[tuple[int, int, int]],
) -> dict[str, object]:
    """Create a detail-suppressed map of large-scale color and luminance placement."""
    grid_scale = DISTRIBUTION_GRID_LONG_EDGE / max(sample_width, sample_height)
    grid_width = max(4, round(sample_width * grid_scale))
    grid_height = max(4, round(sample_height * grid_scale))
    coarse = downsample_spatial_grid(sample_pixels, sample_width, sample_height, grid_width, grid_height)
    coarse = box_blur_grid(coarse, grid_width, grid_height)

    output_scale = DISTRIBUTION_OUTPUT_LONG_EDGE / max(original_width, original_height)
    output_width = max(1, round(original_width * output_scale))
    output_height = max(1, round(original_height * output_scale))
    raster = bilinear_upscale(coarse, grid_width, grid_height, output_width, output_height)
    write_rgb_png(path, output_width, output_height, raster)
    return {
        "method": "coarse spatial averaging, two-pass box blur, and bilinear reconstruction",
        "grid_dimensions": {"width": grid_width, "height": grid_height},
        "pixel_dimensions": {"width": output_width, "height": output_height},
        "purpose": "Large-scale color and luminance placement reference with identifying detail intentionally suppressed.",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input_image", type=Path)
    parser.add_argument("result_dir", type=Path)
    args = parser.parse_args()

    source = args.input_image.resolve()
    if not source.is_file() or source.stat().st_size == 0:
        raise FileNotFoundError(f"input image not found or empty: {source}")
    suffix = infer_suffix(source)
    result_dir = args.result_dir.resolve()
    result_dir.mkdir(parents=True, exist_ok=True)
    protected = [
        result_dir / f"original-image{suffix}",
        result_dir / "color-palette.png",
        result_dir / "color-distribution-map.png",
        result_dir / "image-analysis.json",
    ]
    if any(path.exists() for path in protected):
        raise FileExistsError("result directory already contains analyzer outputs; use a new unique directory")

    original = result_dir / f"original-image{suffix}"
    shutil.copy2(source, original)
    original_width, original_height = image_dimensions(source)
    sample_width, sample_height, pixels, decoder = decode_pixels(source)
    colors = extract_palette(pixels)
    profile = tonal_profile(pixels)
    palette_path = result_dir / "color-palette.png"
    write_palette_png(palette_path, colors)
    distribution_path = result_dir / "color-distribution-map.png"
    distribution = write_color_distribution_png(
        distribution_path,
        original_width,
        original_height,
        sample_width,
        sample_height,
        pixels,
    )

    divisor = math.gcd(original_width, original_height)
    ratio = f"{original_width // divisor}:{original_height // divisor}"
    orientation = "square" if original_width == original_height else "landscape" if original_width > original_height else "portrait"
    analysis = {
        "analysis_schema_version": ANALYSIS_SCHEMA_VERSION,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "original_file": original.name,
        "source_sha256": file_sha256(original),
        "source_bytes": original.stat().st_size,
        "pixel_dimensions": {"width": original_width, "height": original_height},
        "aspect_ratio": ratio,
        "orientation": orientation,
        "sample_dimensions": {"width": sample_width, "height": sample_height},
        "decoder": decoder,
        "palette_file": palette_path.name,
        "palette": colors,
        "color_distribution_file": distribution_path.name,
        "color_distribution": distribution,
        "tonal_profile": profile,
        "measurement_note": "Palette ratios and the blurred spatial color map are deterministic estimates from a decoder-scaled pixel sample; semantic observations require visual inspection.",
    }
    analysis_path = result_dir / "image-analysis.json"
    analysis_path.write_text(json.dumps(analysis, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "status": "ok",
        "result_dir": str(result_dir),
        "original": original.name,
        "aspect_ratio": ratio,
        "colors": colors,
        "color_distribution": distribution_path.name,
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
