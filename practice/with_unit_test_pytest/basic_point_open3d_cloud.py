"""Aleksandr Polskiy practicing creating a point cloud with Open3D and testing using pytest"""
import unittest
import numpy as np
import open3d as o3d


class TestPointCloud(unittest.TestCase):
    """Test suite for point cloud operations using Open3D and pytest."""
    def test_point_cloud_creation(self):
        """
        Test the creation of a point cloud and its properties.
        """
        # 1. Define input data points as a NumPy array
        points_np = np.array([
            [0.0, 0.0, 0.0],
            [1.0, 0.0, 0.0],
            [0.0, 1.0, 0.0],
            [0.0, 0.0, 1.0]
            ], dtype=np.float64)

        # 2. Converting existing NumPy array into an Open3D PointCloud object
        pcd = o3d.geometry.PointCloud()
        pcd.points = o3d.utility.Vector3dVector(points_np)




        # 3. Use pytest assertions to verify expected outcomes
        assert len(pcd.points) == 4,(f"Failed to create point cloud "
                                     f"with 4 points. From {len(pcd.points)} points.")
        assert pcd.is_empty() is False, (f"Point clout created "
                                         f"from {len(pcd.points)} points is empty.")

        # 4. Verify the actual point data using numpy's testing utilities
        np.testing.assert_allclose(np.asarray(pcd.points), points_np, atol=1e-6)


    def test_empty_point_cloud(self):
        """
        Test an empty point cloud.
        """
        pcd = o3d.geometry.PointCloud()
        assert len(pcd.points) == 0, "Failed to create empty point cloud."
        assert pcd.is_empty() is True , "Expected empty point cloud, it is not empty."


    def test_create_mesh_from_points(self):
        """This function tests the creation of
        a mesh from a set of points using Open3D"""
        points = o3d.utility.Vector3dVector([[0, 0, 0], [1, 0, 0], [0, 1, 0]])
        mesh = o3d.geometry.TriangleMesh.create_from_points(points)
        assert len(mesh.vertices) == 3
        assert len(mesh.triangles) == 1


    def test_transform_point_cloud(self):
        """This function tests the translation of a
        numpy array into point cloud using Open3D"""
        points = np.array([[0, 0, 0], [1, 0, 0]])
        pcd = o3d.geometry.PointCloud()
        pcd.points = o3d.utility.Vector3dVector(points)

        # Translate by (1, 2, 3)
        translation = np.array([1, 2, 3])
        pcd.translate(translation)

        transformed_points = np.asarray(pcd.points)
        assert np.allclose(transformed_points,
                           [[1, 2, 3], [2, 2, 3]]), \
            (f"Failed to translate point cloud. "
             f"Expected [[1, 2, 3], [2, 2, 3] "
             f"got {transformed_points}")

if __name__ == "__main__":
    unittest.main()
