import pygame
import math
import time


# whos gonna eat the meats
# lucas s, 3/27/2026 @ 12:53 AM

# use up/down key to move light on the z axis, top left shows ur z axis cord. starts (radius) away

pygame.init()
pygame.font.init()


class sphereObject:
    def __init__(self, radius, centerX, centerY, gridAccuracy):
        self.radius = radius
        self.center = (centerX, centerY)
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

class lightObject:
     def __init__(self,xCord,yCord,intensity):
         self.position = (xCord,yCord)
         self.lightValue = intensity
     def moveLight(self,newX,newY):
         self.position = (newX,newY)
     def lightUpdate(self, newIntensity):
         self.lightValue = newIntensity

def sphereShading(drawSurface, lightSource, sphere, zLocation):
    radius = sphere.radius

    if gridAccuracy == 1:
        pixelArray = pygame.PixelArray(drawSurface)
    
    # light location relative to the spheres center
    lightX = lightSource.position[0] - sphere.center[0]
    lightY = lightSource.position[1] - sphere.center[1]
    lightZ = sphere.radius + zLocation

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


        #formula for light dispersion around a sphere
        numerator = (distanceX * toLightX) + (distanceY * toLightY) + (distanceZ * toLightZ)
        denom = radius * math.sqrt((toLightX ** 2) + (toLightY ** 2) + (toLightZ ** 2))

        if denom != 0:
            lightingChange = numerator / denom
        else:
            lightingChange = 0

        lightSourceScaled = lightSource.lightValue * lightingChange

        #convert to 255, honestly could have be in 255 by def, but this is more fun
        hexValue = int((lightSourceScaled / 100) * 255)
        hexValue = max(0, min(255, hexValue))

        if gridAccuracy == 1:
            #.03s faster for only this size
            mappedColor = drawSurface.map_rgb((hexValue, hexValue, hexValue))
            pixelArray[xGrid][yGrid] = mappedColor
        else:
            #generally faster w/higher gridsize, but above ~5 is pointless
            pygame.draw.rect(drawSurface, (hexValue, hexValue, hexValue), (xGrid, yGrid, gridAccuracy, gridAccuracy))

    if gridAccuracy == 1:
        del pixelArray

def beginRender(zChangem,backGroundColor):
    cachedSurface.fill(backGroundColor)
    for sphere in sphereObjects:
        sphereShading(cachedSurface, myLight, sphere, zChange)



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
gridBlockWidth = int(screen.get_width() / gridAccuracy)
gridBlockHeight =  int(screen.get_height() / gridAccuracy)

# initial values
zChange = 0
newPos = (0,0)  
oldMousePos = None
oldZChange = None

###### objects ########

myLight = lightObject(350,350,100)
mySphere = sphereObject(300, screen.get_width() / 2, screen.get_height() / 2, gridAccuracy)

sphereObjects = (mySphere,)

#######################

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.KEYUP and event.key == pygame.K_UP:
            zChange += 10
        if event.type == pygame.KEYUP and event.key == pygame.K_DOWN:
            zChange -= 10
            

    pos = pygame.mouse.get_pos()

    if (pos != oldMousePos) or (zChange != oldZChange):

        # print("new frame")
        myLight.moveLight(pos[0],pos[1])

        # startTime = time.perf_counter()
        beginRender(zChange,backGroundColor)
        # endTime = time.perf_counter()

        # print(endTime - startTime)

        screen.fill(backGroundColor)
        screen.blit(cachedSurface, (0, 0))

        for sphere in sphereObjects:
            zAxisValue = sphere.radius + zChange
        
        text = myFont.render(str(zAxisValue), False, "White", None)
        screen.blit(text, (10, 10))

        pygame.display.flip()

        oldMousePos = pos
        oldZChange = zChange

pygame.font.quit()
pygame.quit()