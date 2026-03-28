import pygame
import math
import cProfile
import numpy
import time

# whos gonna eat the meats
# lucas s,
# true 3d rewrite to create... clipping. yay!


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
    def __init__(self, cameraPosition):
        self.position = (cameraPosition[0], cameraPosition[1], cameraPosition[2])

        self.xLocation = self.position[0]
        self.yLocation = self.position[1]
        self.zLocation = self.position[2]

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

        if textureFile is not None:
            self.image = pygame.image.load(textureFile).convert()
            self.image = pygame.transform.scale(self.image, (int(self.radius * 2), int(self.radius * 2)))
            # uses 3d array to display all images without losing color depth, 2d is faster by alot, if needed.
            # converts all to numpy data
            self.imagePixelArray = pygame.surfarray.array3d(self.image).astype(numpy.float64)

    def cacheSpherePoints(self):
        radiusSquared = self.radius ** 2
        gridAccuracy = self.world.gridAccuracy

        xDistances = numpy.arange(-self.radius, self.radius, gridAccuracy, dtype=numpy.float64)
        yDistances = numpy.arange(-self.radius, self.radius, gridAccuracy, dtype=numpy.float64)

        xLocation, yLocation = numpy.meshgrid(xDistances, yDistances, indexing="xy")
        # meshes two grids together so everything has a set of coordinates. this makes matrix operations using two arrays possible

        distanceSumSq = (xLocation ** 2) + (yLocation ** 2)
        validPoint = distanceSumSq <= radiusSquared

        zLocation = numpy.sqrt(numpy.clip(radiusSquared - distanceSumSq, 0, None))

        self.localXArray = xLocation[validPoint]
        self.localYArray = yLocation[validPoint]
        self.localZArray = zLocation[validPoint]


class flatPlaneObject:
    def __init__(self, worldPosition, world, textureFile=None):
        # world position is the physical location relative to world
        self.position = (worldPosition[0], worldPosition[1], worldPosition[2])

        self.xLocation = self.position[0]
        self.yLocation = self.position[1]
        self.zLocation = self.position[2]

        self.world = world

        self.width = None
        self.height = None

        self.localXArray = numpy.array([], dtype=numpy.float64)
        self.localYArray = numpy.array([], dtype=numpy.float64)
        self.localZArray = numpy.array([], dtype=numpy.float64)

        self.image = None
        self.imagePixelArray = None

        if textureFile is not None:
            self.image = pygame.image.load(textureFile).convert()

    def createPlane(self, width, height, faceOffset=(0, 0, 0), faceRotation=(0, 0, 0)):
        self.width = width
        self.height = height

        faceSize = (self.width, self.height)
        self.localXArray, self.localYArray, self.localZArray = self.createFace(faceSize, faceOffset, faceRotation)

        if self.image is not None:
            self.image = pygame.transform.scale(self.image, (self.width, self.height))
            # uses 3d array to display all images without losing color depth, 2d is faster by alot, if needed.
            # converts all to numpy data
            self.imagePixelArray = pygame.surfarray.array3d(self.image).astype(numpy.float64)

    def createFace(self, faceSize, faceOffset, faceRotation):
        width, height = faceSize
        xOffset, yOffset, zOffset = faceOffset
        # offset is for placing MULTIPLE planes within one object, not needed if u dont wanna
        xRotation, yRotation, zRotation = faceRotation

        gridAccuracy = self.world.gridAccuracy

        xDistances = numpy.arange(-(width / 2), width / 2, gridAccuracy, dtype=numpy.float64)
        yDistances = numpy.arange(-(height / 2), height / 2, gridAccuracy, dtype=numpy.float64)

        xLocation, yLocation = numpy.meshgrid(xDistances, yDistances, indexing="xy")
        # meshes two grids together so everything has a set of coordinates. this makes matrix operations using two arrays possible

        localXArray = xLocation.ravel()
        localYArray = yLocation.ravel()
        # converts 2d into a 1d ^

        localZArray = numpy.zeros_like(localXArray, dtype=numpy.float64)
        # zeros for the same space of the x array

        yRotated = (localYArray * numpy.cos(xRotation)) - (localZArray * numpy.sin(xRotation))
        zRotated = (localYArray * numpy.sin(xRotation)) + (localZArray * numpy.cos(xRotation))
        localYArray = yRotated
        localZArray = zRotated
        # rotates the face around the x axis

        xRotated = (localXArray * numpy.cos(yRotation)) + (localZArray * numpy.sin(yRotation))
        zRotated = -(localXArray * numpy.sin(yRotation)) + (localZArray * numpy.cos(yRotation))
        localXArray = xRotated
        localZArray = zRotated
        # rotates the face around the y axis

        xRotated = (localXArray * numpy.cos(zRotation)) - (localYArray * numpy.sin(zRotation))
        yRotated = (localXArray * numpy.sin(zRotation)) + (localYArray * numpy.cos(zRotation))
        localXArray = xRotated
        localYArray = yRotated
        # rotates the face around the z axis

        localXArray = localXArray + xOffset
        localYArray = localYArray + yOffset
        localZArray = localZArray + zOffset
        # moves the face after rotation so it can be placed where needed in world plane

        return localXArray, localYArray, localZArray


def main():
    pygame.init()
    pygame.font.init()

    ######## settings pay attention to me ##############

    windowHeight = 700
    windowWidth = 700

    backGroundColor = "black"

    gridAccuracy = 1

    ####################################################

    # pygame definitions
    screen = pygame.display.set_mode((windowWidth, windowHeight))
    myFont = pygame.font.Font(None, 50)
    clock = pygame.time.Clock()

    # scene objects
    myWorld = worldObject(gridAccuracy)
    myCamera = cameraObject((windowWidth / 2, windowHeight / 2, 0))
    myLight = lightObject(100, (windowWidth / 2, windowHeight / 2, 100))

    startTime = time.perf_counter()
    mySphere = sphereObject(100, (windowWidth / 2, windowHeight / 2, 0), myWorld, None)
    endTime = time.perf_counter()
    print("sphere: " + str((endTime) - (startTime)))

    startTime = time.perf_counter()
    myPlane = flatPlaneObject((windowWidth / 2, windowHeight, 150), myWorld, None)
    myPlane.createPlane(windowWidth, 300, faceOffset=(0, 0, 0), faceRotation=(3.14159 / 2, 0, 0))
    endTime = time.perf_counter()
    print("Plane: " + str((endTime) - (startTime)))

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
