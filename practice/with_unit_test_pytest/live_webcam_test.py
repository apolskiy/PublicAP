"""Aleksandr Polskiy this script is testing if the webcam is working and that stream can be closed by the user, by pressing 'q'"""
import unittest
import cv2


def webcamtest():
    """Testing if the webcam is working and that stream can be closed by the user, by pressing 'q'"""
    # 0 is usually the default camera; change if needed [2, 4]
    cap = cv2.VideoCapture(0)

    if not cap.isOpened():
        print("Error: Could not open webcam.")
    else:
        print("Webcam opened successfully.")
        while True:
            ret, frame = cap.read()  # Read a frame [2, 4]
            if not ret:
                print("Error: Can't receive frame (stream end?).")
                return False

            cv2.imshow('Webcam Feed', frame)  # Display the frame [2, 3, 6]

            # Break loop if 'q' is pressed [2, 3, 6, 9]
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

    cap.release()  # Release the camera [2, 4, 9]
    cv2.destroyAllWindows()  # Close all OpenCV windows [9]
    return True

class WebcamTest( unittest.TestCase):
    @staticmethod
    def test_webcam(self):
        assert webcamtest() is True

if __name__ == "__main__":
    unittest.main()