import pygame
import math
import time
import random


# whos gonna eat the meats
# lucas s, 3/27/2026 @ 12:53 AM

# use up/down key to move light on the z axis, top left shows ur z axis cord. starts (radius) away

pygame.init()
pygame.font.init()


class sphereObject:
    def __init__(self, radius, centerX, centerY, gridAccuracy, zLocation):
        self.radius = radius
        self.center = (centerX, centerY)
        self.zLocation = zLocation
        self.fullGrid = self.cacheSpherePoints(gridAccuracy)

    def cacheSpherePoints(self, gridAccuracy):
        radiusSquared = self.radius ** 2
        fullGrid = []

        # this goes through and finds all valid points (pixels) for a sphere  of input radius and center,
        # then saves it to an index. also finds their relative distances from center for later.
        for yGrid in range(int(self.center[1] - self.radius), int(self.center[1] + self.radius), gridAccuracy):
            distanceY = yGrid - self.center[1]
            distanceYsquared = distanceY ** 2

            for xGrid in range(int(self.center[0] - self.radius), int(self.center[0] + self.radius), gridAccuracy):
                distanceX = xGrid - self.center[0]
                distanceXsquared = distanceX ** 2
                distanceSumSq = distanceXsquared + distanceYsquared

                distanceZsquared = max(0, radiusSquared - distanceSumSq)
                distanceZ = math.sqrt(distanceZsquared)

                if distanceSumSq <= radiusSquared:
                    fullGrid.append((xGrid, yGrid, distanceX, distanceY, distanceZ))

        return fullGrid


class flatPlaneObject:
    def __init__(self, width, height, zLocation, gridAccuracy):
        self.width = width
        self.height = height
        self.zLocation = zLocation
        self.fullGrid = self.cacheLightingPoints(gridAccuracy)

    def cacheLightingPoints(self, gridAccuracy):
        fullGrid = []

        for yGrid in range(int(self.height / gridAccuracy)):
            yPixel = yGrid * gridAccuracy

            for xGrid in range(int(self.width / gridAccuracy)):
                xPixel = xGrid * gridAccuracy
                fullGrid.append((xPixel, yPixel))

        return fullGrid


class lightObject:
     def __init__(self,xCord,yCord,intensity,zLocation):
         self.position = (xCord,yCord)
         self.lightValue = intensity
         self.zLocation = zLocation

     def moveLight(self,newX,newY):
         self.position = (newX,newY)

     def lightUpdate(self, newIntensity):
         self.lightValue = newIntensity


def sphereShading(drawSurface, lightSource, sphere):
    radius = sphere.radius

    # light location relative to the spheres center
    lightX = lightSource.position[0] - sphere.center[0]
    lightY = lightSource.position[1] - sphere.center[1]
    lightZ = lightSource.zLocation - sphere.zLocation

    if gridAccuracy == 1:
        pixelArray = pygame.PixelArray(drawSurface)

    for gridPoint in sphere.fullGrid:

        # [x,y] location on the grid
        xGrid = gridPoint[0]
        yGrid = gridPoint[1]

        # grid distance relative to the spheres center
        distanceX = gridPoint[2]
        distanceY = gridPoint[3]

        # z axis for the grid point relative to center
        distanceZ = gridPoint[4]

        # light location relative to the gridPoint
        toLightY = lightY - distanceY
        toLightX = lightX - distanceX
        toLightZ = lightZ - distanceZ

        # formula for light dispersion around a sphere
        numerator = (distanceX * toLightX) + (distanceY * toLightY) + (distanceZ * toLightZ)
        denom = radius * math.sqrt((toLightX ** 2) + (toLightY ** 2) + (toLightZ ** 2))

        if denom != 0:
            lightingChange = numerator / denom
        else:
            lightingChange = 0

        lightSourceScaled = lightSource.lightValue * lightingChange

        # convert to 255, honestly could have be in 255 by def, but this is more fun
        hexValue = int((lightSourceScaled / 100) * 255)
        hexValue = max(0, min(255, hexValue))

        if gridAccuracy == 1:
            # .03s faster for only this size
            mappedColor = drawSurface.map_rgb((hexValue, hexValue, hexValue))
            pixelArray[xGrid][yGrid] = mappedColor
        else:
            # generally faster w/higher gridsize, but above ~5 is pointless
            pygame.draw.rect(drawSurface, (hexValue, hexValue, hexValue), (xGrid, yGrid, gridAccuracy, gridAccuracy))

    if gridAccuracy == 1:
        del pixelArray


def flatPlaneShading(drawSurface, lightSource, flatPlane):
    lightZ = lightSource.zLocation - flatPlane.zLocation

    if gridAccuracy == 1:
        pixelArray = pygame.PixelArray(drawSurface)

    for gridPoint in flatPlane.fullGrid:

        # [x,y] location on the grid
        xPixel = gridPoint[0]
        yPixel = gridPoint[1]

        distanceFromLightX = lightSource.position[0] - xPixel
        distanceFromLightY = lightSource.position[1] - yPixel
        distanceFromLightZ = lightZ

        # formula for light dispersion around a flat plane
        denom = 2 * math.sqrt((distanceFromLightX ** 2) + (distanceFromLightY ** 2) + (distanceFromLightZ ** 2))

        if denom != 0:
            lightingChange = distanceFromLightZ / denom
        else:
            lightingChange = 0

        lightSourceScaled = lightSource.lightValue * lightingChange

        # convert to 255, honestly could have be in 255 by def, but this is more fun
        hexValue = int((lightSourceScaled / 100) * 255)
        hexValue = max(0, min(255, hexValue))

        if gridAccuracy == 1:
            # .03s faster for only this size
            mappedColor = drawSurface.map_rgb((hexValue, hexValue, hexValue))
            pixelArray[xPixel][yPixel] = mappedColor
        else:
            # generally faster w/higher gridsize, but above ~5 is pointless
            pygame.draw.rect(drawSurface, (hexValue, hexValue, hexValue), (xPixel, yPixel, gridAccuracy, gridAccuracy))

    if gridAccuracy == 1:
        del pixelArray


def beginRender(backGroundColor):
    cachedSurface.fill(backGroundColor)

    for flatPlane in flatPlaneObjects:
        flatPlaneShading(cachedSurface, myLight, flatPlane)

    for sphere in sphereObjects:
        sphereShading(cachedSurface, myLight, sphere)


######## settings pay attention to me ##############

gridAccuracy = 3
# 1 is most quality

windowHeight = 700
windowWidth = 700
# this hasnt been tested for window sizes other than 700 square, no reason they shouldnt work tho

backGroundColor = "black"

####################################################


# pygame settings
screen = pygame.display.set_mode((windowWidth,windowHeight))
cachedSurface = pygame.Surface((windowWidth,windowHeight))
myFont = pygame.font.Font(None, 50)
clock = pygame.time.Clock()
running = True

# initial values
newPos = (0,0)
oldMousePos = None
oldLightZ = None

###### objects ########

myLight = lightObject(350,350,50,300)

mySphere = sphereObject(300, windowWidth / 2, windowHeight / 2, gridAccuracy, 0)
sphereObjects = (mySphere,)

myPlane = flatPlaneObject(windowWidth, windowHeight, -300, gridAccuracy)
flatPlaneObjects = (myPlane,)

#######################


while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        if event.type == pygame.KEYUP and event.key == pygame.K_UP:
            myLight.zLocation += 10

        if event.type == pygame.KEYUP and event.key == pygame.K_DOWN:
            myLight.zLocation -= 10

    pos = pygame.mouse.get_pos()

    if (pos != oldMousePos) or (myLight.zLocation != oldLightZ):

        myLight.moveLight(pos[0],pos[1])

        beginRender(backGroundColor)

        screen.fill(backGroundColor)
        screen.blit(cachedSurface, (0, 0))

        zAxisValue = myLight.zLocation
        text = myFont.render(str(zAxisValue), False, "White", None)
        screen.blit(text, (10, 10))

        pygame.display.flip()

        oldMousePos = pos
        oldLightZ = myLight.zLocation

pygame.font.quit()
pygame.quit()
