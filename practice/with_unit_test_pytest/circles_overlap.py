"""Aleksandr Polskiy
This script determines if two circles overlap, one is (is not inside the to other).
It also determines if two circles are tangential to each other touching only at one point"""
import unittest
import math


def analyze_circles(x1, y1, r1, x2, y2, r2):
    """This function determines relationship between 
    two circles, overlap, tangent, no overlap and skew"""
    distancex = x2 - x1
    distancey = y2 - y1
    distance = math.sqrt(distancex ** 2 + distancey ** 2)

    results = {
        "distance": round(distance, 2),
        "relationship": "",
        "alignment": "skewed",
        "intersections": None
    }

    # 1. Test Alignment (Axis-skewed vs. Straight)
    if distancex == 0 and distancey == 0:
        results["alignment"] = "concentric"
    elif distancex == 0:
        results["alignment"] = "vertical (y-axis)"
    elif distancey == 0:
        results["alignment"] = "horizontal (x-axis)"

    # 2. Test Relationship (Overlap and Tangency)
    # Using math.isclose for float precision safety
    if distance > r1 + r2:
        results["relationship"] = "no overlap"
    elif math.isclose(distance, r1 + r2):
        results["relationship"] = "tangent (external)"
    elif distance < abs(r1 - r2):
        results["relationship"] = "one inside other (no touch)"
    elif math.isclose(distance, abs(r1 - r2)):
        results["relationship"] = "tangent (internal)"
    else:
        results["relationship"] = "overlapping"

    # 3. Calculate Intersections
    # Only possible if they touch or overlap
    if distance > 0 and distance <= (r1 + r2) and distance >= abs(r1 - r2):
        a = (r1 ** 2 - r2 ** 2 + distance ** 2) / (2 * distance)
        h = math.sqrt(max(0, r1 ** 2 - a ** 2))

        # Point where the line between intersections crosses the center line
        x0 = x1 + a * distancex / distance
        y0 = y1 + a * distancey / distance

        # Offsets to the intersection points
        rx = -distancey * (h / distance)
        ry = distancex * (h / distance)

        results["intersections"] = ((round(x0 + rx, 2), round(y0 + ry, 2)),
                                    (round(x0 - rx, 2), round(y0 - ry, 2)))

    return results

class TestCirclesOverlap(unittest.TestCase):
    def test_vertical_overlap(self):
        """This experimental_tests case determines vertical overlap"""
        result = analyze_circles(0, 0, 5, 0, 4, 3)
        print("Vertical Overlap: %s", result)
        assert result['relationship'] == "overlapping", \
            f"FAIL | Expected: overlapping, got {result['relationship']}"
        assert result['alignment'] == "vertical (y-axis)", \
            f"FAIL | Expected: overlapping, got {result['alignment']}"
        assert result['intersections'] is not None

    def test_horizontal_tangent(self):
        """This experimental_tests case determines horizontal tangent"""
        result = analyze_circles(0, 0, 5, 8, 0, 3)
        print("Horizontal Tangent: %s", result)
        assert result['relationship'] == "tangent (external)", \
            f"FAIL | Expected: tangent (external), got {result['relationship']}"
        assert result['alignment'] == "horizontal (x-axis)", \
            f"FAIL | Expected: horizontal (x-axis), got {result['alignment']}"
        assert result['intersections'] is not None

    def test_skewed_overlap(self):
        """This experimental_tests case determines skewed overlap"""
        result = analyze_circles(0, 0, 5, 4, 4, 3)
        print("Skewed Overlap: %s", result)
        assert result['relationship'] == "overlapping", \
            f"FAIL | Expected: overlapping, got {result['relationship']}"
        assert result['alignment'] == "skewed", \
            f"FAIL | Expected: skewed, got {result['alignment']}"
        assert result['intersections'] is not None




if __name__ == "__main__":
    unittest.main()
