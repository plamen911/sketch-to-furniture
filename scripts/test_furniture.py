#!/usr/bin/env python3
"""Behavioral checks for geometry, cut arithmetic, nesting and CAD exports."""

import copy
import csv
import io
import json
import math
import tempfile
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

import furniture as f
from make_wardrobe import make_project


class FurnitureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        (f.ROOT / "projects").mkdir(exist_ok=True)

    def setUp(self):
        self.p = make_project()

    def assert_invalid(self, project, fragment):
        with self.assertRaisesRegex(ValueError, fragment):
            f.validate_project(project)

    def test_reference_dimension_chains(self):
        p = f.validate_project(self.p)
        parts = {q["id"]: q for q in p["parts"]}
        self.assertEqual(parts["SIDE_L"]["size_mm"][2] + 100, 2200)
        self.assertEqual(18 + 573 + 18 + 573 + 18, 1200)
        self.assertEqual(18 + 2 + 577 + 3, 600)
        bottom = parts["SHELF_R2"]["origin_mm"][2] + 18
        self.assertEqual(parts["TOP"]["origin_mm"][2] - bottom, 1100)
        left = (
            [parts["DRAWER_TOP"]]
            + [parts[f"SHELF_L{i}"] for i in (1, 2, 3)]
            + [parts["TOP"]]
        )
        gaps = [
            b["origin_mm"][2] - a["origin_mm"][2] - 18 for a, b in zip(left, left[1:])
        ]
        self.assertEqual(gaps, [402.5] * 4)
        right = [parts["BOTTOM"], parts["SHELF_R1"], parts["SHELF_R2"]]
        self.assertEqual(
            [
                b["origin_mm"][2] - a["origin_mm"][2] - 18
                for a, b in zip(right, right[1:])
            ],
            [464] * 2,
        )

    def test_edge_bands_and_model_envelope(self):
        f.validate_project(self.p)
        door = next(p for p in self.p["parts"] if p["id"] == "DOOR_R")
        self.assertEqual(f.cut_dimensions(door), (595, 2094))
        origin, size = f.raw_box(door)
        self.assertEqual(size, [595, 18, 2094])
        self.assertEqual(origin, [602, 0, 103])

    def test_incomplete_and_nonfinite_inputs(self):
        p = copy.deepcopy(self.p)
        p["parts"][0]["size_mm"][0] = float("nan")
        self.assert_invalid(p, "finite")
        p = copy.deepcopy(self.p)
        del p["parts"][0]["bands_mm"]["v1"]
        self.assert_invalid(p, "four bands")
        p = copy.deepcopy(self.p)
        p["parts"][0]["size_mm"][0] = 16
        self.assert_invalid(p, "thickness")
        p = copy.deepcopy(self.p)
        p["parts"][0]["size_mm"][0] = -1
        self.assert_invalid(p, "must be")

    def test_duplicate_and_collision(self):
        p = copy.deepcopy(self.p)
        p["parts"][1]["id"] = p["parts"][0]["id"]
        self.assert_invalid(p, "duplicate")
        p = copy.deepcopy(self.p)
        p["parts"][1]["origin_mm"] = p["parts"][0]["origin_mm"][:]
        self.assert_invalid(p, "intersection")

    def test_nesting_is_complete_and_has_kerf(self):
        p = f.validate_project(self.p)
        boards = f.nest(p)
        self.assertEqual(len(boards), 4)
        self.assertTrue(
            all(
                r["minimum_board_count_proven"]
                for r in f.nesting_bounds(p, boards).values()
            )
        )
        self.assertEqual(
            sorted(b["material"] for b in boards), ["cream", "cream", "white", "white"]
        )
        self.assertEqual(sum(len(b["placements"]) for b in boards), 25)
        self.assertTrue(
            all(
                b["stock"]["x_mm"] == 2800 and b["stock"]["primary_axis"] == "Y"
                for b in boards
            )
        )
        bad = copy.deepcopy(boards)
        bad[0]["placements"][0]["x_mm"] = 0
        with self.assertRaisesRegex(ValueError, "outside"):
            f.validate_layout(p, bad)
        bad = copy.deepcopy(boards)
        placements = bad[0]["placements"]
        placements[1]["x_mm"] = placements[0]["x_mm"]
        placements[1]["y_mm"] = placements[0]["y_mm"]
        with self.assertRaisesRegex(ValueError, "kerf"):
            f.validate_layout(p, bad)

    def test_axis_x_and_axis_y(self):
        for axis in ("X", "Y"):
            p = copy.deepcopy(self.p)
            for m in p["materials"].values():
                if m["stock"]:
                    m["stock"]["primary_axis"] = axis
            boards = f.nest(f.validate_project(p))
            for b in boards:
                for st in b["strips"]:
                    fixed = [
                        q["x_mm"] if axis == "Y" else q["y_mm"]
                        for q in st["placements"]
                    ]
                    self.assertTrue(all(v == fixed[0] for v in fixed))

    def test_grain_enforced(self):
        p = copy.deepcopy(self.p)
        door = next(q for q in p["parts"] if q["id"] == "DOOR_R")
        door["grain"] = "v"  # must follow sheet Y=1220, cannot fit its 2094mm length
        with self.assertRaisesRegex(ValueError, "cannot fit"):
            f.nest(f.validate_project(p))
        door["grain"] = "u"
        f.nest(p)
        door["allow_rotation"] = False
        with self.assertRaisesRegex(ValueError, "cannot fit"):
            f.nest(p)

    def test_declared_bounds_and_unconfigured_stock(self):
        p = copy.deepcopy(self.p)
        p["design_bounds_mm"]["max"][1] = 599
        self.assert_invalid(p, "outside declared")
        p = copy.deepcopy(self.p)
        for m in p["materials"].values():
            m["stock"] = None
        self.assertEqual(f.nest(f.validate_project(p)), [])

    def test_tiny_stock_rejected(self):
        p = copy.deepcopy(self.p)
        p["materials"]["white"]["stock"]["trim_mm"] = 1500
        self.assert_invalid(p, "trimming")

    def test_exports_and_no_overwrite(self):
        # Temporary artifacts remain within the user's skill directory.
        with tempfile.TemporaryDirectory(
            prefix=".test-", dir=f.ROOT / "projects"
        ) as tmp:
            tmp = Path(tmp)
            source = tmp / "project.json"
            test_project = copy.deepcopy(self.p)
            test_project.pop("source_image", None)
            source.write_text(json.dumps(test_project))
            out = tmp / "build"
            report = f.build(source, out)
            self.assertEqual(report["part_count"], 28)
            self.assertEqual(
                report["excluded_from_nesting"], ["D1_BOTTOM", "D2_BOTTOM", "BACK"]
            )
            self.assertEqual(report["model_bounds_mm"]["max"], [1200, 600, 2200])
            self.assertEqual(report["model_bounds_mm"]["min"], [0, -22, 0])
            ns = {"c": "http://www.collada.org/2005/11/COLLADASchema"}
            dae = ET.parse(out / "model.dae")
            self.assertEqual(dae.find("c:asset/c:unit", ns).get("meter"), "0.001")
            self.assertEqual(len(dae.findall(".//c:geometry", ns)), 33)
            for geometry in dae.findall(".//c:geometry", ns):
                array = geometry.find(".//c:float_array", ns)
                coords = list(map(float, array.text.split()))
                self.assertEqual(len(coords), int(array.get("count")))
                triangles = geometry.find(".//c:triangles", ns)
                indices = list(map(int, triangles.find("c:p", ns).text.split()))
                self.assertEqual(len(indices), int(triangles.get("count")) * 3)
                self.assertLess(max(indices), len(coords) // 3)
            obj = (out / "model.obj").read_text().splitlines()
            verts = [l for l in obj if l.startswith("v ")]
            self.assertEqual(sum(l.startswith("o ") for l in obj), 33)
            for line in obj:
                if line.startswith("f "):
                    self.assertTrue(
                        all(0 < int(i) <= len(verts) for i in line.split()[1:])
                    )
            rows = list(
                csv.DictReader(
                    io.StringIO((out / "parts.csv").read_text(encoding="utf-8-sig"))
                )
            )
            self.assertEqual(len(rows), 28)
            right = next(r for r in rows if r["id"] == "DOOR_R")
            self.assertEqual(float(right["cut_v_mm"]), 2094)
            manifest = json.loads((out / "manifest.json").read_text())
            for name, sha in manifest.items():
                self.assertEqual(
                    f.hashlib.sha256((out / name).read_bytes()).hexdigest(), sha
                )
            with self.assertRaisesRegex(ValueError, "already exists"):
                f.build(source, out)
            (out / "model.obj").write_text("changed by user")
            with self.assertRaises(ValueError):
                f.build(source, out)
            self.assertEqual((out / "model.obj").read_text(), "changed by user")

    def test_cylinder_faces_point_outward(self):
        for axis in (0, 1, 2):
            p = dict(
                origin_mm=[0, 0, 0],
                size_mm=[100, 100, 100],
                shape="cylinder",
                axis=axis,
            )
            points, faces = f.mesh(p)
            center = [50] * 3
            for face in faces:
                a, b, c = [points[i] for i in face[:3]]
                ab = [b[i] - a[i] for i in range(3)]
                ac = [c[i] - a[i] for i in range(3)]
                normal = [
                    ab[1] * ac[2] - ab[2] * ac[1],
                    ab[2] * ac[0] - ab[0] * ac[2],
                    ab[0] * ac[1] - ab[1] * ac[0],
                ]
                centroid = [
                    sum(points[j][i] for j in face) / len(face) for i in range(3)
                ]
                self.assertGreater(
                    sum(normal[i] * (centroid[i] - center[i]) for i in range(3)), 0
                )


if __name__ == "__main__":
    unittest.main(verbosity=2)
