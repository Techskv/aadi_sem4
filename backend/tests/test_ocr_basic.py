
import unittest
import numpy as np
import cv2
import sys
import os

# Add backend to path to import services
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.services.ocr_service import ocr_service

class TestOCRService(unittest.TestCase):
    
    def setUp(self):
        # Create a dummy image for testing
        self.test_image_path = "/tmp/test_ocr_image.png"
        
        # Create a white image
        img = 255 * np.ones((300, 800, 3), dtype=np.uint8)
        
        # Add some text
        font = cv2.FONT_HERSHEY_SIMPLEX
        cv2.putText(img, 'Automated Answer Sheet', (50, 150), font, 1.5, (0, 0, 0), 2, cv2.LINE_AA)
        
        # Save it
        cv2.imwrite(self.test_image_path, img)

    def tearDown(self):
        if os.path.exists(self.test_image_path):
            os.remove(self.test_image_path)

    def test_preprocess_image(self):
        """Test image preprocessing steps."""
        img = cv2.imread(self.test_image_path)
        processed = ocr_service.preprocess_image(img)
        
        # Should be single channel (grayscale/binary)
        self.assertEqual(len(processed.shape), 2)
        
        # Should be binary (0 or 255)
        unique_values = np.unique(processed)
        self.assertTrue(all(val in [0, 255] for val in unique_values))

    def test_text_extraction(self):
        """Test text extraction from generated image."""
        text, conf = ocr_service.extract_text_from_image(self.test_image_path)
        
        print(f"Extracted: '{text}' (Conf: {conf})")
        
        self.assertIn("Automated", text)
        self.assertIn("Answer", text)
        self.assertIn("Sheet", text)
        self.assertGreater(conf, 0.5)

if __name__ == '__main__':
    unittest.main()
