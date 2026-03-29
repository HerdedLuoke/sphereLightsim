import pygame
import cProfile
import numpy

from classes import lightObject, worldObject, cameraObject, sphereObject, flatPlaneObject
from functions import getWorldPoints, getCameraPoints, getScreenPoints, matPlot



def main():
    pygame.init()
    pygame.font.init()

    ######## settings pay attention to me ##############

    windowHeight = 700
    windowWidth = 700

    backGroundColor = "black"

    gridAccuracy = 25
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

    mySphere = sphereObject(100, (screenCenterX, screenCenterY, 200), myWorld, None)

    myPlane = flatPlaneObject((screenCenterX, windowHeight, 150), myWorld, None)
    myPlane.createPlane(windowWidth, 300, faceOffset=(0, 0, 0), faceRotation=(3.14159 / 2, 0, 0))

    sphereWorldXArray, sphereWorldYArray, sphereWorldZArray = getWorldPoints(mySphere)
    planeWorldXArray, planeWorldYArray, planeWorldZArray = getWorldPoints(myPlane)

    sphereVertexArray = numpy.column_stack((sphereWorldXArray, sphereWorldYArray, sphereWorldZArray))
    sphereTriangleFaceArray = mySphere.triangleIndexArray

    planeVertexArray = numpy.column_stack((planeWorldXArray, planeWorldYArray, planeWorldZArray))
    planeTriangleFaceArray = myPlane.triangleIndexArray

    matPlot(planeVertexArray,planeTriangleFaceArray)
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

#startTime = time.perf_counter()
#endTime = time.perf_counter()
#print("sphere: " + str((endTime) - (startTime)))

#startTime = time.perf_counter()
#endTime = time.perf_counter()
#print("Plane: " + str((endTime) - (startTime)))

#print(str(len(planeWorldXArray)) + "   " + str(len(planeWorldYArray)) + "   " + str(len(planeWorldZArray)) )

#startTime = time.perf_counter()
# creates vertex array for the sphere mesh instead of cache then finding them
#endTime = time.perf_counter()
#print("sphere meshtime: " + str((endTime) - (startTime)))

#sphereCameraXArray, sphereCameraYArray, sphereCameraZArray = getCameraPoints(mySphere, myCamera)
#planeCameraXArray, planeCameraYArray, planeCameraZArray = getCameraPoints(myPlane, myCamera)
#sphereScreenXArray, sphereScreenYArray, sphereValidPoint = getScreenPoints(sphereCameraXArray, sphereCameraYArray, sphereCameraZArray, myCamera)
#planeScreenXArray, planeScreenYArray, planeValidPoint = getScreenPoints(planeCameraXArray, planeCameraYArray, planeCameraZArray, myCamera)
#startTime = time.perf_counter()
#endTime = time.perf_counter()
#print("plane meshtime: " + str((endTime) - (startTime)))
