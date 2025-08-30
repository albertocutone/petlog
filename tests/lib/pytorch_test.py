#!/usr/bin/env python3
"""
Simple PyTorch Import Test
Tests that PyTorch can be imported successfully.
"""

import unittest


class TestPyTorchImport(unittest.TestCase):
    """Test PyTorch library import."""
    
    def test_pytorch_import(self):
        """Test if PyTorch can be imported."""
        try:
            import torch
            self.assertIsNotNone(torch, "PyTorch should be importable")
        except ImportError as e:
            self.fail(f"Failed to import PyTorch: {e}")


if __name__ == '__main__':
    unittest.main(verbosity=2)