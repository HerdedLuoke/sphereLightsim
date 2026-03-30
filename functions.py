import matplotlib.pyplot
from classesevil import *
import numpy
import pygame


def getWorldPoints(ptCld: pointCloud):
    # all relative to origin
    worldXArray = ptCld.localX + ptCld.center[0]
    worldYArray = ptCld.localY + ptCld.center[1]
    worldZArray = ptCld.localZ + ptCld.center[2]

    # tuple[numpy.ndarray, numpy.ndarray, numpy.ndarray]: 
    return worldXArray, worldYArray, worldZArray

def getCameraPoints(ptCld: pointCloud, camera: camera):
    # all relative to origin
    worldXArray, worldYArray, worldZArray = getWorldPoints(ptCld)

    # all relative to camera
    relativeXArray = worldXArray - camera.position[0]
    relativeYArray = worldYArray - camera.position[1]
    relativeZArray = worldZArray - camera.position[2]

    # tuple[numpy.ndarray, numpy.ndarray, numpy.ndarray]:
    return relativeXArray, relativeYArray, relativeZArray

def getScreenPoints(relativeXArray: numpy.ndarray, relativeYArray: numpy.ndarray,relativeZArray: numpy.ndarray, camera: camera):
    validPoint = relativeZArray > 0

    # all relative to screen center
    screenXArray = camera.window.xCenter + ((relativeXArray[validPoint] / relativeZArray[validPoint]) * camera.focalLength)
    screenYArray = camera.window.yCenter - ((relativeYArray[validPoint] / relativeZArray[validPoint]) * camera.focalLength)

    # tuple[numpy.ndarray, numpy.ndarray, numpy.ndarray]
    return screenXArray, screenYArray, validPoint

def createLocationData(ptCld: pointCloud, camera: camera, name: str):
    centerXArray = ptCld.localX
    centerYArray = ptCld.localY
    centerZArray = ptCld.localZ

    worldXArray, worldYArray, worldZArray = getWorldPoints(ptCld)
    cameraXArray, cameraYArray, cameraZArray = getCameraPoints(ptCld, camera)
    screenXArray, screenYArray, validPoint = getScreenPoints(cameraXArray, cameraYArray, cameraZArray, camera)

    fullScreenXArray = numpy.full(cameraXArray.shape, numpy.nan, dtype=numpy.float64)
    fullScreenYArray = numpy.full(cameraYArray.shape, numpy.nan, dtype=numpy.float64)

    fullScreenXArray[validPoint] = screenXArray
    fullScreenYArray[validPoint] = screenYArray

    return location(name=str(name), parent=ptCld, centerX=centerXArray, centerY=centerYArray,
        centerZ=centerZArray, worldX=worldXArray, worldY=worldYArray, worldZ=worldZArray,
        cameraX=cameraXArray, cameraY=cameraYArray, cameraZ=cameraZArray, screenX=fullScreenXArray,
        screenY=fullScreenYArray)

def cacheSpherePoints(mySphere: sphere, name: str, myWorldGrid=None):
    if mySphere.grid != None:
        if isinstance(mySphere.grid, worldGrid):
            gridAccuracy = mySphere.grid.size
        else:
            gridAccuracy = mySphere.grid
    else:
        gridAccuracy = myWorldGrid.size

    # i hate this.
    latitudeCount = max(4, int((numpy.pi * mySphere.radius) / gridAccuracy))
    longitudeCount = max(8, int((2 * numpy.pi * mySphere.radius) / gridAccuracy))
    # ^ finds the lat / long count for the grid accuracy, making it get smaller (bigger triangle/sections) as grid is bigger

    # creates a linspace of evenly spaced values from 0 to 1, split into latcount + 1 elements
    latitudeFractionArray = numpy.linspace(0.0, 1.0, latitudeCount + 1, dtype=numpy.float64)
    longitudeFractionArray = numpy.linspace(0.0, 1.0, longitudeCount + 1, dtype=numpy.float64)

    phiValueArray = latitudeFractionArray * numpy.pi
    thetaValueArray = longitudeFractionArray * (2 * numpy.pi)

    # all relative to object in a 2d latitude / longitude layout
    phiGridArray = phiValueArray[:, None]
    thetaGridArray = thetaValueArray[None, :]
    # ^ reshapes both into 2d broadcastable arrays, so phi changes by row and theta changes by column

    # i love how nice vectorized code looks
    sinPhiGridArray = numpy.sin(phiGridArray)
    cosPhiGridArray = numpy.cos(phiGridArray)
    # these could be meshed together instead, profile both later
    cosThetaGridArray = numpy.cos(thetaGridArray)
    sinThetaGridArray = numpy.sin(thetaGridArray)

    localXGridArray = mySphere.radius * sinPhiGridArray * cosThetaGridArray
    localYGridArray = mySphere.radius * sinPhiGridArray * sinThetaGridArray
    localZGridArray = mySphere.radius * cosPhiGridArray * numpy.ones_like(thetaGridArray)
    # makes z match the full 2d latitude / longitude layout before flattening

    # all relative to object
    localXArray = localXGridArray.ravel()
    localYArray = localYGridArray.ravel()
    localZArray = localZGridArray.ravel()

    ptCld = pointCloud(name=str(name), shape="sphere", center=mySphere.position, localX=localXArray,
        localY=localYArray, localZ=localZArray, location=None)

    # pointCloud, int, int
    return ptCld, latitudeCount, longitudeCount

def cachePlanePoints(myPlane: plane, name: str, myWorldGrid=None, faceOffset=(0, 0, 0),faceRotation=None):
    width = myPlane.width
    height = myPlane.height
    halfWidth = width / 2
    halfHeight = height / 2

    # all relative to object
    xOffset, yOffset, zOffset = faceOffset
    # offset is for placing MULTIPLE planes within one object, not needed if u dont wanna

    if faceRotation == None:
        xRotation = myPlane.rotation[0]
        yRotation = myPlane.rotation[1]
        zRotation = myPlane.rotation[2]
    else:
        xRotation = faceRotation[0]
        yRotation = faceRotation[1]
        zRotation = faceRotation[2]

    cosXRotation = numpy.cos(xRotation)
    sinXRotation = numpy.sin(xRotation)
    cosYRotation = numpy.cos(yRotation)
    sinYRotation = numpy.sin(yRotation)
    cosZRotation = numpy.cos(zRotation)
    sinZRotation = numpy.sin(zRotation)

    if myPlane.grid != None:
        if isinstance(myPlane.grid, worldGrid):
            gridAccuracy = myPlane.grid.size
        else:
            gridAccuracy = myPlane.grid
    else:
        gridAccuracy = myWorldGrid.size

    # all relative to object
    xPointCount = int(width / gridAccuracy) + 1
    yPointCount = int(height / gridAccuracy) + 1

    xDistances = numpy.linspace(-halfWidth, halfWidth, xPointCount, dtype=numpy.float64)
    yDistances = numpy.linspace(-halfHeight, halfHeight, yPointCount, dtype=numpy.float64)

    rowLength = len(xDistances)
    columnLength = len(yDistances)

    xLocation = numpy.tile(xDistances, len(yDistances))
    yLocation = numpy.repeat(yDistances, len(xDistances))

    uLocation = ((xLocation + halfWidth) / width) * (width - 1)
    vLocation = ((yLocation + halfHeight) / height) * (height - 1)

    localXArray = xLocation
    localYArray = yLocation
    localUArray = uLocation
    localVArray = vLocation
    # already 1d

    localZArray = numpy.zeros_like(localXArray, dtype=numpy.float64)
    # zeros for the same space of the x array

    yRotated = (localYArray * cosXRotation) - (localZArray * sinXRotation)
    zRotated = (localYArray * sinXRotation) + (localZArray * cosXRotation)
    localYArray = yRotated
    localZArray = zRotated
    # rotates the face around the x axis

    xRotated = (localXArray * cosYRotation) + (localZArray * sinYRotation)
    zRotated = -(localXArray * sinYRotation) + (localZArray * cosYRotation)
    localXArray = xRotated
    localZArray = zRotated
    # rotates the face around the y axis

    xRotated = (localXArray * cosZRotation) - (localYArray * sinZRotation)
    yRotated = (localXArray * sinZRotation) + (localYArray * cosZRotation)
    localXArray = xRotated
    localYArray = yRotated
    # rotates the face around the z axis

    localXArray = localXArray + xOffset
    localYArray = localYArray + yOffset
    localZArray = localZArray + zOffset
    # all relative to object after face offset

    ptCld = pointCloud(name=str(name), shape="plane", center=myPlane.position, localX=localXArray,localY=localYArray, localZ=localZArray, location=None, localU=localUArray, localV=localVArray)

    return ptCld, rowLength, columnLength

def createSphereTriangles(latitudeCount: int, longitudeCount: int):
    pointsPerLatitudeRow = longitudeCount + 1

    latitudeIndexArray = numpy.arange(latitudeCount, dtype=numpy.int32)[:, None]
    longitudeIndexArray = numpy.arange(longitudeCount, dtype=numpy.int32)[None, :]
    # each represents one box aka two triangles between two latitude rows and two longitude columns

    topLeftIndexArray = (latitudeIndexArray * pointsPerLatitudeRow) + longitudeIndexArray
    topRightIndexArray = topLeftIndexArray + 1
    bottomLeftIndexArray = ((latitudeIndexArray + 1) * pointsPerLatitudeRow) + longitudeIndexArray
    bottomRightIndexArray = bottomLeftIndexArray + 1

    upperTriangleArray = numpy.stack((topLeftIndexArray, bottomLeftIndexArray, topRightIndexArray), axis=-1)
    lowerTriangleArray = numpy.stack((topRightIndexArray, bottomLeftIndexArray, bottomRightIndexArray), axis=-1)

    validUpperLatitudeArray = numpy.arange(latitudeCount, dtype=numpy.int32) != 0
    validLowerLatitudeArray = numpy.arange(latitudeCount, dtype=numpy.int32) != (latitudeCount - 1)
    # ^ excludes the evil pole triangles that slipped through

    upperTriangleArray = upperTriangleArray[validUpperLatitudeArray, :, :]
    lowerTriangleArray = lowerTriangleArray[validLowerLatitudeArray, :, :]
    # ^ removes the bad triangle rows at the top and bottom poles

    upperTriangleArray = upperTriangleArray.reshape(-1, 3)
    lowerTriangleArray = lowerTriangleArray.reshape(-1, 3)
    # ^ flattens both from 2d triangle grids into normal triangle lists

    triangleIndexArray = numpy.vstack((upperTriangleArray, lowerTriangleArray)).astype(numpy.int32)

    # numpy.ndarray
    return triangleIndexArray

def createPlaneTriangles(rowLength: int, columnLength: int):
    rowArrayIndex = numpy.arange(columnLength - 1, dtype=numpy.int32)[:, None]
    columnArrayIndex = numpy.arange(rowLength - 1, dtype=numpy.int32)[None, :]
    # each represents one box aka two triangles between two rows and two columns

    topLeftIndexArray = (rowArrayIndex * rowLength) + columnArrayIndex
    topRightIndexArray = topLeftIndexArray + 1
    bottomLeftIndexArray = ((rowArrayIndex + 1) * rowLength) + columnArrayIndex
    bottomRightIndexArray = bottomLeftIndexArray + 1

    upperTriangleArray = numpy.stack((topLeftIndexArray, bottomLeftIndexArray, topRightIndexArray), axis=-1)
    lowerTriangleArray = numpy.stack((topRightIndexArray, bottomLeftIndexArray, bottomRightIndexArray), axis=-1)

    upperTriangleArray = upperTriangleArray.reshape(-1, 3)
    lowerTriangleArray = lowerTriangleArray.reshape(-1, 3)
    # flattens both from 2d triangle grids into normal triangle lists

    triangleIndexArray = numpy.vstack((upperTriangleArray, lowerTriangleArray)).astype(numpy.int32)

    return triangleIndexArray

def createSphereMesh(ptCld: pointCloud, triangleIndexArray: numpy.ndarray, name: str):
    vertexArray = numpy.column_stack((ptCld.localX, ptCld.localY, ptCld.localZ)).astype(numpy.float64)

    return mesh(shape="sphere", vertices=vertexArray, indexes=triangleIndexArray)

def createPlaneMesh(ptCld: pointCloud, triangleIndexArray: numpy.ndarray, name: str):
    vertexArray = numpy.column_stack((ptCld.localX, ptCld.localY, ptCld.localZ)).astype(numpy.float64)

    return mesh(shape="plane", vertices=vertexArray, indexes=triangleIndexArray)

def loadSphereTexture(mySphere: sphere):
    image = None
    imagePixelArray = None

    if mySphere.texture != None:
        image = pygame.image.load(mySphere.texture).convert()
        image = pygame.transform.scale(image, (int(mySphere.radius * 2), int(mySphere.radius * 2)))
        # uses 3d array to display all images without losing color depth, 2d is faster by alot, if needed.
        # converts all to numpy data
        imagePixelArray = pygame.surfarray.array3d(image).astype(numpy.float64)

    return image, imagePixelArray

def loadPlaneTexture(myPlane: plane):
    image = None
    imagePixelArray = None

    if myPlane.texture != None:
        image = pygame.image.load(myPlane.texture).convert()
        image = pygame.transform.scale(image, (int(myPlane.width), int(myPlane.height)))
        # uses 3d array to display all images without losing color depth, 2d is faster by alot, if needed.
        # converts all to numpy data
        imagePixelArray = pygame.surfarray.array3d(image).astype(numpy.float64)

    return image, imagePixelArray

def createSphere(mySphere: sphere, myWorldGrid=None):
    ptCld, latitudeCount, longitudeCount = cacheSpherePoints(mySphere, mySphere.name, myWorldGrid)
    triangleIndexArray = createSphereTriangles(latitudeCount, longitudeCount)
    meshObj = createSphereMesh(ptCld, triangleIndexArray, mySphere.name)

    return sphere(name=mySphere.name, grid=mySphere.grid, radius=mySphere.radius, position=mySphere.position,
        texture=mySphere.texture, color=mySphere.color, pointCloud=ptCld, mesh=meshObj)

def createPlane(myPlane: plane, myWorldGrid=None, faceOffset=(0, 0, 0), faceRotation=None):
    ptCld, rowLength, columnLength = cachePlanePoints(myPlane, myPlane.name, myWorldGrid, faceOffset, faceRotation)
    triangleIndexArray = createPlaneTriangles(rowLength, columnLength)
    meshObj = createPlaneMesh(ptCld, triangleIndexArray, myPlane.name)

    return plane(name=myPlane.name, grid=myPlane.grid, position=myPlane.position, rotation=myPlane.rotation,width=myPlane.width, height=myPlane.height, texture=myPlane.texture, color=myPlane.color,pointCloud=ptCld, mesh=meshObj)

def matPlot(meshVertexArray,triangleFaceArray):

    # shamelessly stole this example code so i could make sure my mesh rendered right without writing the lighting system
    fig = matplotlib.pyplot.figure()
    ax = fig.add_subplot(111, projection='3d')

    ax.plot_trisurf(meshVertexArray[:, 0],meshVertexArray[:, 1],meshVertexArray[:, 2],triangles=triangleFaceArray,shade=True,color='w',edgecolor='k',linewidth=0.2)
    ax.set_xlabel('X')
    ax.set_ylabel('Y')
    ax.set_zlabel('Z')
    matplotlib.pyplot.show()
