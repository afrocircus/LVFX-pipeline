__author__ = 'Natasha'
__author__ = 'Natasha'

import maya.cmds as cmds
import maya.mel as mm
import pymel.core as pm
from math import sqrt, acos, pi, atan2


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

def dot(a,b):
    return a[0]*b[0] + a[1]*b[1] + a[2]*b[2]

# Find the distance of center from the sides.

def getProjectionDistance(center, point1, point2):
    v1 = vectorSub(center, point1)
    v2 = vectorSub(point1, point2)
    v3 = cross(v1,v2)
    d = magnitudeVector(v3)/magnitudeVector(v2)
    return d


def getNormal():
    verts = pm.ls(sl=True, fl=True)
    normals = [n.getNormal(space='world') for n in verts]
    vecSum = sum(normals)
    avgNorm = (vecSum/len(normals)).normal()
    normal = avgNorm.x, avgNorm.y, avgNorm.z
    normal = normalizeVector(normal)
    return normal


def getNormal2(selection, center):
    normal = (0., 0., 0.)
    for i in xrange(len(selection)):
        posA = cmds.xform(selection[i], q=1, ws=1, t=1)
        if i == len(selection)-1:
            posB = cmds.xform(selection[0], q=1, ws=1, t=1)
        else:
            posB = cmds.xform(selection[i+1], q=1, ws=1, t=1)
        vecA = vectorSub(center, posA)
        vecB = vectorSub(center, posB)
        normal = vectorAdd(normal, cross(vecA, vecB))
    normal = normalizeVector(normal)
    return normal


def calulateNewPos(unitBase, normal, degSpan, inradius, center, i):
    mm.eval('vector $base = <<%s,%s,%s>>' % (unitBase[0],unitBase[1],unitBase[2]))
    mm.eval('vector $norm = <<%s,%s,%s>>' % (normal[0],normal[1],normal[2]))
    radSpan = (degSpan * i) * pi/180
    mm.eval('float $radSpan = %f' % radSpan)
    rot = mm.eval('rot $base $norm $radSpan')
    rot = vectorMult(rot, inradius)
    newPos = vectorAdd(center, rot)
    return newPos

def calculateAngle(v1, v2):
    d = dot(v1, v2)
    magV1 = magnitudeVector(v1)
    magV2 = magnitudeVector(v2)
    a = d/(magV1*magV2)
    angle = acos(round(a,6))
    return angle

def closestDist(p, l):
    closestDist = -1
    closest = 0
    for x in l:
        dist = sqrt((p[0]-x[0])**2 + (p[1]-x[1])**2 + (p[2]-x[2])**2)
        if (dist < closestDist or closestDist == -1):
            closestDist = dist
            closest = x
    return closest

def sign(f):
    if f  < 0:
        return -1
    elif f > 0:
        return 1
    else:
        return 0

def calculateAngle360(base, point, normal):
    dp = dot(base, point)
    det = base[0]*point[1]*normal[2] + point[0]*normal[1]*base[2] + normal[0]*base[1]*point[2] - base[2]*point[1]*normal[0] - point[2]*normal[1]*base[0] - normal[2]*base[1]*point[0]
    angle = atan2(det,dp)*180 /pi
    s = sign(angle)
    if s == -1:
        angle = 360+angle
    return angle


def findStartPoint(selection):
    last = cmds.polyListComponentConversion(selection[len(selection)-1], fv=1, te=1)
    lastList = cmds.ls(last, fl=1)
    connected = set()
    for sel in selection:
        edges = cmds.polyListComponentConversion(sel, fv=1, te=1)
        edgeList = cmds.ls(edges, fl=1)
        for edge in edgeList:
            if edge in lastList:
                connected.add(sel)
    for vtx in connected:
        if selection.index(vtx) == len(selection)-1 or selection.index(vtx) == len(selection)-2:
            continue
        else:
            break
    return vtx

def makeCircle():
    selection = cmds.ls( sl=1, fl=1 )
    points = getSelectedVertices(selection)
    center = calculateCenter(points)
    inradius = getProjectionDistance(center, points[0], points[1])
    baseVector = vectorSub(center, points[0])
    unitBase = normalizeVector(baseVector)
    degSpan = 360/len(points)
    actualAngles = []
    idealAngles = []

    # Need to figure out a better way to find surface normal
    v1 = vectorSub(center, points[0])
    v2 = vectorSub(center, points[1])
    normal = cross(v1, v2)

    #vtx = findStartPoint(selection)
    newPoints = [calulateNewPos(unitBase, normal, degSpan, inradius, center, i) for i in range(0,len(points))]
    p = closestDist(newPoints[0], points)
    baseVector1 = vectorSub(center, p)
    for point in points:
        ang = calculateAngle360(baseVector1, vectorSub(center, point), normal)
        actualAngles.append(ang)
        idealAngles.append(degSpan * points.index(point))
    pointsSort = [ actualAngles.index(a) for a in sorted(actualAngles)]
    for i in range(0,len(points)):
        x,y,z = newPoints[i]
        cmds.move(x,y,z, selection[pointsSort[i]])
