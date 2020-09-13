#!/usr/bin/env python3
import openmesh as om
import inkex
import tempfile
import os
import numpy as np
import openmesh as om
import networkx as nx
from lxml import etree
from inkex import Transform, TextElement, Tspan, Color

"""
Extension for InkScape 1.0

Paperfold is another flattener for triangle mesh files, heavily based on paperfoldmodels by Felix Scholz aka felixfeliz.

Author: Mario Voigt / FabLab Chemnitz
Mail: mario.voigt@stadtfabrikanten.org
Date: 13.09.2020
Last patch: 13.09.2020
License: GNU GPL v3

To run this you need to install OpenMesh with python pip. 

The algorithm of paperfoldmodels consists of three steps:
  - Find a minimum spanning tree of the dual graph of the mesh.
  - Unfold the dual graph.
  - Remove self-intersections by adding additional cuts along edges.
  
Reference: The code is mostly based on the algorithm presented in a by Straub and Prautzsch (https://geom.ivd.kit.edu/downloads/proj-paper-models_cut_out_sheets.pdf).

Module licenses
- paperfoldmodels (https://github.com/felixfeliz/paperfoldmodels) - MIT License

possible import file types -> https://www.graphics.rwth-aachen.de/media/openmesh_static/Documentations/OpenMesh-8.0-Documentation/a04096.html

ToDos:
- Add glue tabs
- Fix bug with canvas resizing. bounding box of paperfoldMainGroup returns undexplainable wrong results. Why the fuck? How to update the view to get correct values here?
- Print statistics about 
  - groups
  - triagle count
  - edge count per type (valley cut, mountain cut, valley fold, mountain fold)
  - remove unrequired extra folding edges on plane surfaces (compare the output from osresearch/papercraft and paperfoldmodels) which should be removed before printing/cutting. 
    For example take a pentagon - it's face gets divided into three triangles if we put it into a mesh triangulation tool. Means we receive two fold edges which we don't need.
    This would create more convenient output like osresearch/papercraft and dxf2papercraft do. 
    See https://github.com/osresearch/papercraft/blob/master/unfold.c > coplanar_check() method

"""

# Compute the third point of a triangle when two points and all edge lengths are given
def getThirdPoint(v0, v1, l01, l12, l20):
    v2rotx = (l01 ** 2 + l20 ** 2 - l12 ** 2) / (2 * l01)
    v2roty0 = np.sqrt((l01 + l20 + l12) * (l01 + l20 - l12) * (l01 - l20 + l12) * (-l01 + l20 + l12)) / (2 * l01)

    v2roty1 = - v2roty0

    theta = np.arctan2(v1[1] - v0[1], v1[0] - v0[0])

    v2trans0 = np.array(
        [v2rotx * np.cos(theta) - v2roty0 * np.sin(theta), v2rotx * np.sin(theta) + v2roty0 * np.cos(theta), 0])
    v2trans1 = np.array(
        [v2rotx * np.cos(theta) - v2roty1 * np.sin(theta), v2rotx * np.sin(theta) + v2roty1 * np.cos(theta), 0])
    return [v2trans0 + v0, v2trans1 + v0]


# Check if two lines intersect
def lineIntersection(v1, v2, v3, v4, epsilon):
    d = (v4[1] - v3[1]) * (v2[0] - v1[0]) - (v4[0] - v3[0]) * (v2[1] - v1[1])
    u = (v4[0] - v3[0]) * (v1[1] - v3[1]) - (v4[1] - v3[1]) * (v1[0] - v3[0])
    v = (v2[0] - v1[0]) * (v1[1] - v3[1]) - (v2[1] - v1[1]) * (v1[0] - v3[0])
    if d < 0:
        u, v, d = -u, -v, -d
    return ((0 + epsilon) <= u <= (d - epsilon)) and ((0 + epsilon) <= v <= (d - epsilon))

# Check if a point lies inside a triangle
def pointInTriangle(A, B, C, P, epsilon):
    v0 = [C[0] - A[0], C[1] - A[1]]
    v1 = [B[0] - A[0], B[1] - A[1]]
    v2 = [P[0] - A[0], P[1] - A[1]]
    cross = lambda u, v: u[0] * v[1] - u[1] * v[0]
    u = cross(v2, v0)
    v = cross(v1, v2)
    d = cross(v1, v0)
    if d < 0:
        u, v, d = -u, -v, -d
    return u >= (0 + epsilon) and v >= (0 + epsilon) and (u + v) <= (d - epsilon)


# Check if two triangles intersect
def triangleIntersection(t1, t2, epsilon):
    if lineIntersection(t1[0], t1[1], t2[0], t2[1], epsilon): return True
    if lineIntersection(t1[0], t1[1], t2[0], t2[2], epsilon): return True
    if lineIntersection(t1[0], t1[1], t2[1], t2[2], epsilon): return True
    if lineIntersection(t1[0], t1[2], t2[0], t2[1], epsilon): return True
    if lineIntersection(t1[0], t1[2], t2[0], t2[2], epsilon): return True
    if lineIntersection(t1[0], t1[2], t2[1], t2[2], epsilon): return True
    if lineIntersection(t1[1], t1[2], t2[0], t2[1], epsilon): return True
    if lineIntersection(t1[1], t1[2], t2[0], t2[2], epsilon): return True
    if lineIntersection(t1[1], t1[2], t2[1], t2[2], epsilon): return True
    inTri = True
    inTri = inTri and pointInTriangle(t1[0], t1[1], t1[2], t2[0], epsilon)
    inTri = inTri and pointInTriangle(t1[0], t1[1], t1[2], t2[1], epsilon)
    inTri = inTri and pointInTriangle(t1[0], t1[1], t1[2], t2[2], epsilon)
    if inTri == True: return True
    inTri = True
    inTri = inTri and pointInTriangle(t2[0], t2[1], t2[2], t1[0], epsilon)
    inTri = inTri and pointInTriangle(t2[0], t2[1], t2[2], t1[1], epsilon)
    inTri = inTri and pointInTriangle(t2[0], t2[1], t2[2], t1[2], epsilon)
    if inTri == True: return True
    return False


# Functions for visualisation and output
def addVisualisationData(mesh, unfoldedMesh, originalHalfedges, unfoldedHalfedges, glueNumber, foldingDirection):
    for i in range(3):
        # Folding direction
        if mesh.calc_dihedral_angle(originalHalfedges[i]) < 0:
            foldingDirection[unfoldedMesh.edge_handle(unfoldedHalfedges[i]).idx()] = -1
        else:
            foldingDirection[unfoldedMesh.edge_handle(unfoldedHalfedges[i]).idx()] = 1

        # Information, which edges belong together
        glueNumber[unfoldedMesh.edge_handle(unfoldedHalfedges[i]).idx()] = mesh.edge_handle(originalHalfedges[i]).idx()

# Function that unwinds a spanning tree
def unfoldSpanningTree(mesh, spanningTree):
    unfoldedMesh = om.TriMesh()  # Das abgewickelte Netz

    numFaces = mesh.n_faces()
    sizeTree = spanningTree.number_of_edges()
    numUnfoldedEdges = 3 * numFaces - sizeTree

    isFoldingEdge = np.zeros(numUnfoldedEdges, dtype=bool)  # Indicates whether an edge is folded or cut
    glueNumber = np.empty(numUnfoldedEdges, dtype=int)  # Saves with which edge is glued together
    foldingDirection = np.empty(numUnfoldedEdges, dtype=int)  # Valley folding or mountain folding

    connections = np.empty(numFaces, dtype=int)  # Saves which original triangle belongs to the unrolled one

    # Select the first triangle as desired
    startingNode = list(spanningTree.nodes())[0]
    startingTriangle = mesh.face_handle(startingNode)

    # We unwind the first triangle

    # All half edges of the first triangle
    firstHalfEdge = mesh.halfedge_handle(startingTriangle)
    secondHalfEdge = mesh.next_halfedge_handle(firstHalfEdge)
    thirdHalfEdge = mesh.next_halfedge_handle(secondHalfEdge)
    originalHalfEdges = [firstHalfEdge, secondHalfEdge, thirdHalfEdge]

    # Calculate the lengths of the edges, this will determine the shape of the triangle (congruence)
    edgelengths = [mesh.calc_edge_length(firstHalfEdge), mesh.calc_edge_length(secondHalfEdge),
                   mesh.calc_edge_length(thirdHalfEdge)]

    # The first two points
    firstUnfoldedPoint = np.array([0, 0, 0])
    secondUnfoldedPoint = np.array([edgelengths[0], 0, 0])

    # We calculate the third point of the triangle from the first two. There are two possibilities
    [thirdUnfolded0, thirdUnfolded1] = getThirdPoint(firstUnfoldedPoint, secondUnfoldedPoint, edgelengths[0],
                                                     edgelengths[1],
                                                     edgelengths[2])
    if thirdUnfolded0[1] > 0:
        thirdUnfoldedPoint = thirdUnfolded0
    else:
        thirdUnfoldePoint = thirdUnfolded1

    # Add the new corners to the unwound net
    firstUnfoldedVertex = unfoldedMesh.add_vertex(secondUnfoldedPoint)
    secondUnfoldedVertex = unfoldedMesh.add_vertex(thirdUnfoldedPoint)
    thirdUnfoldedVertex = unfoldedMesh.add_vertex(firstUnfoldedPoint)

    #firstUnfoldedVertex = unfoldedMesh.add_vertex(firstUnfoldedPoint)
    #secondUnfoldedVertex = unfoldedMesh.add_vertex(secondUnfoldedPoint)
    #thirdUnfoldedVertex = unfoldedMesh.add_vertex(thirdUnfoldedPoint)

    # Create the page
    unfoldedFace = unfoldedMesh.add_face(firstUnfoldedVertex, secondUnfoldedVertex, thirdUnfoldedVertex)

    # Memory properties of the surface and edges
    # The half edges in unrolled mesh
    firstUnfoldedHalfEdge = unfoldedMesh.opposite_halfedge_handle(unfoldedMesh.halfedge_handle(firstUnfoldedVertex))
    secondUnfoldedHalfEdge = unfoldedMesh.next_halfedge_handle(firstUnfoldedHalfEdge)
    thirdUnfoldedHalfEdge = unfoldedMesh.next_halfedge_handle(secondUnfoldedHalfEdge)

    unfoldedHalfEdges = [firstUnfoldedHalfEdge, secondUnfoldedHalfEdge, thirdUnfoldedHalfEdge]

    # Associated triangle in 3D mesh
    connections[unfoldedFace.idx()] = startingTriangle.idx()
    # Folding direction and adhesive number
    addVisualisationData(mesh, unfoldedMesh, originalHalfEdges, unfoldedHalfEdges, glueNumber, foldingDirection)

    halfEdgeConnections = {firstHalfEdge.idx(): firstUnfoldedHalfEdge.idx(),
                           secondHalfEdge.idx(): secondUnfoldedHalfEdge.idx(),
                           thirdHalfEdge.idx(): thirdUnfoldedHalfEdge.idx()}

    # We walk through the tree
    for dualEdge in nx.dfs_edges(spanningTree, source=startingNode):
        foldingEdge = mesh.edge_handle(spanningTree[dualEdge[0]][dualEdge[1]]['idx'])
        # Find the corresponding half edge in the output triangle
        foldingHalfEdge = mesh.halfedge_handle(foldingEdge, 0)
        if not (mesh.face_handle(foldingHalfEdge).idx() == dualEdge[0]):
            foldingHalfEdge = mesh.halfedge_handle(foldingEdge, 1)

        # Find the corresponding unwound half edge
        unfoldedLastHalfEdge = unfoldedMesh.halfedge_handle(halfEdgeConnections[foldingHalfEdge.idx()])

        # Find the point in the unrolled triangle that is not on the folding edge
        oppositeUnfoldedVertex = unfoldedMesh.to_vertex_handle(unfoldedMesh.next_halfedge_handle(unfoldedLastHalfEdge))

        # We turn the half edges over to lie in the new triangle
        foldingHalfEdge = mesh.opposite_halfedge_handle(foldingHalfEdge)
        unfoldedLastHalfEdge = unfoldedMesh.opposite_halfedge_handle(unfoldedLastHalfEdge)

        # The two corners of the folding edge
        unfoldedFromVertex = unfoldedMesh.from_vertex_handle(unfoldedLastHalfEdge)
        unfoldedToVertex = unfoldedMesh.to_vertex_handle(unfoldedLastHalfEdge)

        # Calculate the edge lengths in the new triangle
        secondHalfEdgeInFace = mesh.next_halfedge_handle(foldingHalfEdge)
        thirdHalfEdgeInFace = mesh.next_halfedge_handle(secondHalfEdgeInFace)

        originalHalfEdges = [foldingHalfEdge, secondHalfEdgeInFace, thirdHalfEdgeInFace]

        edgelengths = [mesh.calc_edge_length(foldingHalfEdge), mesh.calc_edge_length(secondHalfEdgeInFace),
                       mesh.calc_edge_length(thirdHalfEdgeInFace)]

        # We calculate the two possibilities for the third point in the triangle
        [newUnfoldedVertex0, newUnfoldedVertex1] = getThirdPoint(unfoldedMesh.point(unfoldedFromVertex),
                                                                 unfoldedMesh.point(unfoldedToVertex), edgelengths[0],
                                                                 edgelengths[1], edgelengths[2])


        newUnfoldedVertex = unfoldedMesh.add_vertex(newUnfoldedVertex0)

        # Make the face
        newface = unfoldedMesh.add_face(unfoldedFromVertex, unfoldedToVertex, newUnfoldedVertex)

        secondUnfoldedHalfEdge = unfoldedMesh.next_halfedge_handle(unfoldedLastHalfEdge)
        thirdUnfoldedHalfEdge = unfoldedMesh.next_halfedge_handle(secondUnfoldedHalfEdge)
        unfoldedHalfEdges = [unfoldedLastHalfEdge, secondUnfoldedHalfEdge, thirdUnfoldedHalfEdge]

        # Saving the information about edges and page
        # Dotted line in the output
        unfoldedLastEdge = unfoldedMesh.edge_handle(unfoldedLastHalfEdge)
        isFoldingEdge[unfoldedLastEdge.idx()] = True

        # Gluing number and folding direction
        addVisualisationData(mesh, unfoldedMesh, originalHalfEdges, unfoldedHalfEdges, glueNumber, foldingDirection)

        # Related page
        connections[newface.idx()] = dualEdge[1]

        # Identify the half edges
        for i in range(3):
            halfEdgeConnections[originalHalfEdges[i].idx()] = unfoldedHalfEdges[i].idx()

    return [unfoldedMesh, isFoldingEdge, connections, glueNumber, foldingDirection]

def unfold(mesh):
    # Calculate the number of surfaces, edges and corners, as well as the length of the longest shortest edge
    numEdges = mesh.n_edges()
    numVertices = mesh.n_vertices()
    numFaces = mesh.n_faces()

    # Generate the dual graph of the mesh and calculate the weights
    dualGraph = nx.Graph()

    # For the weights: calculate the longest and shortest edge of the triangle
    minLength = 1000
    maxLength = 0
    for edge in mesh.edges():
        edgelength = mesh.calc_edge_length(edge)
        if edgelength < minLength:
            minLength = edgelength
        if edgelength > maxLength:
            maxLength = edgelength

    # All edges in the net
    for edge in mesh.edges():
        # The two sides adjacent to the edge
        face1 = mesh.face_handle(mesh.halfedge_handle(edge, 0))
        face2 = mesh.face_handle(mesh.halfedge_handle(edge, 1))

        # The weight
        edgeweight = 1.0 - (mesh.calc_edge_length(edge) - minLength) / (maxLength - minLength)

        # Calculate the centres of the pages (only necessary for visualisation)
        center1 = (0, 0)
        for vertex in mesh.fv(face1):
            center1 = center1 + 0.3333333333333333 * np.array([mesh.point(vertex)[0], mesh.point(vertex)[2]])
        center2 = (0, 0)
        for vertex in mesh.fv(face2):
            center2 = center2 + 0.3333333333333333 * np.array([mesh.point(vertex)[0], mesh.point(vertex)[2]])

        # Add the new nodes and edge to the dual graph
        dualGraph.add_node(face1.idx(), pos=center1)
        dualGraph.add_node(face2.idx(), pos=center2)
        dualGraph.add_edge(face1.idx(), face2.idx(), idx=edge.idx(), weight=edgeweight)

    # Calculate the minimum spanning tree
    spanningTree = nx.minimum_spanning_tree(dualGraph)

    # Unfold the tree
    fullUnfolding = unfoldSpanningTree(mesh, spanningTree)
    [unfoldedMesh, isFoldingEdge, connections, glueNumber, foldingDirection] = fullUnfolding


    # Resolve the intersections
    # Find all intersections
    epsilon = 1E-12  # Accuracy
    faceIntersections = []
    for face1 in unfoldedMesh.faces():
        for face2 in unfoldedMesh.faces():
            if face2.idx() < face1.idx():  # so that we do not double check the couples
                # Get the triangle faces
                triangle1 = []
                triangle2 = []
                for halfedge in unfoldedMesh.fh(face1):
                    triangle1.append(unfoldedMesh.point(unfoldedMesh.from_vertex_handle(halfedge)))
                for halfedge in unfoldedMesh.fh(face2):
                    triangle2.append(unfoldedMesh.point(unfoldedMesh.from_vertex_handle(halfedge)))
                if triangleIntersection(triangle1, triangle2, epsilon):
                    faceIntersections.append([connections[face1.idx()], connections[face2.idx()]])

    # Find the paths
    # We find the minimum number of cuts to resolve any self-intersection

    # Search all paths between overlapping triangles
    paths = []
    for intersection in faceIntersections:
        paths.append(
            nx.algorithms.shortest_paths.shortest_path(spanningTree, source=intersection[0], target=intersection[1]))

    # Find all edges in all threads
    edgepaths = []
    for path in paths:
        edgepath = []
        for i in range(len(path) - 1):
            edgepath.append((path[i], path[i + 1]))
        edgepaths.append(edgepath)

    # List of all edges in all paths
    allEdgesInPaths = list(set().union(*edgepaths))

    # Count how often each edge occurs
    numEdgesInPaths = []
    for edge in allEdgesInPaths:
        num = 0
        for path in edgepaths:
            if edge in path:
                num = num + 1
        numEdgesInPaths.append(num)

    S = []
    C = []

    while len(C) != len(paths):
        # Calculate the weights to decide which edge to cut
        cutWeights = np.empty(len(allEdgesInPaths))
        for i in range(len(allEdgesInPaths)):
            currentEdge = allEdgesInPaths[i]

            # Count how many of the paths in which the edge occurs have already been cut
            numInC = 0
            for path in C:
                if currentEdge in path:
                    numInC = numInC + 1

            # Determine the weight
            if (numEdgesInPaths[i] - numInC) > 0:
                cutWeights[i] = 1 / (numEdgesInPaths[i] - numInC)
            else:
                cutWeights[i] = 1000  # 1000 = infinite
        # Find the edge with the least weight
        minimalIndex = np.argmin(cutWeights)
        S.append(allEdgesInPaths[minimalIndex])
        # Find all paths where the edge occurs and add them to C
        for path in edgepaths:
            if allEdgesInPaths[minimalIndex] in path and not path in C:
                C.append(path)

    # Now we remove the cut edges from the minimum spanning tree
    spanningTree.remove_edges_from(S)

    # Find the cohesive components
    connectedComponents = nx.algorithms.components.connected_components(spanningTree)
    connectedComponentList = list(connectedComponents)

    # Unfolding of the components
    unfoldings = []
    for component in connectedComponentList:
        unfoldings.append(unfoldSpanningTree(mesh, spanningTree.subgraph(component)))

    return fullUnfolding, unfoldings


def findBoundingBox(mesh):
    firstpoint = mesh.point(mesh.vertex_handle(0))
    xmin = firstpoint[0]
    xmax = firstpoint[0]
    ymin = firstpoint[1]
    ymax = firstpoint[1]
    for vertex in mesh.vertices():
        coordinates = mesh.point(vertex)
        if (coordinates[0] < xmin):
            xmin = coordinates[0]
        if (coordinates[0] > xmax):
            xmax = coordinates[0]
        if (coordinates[1] < ymin):
            ymin = coordinates[1]
        if (coordinates[1] > ymax):
            ymax = coordinates[1]
    boxSize = np.maximum(np.abs(xmax - xmin), np.abs(ymax - ymin))

    return [xmin, ymin, boxSize]


def writeSVG(self, unfolding, size, printNumbers):
    mesh = unfolding[0]
    isFoldingEdge = unfolding[1]
    glueNumber = unfolding[3]
    foldingDirection = unfolding[4]

    # Calculate the bounding box
    [xmin, ymin, boxSize] = findBoundingBox(unfolding[0])

    if size > 0:
        boxSize = size

    strokewidth = 0.002 * boxSize
    dashLength = 0.008 * boxSize
    spaceLength = 0.02 * boxSize
    textDistance = 0.02 * boxSize
    textStrokewidth = 0.05 * strokewidth
    textLength = 0.001 * boxSize
    fontsize = 0.015 * boxSize

    # Generate a main group
    paperfoldPageGroup = self.document.getroot().add(inkex.Group(id=self.svg.get_unique_id("paperfold-page-")))

    # Go over all edges of the grid
    for edge in mesh.edges():
        # The two endpoints
        he = mesh.halfedge_handle(edge, 0)
        vertex0 = mesh.point(mesh.from_vertex_handle(he))
        vertex1 = mesh.point(mesh.to_vertex_handle(he))

        # Write a straight line between the two corners
        line = paperfoldPageGroup.add(inkex.PathElement())
        #line.path = [
        #       ["M", [vertex0[0], vertex0[1]]],
        #       ["L", [vertex1[0], vertex1[1]]]
        #    ]
        line.set('d', "M " + str(vertex0[0]) + "," + str(vertex0[1]) + " " + str(vertex1[0]) + "," + str(vertex1[1]))
        # Colour depending on folding direction
        lineStyle = {"fill": "none"}
        if foldingDirection[edge.idx()] > 0:
            lineStyle.update({"stroke": self.options.color_mountain_cut})
            line.set("id", self.svg.get_unique_id("mountain-cut-"))
        elif foldingDirection[edge.idx()] < 0:
            lineStyle.update({"stroke": self.options.color_valley_cut})
            line.set("id", self.svg.get_unique_id("valley-cut-"))
                     
        lineStyle.update({"stroke-width":str(strokewidth)})
        lineStyle.update({"stroke-linecap":"butt"})
        lineStyle.update({"stroke-linejoin":"miter"})
        lineStyle.update({"stroke-miterlimit":"4"})  
            
        # Dotted lines for folding edges    
        if isFoldingEdge[edge.idx()]: 
            lineStyle.update({"stroke-dasharray":(str(dashLength) + ", " + str(spaceLength))})
            if foldingDirection[edge.idx()] > 0:
                lineStyle.update({"stroke": self.options.color_mountain_perforate})
                line.set("id", self.svg.get_unique_id("mountain-perforate-"))
            if foldingDirection[edge.idx()] < 0:
                lineStyle.update({"stroke": self.options.color_valley_perforate})
                line.set("id", self.svg.get_unique_id("valley-perforate-"))     
        else:
            lineStyle.update({"stroke-dasharray":"none"})


        lineStyle.update({"stroke-dashoffset":"0"})
        lineStyle.update({"stroke-opacity":"1"})       
        line.style = lineStyle

        # The number of the edge to be glued
        if not isFoldingEdge[edge.idx()]:
            # Find halfedge in the face
            halfEdge = mesh.halfedge_handle(edge, 0)
            if mesh.face_handle(halfEdge).idx() == -1:
                halfEdge = mesh.opposite_halfedge_handle(halfEdge)
            vector = mesh.calc_edge_vector(halfEdge)
            # normalize
            vector = vector / np.linalg.norm(vector)
            midPoint = 0.5 * (
                    mesh.point(mesh.from_vertex_handle(halfEdge)) + mesh.point(mesh.to_vertex_handle(halfEdge)))
            rotatedVector = np.array([-vector[1], vector[0], 0])
            angle = np.arctan2(vector[1], vector[0])
            position = midPoint + textDistance * rotatedVector
            rotation = 180 / np.pi * angle

            if (printNumbers):
                text = paperfoldPageGroup.add(TextElement(id=self.svg.get_unique_id("number-")))
                text.set("x", str(position[0]))
                text.set("y", str(position[1]))
                text.set("font-size", str(fontsize))
                text.set("style", "stroke-width:" + str(textStrokewidth))
                text.set("transform", "rotate(" + str(rotation) + "," + str(position[0]) + "," + str(position[1]) + ")")
                
                tspan = text.add(Tspan())
                tspan.set("x", str(position[0]))
                tspan.set("y", str(position[1]))
                tspan.set("style", "stroke-width:" + str(textStrokewidth))
                tspan.text = str(glueNumber[edge.idx()])       
    return paperfoldPageGroup
                
class Unfold(inkex.Effect):
    def __init__(self):
        inkex.Effect.__init__(self)
        self.arg_parser.add_argument("--inputfile")
        self.arg_parser.add_argument("--printNumbers", type=inkex.Boolean, default=False, help="Print numbers on the cut edges")
        self.arg_parser.add_argument("--scalefactor", type=float, default=1.0, help="Manual scale factor")
        self.arg_parser.add_argument("--resizetoimport", type=inkex.Boolean, default=True, help="Resize the canvas to the imported drawing's bounding box") 
        self.arg_parser.add_argument("--extraborder", type=float, default=0.0)
        self.arg_parser.add_argument("--extraborder_units")         
        self.arg_parser.add_argument("--color_valley_cut", type=Color, default='255', help="Color for valley cuts")
        self.arg_parser.add_argument("--color_mountain_cut", type=Color, default='1968208895', help="Color for mountain cuts")
        self.arg_parser.add_argument("--color_valley_perforate", type=Color, default='3422552319', help="Color for valley perforations")
        self.arg_parser.add_argument("--color_mountain_perforate", type=Color, default='879076607', help="Color for mountain perforations")
                                
    def effect(self):
        mesh = om.read_trimesh(self.options.inputfile)
        fullUnfolded, unfoldedComponents = unfold(mesh)
        # Compute maxSize of the components
        # All components must be scaled to the same size as the largest component
        maxSize = 0
        for unfolding in unfoldedComponents:
            [xmin, ymin, boxSize] = findBoundingBox(unfolding[0])
            if boxSize > maxSize:
                maxSize = boxSize
                     
        # Create a new container group to attach all paperfolds
        paperfoldMainGroup = self.document.getroot().add(inkex.Group(id=self.svg.get_unique_id("paperfold-"))) #make a new group at root level
        for i in range(len(unfoldedComponents)):
            paperfoldPageGroup = writeSVG(self, unfoldedComponents[i], maxSize, self.options.printNumbers)
            #translate the groups next to each other to remove overlappings
            if i != 0:
                previous_bbox = paperfoldMainGroup[i-1].bounding_box()
                this_bbox = paperfoldPageGroup.bounding_box()
                paperfoldPageGroup.set("transform","translate(" + str(previous_bbox.left + previous_bbox.width - this_bbox.left) + ", 0.0)")
            paperfoldMainGroup.append(paperfoldPageGroup) 

        
        #apply scale factor
        translation_matrix = [[self.options.scalefactor, 0.0, 0.0], [0.0, self.options.scalefactor, 0.0]]            
        paperfoldMainGroup.transform = Transform(translation_matrix) * paperfoldMainGroup.transform
        #paperfoldMainGroup.set('transform', 'scale(%f,%f)' % (self.options.scalefactor, self.options.scalefactor))

        #adjust canvas to the inserted unfolding
        if self.options.resizetoimport:
            bbox = paperfoldMainGroup.bounding_box()
            namedView = self.document.getroot().find(inkex.addNS('namedview', 'sodipodi'))
            doc_units = namedView.get(inkex.addNS('document-units', 'inkscape'))
            root = self.svg.getElement('//svg:svg');
            offset = self.svg.unittouu(str(self.options.extraborder) + self.options.extraborder_units)
            root.set('viewBox', '%f %f %f %f' % (bbox.left - offset, bbox.top - offset, bbox.width + 2 * offset, bbox.height + 2 * offset))
            root.set('width', str(bbox.width + 2 * offset) + doc_units)
            root.set('height', str(bbox.height + 2 * offset) + doc_units)

if __name__ == '__main__':
    Unfold().run()