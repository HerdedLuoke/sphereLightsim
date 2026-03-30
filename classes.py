import numpy
from dataclasses import dataclass


@dataclass(frozen=True)
class worldGrid:
    type: str | None
    size: int

@dataclass(frozen=True)
class window:
    height: int
    width: int
    xCenter: float
    yCenter: float

@dataclass
class light:
    intensity: int
    position: tuple[float, float, float]
    color: str | None = "White"

@dataclass
class camera:
    position: tuple[float, float, float]
    focalLength: int
    window: window

@dataclass
class mesh:
    shape: str
    vertices: numpy.ndarray[numpy.float64]
    indexes: numpy.ndarray[numpy.int32]

@dataclass
class pointCloud:
    shape: str
    center: tuple[float, float, float]
    localX: numpy.ndarray[numpy.float64]
    localY: numpy.ndarray[numpy.float64]
    localZ: numpy.ndarray[numpy.float64]
    location: "location" 
    localU: numpy.ndarray[numpy.float64] | None = None
    localV: numpy.ndarray[numpy.float64] | None = None

@dataclass(frozen=True)
class location:
    parent: pointCloud
    # location relative to center of parent
    centerX: numpy.ndarray[numpy.float64]
    centerY: numpy.ndarray[numpy.float64]
    centerZ: numpy.ndarray[numpy.float64]
    # location on world grid
    worldX: numpy.ndarray[numpy.float64]
    worldY: numpy.ndarray[numpy.float64]
    worldZ: numpy.ndarray[numpy.float64]
    # location relative to camera
    cameraX: numpy.ndarray[numpy.float64]
    cameraY: numpy.ndarray[numpy.float64]
    cameraZ: numpy.ndarray[numpy.float64]
    # pixelwise location
    screenX: numpy.ndarray[numpy.float64] | None
    screenY: numpy.ndarray[numpy.float64] | None

@dataclass
class sphere:
    name: str
    grid: int | worldGrid
    radius: int
    position: tuple[float, float, float]
    texture: str | None = None
    color: str | None = None
    pointCloud: pointCloud
    mesh: mesh | None = None


@dataclass
class plane:
    name: str
    grid: int | worldGrid
    position: tuple[float, float, float]
    rotation: tuple[float, float, float]  # yaw pitch roll
    width: float
    height: float
    texture: str | None = None
    color: str | None = None
    pointCloud: pointCloud | None = None
    mesh: mesh | None = None
