#!/usr/bin/env python3
import copy
import json
import unittest
from decimal import Decimal
from pathlib import Path
import costing
import furniture
from make_wardrobe import make_project

ROOT = Path(__file__).resolve().parents[1]


class CostingTests(unittest.TestCase):
    def setUp(self):
        self.project = furniture.validate_project(make_project())
        self.boards = furniture.nest(self.project)
        self.catalog = json.loads(
            (ROOT / "pricing/catalog-2026-11-20.json").read_text()
        )

    def test_whole_boards_and_vat_not_added_twice(self):
        result = costing.estimate(self.project, self.boards, self.catalog)
        front = next(r for r in result["rows"] if r["product_id"] == "agt-730a-18")
        self.assertEqual(front["quantity"], 2)
        self.assertEqual(front["total_eur"], 122.88)
        self.assertEqual(front["regular_total_eur"], 153.60)

    def test_incomplete_is_not_a_final_quote(self):
        result = costing.estimate(self.project, self.boards, self.catalog)
        self.assertEqual(result["status"], "incomplete")
        self.assertIsNone(result["materials_total_eur"])
        self.assertIsNone(result["labor_eur"])
        self.assertIsNone(result["profit_eur"])
        self.assertIsNone(result["client_total_eur"])
        self.assertTrue(any(r["total_eur"] is None for r in result["rows"]))

    def test_pack_rounding(self):
        self.assertEqual(costing.purchase_quantity(9, 10), Decimal(10))
        self.assertEqual(costing.purchase_quantity(10, 10), Decimal(10))
        self.assertEqual(costing.purchase_quantity(10.01, 10), Decimal(20))
        self.assertEqual(costing.purchase_quantity(3.11, 0.5), Decimal("3.5"))

    def test_wrong_sheet_format_is_rejected(self):
        self.catalog["products"]["white-p0-18"]["sheet_mm"] = [2800, 2100]
        with self.assertRaisesRegex(ValueError, "format"):
            costing.estimate(self.project, self.boards, self.catalog)

    def test_wrong_thickness_and_unit_are_rejected(self):
        c = copy.deepcopy(self.catalog)
        c["products"]["white-p0-18"]["thickness_mm"] = 16
        with self.assertRaisesRegex(ValueError, "thickness"):
            costing.estimate(self.project, self.boards, c)
        self.catalog["products"]["slide-500-h35"]["unit"] = "piece"
        with self.assertRaisesRegex(ValueError, "Unit mismatch"):
            costing.estimate(self.project, self.boards, self.catalog)

    def test_stale_price_is_flagged(self):
        self.project["pricing"]["as_of_date"] = "2026-12-20"
        result = costing.estimate(self.project, self.boards, self.catalog)
        self.assertTrue(any(r.get("stale") for r in result["rows"]))
        self.assertEqual(result["status"], "incomplete")

    def test_band_quantity_is_based_on_selected_edges(self):
        result = costing.estimate(self.project, self.boards, self.catalog)
        band = next(
            r for r in result["rows"] if r["label"].startswith("Кант MDF AGT 730A")
        )
        self.assertAlmostEqual(band["quantity"], 13.152)
        self.assertIsNone(band["total_eur"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
