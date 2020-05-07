import compas
from compas.datastructures import Mesh, mesh_contours_numpy
from compas.geometry import  Point, distance_point_point

import numpy as np

from compas_am.slicing.printpath import Contour
from compas_am.slicing.printpath import Layer
import compas_am.slicing.curved_slicing as curved_slicing
import compas_am.slicing.adaptive_slicing as adaptive_slicing
import compas_am.slicing.planar_slicing as planar_slicing
from compas_am.utilities import utils
from compas_am.sorting.shortest_path_sorting import shortest_path_sorting
from compas_am.sorting.per_segment_sorting import per_segment_sorting
from compas_am.sorting.align_seams import align_seams
from compas_am.sorting.align_seams_random import align_seams_random

import logging
logger = logging.getLogger('logger')

class Slicer:
    """
    Slicer class is an organizational class that holds all the information for the slice process
    It does not implement functions, but rather links to the implementation in other parts of the compas_am library 
    Should be kept as clean and short as possible 
    
    Attributes
    ----------
    mesh         : <compas.datastructures.Mesh> Input mesh
    slicer_type  : <str> "planar_numpy", "planar_meshcut", "curved", "adaptive"
    layer_height : <float> 
    """

    def __init__(self, mesh, slicer_type = "planar", layer_height = 0.01):
        assert isinstance(mesh, compas.datastructures.Mesh), "Input mesh has to be of type <compas.datastructures.Mesh>, yours is of type: "+str(type(mesh))
        self.check_triangular_mesh(mesh)

        ### input
        self.mesh = mesh
        self.layer_height = layer_height
        self.slicer_type = slicer_type

        ### print paths
        self.contours = []
        self.infill_paths = []
        self.support_paths = []

        self.sorted_paths = []

        self.layers = []


    ##############################
    ### --- Slicing 
    def slice_model(self, create_contours, create_infill, create_supports):
        if create_contours:
            self.generate_contours()

        if create_infill:
            self.generate_infill()

        if create_supports:
            self.generate_supports()

    ### --- Contours
    def generate_contours(self):
        if self.slicer_type == "planar_numpy":
            logger.info("Planar contours compas numpy slicing")
            self.layers = planar_slicing.create_planar_contours_numpy(self.mesh, self.layer_height)

        elif self.slicer_type == "planar_meshcut":
            logger.info("Planar contours meshcut slicing")
            self.layers = planar_slicing.create_planar_contours_meshcut(self.mesh, self.layer_height)

        elif self.slicer_type == "curved":
            self.layers = curved_slicing.create_curved_contours(mesh, boundaries = None, min_layer_height = None, max_layer_height = None)

        elif self.slicer_type == "adaptive":
            self.layers = adaptive_slicing.create_adaptive_height_contours(mesh, min_layer_height = None, max_layer_height = None)

        else: 
            raise "Invalid slicing type : " + slicer_type


    ##############################
    ### --- Polyline Simplification

    def simplify_paths(self, threshold):
        logger.info("Paths simplification")
        for contour in self.contours:
            [path.simplify(threshold) for path in contour]
            [path.simplify(threshold) for path in self.infill_paths]
            [path.simplify(threshold) for path in self.support_paths]


    ##############################
    ### --- Sorting paths

    def sort_paths(self, sorting_type):
        logger.info("Paths sorting")
        if sorting_type == "shortest_path":
            self.layers = shortest_path_sorting(self.layers)
        elif sorting_type == "per_segment":
            self.layers = per_segment_sorting(self.layers)


    ##############################
    ### --- Seam alignment

    def align_seams(self, seam_alignment):
        logger.info("Aligning seams")
        if seam_alignment == "align_seams":
            self.seam_alignment = align_seams(self.contours, self.infill_paths, self.support_paths)
        elif seam_alignment == "random":
            self.seam_alignment = align_seams_random(self.contours, self.infill_paths, self.support_paths)


    ##############################
    ### --- Output 

    def printout_info(self):
        open_contours = 0
        closed_contours = 0
        total_number_of_pts = 0
        number_of_layers = 0


        for layer in self.layers:
            number_of_layers +=1
            for contour in layer.contours:
                total_number_of_pts += len(contour.points)
                if contour.is_closed:
                    closed_contours +=1
                else: 
                    open_contours +=1

        print ("\n---- Slicer Info ----")
        print ("Slicer type : ", self.slicer_type)
        print ("Layer height: ", self.layer_height, " mm")
        print ("Number of layers: %d"% number_of_layers)
        print ("Number of contours: %d, open contours: %d, closed contours: %d"%(open_contours+closed_contours,open_contours, closed_contours))
        print ("Number of sampling points on contours: %d \n"% total_number_of_pts)


    def get_contour_lines_for_plotter(self, color = (255,0,0)):
        lines = []
        for contour in self.contours:
            lines.extend(contour.get_lines_for_plotter(color))
        return lines

    def save_contours_to_json(self, path, name):
        data = {}
        count = 0
        for i,contour in enumerate(self.sorted_paths):
            print(i)
            for j, c in enumerate(contour): 
                data[count] = [list(point) for point in c.points]
                count += 1
        utils.save_to_json(data, path, name)

    def check_triangular_mesh(self, mesh):
        for fkey in mesh.faces():
            vs = mesh.face_vertices(fkey)
            assert len(vs)==3, "face key: "+str(fkey)+" , has number of vertices:"+str(len(vs))+" . Only triangular meshes supported"

if __name__ == "__main__":
    pass       
        