
import cv2
import numpy as np
from skimage.metrics import peak_signal_noise_ratio
import unittest
import os
def psnr(template, file):
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
    def test_psnr_same_images(self):
        template_path = './img/dog1.jpg'
        file_path = './img/dog1.jpg'
        test_result = psnr(template_path, file_path)
        assert test_result > 100.00, f"PSNR should be near 100 for same image. Test Result {test_result}"

    def test_psnr_same_images_second_smaller(self):
        template_path = './img/dog1.jpg'
        file_path = './img/dog3.jpg'
        test_result = psnr(template_path, file_path)
        assert test_result < 100.00, f"PSNR should be below 100 for different images. Test Result {test_result}"

if __name__ == "__main__":
    unittest.main()