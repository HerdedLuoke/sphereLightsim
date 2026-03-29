import cProfile
import numpy

from classes import worldObject, flatPlaneObject
from functions import getWorldPoints, matPlot

def main():

    ######## settings pay attention to me ##############

    windowHeight = 700
    windowWidth = 700

    backGroundColor = "black"

    gridAccuracy = 10
    ####################################################

    screenCenterX = windowWidth / 2
    screenCenterY = windowHeight / 2


    # scene objects
    myWorld = worldObject(gridAccuracy)

    boxSize = 100
    halfBoxSize = boxSize / 2

    cubeCenterX = 0
    cubeCenterY = 0
    cubeCenterZ = 200

    objectList = []

    frontFaceZLocation = cubeCenterZ + halfBoxSize

    #front +z
    frontPlane = flatPlaneObject((cubeCenterX, cubeCenterY, frontFaceZLocation), myWorld)
    frontPlane.createPlane(boxSize, boxSize, faceRotation=(0, numpy.pi, 0))
    objectList.append(frontPlane)

    # back -z
    backPlane = flatPlaneObject((cubeCenterX, cubeCenterY, frontFaceZLocation - boxSize), myWorld)
    backPlane.createPlane(boxSize, boxSize)
    objectList.append(backPlane)

    #left -x
    leftPlane = flatPlaneObject((cubeCenterX - halfBoxSize, cubeCenterY, cubeCenterZ), myWorld)
    leftPlane.createPlane(boxSize, boxSize, faceRotation=(0, numpy.pi / 2, 0))
    objectList.append(leftPlane)

    # right x
    rightPlane = flatPlaneObject((cubeCenterX + halfBoxSize, cubeCenterY, cubeCenterZ), myWorld)
    rightPlane.createPlane(boxSize, boxSize, faceRotation=(0, -numpy.pi / 2, 0))
    objectList.append(rightPlane)

    #top y
    topPlane = flatPlaneObject((cubeCenterX, cubeCenterY + halfBoxSize, cubeCenterZ), myWorld)
    topPlane.createPlane(boxSize, boxSize, faceRotation=(numpy.pi / 2, 0, 0))
    objectList.append(topPlane)

    #bottom -y
    bottomPlane = flatPlaneObject((cubeCenterX, cubeCenterY - halfBoxSize, cubeCenterZ), myWorld)
    bottomPlane.createPlane(boxSize, boxSize, faceRotation=(-numpy.pi / 2, 0, 0))
    objectList.append(bottomPlane)

    combinedVertexList = []
    combinedTriangleList = []

    vertexOffset = 0

    for currentObject in objectList:
        worldXArray, worldYArray, worldZArray = getWorldPoints(currentObject)

        currentVertexArray = numpy.column_stack((worldXArray, worldYArray, worldZArray))
        currentTriangleArray = currentObject.triangleIndexArray

        combinedVertexList.append(currentVertexArray)
        combinedTriangleList.append(currentTriangleArray + vertexOffset)

        vertexOffset = vertexOffset + len(currentVertexArray)

    combinedVertexArray = numpy.vstack(combinedVertexList)
    combinedTriangleArray = numpy.vstack(combinedTriangleList)

    matPlot(combinedVertexArray, combinedTriangleArray)
    # grabs all of the different planes, makes one list of triangles and their verticies, then passes

   



testingMode = False
if testingMode == True:
    cProfile.run("main()", sort="cumulative")
else:
    main()