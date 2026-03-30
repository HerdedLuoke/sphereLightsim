import cProfile
import numpy

from classesevil import *
from evilfunctions import *


def main():

    ######## settings pay attention to me ##############

    windowHeight = 700
    windowWidth = 700

    backGroundColor = "black"

    gridAccuracy = 4
    ####################################################

    screenCenterX = windowWidth / 2
    screenCenterY = windowHeight / 2

    # scene objects
    myWorld = worldGrid(type=None, size=gridAccuracy)

    boxSize = 100
    halfBoxSize = boxSize / 2

    cubeCenterX = 0
    cubeCenterY = 0
    cubeCenterZ = 200

    objectList = []

    frontFaceZLocation = cubeCenterZ + halfBoxSize

    # front z
    frontPlane = plane(name="frontPlane", grid=20, position=(cubeCenterX, cubeCenterY, frontFaceZLocation), rotation=(0, numpy.pi, 0), width=boxSize, height=boxSize)
    frontPlane = createPlane(frontPlane, myWorld)
    objectList.append(frontPlane)

    # back
    backPlane = plane(name="backPlane", grid=20, position=(cubeCenterX, cubeCenterY, frontFaceZLocation - boxSize), rotation=(0, 0, 0), width=boxSize, height=boxSize)
    backPlane = createPlane(backPlane, myWorld)
    objectList.append(backPlane)

    # -x
    leftPlane = plane(name="leftPlane", grid=20, position=(cubeCenterX - halfBoxSize, cubeCenterY, cubeCenterZ), rotation=(0, numpy.pi / 2, 0), width=boxSize, height=boxSize)
    leftPlane = createPlane(leftPlane, myWorld)
    objectList.append(leftPlane)

    # x
    rightPlane = plane(name="rightPlane", grid=20, position=(cubeCenterX + halfBoxSize, cubeCenterY, cubeCenterZ), rotation=(0, -numpy.pi / 2, 0), width=boxSize, height=boxSize)
    rightPlane = createPlane(rightPlane, myWorld)
    objectList.append(rightPlane)

    # y
    topPlane = plane(name="topPlane", grid=20, position=(cubeCenterX, cubeCenterY + halfBoxSize, cubeCenterZ), rotation=(numpy.pi / 2, 0, 0), width=boxSize, height=boxSize)
    topPlane = createPlane(topPlane, myWorld)
    objectList.append(topPlane)

    # -y
    bottomPlane = plane(name="bottomPlane", grid=20, position=(cubeCenterX, cubeCenterY - halfBoxSize, cubeCenterZ), rotation=(-numpy.pi / 2, 0, 0), width=boxSize, height=boxSize)
    bottomPlane = createPlane(bottomPlane, myWorld)
    objectList.append(bottomPlane)

    combinedVertexList = []
    combinedTriangleList = []

    vertexOffset = 0

    for currentObject in objectList:
        worldXArray, worldYArray, worldZArray = getWorldPoints(currentObject.pointCloud)

        currentVertexArray = numpy.column_stack((worldXArray, worldYArray, worldZArray))
        currentTriangleArray = currentObject.mesh.indexes

        combinedVertexList.append(currentVertexArray)
        combinedTriangleList.append(currentTriangleArray + vertexOffset)

        vertexOffset = vertexOffset + len(currentVertexArray)

    combinedVertexArray = numpy.vstack(combinedVertexList)
    combinedTriangleArray = numpy.vstack(combinedTriangleList)

    matPlot(combinedVertexArray, combinedTriangleArray)
    # grabs all of the different planes, makes one list of triangles and their verticies, then passes


testingMode = False
if testingMode == True:
    cProfile.run("main()", sort="tottime")
else:
    main()
