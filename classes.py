import pygame
import numpy



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
        # UV STYLE SPHERE GENERATION
    def __init__(self, radius, worldPosition, world, textureFile=None):
        self.radius = radius
        self.position = (worldPosition[0], worldPosition[1], worldPosition[2])

        self.xLocation = self.position[0]
        self.yLocation = self.position[1]
        self.zLocation = self.position[2]

        self.world = world

        self.cacheSpherePoints()
        self.createSphereTriangles()

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
        latitudeCount = max(4, int((numpy.pi * self.radius) / gridAccuracy))
        longitudeCount = max(8, int((2 * numpy.pi * self.radius) / gridAccuracy))
        # ^ finds the lat / long count for the grid accuracy, making it get smaller (bigger triangle/sections) as grid is bigger

        self.latitudeCount = latitudeCount
        self.longitudeCount = longitudeCount
        # stored for triangle stage

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

    def createSphereTriangles(self):
        latitudeCount = self.latitudeCount
        longitudeCount = self.longitudeCount

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
        # ^ excludes the degenerate pole triangles that slipped through

        upperTriangleArray = upperTriangleArray[validUpperLatitudeArray, :, :]
        lowerTriangleArray = lowerTriangleArray[validLowerLatitudeArray, :, :]
        # ^ removes the bad triangle rows at the top and bottom poles

        upperTriangleArray = upperTriangleArray.reshape(-1, 3)
        lowerTriangleArray = lowerTriangleArray.reshape(-1, 3)
        # ^ flattens both from 2d triangle grids into normal triangle lists

        
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

        self.triangleIndexArray = numpy.array([], dtype=numpy.int32)

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

        self.localXArray, self.localYArray, self.localZArray, self.localUArray, self.localVArray = self.cachePlanePoints(faceSize, faceOffset, faceRotation)
        self.createPlaneTriangles()

        if self.image is not None:
            self.image = pygame.transform.scale(self.image, (self.width, self.height))
            # uses 3d array to display all images without losing color depth, 2d is faster by alot, if needed.
            # converts all to numpy data
            self.imagePixelArray = pygame.surfarray.array3d(self.image).astype(numpy.float64)

    def cachePlanePoints(self, faceSize, faceOffset, faceRotation):
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
        xPointCount = int(width / gridAccuracy) + 1
        yPointCount = int(height / gridAccuracy) + 1

        xDistances = numpy.linspace(-halfWidth, halfWidth, xPointCount, dtype=numpy.float64)
        yDistances = numpy.linspace(-halfHeight, halfHeight, yPointCount, dtype=numpy.float64)

        self.rowLength = len(xDistances)
        self.columnLength = len(yDistances)

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

    def createPlaneTriangles(self):
        rowLength = self.rowLength
        columnLength = self.columnLength

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

        
        self.triangleIndexArray = numpy.vstack((upperTriangleArray, lowerTriangleArray)).astype(numpy.int32)