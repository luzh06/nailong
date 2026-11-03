import sys
import unittest
from pathlib import Path
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import gltf_geometry as geometry

class GeometryTests(unittest.TestCase):
    def test_partial_triangle_is_cut_at_fragment_boundaries(self):
        self.assertTrue(hasattr(geometry,'outside_box'))
        # This wall's centroid is outside the cut but its end crosses it.
        t=np.array([[[-3.25,0,19],[-3.25,3,19],[-3.25,0,24]]],dtype='f4')
        out=geometry.outside_box(t,(-10.5,10.5,20.1,28.7))
        self.assertGreater(len(out),0)
        self.assertLessEqual(float(out[:,:,2].max()),20.10001)
    def test_fully_inside_triangle_is_removed(self):
        t=np.array([[[0,0,21],[1,0,21],[1,1,22]]],dtype='f4')
        self.assertEqual(len(geometry.outside_box(t,(-10.5,10.5,20.1,28.7))),0)
    def test_outside_triangle_preserves_geometry(self):
        t=np.array([[[20,0,21],[21,0,21],[21,1,22]]],dtype='f4')
        np.testing.assert_array_equal(geometry.outside_box(t,(-10.5,10.5,20.1,28.7)),t)
if __name__=='__main__':unittest.main()
