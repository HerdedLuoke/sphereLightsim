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
        self.image = None
        self.imagePixelArray = None

        self.world = world
        self.radius = radius
        self.position = (worldPosition[0], worldPosition[1], worldPosition[2])

        self.xLocation = self.position[0]
        self.yLocation = self.position[1]
        self.zLocation = self.position[2]

        
        self.fullGrid = self.cacheSpherePoints()

        self.localXArray = numpy.array([gridPoint[0] for gridPoint in self.fullGrid], dtype=numpy.float64)
        self.localYArray = numpy.array([gridPoint[1] for gridPoint in self.fullGrid], dtype=numpy.float64)
        self.localZArray = numpy.array([gridPoint[2] for gridPoint in self.fullGrid], dtype=numpy.float64)

        if textureFile is not None:
            self.image = pygame.image.load(textureFile).convert()
            self.image = pygame.transform.scale(self.image, (int(self.radius * 2), int(self.radius * 2)))
            # uses 3d array to display all images without losing color depth, 2d is faster by alot, if needed.
            # converts all to numpy data
            self.imagePixelArray = pygame.surfarray.array3d(self.image).astype(numpy.float64)

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
            self.imagePixelArray = pygame.surfarray.array3d(self.image).astype(numpy.float64)

    def cacheSpherePoints(self):
        radiusSquared = self.radius ** 2
        gridAccuracy = self.world.gridAccuracy

        xDistances = numpy.arange(-self.radius, self.radius, gridAccuracy, dtype=numpy.float64)
        yDistances = numpy.arange(-self.radius, self.radius, gridAccuracy, dtype=numpy.float64)

        xLocation, yLocation = numpy.meshgrid(xDistances, yDistances, indexing="xy")

        distanceSumSq = (xLocation ** 2) + (yLocation ** 2)
        validPoint = distanceSumSq <= radiusSquared

        zLocation = numpy.sqrt(numpy.clip(radiusSquared - distanceSumSq, 0, None))

        self.localXArray = xLocation[validPoint]
        self.localYArray = yLocation[validPoint]
        self.localZArray = zLocation[validPoint]

class flatPlaneObject:
    def __init__(self, width, height, worldPosition, world, textureFile=None):
        self.width = width
        self.height = height
        self.position = (worldPosition[0], worldPosition[1], worldPosition[2])

        self.xLocation = self.position[0]
        self.yLocation = self.position[1]
        self.zLocation = self.position[2]

        self.world = world
        self.fullGrid = self.cacheLightingPoints()

        self.xArray = numpy.arange(self.xLocation, self.xLocation + self.width, self.world.gridAccuracy, dtype=numpy.float64)
        self.yArray = numpy.arange(self.yLocation, self.yLocation + self.height, self.world.gridAccuracy, dtype=numpy.float64)
        self.xGridArray, self.yGridArray = numpy.meshgrid(self.xArray, self.yArray, indexing="ij")

        self.image = None
        self.imagePixelArray = None

        if textureFile is not None:
            self.image = pygame.image.load(textureFile).convert()
            self.image = pygame.transform.scale(self.image, (self.width, self.height))
            # uses 3d array to display all images without losing color depth, 2d is faster by alot, if needed.
            # converts all to numpy data
            self.imagePixelArray = pygame.surfarray.array3d(self.image).astype(numpy.float64)

    def cacheLightingPoints(self):
        fullGrid = []
        gridAccuracy = self.world.gridAccuracy

        for yPixel in range(int(self.yLocation), int(self.yLocation + self.height), int(gridAccuracy)):
            for xPixel in range(int(self.xLocation), int(self.xLocation + self.width), int(gridAccuracy)):
                fullGrid.append((xPixel, yPixel, self.zLocation))

        return fullGrid


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
    print(f"sphere cache time: {endTime - startTime}")
    myPlane = flatPlaneObject(windowWidth, windowHeight, (0, 0, -100), myWorld, None)

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
