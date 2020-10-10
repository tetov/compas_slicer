import logging
from compas.geometry import normalize_vector, subtract_vectors, dot_vectors
from collections import deque

logger = logging.getLogger('logger')

__all__ = ['unify_paths_orientation']


def unify_paths_orientation(slicer):
    """
    Unifies the orientation of paths that are closed.

    Parameters
    ----------
    slicer : compas_slicer.slicers.BaseSlicer
        An instance of the compas_slicer.slicers.PlanarSlicer class.
    """

    for i, layer in enumerate(slicer.layers):
        for j, path in enumerate(layer.paths):
            ## find reference points for each path, if possible
            if path.is_closed:
                reference_points = None
                if j > 0:
                    reference_points = layer.paths[0].points
                elif i > 0 and j == 0:
                    reference_points = slicer.layers[i - 1].paths[0].points

                if reference_points:  # then reorient current pts based on reference
                    path.points = make_pts_have_same_direction_as_pts_reference(path.points,
                                                                                reference_points)


def make_pts_have_same_direction_as_pts_reference(pts, reference_points):
    # check if new curve has same direction as prev curve, otherwise reverse
    if len(pts) > 2 and len(reference_points) > 2:
        v1 = normalize_vector(subtract_vectors(pts[0], pts[2]))
        v2 = normalize_vector(subtract_vectors(reference_points[0], reference_points[2]))
    else:
        v1 = normalize_vector(subtract_vectors(pts[0], pts[1]))
        v2 = normalize_vector(subtract_vectors(reference_points[0], reference_points[1]))

    if dot_vectors(v1, v2) < 0:
        items = deque(reversed(pts))
        items.rotate(1)  # bring last point again in the front
        pts = list(items)
    return pts
