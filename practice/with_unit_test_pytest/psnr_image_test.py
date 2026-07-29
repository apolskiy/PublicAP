
"""Aleksandr Polskiy practicing extracting and
comparing 'PSNR' metric for image quality
for the same image and similar but differently sized images"""
import unittest
import os
import cv2

def psnr(template, file):
    """This function calculates PSNR between two images"""
    # Load images (ensure they are the same size)
    current_directory = os.getcwd()
    print(f"Current directory {current_directory}")
    if not os.path.exists(template):
        assert False, f"Template not found: {template}"
    if not os.path.exists(file):
        assert False, f"File not found: {file}"

    img1 = cv2.imread(template)
    img2 = cv2.imread(file)

    # Resize if needed
    h, w = img1.shape[:2]
    img2_resized = cv2.resize(img2, (w, h), interpolation=cv2.INTER_CUBIC)

    return cv2.PSNR(img1, img2_resized)

class TestPSNR(unittest.TestCase):
    """Class to run unit tests for PSNR function"""
    def test_psnr_same_images(self):
        """Test PSNR for same image"""
        template_path = './img/dog1.jpg'
        file_path = './img/dog1.jpg'
        test_result = psnr(template_path, file_path)
        assert test_result > 100.00, (f"PSNR should "
                                      f"be near 100 for same image. Test Result {test_result}")

    def test_psnr_same_images_second_smaller(self):
        """Test PSNR for different sized/resolution images"""
        template_path = './img/dog1.jpg'
        file_path = './img/dog3.jpg'
        test_result = psnr(template_path, file_path)
        assert test_result < 100.00, (f"PSNR should be below 100"
                                      f" for different sized/resolution images. Test Result {test_result}")

if __name__ == "__main__":
    unittest.main()
