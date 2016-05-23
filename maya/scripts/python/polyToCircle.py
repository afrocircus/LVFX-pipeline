__author__ = 'Natasha'

import maya.cmds as cmds
from math import sqrt, tan


def getSelectedVertices(selection):
    points = []

    for each in selection:
        sel = each.split("'")
        tempVert = cmds.xform( sel, q=True, ws=True, t=True )
        points.append(zip(*[iter(tempVert)]*3))

    pointsList = []
    for pointList in points:
        for point in pointList:
            if point not in pointsList:
                pointsList.append(point)

    return pointsList


def calculateCenter(points):
    x,y,z = zip(*points)
    center = (max(x)+min(x))/2.0, (max(y)+min(y))/2, (max(z)+min(z))/2
    return center


def vectorAdd(p1, p2):
    x1, y1, z1 = p1
    x2, y2, z2 = p2
    x = x1 + x2
    y = y1 + y2
    z = z1 + z2
    return x,y,z


def vectorSub(p1, p2):
    x1,y1,z1 = p1
    x2, y2,z2 = p2
    x = x1 - x2
    y = y1 - y2
    z = z1 - z2
    return x,y,z


def normalizeVector(p):
    x,y,z = p
    x1 = x/sqrt(x*x + y*y + z*z)
    y1 = y/sqrt(x*x + y*y + z*z)
    z1 = y/sqrt(x*x + y*y + z*z)
    return x1,y1,z1


def vectorMult(p1, multiplier):
    x,y,z = p1
    return x*multiplier, y*multiplier,z*multiplier


def magnitudeVector(p):
    x,y,z = p
    return sqrt(x*x + y*y + z*z)


def findNewVertex(p1, center, dist):
    v = vectorSub(p1, center)
    m = magnitudeVector(v)
    u = (v[0]/m, v[1]/m, v[2]/m)
    mult = vectorMult(u, dist)
    newPoint = vectorAdd(center, mult)
    return newPoint


def cross(a, b):
    c = [a[1]*b[2] - a[2]*b[1],
         a[2]*b[0] - a[0]*b[2],
         a[0]*b[1] - a[1]*b[0]]

    return c

# Find the distance of center from the sides.

def getProjectionDistance(center, point1, point2):
    v1 = vectorSub(center, point1)
    v2 = vectorSub(point1, point2)
    v3 = cross(v1,v2)
    d = magnitudeVector(v3)/magnitudeVector(v2)
    return d


def polyToCircle():
    selection = cmds.ls( sl=1, fl=1 )
    points = getSelectedVertices(selection)
    center = calculateCenter(points)
    inradius = getProjectionDistance(center, points[0], points[1])
    newPos = [findNewVertex(point, center, inradius) for point in points ]
    for i in range(0,len(newPos)):
        x,y,z = newPos[i]
        cmds.move(x,y,z, selection[i])
