#!/usr/bin/env python3
"""Review stages and model-linked measurements must not imply manufacturing approval."""
import copy
import unittest
from make_wardrobe import make_project
from project_review import dimension_annotations, review_metadata


class ReviewTests(unittest.TestCase):
    def setUp(self):
        self.p = make_project()

    def test_clear_dimension_follows_real_shelf_geometry(self):
        self.assertEqual(dimension_annotations(self.p)[0]['value_mm'], 1100)
        shelf = next(p for p in self.p['parts'] if p['id'] == 'SHELF_R2')
        shelf['origin_mm'][2] += 25
        self.assertEqual(dimension_annotations(self.p)[0]['value_mm'], 1075)

    def test_invalid_measurement_rejected(self):
        for patch in ({'axis': True}, {'axis': 3}, {'start_part': 'missing'}, {'start_face': 'centre'}, {'end_part': 'BOTTOM'}):
            p = copy.deepcopy(self.p)
            p['dimension_annotations'][0].update(patch)
            with self.assertRaises(ValueError):
                dimension_annotations(p)

    def test_duplicate_measurement_rejected(self):
        self.p['dimension_annotations'] *= 2
        with self.assertRaises(ValueError): dimension_annotations(self.p)

    def test_excluded_material_and_missing_cost_are_not_complete(self):
        review = review_metadata(self.p, [], None, False)
        stages = {s['id']: s for s in review['stages']}
        self.assertEqual(stages['nesting']['status'], 'partial')
        self.assertEqual(stages['cost']['status'], 'pending')
        self.assertIn('BACK', review['excluded_part_ids'])
        self.assertFalse(review['production_approved'])
        self.assertEqual(stages['production']['status'], 'pending')

    def test_no_assumptions_never_auto_approves(self):
        self.p['assumptions'] = []
        review = review_metadata(self.p, [], {'status': 'complete'}, True)
        self.assertFalse(review['production_approved'])
        self.assertEqual(review['stages'][0]['status'], 'review')
        self.assertEqual(review['assumption_count'], 0)


if __name__ == '__main__':
    unittest.main()
