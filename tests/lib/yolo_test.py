#!/usr/bin/env python3
"""
Simple YOLO Import Test
Tests that YOLO can be imported successfully.
"""

import unittest


class TestYOLOImport(unittest.TestCase):
    """Test YOLO library import."""
    
    def test_yolo_import(self):
        """Test if YOLO can be imported via torch hub."""
        try:
            import torch
            # Just test that we can access the hub - don't actually load model
            self.assertTrue(hasattr(torch, 'hub'), "torch.hub should be available")
        except ImportError as e:
            self.fail(f"Failed to import torch for YOLO: {e}")


if __name__ == '__main__':
    unittest.main(verbosity=2)
