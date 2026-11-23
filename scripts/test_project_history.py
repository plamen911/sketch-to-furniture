#!/usr/bin/env python3
"""Behavioral revision tests: actual changes, missing prices and tamper detection."""
import copy
import json
from pathlib import Path
import tempfile
import unittest
from make_wardrobe import make_project
from project_history import snapshot, compare, load_snapshot


class HistoryTests(unittest.TestCase):
    def setUp(self):
        self.p = make_project()
        self.boards = [{'material':'white'}, {'material':'white'}, {'material':'cream'}]
        self.cost = {'estimated_priced_subtotal_eur':0.3,'status':'incomplete','as_of_date':'2026-11-20','rows':[]}

    def snap(self, project=None, cost=None):
        return snapshot(project or self.p, self.boards, cost, 'test')

    def test_identical_geometry_is_unchanged(self):
        before = self.snap()
        after = self.snap()
        report = compare(before, after)
        self.assertEqual(before['snapshot_sha256'], after['snapshot_sha256'])
        for section in report['changes'].values():
            self.assertEqual(section, {'added':[], 'removed':[], 'changed':[]})
        self.assertFalse(report['decisions_changed'])

    def test_dimensions_edges_and_removed_added_parts(self):
        before = self.snap()
        p = copy.deepcopy(self.p)
        p['parts'][0]['size_mm'][2] -= 20
        p['parts'][0]['bands_mm']['u0'] = 0.8
        removed = p['parts'].pop()
        new = copy.deepcopy(removed);new['id'] = 'NEW_PANEL';p['parts'].append(new)
        report = compare(before, self.snap(p))
        changes = report['changes']['parts']
        self.assertEqual(changes['added'], ['NEW_PANEL'])
        self.assertEqual(changes['removed'], [removed['id']])
        self.assertEqual(changes['changed'][0]['fields'], ['bands_mm','size_mm'])
        self.assertEqual(changes['changed'][0]['before']['size_mm'][2] - changes['changed'][0]['after']['size_mm'][2], 20)

    def test_missing_prices_are_not_zero_and_delta_is_decimal(self):
        before = self.snap(cost=self.cost)
        report = compare(before, self.snap())
        self.assertIsNone(report['cost']['delta_priced_subtotal_eur'])
        next_cost = dict(self.cost, estimated_priced_subtotal_eur=0.4)
        report = compare(before, self.snap(cost=next_cost))
        self.assertEqual(report['cost']['delta_priced_subtotal_eur'], 0.1)

    def test_snapshot_is_order_independent_and_tampering_rejected(self):
        before = self.snap()
        reordered = copy.deepcopy(self.p);reordered['parts'].reverse()
        self.assertEqual(before['parts'], self.snap(reordered)['parts'])
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'revision.json';path.write_text(json.dumps(before))
            self.assertEqual(load_snapshot(path), before)
            before['parts'][next(iter(before['parts']))]['name'] = 'Changed outside the build'
            path.write_text(json.dumps(before))
            with self.assertRaisesRegex(ValueError, 'hash mismatch'): load_snapshot(path)


if __name__ == '__main__': unittest.main()
