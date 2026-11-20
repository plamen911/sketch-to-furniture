#!/usr/bin/env python3
"""Export geometry-based PNG views for sharing in a phone conversation.

Optional authoring dependency: Pillow. The CAD generator/viewer do not need it.
"""

import argparse
import json
import math
from array import array
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter, ImageFont
import furniture as f

FONTS = [
    "/System/Library/Fonts/Supplemental/Arial.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
]


def font(size):
    for path in FONTS:
        if Path(path).is_file():
            return ImageFont.truetype(path, size)
    return ImageFont.load_default(size=size)


def render(project, path, inside=False, width=1000, height=1150):
    image = Image.new("RGB", (width, height), "#e9eff3")
    draw = ImageDraw.Draw(image)
    bounds = project.get("design_bounds_mm", dict(min=[0, 0, 0], max=[1200, 600, 2200]))
    lo, hi = bounds["min"], bounds["max"]
    center = [(lo[i] + hi[i]) / 2 for i in range(3)]
    yaw, pitch = -0.48, 0.16
    scale = min(
        (width - 220) / math.hypot(hi[0] - lo[0], hi[1] - lo[1]),
        (height - 310) / (hi[2] - lo[2] + 0.4 * (hi[1] - lo[1])),
    )

    def point(v):
        x, y, z = [v[i] - center[i] for i in range(3)]
        xx = x * math.cos(yaw) - y * math.sin(yaw)
        yy = x * math.sin(yaw) + y * math.cos(yaw)
        return (
            width / 2 + xx * scale,
            height / 2 - (z * math.cos(pitch) + yy * math.sin(pitch)) * scale + 25,
            yy * math.cos(pitch) - z * math.sin(pitch),
        )

    floor = [
        [lo[0] - 600, lo[1] - 600, 0],
        [hi[0] + 600, lo[1] - 600, 0],
        [hi[0] + 600, hi[1] + 600, 0],
        [lo[0] - 600, hi[1] + 600, 0],
    ]
    draw.polygon([point(v)[:2] for v in floor], fill="#dce5eb")
    shadow = Image.new("RGBA", (width, height))
    sd = ImageDraw.Draw(shadow)
    sd.polygon(
        [
            point(v)[:2]
            for v in [
                [lo[0] - 20, lo[1] - 20, 0],
                [hi[0] + 50, lo[1] - 20, 0],
                [hi[0] + 180, hi[1] + 100, 0],
                [lo[0] + 20, hi[1] + 100, 0],
            ]
        ],
        fill=(25, 45, 60, 65),
    )
    image = Image.alpha_composite(
        image.convert("RGBA"), shadow.filter(ImageFilter.GaussianBlur(18))
    ).convert("RGB")
    pixels = bytearray(image.tobytes())
    depth = array("f", [float("inf")]) * (width * height)
    faces = []
    light = [-1 / math.sqrt(14), -2 / math.sqrt(14), 3 / math.sqrt(14)]
    for part in f.model_parts(project):
        if inside and (part.get("group") == "front" or part.get("hide_with_fronts")):
            continue
        vertices, polygons = f.mesh(part)
        projected = [point(v) for v in vertices]
        color = part.get(
            "color",
            project["materials"].get(part["material"], {}).get("color", "#778188"),
        )
        rgb = [int(color[i : i + 2], 16) for i in (1, 3, 5)]
        for polygon in polygons:
            a, b, c = [vertices[i] for i in polygon[:3]]
            ab = [b[k] - a[k] for k in range(3)]
            ac = [c[k] - a[k] for k in range(3)]
            normal = [
                ab[1] * ac[2] - ab[2] * ac[1],
                ab[2] * ac[0] - ab[0] * ac[2],
                ab[0] * ac[1] - ab[1] * ac[0],
            ]
            length = math.sqrt(sum(v * v for v in normal))
            normal = [v / length for v in normal]
            facing = (normal[0] * math.sin(yaw) + normal[1] * math.cos(yaw)) * math.cos(
                pitch
            ) - normal[2] * math.sin(pitch)
            if facing >= -1e-5:
                continue
            shade = 0.82 + 0.18 * max(0, sum(a * b for a, b in zip(normal, light)))
            surface = bytes(max(0, min(255, round(v * shade))) for v in rgb)
            face = [projected[i] for i in polygon]
            faces.append(face)
            for j in range(1, len(face) - 1):
                a, b, c = face[0], face[j], face[j + 1]
                den = (b[1] - c[1]) * (a[0] - c[0]) + (c[0] - b[0]) * (a[1] - c[1])
                if abs(den) < 1e-9:
                    continue
                xmin = max(0, int(min(a[0], b[0], c[0])))
                xmax = min(width - 1, math.ceil(max(a[0], b[0], c[0])))
                ymin = max(0, int(min(a[1], b[1], c[1])))
                ymax = min(height - 1, math.ceil(max(a[1], b[1], c[1])))
                for y in range(ymin, ymax + 1):
                    for x in range(xmin, xmax + 1):
                        u = (
                            (b[1] - c[1]) * (x + 0.5 - c[0])
                            + (c[0] - b[0]) * (y + 0.5 - c[1])
                        ) / den
                        v = (
                            (c[1] - a[1]) * (x + 0.5 - c[0])
                            + (a[0] - c[0]) * (y + 0.5 - c[1])
                        ) / den
                        w = 1 - u - v
                        if min(u, v, w) < -1e-5:
                            continue
                        z = u * a[2] + v * b[2] + w * c[2]
                        i = y * width + x
                        if z < depth[i]:
                            depth[i] = z
                            pixels[i * 3 : i * 3 + 3] = surface
    for face in faces:
        for a, b in zip(face, face[1:] + face[:1]):
            count = max(1, math.ceil(math.hypot(a[0] - b[0], a[1] - b[1])))
            for j in range(count + 1):
                t = j / count
                x = round(a[0] + (b[0] - a[0]) * t)
                y = round(a[1] + (b[1] - a[1]) * t)
                z = a[2] + (b[2] - a[2]) * t
                if 0 <= x < width and 0 <= y < height:
                    i = y * width + x
                    if z <= depth[i] + 1:
                        for k in range(3):
                            pixels[i * 3 + k] = round(pixels[i * 3 + k] * 0.78)
    image = Image.frombytes("RGB", (width, height), bytes(pixels))
    draw = ImageDraw.Draw(image)
    draw.text(
        (48, 38),
        "Вътрешно разпределение" if inside else "Външен изглед",
        font=font(30),
        fill="#193744",
    )
    draw.text((48, 83), project["name"], font=font(21), fill="#57717d")
    dims = " × ".join(f"{hi[i]-lo[i]:g}" for i in (0, 2, 1)) + " mm"
    draw.text(
        (48, 118),
        dims + " · ширина × височина × дълбочина",
        font=font(17),
        fill="#57717d",
    )
    draw.text((48, height - 95), "ПРЕДВАРИТЕЛЕН ПРОЕКТ", font=font(20), fill="#925125")
    draw.text(
        (48, height - 61),
        "Приблизителни цветове. Обковът и сглобките подлежат на проверка.",
        font=font(17),
        fill="#57717d",
    )
    image.save(path)


def render_both(project, out):
    render(project, out / "exterior.png")
    render(project, out / "interior.png", inside=True)


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("project", type=Path)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()
    project = f.validate_project(json.loads(args.project.read_text()))
    args.out.mkdir(parents=True, exist_ok=True)
    if any((args.out / n).exists() for n in ("exterior.png", "interior.png")):
        ap.error("Preview images already exist")
    render_both(project, args.out)
