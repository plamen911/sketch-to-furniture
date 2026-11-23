#!/usr/bin/env python3
"""Panel furniture generator. Millimetres; Python standard library only."""

import argparse
import csv
from datetime import datetime, timezone
import hashlib
import html
import io
import json
import math
import re
import shutil
import sys
import tempfile
import zipfile
from pathlib import Path
from xml.sax.saxutils import escape

ROOT = Path(__file__).resolve().parents[1]
EPS = 1e-6
VERSION = (ROOT / "VERSION").read_text().strip()
STANDARD = {
    "particleboard": [(2800, 2070), (2800, 2100)],
    "mdf": [(2800, 1220), (2800, 2070), (2800, 1300)],
}


def number(value, label, minimum=0, strict=False):
    if (
        isinstance(value, bool)
        or not isinstance(value, (int, float))
        or not math.isfinite(value)
    ):
        raise ValueError(f"{label}: expected a finite number")
    if value < minimum or (strict and value <= minimum):
        raise ValueError(f'{label}: must be {">" if strict else ">="} {minimum}')
    return float(value)


def vec(value, label, positive=False):
    if not isinstance(value, list) or len(value) != 3:
        raise ValueError(f"{label}: expected [x,y,z]")
    return [number(v, label, 0 if positive else -1e9, positive) for v in value]


def validate_project(project):
    if not isinstance(project, dict):
        raise ValueError("Project must be a JSON object")
    if project.get("schema_version") != 1 or project.get("units") != "mm":
        raise ValueError("Expected schema_version=1 and units=mm")
    if not isinstance(project.get("name"), str) or not project["name"].strip():
        raise ValueError("Project name is required")
    materials = project.get("materials", {})
    if (
        not isinstance(materials, dict)
        or not materials
        or not isinstance(project.get("parts"), list)
        or not project["parts"]
    ):
        raise ValueError("Materials and explicit parts are required")
    for key, m in materials.items():
        if not re.fullmatch(r"[a-zA-Z][a-zA-Z0-9_-]*", key):
            raise ValueError(f"Invalid material ID: {key}")
        if not re.fullmatch(r"#[0-9a-fA-F]{6}", m.get("color", "")):
            raise ValueError(f"{key}: color must be #RRGGBB")
        number(m.get("thickness_mm"), f"{key}: thickness", strict=True)
        if not isinstance(m.get("name"), str):
            raise ValueError(f"{key}: material name required")
        stock = m.get("stock")
        if stock is None:
            continue
        x = number(stock.get("x_mm"), f"{key}: stock X", strict=True)
        y = number(stock.get("y_mm"), f"{key}: stock Y", strict=True)
        trim = number(stock.get("trim_mm"), f"{key}: trim")
        kerf = number(stock.get("kerf_mm"), f"{key}: kerf", strict=True)
        if x <= 2 * trim or y <= 2 * trim:
            raise ValueError(f"{key}: trimming leaves no usable sheet")
        if stock.get("primary_axis") not in ("X", "Y"):
            raise ValueError(f"{key}: primary_axis must be X or Y")
        if m.get("kind") in STANDARD and tuple(sorted((x, y))) not in [
            tuple(sorted(s)) for s in STANDARD[m["kind"]]
        ]:
            if not stock.get("custom_format_confirmed", False):
                raise ValueError(
                    f"{key}: nonstandard sheet needs custom_format_confirmed=true"
                )
        if not isinstance(m.get("name"), str):
            raise ValueError(f"{key}: material name required")
    ids = set()
    for p in project["parts"]:
        pid = p.get("id", "")
        if not re.fullmatch(r"[a-zA-Z][a-zA-Z0-9_-]*", pid) or pid in ids:
            raise ValueError(f"Invalid or duplicate part ID: {pid}")
        ids.add(pid)
        m = materials.get(p.get("material"))
        if m is None:
            raise ValueError(f"{pid}: unknown material")
        if not isinstance(p.get("name"), str):
            raise ValueError(f"{pid}: name required")
        p["origin_mm"] = vec(p.get("origin_mm"), f"{pid}: origin")
        p["size_mm"] = vec(p.get("size_mm"), f"{pid}: size", positive=True)
        axes = p.get("panel_axes")
        if (
            not isinstance(axes, list)
            or len(axes) != 2
            or len(set(axes)) != 2
            or any(a not in (0, 1, 2) for a in axes)
        ):
            raise ValueError(
                f"{pid}: panel_axes must contain two distinct indices 0,1,2"
            )
        t_axis = next(a for a in (0, 1, 2) if a not in axes)
        if abs(p["size_mm"][t_axis] - m["thickness_mm"]) > EPS:
            raise ValueError(
                f"{pid}: geometry thickness differs from material thickness"
            )
        bands = p.get("bands_mm")
        if not isinstance(bands, dict) or set(bands) != {"u0", "u1", "v0", "v1"}:
            raise ValueError(f"{pid}: explicitly specify all four bands: u0,u1,v0,v1")
        for edge, thickness in bands.items():
            number(thickness, f"{pid}: band {edge}")
            if thickness not in (0, 0.8, 1, 2):
                raise ValueError(f"{pid}: unsupported edge thickness {thickness}")
        if p.get("grain") not in ("u", "v", "none") or not isinstance(
            p.get("allow_rotation"), bool
        ):
            raise ValueError(f"{pid}: grain (u/v/none) and allow_rotation are required")
        if p.get("group") not in (
            "carcass",
            "front",
            "back",
            "shelf",
            "drawer",
            "plinth",
        ):
            raise ValueError(f"{pid}: unknown part group")
        cut_dimensions(p)
    for fitting in project.get("fittings", []):
        fid = fitting.get("id", "")
        if not re.fullmatch(r"[a-zA-Z][a-zA-Z0-9_-]*", fid) or fid in ids:
            raise ValueError(f"Invalid or duplicate fitting ID: {fid}")
        ids.add(fid)
        fitting["origin_mm"] = vec(fitting.get("origin_mm"), f"{fid}: origin")
        fitting["size_mm"] = vec(fitting.get("size_mm"), f"{fid}: size", positive=True)
        if fitting.get("shape", "box") not in ("box", "cylinder"):
            raise ValueError(f"{fid}: unsupported fitting shape")
        if fitting.get("shape") == "cylinder":
            axis = fitting.get("axis")
            if axis not in (0, 1, 2):
                raise ValueError(f"{fid}: cylinder axis must be 0,1,2")
        if not re.fullmatch(r"#[0-9a-fA-F]{6}", fitting.get("color", "")):
            raise ValueError(f"{fid}: fitting color must be #RRGGBB")
    if project.get("design_bounds_mm") is not None:
        bounds = project["design_bounds_mm"]
        lower = vec(bounds.get("min"), "design bounds min")
        upper = vec(bounds.get("max"), "design bounds max")
        if any(upper[k] <= lower[k] for k in range(3)):
            raise ValueError("Design bounds must have positive extents")
        for panel in project["parts"]:
            if any(
                panel["origin_mm"][k] < lower[k] - EPS
                or panel["origin_mm"][k] + panel["size_mm"][k] > upper[k] + EPS
                for k in range(3)
            ):
                raise ValueError(f'{panel["id"]}: panel outside declared design bounds')
    # Positive volume intersections are errors. Merely touching is allowed.
    for i, a in enumerate(project["parts"]):
        for b in project["parts"][i + 1 :]:
            overlap = [
                min(
                    a["origin_mm"][k] + a["size_mm"][k],
                    b["origin_mm"][k] + b["size_mm"][k],
                )
                - max(a["origin_mm"][k], b["origin_mm"][k])
                for k in range(3)
            ]
            if all(v > EPS for v in overlap):
                raise ValueError(f'3D intersection: {a["id"]} / {b["id"]}')
    return project


def cut_dimensions(part):
    u, v = (part["size_mm"][i] for i in part["panel_axes"])
    b = part["bands_mm"]
    cu, cv = u - b["u0"] - b["u1"], v - b["v0"] - b["v1"]
    if min(cu, cv) <= 0:
        raise ValueError(f'{part["id"]}: edge banding leaves no raw panel')
    return cu, cv


def raw_box(part):
    origin, size = part["origin_mm"][:], part["size_mm"][:]
    for letter, axis in zip("uv", part["panel_axes"]):
        origin[axis] += part["bands_mm"][letter + "0"]
        size[axis] -= part["bands_mm"][letter + "0"] + part["bands_mm"][letter + "1"]
    return origin, size


def orientations(part):
    u, v = cut_dimensions(part)
    # Stock grain follows global sheet Y. A grain-aligned part may have only one orientation.
    for rotated, w, h in [(False, u, v), (True, v, u)]:
        if rotated and not part["allow_rotation"]:
            continue
        if part["grain"] == "u" and not rotated:
            continue
        if part["grain"] == "v" and rotated:
            continue
        yield rotated, w, h


def nest_once(project, ordering="long"):
    """Conservative two-stage guillotine strips, primary cut axis X or Y.

    Every part has clearance for kerf between neighbours. Strip width is fixed
    by its first (widest) part; downstream crosscuts can leave rectangular waste.
    This heuristic is valid but does not guarantee minimum board count.
    """
    boards = []
    for material_id, material in project["materials"].items():
        parts = [p for p in project["parts"] if p["material"] == material_id]
        stock = material.get("stock")
        if stock is None:
            continue
        trim, kerf = stock["trim_mm"], stock["kerf_mm"]
        axis_y = stock["primary_axis"] == "Y"
        cross_cap = (stock["x_mm"] if axis_y else stock["y_mm"]) - 2 * trim
        run_cap = (stock["y_mm"] if axis_y else stock["x_mm"]) - 2 * trim
        material_boards = []

        def opts(part):
            for rotated, w, h in orientations(part):
                cross, run = (w, h) if axis_y else (h, w)
                if cross <= cross_cap + EPS and run <= run_cap + EPS:
                    yield rotated, w, h, cross, run

        keys = {
            "long": lambda p: max(cut_dimensions(p)),
            "area": lambda p: math.prod(cut_dimensions(p)),
            "short": lambda p: min(cut_dimensions(p)),
            "perimeter": lambda p: sum(cut_dimensions(p)),
        }
        parts.sort(key=keys[ordering], reverse=True)
        for part in parts:
            options = list(opts(part))
            if not options:
                raise ValueError(
                    f'{part["id"]}: cannot fit usable sheet with its grain/rotation constraints'
                )
            best = None
            # Prefer an existing strip, then a fresh strip, then a new sheet.
            for board in material_boards:
                for strip in board["strips"]:
                    for option in options:
                        rotated, w, h, cross, run = option
                        start = strip["used_run"] + (kerf if strip["placements"] else 0)
                        if (
                            cross <= strip["width"] + EPS
                            and start + run <= run_cap + EPS
                        ):
                            score = (0, strip["width"] - cross, run_cap - start - run)
                            if best is None or score < best[0]:
                                best = (score, board, strip, option, start)
                cross_start = sum(s["width"] + kerf for s in board["strips"])
                for option in options:
                    if cross_start + option[3] <= cross_cap + EPS:
                        score = (1, option[3], run_cap - option[4])
                        if best is None or score < best[0]:
                            best = (score, board, None, option, 0)
            if best is None:
                board = {
                    "id": f"{material_id}-{len(material_boards)+1}",
                    "material": material_id,
                    "stock": stock.copy(),
                    "strips": [],
                    "placements": [],
                }
                material_boards.append(board)
                option = min(options, key=lambda o: (o[3], -o[4]))
                best = ((2, 0, 0), board, None, option, 0)
            _, board, strip, option, start = best
            rotated, w, h, cross, run = option
            if strip is None:
                strip = {
                    "start": sum(s["width"] + kerf for s in board["strips"]),
                    "width": cross,
                    "used_run": 0,
                    "placements": [],
                }
                board["strips"].append(strip)
            cx, ry = trim + strip["start"], trim + start
            x, y = (cx, ry) if axis_y else (ry, cx)
            placement = {
                "part_id": part["id"],
                "x_mm": x,
                "y_mm": y,
                "width_mm": w,
                "height_mm": h,
                "rotated": rotated,
            }
            strip["placements"].append(placement)
            strip["used_run"] = start + run
            board["placements"].append(placement)
        for b in material_boards:
            area = sum(p["width_mm"] * p["height_mm"] for p in b["placements"])
            total = stock["x_mm"] * stock["y_mm"]
            usable = (stock["x_mm"] - 2 * trim) * (stock["y_mm"] - 2 * trim)
            b["part_area_mm2"] = area
            b["yield_nominal_percent"] = round(100 * area / total, 2)
            b["yield_usable_percent"] = round(100 * area / usable, 2)
            b["nonpart_area_mm2"] = total - area  # includes trim, kerf and offcuts
        boards += material_boards
    validate_layout(project, boards)
    return boards


def nest(project):
    candidates = [
        nest_once(project, ordering)
        for ordering in ("long", "area", "short", "perimeter")
    ]

    def score(boards):
        # Primary objective is stock purchase area; secondary is strip-cut length.
        return (
            sum(b["stock"]["x_mm"] * b["stock"]["y_mm"] for b in boards),
            sum(
                len(b["strips"])
                * (
                    b["stock"]["y_mm"]
                    if b["stock"]["primary_axis"] == "Y"
                    else b["stock"]["x_mm"]
                )
                for b in boards
            ),
        )

    best = min(candidates, key=score)
    validate_layout(project, best)
    return best


def nesting_bounds(project, boards):
    results = {}
    for mid, material in project["materials"].items():
        stock = material.get("stock")
        if not stock:
            continue
        parts = [p for p in project["parts"] if p["material"] == mid]
        if not parts:
            continue
        w, h = (
            stock["x_mm"] - 2 * stock["trim_mm"],
            stock["y_mm"] - 2 * stock["trim_mm"],
        )
        kerf = stock["kerf_mm"]
        area_bound = math.ceil(
            (sum(math.prod(cut_dimensions(p)) for p in parts) - EPS) / (w * h)
        )

        def compatible(a, b):
            for _, aw, ah in orientations(a):
                for _, bw, bh in orientations(b):
                    if max(aw, bw) <= w + EPS and ah + bh + kerf <= h + EPS:
                        return True
                    if aw + bw + kerf <= w + EPS and max(ah, bh) <= h + EPS:
                        return True
            return False

        graph = {p["id"]: set() for p in parts}
        for i, a in enumerate(parts):
            for b in parts[i + 1 :]:
                if not compatible(a, b):
                    graph[a["id"]].add(b["id"])
                    graph[b["id"]].add(a["id"])
        # Every clique requires separate boards; a greedy clique remains a valid lower bound.
        clique_bound = 1
        for seed in graph:
            clique = [seed]
            for vertex in sorted(graph, key=lambda k: len(graph[k]), reverse=True):
                if vertex != seed and all(vertex in graph[v] for v in clique):
                    clique.append(vertex)
            clique_bound = max(clique_bound, len(clique))
        lower = max(area_bound, clique_bound)
        count = sum(b["material"] == mid for b in boards)
        results[mid] = {
            "boards": count,
            "area_lower_bound": area_bound,
            "incompatible_parts_lower_bound": clique_bound,
            "lower_bound": lower,
            "minimum_board_count_proven": count == lower,
            "scope": "rectangular panels, declared stock/trim/kerf/grain/rotation only; no CNC or time optimality claim",
        }
    return results


def validate_layout(project, boards):
    found = []
    lookup = {p["id"]: p for p in project["parts"]}
    for b in boards:
        s = b["stock"]
        t = s["trim_mm"]
        kerf = s["kerf_mm"]
        for p in b["placements"]:
            found.append(p["part_id"])
            original = lookup[p["part_id"]]
            if original["material"] != b["material"]:
                raise ValueError("Wrong material assignment")
            u, v = cut_dimensions(original)
            expected = (v, u) if p["rotated"] else (u, v)
            if any(
                abs(a - bb) > EPS
                for a, bb in zip(expected, (p["width_mm"], p["height_mm"]))
            ):
                raise ValueError("Layout dimensions differ from cut list")
            allowed = list(orientations(original))
            if not any(o[0] == p["rotated"] for o in allowed):
                raise ValueError("Layout violates grain or rotation")
            if (
                p["x_mm"] < t - EPS
                or p["y_mm"] < t - EPS
                or p["x_mm"] + p["width_mm"] > s["x_mm"] - t + EPS
                or p["y_mm"] + p["height_mm"] > s["y_mm"] - t + EPS
            ):
                raise ValueError("Part outside usable stock")
        for i, a in enumerate(b["placements"]):
            for c in b["placements"][i + 1 :]:
                dx = max(
                    c["x_mm"] - a["x_mm"] - a["width_mm"],
                    a["x_mm"] - c["x_mm"] - c["width_mm"],
                )
                dy = max(
                    c["y_mm"] - a["y_mm"] - a["height_mm"],
                    a["y_mm"] - c["y_mm"] - c["height_mm"],
                )
                if dx < kerf - EPS and dy < kerf - EPS:
                    raise ValueError(
                        f'Missing kerf clearance: {a["part_id"]}/{c["part_id"]}'
                    )
    expected_ids = [
        p["id"]
        for p in project["parts"]
        if project["materials"][p["material"]].get("stock") is not None
    ]
    if sorted(found) != sorted(expected_ids):
        raise ValueError("Layout omits or duplicates parts")


def vertices(origin, size):
    x, y, z = origin
    w, d, h = size
    return [
        (x, y, z),
        (x + w, y, z),
        (x + w, y + d, z),
        (x, y + d, z),
        (x, y, z + h),
        (x + w, y, z + h),
        (x + w, y + d, z + h),
        (x, y + d, z + h),
    ]


FACES = [
    (0, 3, 2, 1),
    (4, 5, 6, 7),
    (0, 1, 5, 4),
    (3, 7, 6, 2),
    (0, 4, 7, 3),
    (1, 2, 6, 5),
]


def model_materials(project):
    materials = dict(project["materials"])
    for f in project.get("fittings", []):
        materials["hardware_" + f["id"]] = {"name": f["name"], "color": f["color"]}
    return materials


def model_parts(project):
    return project["parts"] + [
        dict(f, material="hardware_" + f["id"]) for f in project.get("fittings", [])
    ]


def mesh(part):
    if part.get("shape") != "cylinder":
        return vertices(part["origin_mm"], part["size_mm"]), FACES
    axis = part["axis"]
    others = [k for k in (0, 1, 2) if k != axis]
    # Cyclic basis has positive winding for X and Z, negative for Y.
    if axis == 1:
        others.reverse()
    points = []
    n = 24
    for end in (0, 1):
        for i in range(n):
            angle = 2 * math.pi * i / n
            point = part["origin_mm"][:]
            point[axis] += end * part["size_mm"][axis]
            for j, func in enumerate((math.cos, math.sin)):
                k = others[j]
                point[k] += part["size_mm"][k] / 2 * (1 + func(angle))
            points.append(point)
    polygons = [tuple(reversed(range(n))), tuple(range(n, 2 * n))]
    for i in range(n):
        j = (i + 1) % n
        polygons.append((i, j, j + n, i + n))
    return points, polygons


def export_obj(project, out):
    # Finished panel envelopes: edges are not added a second time.
    lines = ["# Units: millimetres. Finished panel envelopes.", "mtllib model.mtl"]
    mtl = []
    for mid, m in model_materials(project).items():
        rgb = [int(m["color"][i : i + 2], 16) / 255 for i in (1, 3, 5)]
        mtl += [
            f"newmtl {mid}",
            "Kd " + " ".join(f"{v:.6f}" for v in rgb),
            "Ka 0.15 0.15 0.15",
            "Ns 20",
            "",
        ]
    offset = 1
    for p in model_parts(project):
        lines += [f'o {p["id"]}', f'usemtl {p["material"]}']
        lines += ["v " + " ".join(f"{v:.6f}" for v in point) for point in mesh(p)[0]]
        lines += ["f " + " ".join(str(offset + i) for i in face) for face in mesh(p)[1]]
        offset += len(mesh(p)[0])
    (out / "model.obj").write_text("\n".join(lines) + "\n")
    (out / "model.mtl").write_text("\n".join(mtl) + "\n")


def export_dae(project, out):
    effects = []
    materials = []
    geometries = []
    nodes = []
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    for mid, m in model_materials(project).items():
        rgb = " ".join(str(int(m["color"][i : i + 2], 16) / 255) for i in (1, 3, 5))
        effects.append(
            f'<effect id="{mid}-effect"><profile_COMMON><technique sid="common"><lambert><diffuse><color>{rgb} 1</color></diffuse></lambert></technique></profile_COMMON></effect>'
        )
        materials.append(
            f'<material id="{mid}-material" name="{escape(m["name"])}"><instance_effect url="#{mid}-effect"/></material>'
        )
    for p in model_parts(project):
        points, polygons = mesh(p)
        pid = p["id"]
        coords = " ".join(str(v) for point in points for v in point)
        triangles = []
        for face in polygons:
            for i in range(1, len(face) - 1):
                triangles += [face[0], face[i], face[i + 1]]
        geometries.append(
            f"""<geometry id="{pid}-geom" name="{pid}"><mesh>
<source id="{pid}-positions"><float_array id="{pid}-array" count="{len(points)*3}">{coords}</float_array><technique_common><accessor source="#{pid}-array" count="{len(points)}" stride="3"><param name="X" type="float"/><param name="Y" type="float"/><param name="Z" type="float"/></accessor></technique_common></source>
<vertices id="{pid}-vertices"><input semantic="POSITION" source="#{pid}-positions"/></vertices><triangles count="{len(triangles)//3}" material="surface"><input semantic="VERTEX" source="#{pid}-vertices" offset="0"/><p>{' '.join(map(str,triangles))}</p></triangles></mesh></geometry>"""
        )
        nodes.append(
            f'<node id="{pid}" name="{escape(p["name"])}"><instance_geometry url="#{pid}-geom"><bind_material><technique_common><instance_material symbol="surface" target="#{p["material"]}-material"/></technique_common></bind_material></instance_geometry></node>'
        )
    dae = f"""<?xml version="1.0" encoding="utf-8"?>
<COLLADA xmlns="http://www.collada.org/2005/11/COLLADASchema" version="1.4.1"><asset><contributor><authoring_tool>Furniture CAD {VERSION}</authoring_tool></contributor><created>{timestamp}</created><modified>{timestamp}</modified><unit name="millimeter" meter="0.001"/><up_axis>Z_UP</up_axis></asset><library_effects>{''.join(effects)}</library_effects><library_materials>{''.join(materials)}</library_materials><library_geometries>{''.join(geometries)}</library_geometries><library_visual_scenes><visual_scene id="Scene" name="Scene">{''.join(nodes)}</visual_scene></library_visual_scenes><scene><instance_visual_scene url="#Scene"/></scene></COLLADA>"""
    (out / "model.dae").write_text(dae)


def csv_parts(project, out):
    columns = [
        "id",
        "name",
        "material",
        "thickness_mm",
        "finished_u_mm",
        "finished_v_mm",
        "cut_u_mm",
        "cut_v_mm",
        "band_u0_mm",
        "band_u1_mm",
        "band_v0_mm",
        "band_v1_mm",
        "band_length_m",
        "grain",
        "allow_rotation",
    ]
    with (out / "parts.csv").open("w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow(columns)
        for p in project["parts"]:
            u, v = (p["size_mm"][i] for i in p["panel_axes"])
            cu, cv = cut_dimensions(p)
            b = p["bands_mm"]
            band_length = (
                v * ((b["u0"] > 0) + (b["u1"] > 0))
                + u * ((b["v0"] > 0) + (b["v1"] > 0))
            ) / 1000
            w.writerow(
                [
                    p["id"],
                    p["name"],
                    p["material"],
                    project["materials"][p["material"]]["thickness_mm"],
                    u,
                    v,
                    cu,
                    cv,
                    *[b[k] for k in ("u0", "u1", "v0", "v1")],
                    round(band_length, 4),
                    p["grain"],
                    p["allow_rotation"],
                ]
            )


def board_svg(project, b):
    s = b["stock"]
    sw, sh = s["x_mm"], s["y_mm"]
    t = s["trim_mm"]
    # Model coordinates are X-right/Y-up, SVG Y is inverted deliberately.
    h = sh + 530
    w = sw + 180
    e = html.escape
    lines = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}">',
        '<rect width="100%" height="100%" fill="white"/>',
        f'<g font-family="Arial,sans-serif" fill="#172d3a"><text x="90" y="85" font-size="44">{e(project["name"])}</text>',
        f'<text x="90" y="145" font-size="32">{e(b["id"])} | {e(project["materials"][b["material"]]["name"])}</text>',
        f'<text x="90" y="195" font-size="28">{sw:g} × {sh:g} mm | срез {s["kerf_mm"]:g} mm | окрайчване {t:g} mm/страна</text>',
        '<text x="90" y="245" font-size="31" fill="#a03c29">ПРЕДВАРИТЕЛНО — НЕ ЗА ПРОИЗВОДСТВО</text>',
        f'<g transform="translate(90 300)"><rect width="{sw}" height="{sh}" fill="#e5e7eb" stroke="#223b4a" stroke-width="5"/>',
        f'<rect x="{t}" y="{t}" width="{sw-2*t}" height="{sh-2*t}" fill="#fff" stroke="#89979e" stroke-dasharray="12 8"/>',
    ]
    for st in b["strips"]:
        boundary = t + st["start"] + st["width"]
        if s["primary_axis"] == "Y":
            x1 = x2 = boundary
            y1 = t
            y2 = sh - t
        else:
            x1 = t
            x2 = sw - t
            y1 = y2 = sh - boundary
        lines.append(
            f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="#b6543d" stroke-width="3" stroke-dasharray="15 10"/>'
        )
    for p in b["placements"]:
        x = p["x_mm"]
        y = sh - p["y_mm"] - p["height_mm"]
        pw = p["width_mm"]
        ph = p["height_mm"]
        color = project["materials"][b["material"]]["color"]
        lines.append(
            f'<rect x="{x}" y="{y}" width="{pw}" height="{ph}" fill="{color}" stroke="#243e4b" stroke-width="3"/>'
        )
        # Rotate narrow/tall labels so labels remain inside the panel.
        cx = x + pw / 2
        cy = y + ph / 2
        angle = -90 if pw < 180 and ph > pw else 0
        length = max(pw, ph) if angle else pw
        fs = min(31, max(9, length / (len(p["part_id"]) + 1) * 1.25))
        lines.append(
            f'<g transform="translate({cx} {cy}) rotate({angle})" text-anchor="middle"><text y="-5" font-size="{fs}">{e(p["part_id"])}</text><text y="{fs}" font-size="{fs*.72}">{pw:g} × {ph:g}{" R" if p["rotated"] else ""}</text></g>'
        )
    lines += [
        "</g>",
        f'<text x="90" y="{sh+385}" font-size="27">X → / Y ↑ | Основни срезове: {s["primary_axis"]} | R: завъртян детайл</text>',
        f'<text x="90" y="{sh+430}" font-size="27">Използване на цялата плоча: {b["yield_nominal_percent"]}% | Схематично, не в мащаб за измерване</text>',
        "</g></svg>",
    ]
    return "\n".join(lines)


class PDF:
    """Small vector PDF writer for one-page-per-board landscape A4 plans; ASCII labels."""

    def __init__(self):
        self.pages = []

    def add(self, commands, width=841.89, height=595.276):
        self.pages.append(("\n".join(commands).encode("ascii"), width, height))

    def write(self, path):
        objects = [
            b"<< /Type /Catalog /Pages 2 0 R >>",
            b"",
            b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
        ]
        page_ids = []
        for stream, page_width, page_height in self.pages:
            pageid = len(objects) + 1
            contentid = pageid + 1
            page_ids.append(pageid)
            objects.append(
                f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 {page_width} {page_height}] /Resources << /Font << /F1 3 0 R >> >> /Contents {contentid} 0 R >>".encode()
            )
            objects.append(
                b"<< /Length "
                + str(len(stream)).encode()
                + b" >>\nstream\n"
                + stream
                + b"\nendstream"
            )
        objects[1] = (
            f'<< /Type /Pages /Count {len(page_ids)} /Kids [{" ".join(f"{i} 0 R" for i in page_ids)}] >>'.encode()
        )
        data = bytearray(b"%PDF-1.4\n")
        offsets = [0]
        for i, obj in enumerate(objects, 1):
            offsets.append(len(data))
            data += f"{i} 0 obj\n".encode() + obj + b"\nendobj\n"
        start = len(data)
        data += f"xref\n0 {len(objects)+1}\n0000000000 65535 f \n".encode()
        for offset in offsets[1:]:
            data += f"{offset:010d} 00000 n \n".encode()
        data += f"trailer\n<< /Size {len(objects)+1} /Root 1 0 R >>\nstartxref\n{start}\n%%EOF\n".encode()
        path.write_bytes(data)


def pdf_text(x, y, size, text):
    text = (
        str(text)
        .encode("ascii", "replace")
        .decode()
        .replace("\\", "\\\\")
        .replace("(", "\\(")
        .replace(")", "\\)")
    )
    return f"BT /F1 {size:.2f} Tf {x:.2f} {y:.2f} Td ({text}) Tj ET"


def board_pdf(boards, out):
    pdf = PDF()
    if not boards:
        pdf.add(
            [
                pdf_text(40, 540, 18, "No cutting layout: no stock formats specified."),
                pdf_text(
                    40,
                    510,
                    12,
                    "All panels remain in the model and parts.csv. Specify stock formats before cutting.",
                ),
                pdf_text(40, 480, 12, "PRELIMINARY - NOT FOR PRODUCTION"),
            ]
        )
    for page, b in enumerate(boards, 1):
        s = b["stock"]
        sw, sh = s["x_mm"], s["y_mm"]
        trim = s["trim_mm"]
        page_w, page_h = 841.89, 595.276
        available_w, available_h = page_w - 80, page_h - 195
        scale = min(available_w / sw, available_h / sh)
        ox = 40 + (available_w - sw * scale) / 2
        oy = 95 + (available_h - sh * scale) / 2
        c = [
            "0.08 0.16 0.21 rg",
            pdf_text(40, page_h - 38, 18, "Furniture CAD / " + b["id"]),
            pdf_text(
                40,
                page_h - 63,
                10,
                f'Sheet {sw:g} x {sh:g} mm | trim {trim:g} mm each edge | kerf {s["kerf_mm"]:g} mm',
            ),
            "0.65 0.18 0.12 rg",
            pdf_text(40, page_h - 86, 11, "PRELIMINARY - NOT FOR PRODUCTION"),
            "0.9 0.91 0.93 rg",
            f"{ox:.3f} {oy:.3f} {sw*scale:.3f} {sh*scale:.3f} re f",
            "1 1 1 rg",
            f"{ox+trim*scale:.3f} {oy+trim*scale:.3f} {(sw-2*trim)*scale:.3f} {(sh-2*trim)*scale:.3f} re f",
            "0.12 0.22 0.28 RG 0.6 w",
            f"{ox:.3f} {oy:.3f} {sw*scale:.3f} {sh*scale:.3f} re S",
        ]
        c += ["0.7 0.28 0.18 RG [4 3] 0 d"]
        for strip in b["strips"]:
            bound = trim + strip["start"] + strip["width"]
            x1, y1, x2, y2 = (
                (bound, trim, bound, sh - trim)
                if s["primary_axis"] == "Y"
                else (trim, bound, sw - trim, bound)
            )
            c.append(
                f"{ox+x1*scale:.3f} {oy+y1*scale:.3f} m {ox+x2*scale:.3f} {oy+y2*scale:.3f} l S"
            )
        c += ["[] 0 d", "0.12 0.22 0.28 RG 0.4 w", "0.08 0.16 0.21 rg"]
        for p in b["placements"]:
            x, y = ox + p["x_mm"] * scale, oy + p["y_mm"] * scale
            w, h = p["width_mm"] * scale, p["height_mm"] * scale
            c.append(f"{x:.3f} {y:.3f} {w:.3f} {h:.3f} re S")
            rotate = w < 35 and h > w
            available = h if rotate else w
            size = min(9, max(4, available / (len(p["part_id"]) + 2) * 1.5))
            text = p["part_id"]
            dims = f'{p["width_mm"]:g} x {p["height_mm"]:g}' + (
                " R" if p["rotated"] else ""
            )
            if rotate:
                c += [
                    "q",
                    f"0 1 -1 0 {x+w/2:.3f} {y+5:.3f} cm",
                    pdf_text(0, 3, size, text),
                    pdf_text(0, -size, size * 0.75, dims),
                    "Q",
                ]
            else:
                c += [
                    pdf_text(x + 3, y + h / 2 + 2, size, text),
                    pdf_text(x + 3, y + h / 2 - size, size * 0.75, dims),
                ]
        c += [
            pdf_text(
                40,
                72,
                10,
                f'X right / Y up | Primary rip cuts: {s["primary_axis"]} | Dashed lines: strip boundaries',
            ),
            pdf_text(
                40,
                55,
                10,
                f'Nominal sheet yield: {b["yield_nominal_percent"]}% | R: rotated part | mm; do not measure drawing',
            ),
            pdf_text(
                40,
                36,
                9,
                f"Page {page}/{len(boards)} | Board IDs match parts.csv and layout.json",
            ),
        ]
        pdf.add(c)
    pdf.write(out / "cutting.pdf")


def export_drawing(project, out):
    """Finished-envelope front, side and top orthographic views, 1:1 mm DXF."""
    parts = project["parts"]
    bounds = project.get("design_bounds_mm")
    if bounds:
        lo, hi = bounds["min"], bounds["max"]
    else:
        lo = [min(p["origin_mm"][k] for p in parts) for k in range(3)]
        hi = [max(p["origin_mm"][k] + p["size_mm"][k] for p in parts) for k in range(3)]
    W, D, H = [hi[k] - lo[k] for k in range(3)]
    views = [
        ("FRONT", 0, 2, 0, 0),
        ("SIDE", 1, 2, W + 500, 0),
        ("TOP", 0, 1, 0, H + 500),
    ]
    dxf = [
        "0",
        "SECTION",
        "2",
        "HEADER",
        "9",
        "$INSUNITS",
        "70",
        "4",
        "0",
        "ENDSEC",
        "0",
        "SECTION",
        "2",
        "ENTITIES",
    ]
    total_w = W + D + 950
    total_h = H + D + 1000
    svg = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="-300 -300 {total_w} {total_h}"><rect x="-300" y="-300" width="{total_w}" height="{total_h}" fill="white"/>',
        '<g font-family="Arial,sans-serif" fill="#193744" stroke="#193744">',
    ]

    def ln(x1, y1, x2, y2, layer="DIM"):
        dxf.extend(
            [
                "0",
                "LINE",
                "8",
                layer,
                "10",
                str(x1),
                "20",
                str(y1),
                "30",
                "0",
                "11",
                str(x2),
                "21",
                str(y2),
                "31",
                "0",
            ]
        )
        svg.append(
            f'<line x1="{x1}" y1="{total_h-600-y1}" x2="{x2}" y2="{total_h-600-y2}" stroke-width="2"/>'
        )

    def text(x, y, value, size=28):
        dxf.extend(
            [
                "0",
                "TEXT",
                "8",
                "LABELS",
                "10",
                str(x),
                "20",
                str(y),
                "30",
                "0",
                "40",
                str(size),
                "1",
                str(value),
            ]
        )
        svg.append(
            f'<text x="{x}" y="{total_h-600-y}" font-size="{size}" stroke="none">{html.escape(str(value))}</text>'
        )

    def dim(x1, y1, x2, y2, label):
        ln(x1, y1, x2, y2)
        for x, y in ((x1, y1), (x2, y2)):
            ln(x - 9, y - 9, x + 9, y + 9)
        text((x1 + x2) / 2 + 15, (y1 + y2) / 2 + 15, label)

    for name, ax, ay, ox, oy in views:
        for p in parts:
            x = p["origin_mm"][ax] - lo[ax] + ox
            y = p["origin_mm"][ay] - lo[ay] + oy
            w = p["size_mm"][ax]
            h = p["size_mm"][ay]
            for a, b in [
                ((x, y), (x + w, y)),
                ((x + w, y), (x + w, y + h)),
                ((x + w, y + h), (x, y + h)),
                ((x, y + h), (x, y)),
            ]:
                ln(*a, *b, p["id"])
        width = hi[ax] - lo[ax]
        height = hi[ay] - lo[ay]
        dim(ox, oy - 100, ox + width, oy - 100, f"{width:g} mm")
        dim(ox - 100, oy, ox - 100, oy + height, f"{height:g} mm")
        text(ox, oy + height + 70, name, 40)
    text(0, -220, "PRELIMINARY - NOT FOR PRODUCTION", 32)
    dxf += ["0", "ENDSEC", "0", "EOF"]
    svg += ["</g></svg>"]
    (out / "drawing.dxf").write_text("\n".join(dxf) + "\n")
    (out / "drawing.svg").write_text("\n".join(svg))


def dxf_layout(boards, out):
    lines = [
        "0",
        "SECTION",
        "2",
        "HEADER",
        "9",
        "$INSUNITS",
        "70",
        "4",
        "0",
        "ENDSEC",
        "0",
        "SECTION",
        "2",
        "ENTITIES",
    ]
    offset = 0

    def line(x1, y1, x2, y2, layer):
        lines.extend(
            [
                "0",
                "LINE",
                "8",
                layer,
                "10",
                str(x1),
                "20",
                str(y1),
                "30",
                "0",
                "11",
                str(x2),
                "21",
                str(y2),
                "31",
                "0",
            ]
        )

    def rect(x, y, w, h, layer):
        for a, b in [
            ((x, y), (x + w, y)),
            ((x + w, y), (x + w, y + h)),
            ((x + w, y + h), (x, y + h)),
            ((x, y + h), (x, y)),
        ]:
            line(*a, *b, layer)

    for b in boards:
        s = b["stock"]
        rect(offset, 0, s["x_mm"], s["y_mm"], "STOCK")
        t = s["trim_mm"]
        rect(offset + t, t, s["x_mm"] - 2 * t, s["y_mm"] - 2 * t, "TRIM")
        for p in b["placements"]:
            rect(
                offset + p["x_mm"],
                p["y_mm"],
                p["width_mm"],
                p["height_mm"],
                p["part_id"],
            )
            lines.extend(
                [
                    "0",
                    "TEXT",
                    "8",
                    "LABELS",
                    "10",
                    str(offset + p["x_mm"] + 5),
                    "20",
                    str(p["y_mm"] + 10),
                    "30",
                    "0",
                    "40",
                    "12",
                    "1",
                    p["part_id"],
                ]
            )
        offset += s["x_mm"] + 200
    lines += ["0", "ENDSEC", "0", "EOF"]
    (out / "cutting.dxf").write_text("\n".join(lines) + "\n")


def build(project_path, output, compare_to=None):
    project_path = Path(project_path).resolve()
    output = Path(output).resolve()
    if output.exists():
        raise ValueError(
            f"Output already exists: {output}. Choose a new folder; existing files are never overwritten."
        )
    project = validate_project(json.loads(project_path.read_text()))
    from project_history import load_snapshot, snapshot, compare

    previous = load_snapshot(compare_to) if compare_to else None
    boards = nest(project)
    output.parent.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix=".furniture-", dir=output.parent))
    try:
        source_image = project.get("source_image")
        if source_image:
            image_path = Path(source_image)
            if image_path.is_absolute() or ".." in image_path.parts:
                raise ValueError(
                    "source_image must be a relative file within the input project folder"
                )
            source = (project_path.parent / image_path).resolve()
            if not source.is_relative_to(project_path.parent) or not source.is_file():
                raise ValueError(
                    "source_image is missing or outside the input project folder"
                )
            destination = "source" + source.suffix.lower()
            shutil.copyfile(source, staging / destination)
            project["source_image"] = destination
        (staging / "project.json").write_text(
            json.dumps(project, ensure_ascii=False, indent=2)
        )
        (staging / "layout.json").write_text(
            json.dumps(boards, ensure_ascii=False, indent=2)
        )
        csv_parts(project, staging)
        export_obj(project, staging)
        export_dae(project, staging)
        export_drawing(project, staging)
        board_pdf(boards, staging)
        dxf_layout(boards, staging)
        for b in boards:
            (staging / f'{b["id"]}.svg').write_text(board_svg(project, b))
        cost = None
        if project.get("pricing"):
            from costing import write_estimate

            catalog = json.loads((ROOT / "pricing/catalog-2026-11-20.json").read_text())
            cost = write_estimate(project, boards, catalog, staging)
        revision = snapshot(project, boards, cost, VERSION)
        comparison = compare(previous, revision) if previous else None
        (staging / "revision.json").write_text(json.dumps(revision, ensure_ascii=False, indent=2))
        if comparison:
            (staging / "comparison.json").write_text(json.dumps(comparison, ensure_ascii=False, indent=2))
        png_previews = False
        try:
            from render_preview import render_both
        except ImportError:
            pass
        else:
            render_both(project, staging)
            png_previews = True
        from project_review import review_metadata

        review = review_metadata(project, boards, cost, png_previews)
        with (staging / "assembly-parts.csv").open("w", encoding="utf-8-sig", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=["number", "part_id", "name"])
            writer.writeheader()
            writer.writerows({k: item[k] for k in ("number", "part_id", "name")} for item in review["exploded"])
        (staging / "review.json").write_text(json.dumps(review, ensure_ascii=False, indent=2))
        payload = (
            json.dumps(
                {
                    "project": project,
                    "boards": boards,
                    "version": VERSION,
                    "cost": cost,
                    "review": review,
                    "comparison": comparison,
                },
                ensure_ascii=False,
            )
            .replace("<", "\\u003c")
            .replace("\u2028", "\\u2028")
            .replace("\u2029", "\\u2029")
        )
        template = (ROOT / "assets/viewer.html").read_text()
        (staging / "index.html").write_text(
            template.replace("__PROJECT_DATA__", payload)
        )
        warnings = [
            "PRELIMINARY: joinery, hardware and manufacturing tolerances are not verified by this generator.",
            "The original photographed sketch is not included in the demo; dimensions are provisional.",
            "Sheet placement compares four guillotine-strip heuristics; see nesting_bounds for any proven minimum board counts. No global cut-time optimality is claimed.",
            "Colors are approximate sRGB swatches; manufacturer textures and physical samples are not supplied.",
            "3D geometry represents finished panel envelopes. Holes, hardware and edge strips are not separately modeled.",
            "3D overlap checks do not verify drawer/door motion or hardware clearances.",
        ]
        if not png_previews:
            warnings.append(
                "PNG rendering unavailable: install Pillow or save a PNG from the HTML viewer."
            )
        if not project.get("demo", False):
            warnings.pop(1)
        if any(not m.get("stock") for m in project["materials"].values()):
            warnings.append(
                "Materials without a stock format are listed in CSV/model but excluded from sheet nesting."
            )
        report = {
            "generator_version": VERSION,
            "status": "preliminary",
            "part_count": len(project["parts"]),
            "board_count": len(boards),
            "nesting_bounds": nesting_bounds(project, boards),
            "project_input_sha256": hashlib.sha256(
                project_path.read_bytes()
            ).hexdigest(),
            "png_previews": png_previews,
            "checks": {
                "finite_dimensions": True,
                "material_thickness": True,
                "no_solid_intersections": True,
                "all_parts_nested_once": True,
                "stock_bounds_and_kerf": True,
                "grain_and_rotation": True,
            },
            "excluded_from_nesting": [
                p["id"]
                for p in project["parts"]
                if not project["materials"][p["material"]].get("stock")
            ],
            "model_bounds_mm": {
                "min": [
                    min(p["origin_mm"][k] for p in model_parts(project))
                    for k in range(3)
                ],
                "max": [
                    max(
                        p["origin_mm"][k] + p["size_mm"][k]
                        for p in model_parts(project)
                    )
                    for k in range(3)
                ],
            },
            "warnings": warnings,
            "assumptions": project.get("assumptions", []),
        }
        (staging / "validation.json").write_text(
            json.dumps(report, ensure_ascii=False, indent=2)
        )
        (staging / "IMPORT.txt").write_text(
            "All dimensions are millimetres.\nDAE declares unit meter=0.001 and Z_UP. Import with a SketchUp version that supports COLLADA; verify a known part dimension.\nOBJ uses mm coordinates and references model.mtl; keep both files together.\nNo native SKP is produced. Import into SketchUp has not been verified in this environment.\nindex.html is a self-contained local viewer; no external libraries or network requests.\ncutting.pdf: one A4 page per sheet, schematic; not to measurement scale.\nThe viewer shows finished dimensions; cutting files show raw dimensions after edge-band subtraction.\nAll outputs are PRELIMINARY; see validation.json.\n"
        )
        manifest = {
            p.name: hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(staging.iterdir())
            if p.is_file()
        }
        (staging / "manifest.json").write_text(json.dumps(manifest, indent=2))
        with zipfile.ZipFile(staging / "package.zip", "w", zipfile.ZIP_DEFLATED) as z:
            for p in sorted(staging.iterdir()):
                if p.name != "package.zip":
                    z.write(p, p.name)
        staging.rename(output)
    except BaseException:
        shutil.rmtree(staging)
        raise
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("project", type=Path)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--compare-to", type=Path, help="A previous revision.json file or output folder containing it")
    args = parser.parse_args()
    try:
        result = build(args.project, args.out, args.compare_to)
        print(
            json.dumps(
                {
                    "output": str(args.out.resolve()),
                    "parts": result["part_count"],
                    "boards": result["board_count"],
                    "status": result["status"],
                },
                ensure_ascii=False,
            )
        )
    except (ValueError, KeyError, TypeError, OSError, json.JSONDecodeError) as error:
        parser.exit(2, f"Error: {error}\n")


if __name__ == "__main__":
    main()
