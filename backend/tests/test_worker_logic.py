
import unittest
from unittest.mock import MagicMock, patch
from app.worker import parse_questions_from_text

class TestWorkerLogic(unittest.TestCase):
    
    def test_parse_questions_simple(self):
        """Test parsing simple formatted text."""
        text = """
        1. Photosynthesis is the process by which plants make food.
        2. The capital of France is Paris.
        3. 2 + 2 = 4
        """
        parsed = parse_questions_from_text(text, 3)
        
        self.assertEqual(len(parsed), 3)
        self.assertIn("Photosynthesis", parsed[1])
        self.assertIn("Paris", parsed[2])
        self.assertIn("4", parsed[3])
        
    def test_parse_questions_messy(self):
        """Test parsing with messy formatting."""
        text = """
        Q1) First answer here
        
        Q2. Second answer
        continued on next line
        
        3- Third answer
        """
        parsed = parse_questions_from_text(text, 3)
        
        self.assertEqual(len(parsed), 3)
        self.assertEqual(parsed[1], "First answer here")
        self.assertIn("Second answer", parsed[2])
        self.assertIn("continued", parsed[2])
        self.assertEqual(parsed[3], "Third answer")
        
    def test_fallback_single_block(self):
        """Test fallback when no numbers found."""
        text = "Just a single paragraph answer without numbers."
        parsed = parse_questions_from_text(text, 1)
        
        self.assertEqual(len(parsed), 1)
        self.assertEqual(parsed[1], text)

if __name__ == '__main__':
    unittest.main()
