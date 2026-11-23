#!/usr/bin/env python3
"""Ensure publishing is explicit, confined to examples, and rejects private inputs."""
import json
from pathlib import Path
import tempfile
import unittest
from build_demo import entries, build


class GalleryTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        (self.root / 'examples').mkdir()
        self.project = self.root / 'examples/project.json'
        self.project.write_text('{}')
        self.item = dict(id='wardrobe-001', source='examples/project.json', title='Test', summary='Test')

    def write(self, items):
        (self.root / 'public-projects.json').write_text(json.dumps(items))

    def test_explicit_example(self):
        self.write([self.item])
        self.assertEqual(entries(self.root)[0][0]['id'], 'wardrobe-001')

    def test_duplicate_or_path_id(self):
        self.write([self.item, self.item])
        with self.assertRaises(ValueError): entries(self.root)
        self.write([dict(self.item, id='../private')])
        with self.assertRaises(ValueError): entries(self.root)

    def test_private_folder_cannot_be_selected(self):
        (self.root / 'private.json').write_text('{}')
        self.write([dict(self.item, source='examples/../private.json')])
        with self.assertRaises(ValueError): entries(self.root)

    def test_comparison_cannot_publish_private_snapshot(self):
        (self.root / 'private.json').write_text('{}')
        self.write([dict(self.item, compare_to='examples/../private.json')])
        with self.assertRaisesRegex(ValueError, 'Public comparison'):
            build(self.root)

    def test_provenance_rejected(self):
        self.write([self.item])
        for project in ({'source_image':'photo.jpeg'}, {'source_conversation':'private'}, {'assumptions':['/Users/name/private']}):
            self.project.write_text(json.dumps(project))
            with self.assertRaises(ValueError): entries(self.root)


if __name__ == '__main__':
    unittest.main()
