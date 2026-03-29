import pygame
import math
import cProfile
import numpy


# whos gonna eat the meats
# lucas s, 3/27/2026 @ 12:53 AM

# use up/down key to move light on the z axis, top left shows ur z axis cord. starts (radius) away


class sphereObject:
    def __init__(self, radius, centerX, centerY, gridAccuracy, zLocation, textureFile=None):
        self.radius = radius
        self.center = (centerX, centerY)
        self.zLocation = zLocation
        self.fullGrid = self.cacheSpherePoints(gridAccuracy)

        self.xGridArray = numpy.array([gridPoint[0] for gridPoint in self.fullGrid], dtype=numpy.int32)
        self.yGridArray = numpy.array([gridPoint[1] for gridPoint in self.fullGrid], dtype=numpy.int32)
        self.distanceXArray = numpy.array([gridPoint[2] for gridPoint in self.fullGrid], dtype=numpy.float64)
        self.distanceYArray = numpy.array([gridPoint[3] for gridPoint in self.fullGrid], dtype=numpy.float64)
        self.distanceZArray = numpy.array([gridPoint[4] for gridPoint in self.fullGrid], dtype=numpy.float64)

        self.image = None
        self.imagePixelArray = None

        if textureFile is not None:
            self.image = pygame.image.load(textureFile).convert()
            self.image = pygame.transform.scale(self.image, (int(self.radius * 2), int(self.radius * 2)))
            # uses 3d array to display all images without losing color depth, 2d is faster by alot, if needed.
            # converts all to numpy data
            self.imagePixelArray = pygame.surfarray.array3d(self.image).astype(numpy.float64)

    def cacheSpherePoints(self, gridAccuracy):
        radiusSquared = self.radius ** 2
        fullGrid = []

        # this goes through and finds all valid points (pixels) for a sphere of input radius and center,
        # then saves them to an index. also finds their relative distances from center for later.
        for yGrid in range(int(self.center[1] - self.radius), int(self.center[1] + self.radius), int(gridAccuracy)):
            distanceY = yGrid - self.center[1]
            distanceYsquared = distanceY ** 2

            for xGrid in range(int(self.center[0] - self.radius), int(self.center[0] + self.radius), int(gridAccuracy)):
                distanceX = xGrid - self.center[0]
                distanceXsquared = distanceX ** 2
                distanceSumSq = distanceXsquared + distanceYsquared

                distanceZsquared = max(0, radiusSquared - distanceSumSq)
                distanceZ = math.sqrt(distanceZsquared)

                if distanceSumSq <= radiusSquared:
                    fullGrid.append((xGrid, yGrid, distanceX, distanceY, distanceZ))

        return fullGrid


class flatPlaneObject:
    def __init__(self, width, height, zLocation, gridAccuracy, textureFile):
        self.width = width
        self.height = height
        self.zLocation = zLocation
        self.fullGrid = self.cacheLightingPoints(gridAccuracy)

        self.xArray = numpy.arange(0, self.width, gridAccuracy, dtype=numpy.float64)
        self.yArray = numpy.arange(0, self.height, gridAccuracy, dtype=numpy.float64)
        self.xGridArray, self.yGridArray = numpy.meshgrid(self.xArray, self.yArray, indexing="ij")

        self.image = None
        self.imagePixelArray = None

        if textureFile != None:
            self.image = pygame.image.load(textureFile).convert()
            self.image = pygame.transform.scale(self.image, (self.width, self.height))
            # uses 3d array to display all images without losing color depth, 2d is faster by alot, if needed.
            # converts all to numpy data
            self.imagePixelArray = pygame.surfarray.array3d(self.image).astype(numpy.float64)



            

    def cacheLightingPoints(self, gridAccuracy):
        fullGrid = []

        for yGrid in range(int(self.height / gridAccuracy)):
            yPixel = yGrid * gridAccuracy

            for xGrid in range(int(self.width / gridAccuracy)):
                xPixel = xGrid * gridAccuracy
                fullGrid.append((xPixel, yPixel))

        return fullGrid


class lightObject:
    def __init__(self, xCord, yCord, intensity, zLocation):
        self.position = (xCord, yCord)
        self.lightValue = intensity
        self.zLocation = zLocation

    def moveLight(self, newX, newY):
        self.position = (newX, newY)

    def lightUpdate(self, newIntensity):
        self.lightValue = newIntensity


def sphereShading(drawSurface, lightSource, sphere, gridAccuracy):
    radius = sphere.radius

    # light location relative to the sphere's center
    lightX = lightSource.position[0] - sphere.center[0]
    lightY = lightSource.position[1] - sphere.center[1]
    lightZ = lightSource.zLocation - sphere.zLocation

    # light location relative to every cached grid point at once
    toLightY = lightY - sphere.distanceYArray
    toLightX = lightX - sphere.distanceXArray
    toLightZ = lightZ - sphere.distanceZArray

    # formula for light dispersion around a sphere, but done across the full cached arrays
    numerator = (sphere.distanceXArray * toLightX) + (sphere.distanceYArray * toLightY) + (sphere.distanceZArray * toLightZ)
    
    denom = radius * numpy.sqrt((toLightX ** 2)*3 + (toLightY ** 2)*3 + (toLightZ ** 2)*3)

    lightingChange = numpy.zeros_like(numerator)

    # keep the old denom check behavior, just applied to all valid entries at once
    validDenom = denom != 0
    lightingChange[validDenom] = numerator[validDenom] / denom[validDenom]

    lightSourceScaled = lightSource.lightValue * lightingChange

    # convert to 255, honestly could have be in 255 by def, but this is more fun
    hexValues = ((lightSourceScaled / 100) * 255).astype(numpy.int32)
    hexValues = numpy.clip(hexValues, 0, 255).astype(numpy.uint8)

    if gridAccuracy == 1 and sphere.image == None:
        pixelArray = pygame.surfarray.pixels3d(drawSurface)

        # write all cached sphere pixels in one pass, same grayscale value on all 3 color channels
        pixelArray[sphere.xGridArray, sphere.yGridArray] = hexValues[:, None]
        del pixelArray

    elif gridAccuracy == 1 and sphere.image != None:
        pixelArray = pygame.surfarray.pixels3d(drawSurface)

        brightnessScale = numpy.clip(lightSourceScaled / 100.0, 0.0, 1.0)

        imageXArray = sphere.xGridArray - int(sphere.center[0] - sphere.radius)
        imageYArray = sphere.yGridArray - int(sphere.center[1] - sphere.radius)

        sampledColors = sphere.imagePixelArray[imageXArray, imageYArray]

        pixelArray[sphere.xGridArray, sphere.yGridArray, 0] = (sampledColors[:, 0] * brightnessScale).astype(numpy.uint8)
        pixelArray[sphere.xGridArray, sphere.yGridArray, 1] = (sampledColors[:, 1] * brightnessScale).astype(numpy.uint8)
        pixelArray[sphere.xGridArray, sphere.yGridArray, 2] = (sampledColors[:, 2] * brightnessScale).astype(numpy.uint8)
        del pixelArray

    else:
        for index in range(len(hexValues)):
            xGrid = sphere.xGridArray[index]
            yGrid = sphere.yGridArray[index]

            if sphere.image == None:
                hexValue = int(hexValues[index])
                pygame.draw.rect(drawSurface, (hexValue, hexValue, hexValue), (xGrid, yGrid, gridAccuracy, gridAccuracy))
            else:
                imageX = int(xGrid - int(sphere.center[0] - sphere.radius))
                imageY = int(yGrid - int(sphere.center[1] - sphere.radius))

                brightnessScale = max(0.0, min(1.0, lightSourceScaled[index] / 100.0))
                baseColor = sphere.imagePixelArray[imageX, imageY]

                finalColor = (
                    int(baseColor[0] * brightnessScale),
                    int(baseColor[1] * brightnessScale),
                    int(baseColor[2] * brightnessScale)
                )

                pygame.draw.rect(drawSurface, finalColor, (xGrid, yGrid, gridAccuracy, gridAccuracy))


def flatPlaneShading(drawSurface, lightSource, flatPlane, gridAccuracy):
    lightZ = lightSource.zLocation - flatPlane.zLocation

    distanceFromLightX = lightSource.position[0] - flatPlane.xGridArray
    distanceFromLightY = lightSource.position[1] - flatPlane.yGridArray
    distanceFromLightZ = lightZ

    # formula for light dispersion around a flat plane, but done across the full grid at once
    denom = numpy.sqrt(distanceFromLightZ/15) * numpy.sqrt((distanceFromLightX ** 2) + (distanceFromLightY ** 2) + (distanceFromLightZ ** 2))

    lightingChange = numpy.zeros_like(denom)

    # keep the old denom check behavior, just applied to the whole grid at once
    validDenom = denom != 0
    lightingChange[validDenom] = distanceFromLightZ / denom[validDenom]

    lightSourceScaled = lightSource.lightValue * lightingChange

    # convert to 255, honestly could have be in 255 by def, but this is more fun
    hexValues = ((lightSourceScaled / 100) * 255).astype(numpy.int32)
    hexValues = numpy.clip(hexValues, 0, 255).astype(numpy.uint8)

    if gridAccuracy == 1 and flatPlane.image == None:
        pixelArray = pygame.surfarray.pixels3d(drawSurface)

        # fill each RGB channel with the same grayscale values
        pixelArray[:, :, 0] = hexValues
        pixelArray[:, :, 1] = hexValues
        pixelArray[:, :, 2] = hexValues
        del pixelArray
    elif gridAccuracy == 1 and flatPlane.image != None:
        pixelArray = pygame.surfarray.pixels3d(drawSurface)
        brightnessScale = numpy.clip(lightSourceScaled / 100.0, 0.0, 1.0)
        # accesses all of the color vals for all x/y and does vector operation of * the multiplier to all
        pixelArray[:, :, 0] = (flatPlane.imagePixelArray[:, :, 0] * brightnessScale).astype(numpy.uint8)
        pixelArray[:, :, 1] = (flatPlane.imagePixelArray[:, :, 1] * brightnessScale).astype(numpy.uint8)
        pixelArray[:, :, 2] = (flatPlane.imagePixelArray[:, :, 2] * brightnessScale).astype(numpy.uint8)
        del pixelArray
    else:
        for gridPoint in flatPlane.fullGrid:
            xPixel = gridPoint[0]
            yPixel = gridPoint[1]
            hexValue = int(hexValues[int(xPixel / gridAccuracy)][int(yPixel / gridAccuracy)])
            pygame.draw.rect(drawSurface, (hexValue, hexValue, hexValue), (xPixel, yPixel, gridAccuracy, gridAccuracy))


def beginRender(cachedSurface, backGroundColor, flatPlaneObjects, sphereObjects, myLight, gridAccuracy):
    cachedSurface.fill(backGroundColor)
    indx = 0
    renderList = []

    for flatPlane in flatPlaneObjects:
        renderList.append(("pln", flatPlane))
    for sphere in sphereObjects:
        renderList.append(("sph", sphere))

    renderList.sort(key=lambda item: item[1].zLocation)
    
    for object in renderList:
        if renderList[indx][0] == "pln":
            flatPlaneShading(cachedSurface, myLight, renderList[indx][1], gridAccuracy)
        elif len(renderList) - 1 > indx:
            if renderList[indx + 1][0] != "pln":
                sphereShading(cachedSurface, myLight, object[1], gridAccuracy)
        else:
            sphereShading(cachedSurface, myLight, object[1], gridAccuracy)



        indx += 1

def renderBenchmark(screen, cachedSurface, backGroundColor, flatPlaneObjects, sphereObjects, myLight, gridAccuracy, myFont, clock):
    # move the light from the left side of the screen to the right, then stop
    # hopefully edit this to handle multiple lights. does light combine? it should increase intensity somewhat but id guess theres a point of dimin returns
    for lightX in range(0, screen.get_width()):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                # exits on being done and returns the benchmark
                return

            if event.type == pygame.KEYUP and event.key == pygame.K_UP:
                myLight.zLocation += 10

            if event.type == pygame.KEYUP and event.key == pygame.K_DOWN:
                myLight.zLocation -= 10

        myLight.moveLight(lightX, myLight.position[1])

        beginRender(cachedSurface, backGroundColor, flatPlaneObjects, sphereObjects, myLight, gridAccuracy)

        screen.fill(backGroundColor)
        screen.blit(cachedSurface, (0, 0))

        zAxisValue = myLight.zLocation
        text = myFont.render(str(zAxisValue), False, "White", None)
        screen.blit(text, (10, 10))

        pygame.display.flip()

        clock.tick(60)


def mouseStyle(screen, cachedSurface, backGroundColor, flatPlaneObjects, sphereObjects, myLight, gridAccuracy, myFont, clock):
    running = True
    oldMousePos = None
    oldLightZ = None

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            if event.type == pygame.KEYUP and event.key == pygame.K_UP:
                myLight.zLocation += 10
                cordChange = True

            if event.type == pygame.KEYUP and event.key == pygame.K_DOWN:
                myLight.zLocation -= 10
                cordChange = True
            
            if event.type == pygame.KEYUP and event.key == pygame.K_RIGHT:
                if len(flatPlaneObjects) > 0:
                    flatPlaneObjects[0].zLocation += 10
                    print(flatPlaneObjects[0].zLocation)
                    cordChange = True

            if event.type == pygame.KEYUP and event.key == pygame.K_LEFT:
                if len(flatPlaneObjects) > 0:
                    flatPlaneObjects[0].zLocation -= 10
                    print(flatPlaneObjects[0].zLocation)
                    cordChange = True

        pos = pygame.mouse.get_pos()

        if (pos != oldMousePos) or (cordChange):
            cordChange = False
            myLight.moveLight(pos[0], pos[1])

            beginRender(cachedSurface, backGroundColor, flatPlaneObjects, sphereObjects, myLight, gridAccuracy)

            screen.fill(backGroundColor)
            screen.blit(cachedSurface, (0, 0))

            zAxisValue = myLight.zLocation
            text = myFont.render(str(zAxisValue), False, "White", None)
            screen.blit(text, (10, 10))

            pygame.display.flip()

            oldMousePos = pos
            oldLightZ = myLight.zLocation

        clock.tick(60)


def main(testingMode):
    pygame.init()
    pygame.font.init()

    ######## settings pay attention to me ##############

    gridAccuracy = 1
    # 1 is most quality

    windowHeight = 700
    windowWidth = 700
    # this hasnt been tested for window sizes other than 700 square, no reason they shouldnt work tho

    backGroundColor = "black"

    # True runs the left to right test, False follows the mouse

    ####################################################

    # pygame settings
    screen = pygame.display.set_mode((windowWidth, windowHeight))
    cachedSurface = pygame.Surface((windowWidth, windowHeight))
    myFont = pygame.font.Font(None, 50)
    clock = pygame.time.Clock()

    ###### objects ########

    myLight = lightObject(350, 350, 100, 300)

    mySphere = sphereObject(100, windowWidth / 4, windowHeight / 4, gridAccuracy, 150, "trollface.png")
    sphereObjects = (mySphere,)

    myPlane = flatPlaneObject(windowWidth, windowHeight, -600, gridAccuracy, None)
    flatPlaneObjects = [myPlane]

    #######################

    if testingMode:
        renderBenchmark(screen, cachedSurface, backGroundColor, flatPlaneObjects, sphereObjects, myLight, gridAccuracy, myFont, clock)
    else:
        mouseStyle(screen, cachedSurface, backGroundColor, flatPlaneObjects, sphereObjects, myLight, gridAccuracy, myFont, clock)

    pygame.font.quit()
    pygame.quit()


testingMode = False
if testingMode == True:
    cProfile.run("main(testingMode)", sort="cumulative")
else:
    main(testingMode)
