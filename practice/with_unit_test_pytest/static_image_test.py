from PIL import Image, ImageChops
import unittest
import os

class TestImageComparison(unittest.TestCase):
    def test_images_are_identical(self):
        # Define paths to your images
        # Replace 'baseline_image.png' and 'generated_image.png' with your actual file paths
        img1_path = './img/baseline_image.png'
        img2_path = './img/generated_image.png'

        # Ensure image files exist for the test to run
        if not(img1_path) or not os.path.exists(img2_path):
            # Create dummy images for demonstration if they don't exist
            Image.new('RGB', (100, 100), color = 'red').save(img1_path)
            Image.new('RGB', (100, 100), color = 'red').save(img2_path)

        img1 = Image.open(img1_path)
        img2 = Image.open(img2_path)

        # Use ImageChops.difference to find the difference between images
        diff = ImageChops.difference(img1, img2)

        # If images are identical, the bounding box of the difference image will be None
        self.assertFalse(diff.getbbox(), "Images are different")

    def test_images_are_different(self):
        # Define paths to your images
        # Replace 'baseline_image.png' and 'generated_image.png' with your actual file paths
        img1_path = './img/baseline_image1.png'
        img2_path = './img/generated_image1.png'

        # Ensure image files exist for the test to run
        if not os.path.exists(img1_path) or not os.path.exists(img2_path):
            # Create dummy images for demonstration if they don't exist
            Image.new('RGB', (100, 100), color='red').save(img1_path)
            Image.new('RGB', (100, 100), color='blue').save(img2_path)

        img1 = Image.open(img1_path)
        img2 = Image.open(img2_path)

        # Use ImageChops.difference to find the difference between images
        diff = ImageChops.difference(img1, img2)

        # If images are identical, the bounding box of the difference image will be None
        self.assertTrue(diff.getbbox(), "Images are different")

if __name__ == '__main__':
    unittest.main()