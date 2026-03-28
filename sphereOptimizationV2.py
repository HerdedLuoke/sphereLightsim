import pygame
import math
import cProfile
import numpy
import time

# whos gonna eat the meats
# lucas s,
# true 3d rewrite to create... clipping. yay!


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

        self.image = None
        self.imagePixelArray = None

        if textureFile != None:
            self.image = pygame.image.load(textureFile).convert()
            self.image = pygame.transform.scale(self.image, (int(self.radius * 2), int(self.radius * 2)))
            # uses 3d array to display all images without losing color depth, 2d is faster by alot, if needed.
            # converts all to numpy data
            self.imagePixelArray = pygame.surfarray.array3d(self.image).astype(numpy.float64)

    def cacheSpherePoints(self):
        radiusSquared = self.radius ** 2
        gridAccuracy = self.world.gridAccuracy

        # all relative to object
        xDistances = numpy.arange(-self.radius, self.radius, gridAccuracy, dtype=numpy.float64)
        yDistances = numpy.arange(-self.radius, self.radius, gridAccuracy, dtype=numpy.float64)

        xLocation = numpy.tile(xDistances, len(yDistances))
        yLocation = numpy.repeat(yDistances, len(xDistances))
        # creates the same coordinate pair pattern as the old meshgrid+ravel setup

        distanceSumSq = (xLocation ** 2) + (yLocation ** 2)
        validPoint = distanceSumSq <= radiusSquared

        zLocation = numpy.sqrt(numpy.clip(radiusSquared - distanceSumSq, 0, None))

        self.localXArray = xLocation[validPoint]
        self.localYArray = yLocation[validPoint]
        self.localZArray = zLocation[validPoint]


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


def main():
    pygame.init()
    pygame.font.init()

    ######## settings pay attention to me ##############

    windowHeight = 700
    windowWidth = 700

    backGroundColor = "black"

    gridAccuracy = 1
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

    startTime = time.perf_counter()
    mySphere = sphereObject(100, (screenCenterX, screenCenterY, 200), myWorld, None)
    endTime = time.perf_counter()
    print("sphere: " + str((endTime) - (startTime)))

    startTime = time.perf_counter()
    myPlane = flatPlaneObject((screenCenterX, windowHeight, 150), myWorld, None)
    myPlane.createPlane(windowWidth, 300, faceOffset=(0, 0, 0), faceRotation=(3.14159 / 2, 0, 0))
    endTime = time.perf_counter()
    print("Plane: " + str((endTime) - (startTime)))

    sphereWorldXArray, sphereWorldYArray, sphereWorldZArray = getWorldPoints(mySphere)
    planeWorldXArray, planeWorldYArray, planeWorldZArray = getWorldPoints(myPlane)

    sphereCameraXArray, sphereCameraYArray, sphereCameraZArray = getCameraPoints(mySphere, myCamera)
    planeCameraXArray, planeCameraYArray, planeCameraZArray = getCameraPoints(myPlane, myCamera)

    sphereScreenXArray, sphereScreenYArray, sphereValidPoint = getScreenPoints(sphereCameraXArray, sphereCameraYArray, sphereCameraZArray, myCamera)

    planeScreenXArray, planeScreenYArray, planeValidPoint = getScreenPoints(planeCameraXArray, planeCameraYArray, planeCameraZArray, myCamera)

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
