import pygame
import cProfile
import numpy
import time
import matplotlib.pyplot
from mpl_toolkits import mplot3d

# lucas!


def getWorldPoints(myObject):
    # all relative to origin
    worldXArray = myObject.localXArray + myObject.xLocation
    worldYArray = myObject.localYArray + myObject.yLocation
    worldZArray = myObject.localZArray + myObject.zLocation

    return worldXArray, worldYArray, worldZArray

def getCameraPoints(myObject, myCamera):
    # all relative to origin
    worldXArray, worldYArray, worldZArray = getWorldPoints(myObject)

    # all relative to camera
    relativeXArray = worldXArray - myCamera.xLocation
    relativeYArray = worldYArray - myCamera.yLocation
    relativeZArray = worldZArray - myCamera.zLocation

    return relativeXArray, relativeYArray, relativeZArray

def getScreenPoints(relativeXArray, relativeYArray, relativeZArray, myCamera):
    validPoint = relativeZArray > 0

    # all relative to screen center
    screenXArray = myCamera.screenCenterX + ((relativeXArray[validPoint] / relativeZArray[validPoint]) * myCamera.focalLength)
    screenYArray = myCamera.screenCenterY - ((relativeYArray[validPoint] / relativeZArray[validPoint]) * myCamera.focalLength)

    return screenXArray, screenYArray, validPoint

class lightObject:
    def __init__(self, intensity, lightPosition):
        self.position = (lightPosition[0], lightPosition[1], lightPosition[2])

        self.xLocation = self.position[0]
        self.yLocation = self.position[1]
        self.zLocation = self.position[2]

        self.lightValue = intensity

    def moveLight(self, lightPosition):
        self.position = (lightPosition[0], lightPosition[1], lightPosition[2])

        self.xLocation = self.position[0]
        self.yLocation = self.position[1]
        self.zLocation = self.position[2]

    def lightUpdate(self, intensity):
        self.lightValue = intensity

class worldObject:
    def __init__(self, gridAccuracy):
        self.gridAccuracy = gridAccuracy

class cameraObject:
    def __init__(self, cameraPosition, focalLength, windowWidth, windowHeight):
        self.position = (cameraPosition[0], cameraPosition[1], cameraPosition[2])

        self.xLocation = self.position[0]
        self.yLocation = self.position[1]
        self.zLocation = self.position[2]

        self.focalLength = focalLength
        # note this is used for fov 

        self.windowWidth = windowWidth
        self.windowHeight = windowHeight
        self.screenCenterX = windowWidth / 2
        self.screenCenterY = windowHeight / 2

    def moveCamera(self, cameraPosition):
        self.position = (cameraPosition[0], cameraPosition[1], cameraPosition[2])

        self.xLocation = self.position[0]
        self.yLocation = self.position[1]
        self.zLocation = self.position[2]

class sphereObject:

    def __init__(self, radius, worldPosition, world, textureFile=None):
        self.radius = radius
        self.position = (worldPosition[0], worldPosition[1], worldPosition[2])

        self.xLocation = self.position[0]
        self.yLocation = self.position[1]
        self.zLocation = self.position[2]

        self.world = world
        self.cacheSpherePoints()
        #print(len(self.localXArray))
        #print(len(self.localYArray))
        #print(len(self.localZArray))
        self.image = None
        self.imagePixelArray = None

        if textureFile is not None:
            self.image = pygame.image.load(textureFile).convert()
            self.image = pygame.transform.scale(self.image, (int(self.radius * 2), int(self.radius * 2)))
            # uses 3d array to display all images without losing color depth, 2d is faster by alot, if needed.
            # converts all to numpy data
            self.imagePixelArray = pygame.surfarray.array3d(self.image).astype(numpy.float64)

    def cacheSpherePoints(self):
        gridAccuracy = self.world.gridAccuracy

        # i hate this.
        latitudeCount = max(4, int((self.radius * 2) / gridAccuracy))
        longitudeCount = max(8, int((self.radius * 2) / gridAccuracy))
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

        localXGridArray = self.radius * sinPhiGridArray * cosThetaGridArray
        localYGridArray = self.radius * sinPhiGridArray * sinThetaGridArray
        localZGridArray = self.radius * cosPhiGridArray * numpy.ones_like(thetaGridArray)
        # makes z match the full 2d latitude / longitude layout before flattening

        # all relative to object
        self.localXArray = localXGridArray.ravel()
        self.localYArray = localYGridArray.ravel()
        self.localZArray = localZGridArray.ravel()

        pointsPerLatitudeRow = longitudeCount + 1

        latitudeIndexArray = numpy.arange(latitudeCount, dtype=numpy.int32)[:, None]
        longitudeIndexArray = numpy.arange(longitudeCount, dtype=numpy.int32)[None, :]
        # each represents one box aka two triangles between two latitude rows and two longitude columns

        topLeftIndexArray = (latitudeIndexArray * pointsPerLatitudeRow) + longitudeIndexArray
        topRightIndexArray = topLeftIndexArray + 1
        bottomLeftIndexArray = ((latitudeIndexArray + 1) * pointsPerLatitudeRow) + longitudeIndexArray
        bottomRightIndexArray = bottomLeftIndexArray + 1

        upperTriangleArray = numpy.stack((topLeftIndexArray,bottomLeftIndexArray,topRightIndexArray), axis=-1)

        lowerTriangleArray = numpy.stack((topRightIndexArray,bottomLeftIndexArray,bottomRightIndexArray), axis=-1)

        validUpperLatitudeArray = numpy.arange(latitudeCount, dtype=numpy.int32) != 0
        validLowerLatitudeArray = numpy.arange(latitudeCount, dtype=numpy.int32) != (latitudeCount - 1)
        # ^ excludes the evil triangles that shouldnt exist if they do

        upperTriangleArray = upperTriangleArray[validUpperLatitudeArray, :, :]
        lowerTriangleArray = lowerTriangleArray[validLowerLatitudeArray, :, :]
        # ^ removes the funky glitchy rows at the top and bottom 

        upperTriangleArray = upperTriangleArray.reshape(-1, 3)
        lowerTriangleArray = lowerTriangleArray.reshape(-1, 3)
        # ^ flattens both from 2d triangle grids into normal triangle lists

        # stores the triangle mesh connectivity for direct plotting / rendering
        self.triangleIndexArray = numpy.vstack((upperTriangleArray, lowerTriangleArray)).astype(numpy.int32)

class flatPlaneObject:
    def __init__(self, worldPosition, world, textureFile=None):
        # world position is the physical location relative to origin
        self.position = (worldPosition[0], worldPosition[1], worldPosition[2])

        self.xLocation = self.position[0]
        self.yLocation = self.position[1]
        self.zLocation = self.position[2]

        self.world = world

        self.width = None
        self.height = None
        self.halfWidth = None
        self.halfHeight = None

        self.localXArray = numpy.array([], dtype=numpy.float64)
        self.localYArray = numpy.array([], dtype=numpy.float64)
        self.localZArray = numpy.array([], dtype=numpy.float64)

        self.localUArray = numpy.array([], dtype=numpy.float64)
        self.localVArray = numpy.array([], dtype=numpy.float64)

        self.image = None
        self.imagePixelArray = None

        if textureFile is not None:
            self.image = pygame.image.load(textureFile).convert()

    def createPlane(self, width, height, faceOffset=(0, 0, 0), faceRotation=(0, 0, 0)):
        self.width = width
        self.height = height
        self.halfWidth = width / 2
        self.halfHeight = height / 2
        # just makes a flat background object
        faceSize = (self.width, self.height)
        self.localXArray, self.localYArray, self.localZArray, self.localUArray, self.localVArray = self.createFace(faceSize, faceOffset, faceRotation)

        if self.image is not None:
            self.image = pygame.transform.scale(self.image, (self.width, self.height))
            # uses 3d array to display all images without losing color depth, 2d is faster by alot, if needed.
            # converts all to numpy data
            self.imagePixelArray = pygame.surfarray.array3d(self.image).astype(numpy.float64)

    def createFace(self, faceSize, faceOffset, faceRotation):
        width, height = faceSize
        halfWidth = width / 2
        halfHeight = height / 2

        # all relative to object
        xOffset, yOffset, zOffset = faceOffset
        # offset is for placing MULTIPLE planes within one object, not needed if u dont wanna

        xRotation = faceRotation[0]
        yRotation = faceRotation[1]
        zRotation = faceRotation[2]

        cosXRotation = numpy.cos(xRotation)
        sinXRotation = numpy.sin(xRotation)
        cosYRotation = numpy.cos(yRotation)
        sinYRotation = numpy.sin(yRotation)
        cosZRotation = numpy.cos(zRotation)
        sinZRotation = numpy.sin(zRotation)

        gridAccuracy = self.world.gridAccuracy

        # all relative to object
        xDistances = numpy.arange(-halfWidth, halfWidth, gridAccuracy, dtype=numpy.float64)
        yDistances = numpy.arange(-halfHeight, halfHeight, gridAccuracy, dtype=numpy.float64)

        xLocation = numpy.tile(xDistances, len(yDistances))
        yLocation = numpy.repeat(yDistances, len(xDistances))
        # creates the same coordinate pair pattern as the old meshgrid+ravel setup

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

        return localXArray, localYArray, localZArray, localUArray, localVArray

def matPlot(meshVertexArray,triangleFaceArray):

    # shamelessly stole this example code so i could make sure my mesh rendered right without writing the lighting system
    fig = matplotlib.pyplot.figure()
    ax = fig.add_subplot(111, projection='3d')

    ax.plot_trisurf(meshVertexArray[:, 0],meshVertexArray[:, 1],meshVertexArray[:, 2],triangles=triangleFaceArray,shade=True,color='w',edgecolor='k',inewidth=0.2)
    ax.set_xlabel('X')
    ax.set_ylabel('Y')
    ax.set_zlabel('Z')
    matplotlib.pyplot.show()

def main():
    pygame.init()
    pygame.font.init()

    ######## settings pay attention to me ##############

    windowHeight = 700
    windowWidth = 700

    backGroundColor = "black"

    gridAccuracy = 10
    focalLength = 500
    # projection
    ####################################################

    screenCenterX = windowWidth / 2
    screenCenterY = windowHeight / 2

    # pygame definitions
    screen = pygame.display.set_mode((windowWidth, windowHeight))
    myFont = pygame.font.Font(None, 50)
    clock = pygame.time.Clock()

    # scene objects
    myWorld = worldObject(gridAccuracy)
    myCamera = cameraObject((screenCenterX, screenCenterY, 0), focalLength, windowWidth, windowHeight)
    myLight = lightObject(100, (screenCenterX, screenCenterY, 100))

    #startTime = time.perf_counter()
    mySphere = sphereObject(100, (screenCenterX, screenCenterY, 200), myWorld, None)
    #endTime = time.perf_counter()
    
    
    #print("sphere: " + str((endTime) - (startTime)))

    #startTime = time.perf_counter()
    myPlane = flatPlaneObject((screenCenterX, windowHeight, 150), myWorld, None)
    myPlane.createPlane(windowWidth, 300, faceOffset=(0, 0, 0), faceRotation=(3.14159 / 2, 0, 0))
    #endTime = time.perf_counter()
    #print("Plane: " + str((endTime) - (startTime)))

    sphereWorldXArray, sphereWorldYArray, sphereWorldZArray = getWorldPoints(mySphere)
    planeWorldXArray, planeWorldYArray, planeWorldZArray = getWorldPoints(myPlane)

    #print(str(len(planeWorldXArray)) + "   " + str(len(planeWorldYArray)) + "   " + str(len(planeWorldZArray)) )
    

    startTime = time.perf_counter()

    # creates vertex array for the sphere mesh instead of cache then finding them
    
    sphereVertexArray = numpy.column_stack((sphereWorldXArray, sphereWorldYArray, sphereWorldZArray))
    sphereTriangleFaceArray = mySphere.triangleIndexArray
    endTime = time.perf_counter()
    print("sphere meshtime: " + str((endTime) - (startTime)))

    matPlot(sphereVertexArray,sphereTriangleFaceArray)



    







    




    running = True

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        screen.fill(backGroundColor)

        pygame.display.flip()
        clock.tick(60)

    pygame.font.quit()
    pygame.quit()

testingMode = False
if testingMode == True:
    cProfile.run("main()", sort="cumulative")
else:
    main()



# unused, dont want to delete tho

#sphereCameraXArray, sphereCameraYArray, sphereCameraZArray = getCameraPoints(mySphere, myCamera)
#planeCameraXArray, planeCameraYArray, planeCameraZArray = getCameraPoints(myPlane, myCamera)
#sphereScreenXArray, sphereScreenYArray, sphereValidPoint = getScreenPoints(sphereCameraXArray, sphereCameraYArray, sphereCameraZArray, myCamera)
#planeScreenXArray, planeScreenYArray, planeValidPoint = getScreenPoints(planeCameraXArray, planeCameraYArray, planeCameraZArray, myCamera)
#startTime = time.perf_counter()
#endTime = time.perf_counter()
#print("plane meshtime: " + str((endTime) - (startTime)))
