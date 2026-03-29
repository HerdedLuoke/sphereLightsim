import matplotlib.pyplot

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

def matPlot(meshVertexArray,triangleFaceArray):

    # shamelessly stole this example code so i could make sure my mesh rendered right without writing the lighting system
    fig = matplotlib.pyplot.figure()
    ax = fig.add_subplot(111, projection='3d')

    ax.plot_trisurf(meshVertexArray[:, 0],meshVertexArray[:, 1],meshVertexArray[:, 2],triangles=triangleFaceArray,shade=True,color='w',edgecolor='k',linewidth=0.2)
    ax.set_xlabel('X')
    ax.set_ylabel('Y')
    ax.set_zlabel('Z')
    matplotlib.pyplot.show()