#!/usr/bin/python

import os
import sys
import PIL
import math
import numpy as np
import cv
import SimpleCV
import imageIO
import imthr_lib
import sudokuSolver


class Sudoku:

    def __init__(self, imgPath):
        self.pilImg = PIL.Image.open(imgPath)
        self.img = SimpleCV.Image(imgPath)

        self.sudokuString = ""

        self.topleft = None
        self.topright = None
        self.bottomleft = None
        self.bottomright = None

    @property
    def img(self):
        return self.img

    @property
    def toString(self):
        return self.sudokuString

    def threshold(self):
        print "Applying the threshold..."

        self.pilImg = self.pilImg.convert('L')
        self.pilImg = np.asarray(self.pilImg)

        self.pilImg = imthr_lib.sauvola(self.pilImg, k=0.05)
        imageIO.imwrite_gray('images/temp-threshold.png', self.pilImg)

        self.img = SimpleCV.Image('images/temp-threshold.png')

    def findCorners(self):
        print "Finding the corners..."

        edgeMap = self.img.edges()
        lines = edgeMap.findLines(threshold=150, maxlinegap=3)

        pts = []

        for line in lines:

            a = line.bottomLeftCorner()
            b = line.topRightCorner()
            intersections = edgeMap.edgeIntersections(a, b, width=1)

            if intersections[0] != None and intersections[1] != None:
                pts.append(intersections[0])
                pts.append(intersections[1])

        self.findCornerPositions(pts)

    def findCornersManually(self):

        print "\nSelect the corners of the sudoku puzzle..."
        print "- click to choose a corner"
        print "- right click to clear all points currently selected"
        print "- click a fifth time to exit.\n"

        temp = self.img.copy()
        layer = SimpleCV.DrawingLayer(temp.size())
        temp.addDrawingLayer(layer)

        display = SimpleCV.Display()
        pts = []

        while display.isNotDone():

            if display.leftButtonUp:
                if len(pts) >= 4:
                    break

                pts.append((display.mouseX, display.mouseY))
                layer.circle(pts[-1], 10, color=SimpleCV.Color.RED)
                temp.applyLayers()

            if display.rightButtonUp:
                del pts[:]
                temp.clearLayers()
                layer = SimpleCV.DrawingLayer(temp.size())
                temp.addDrawingLayer(layer)

            temp.save(display)

        self.findCornerPositions(pts)

    def findCornerPositions(self, pts):

        radius = 10
        tl, tr, bl, br = False, False, False, False
        while(radius <= min(self.img.width, self.img.height)):

            for pt in pts:

                # top left
                if not tl and pt[0] < radius and pt[1] < radius:
                    self.topleft = pt
                    tl = True

                # bottom left
                if not bl and pt[0] < radius and pt[1] > (self.img.height - radius):
                    self.bottomleft = pt
                    bl = True

                # top right
                if not tr and pt[0] > (self.img.width - radius) and pt[1] < radius:
                    self.topright = pt
                    tr = True

                # bottom right
                if not br and pt[0] > (self.img.width - radius) and pt[1] > (self.img.height - radius):
                    self.bottomright = pt
                    br = True

            if tl and tr and bl and br:
                break

            radius = radius + 10

        tempImg = self.img.copy()
        tempImg.drawCircle(self.topleft, 10, color=SimpleCV.Color.RED)
        tempImg.drawCircle(self.bottomleft, 10, color=SimpleCV.Color.RED)
        tempImg.drawCircle(self.topright, 10, color=SimpleCV.Color.RED)
        tempImg.drawCircle(self.bottomright, 10, color=SimpleCV.Color.RED)

        tempImg.save('images/temp-corners.png')

    def correctPerspective(self):
        print "Fixing the perspective..."

        if self.topleft == None or self.topright == None or self.bottomright == None or self.bottomleft == None:
            print "You must first run find corners."
            return

        minX = min(self.topleft[0], self.topright[0], self.bottomright[0], self.bottomleft[0])
        maxX = max(self.topleft[0], self.topright[0], self.bottomright[0], self.bottomleft[0])
        minY = min(self.topleft[1], self.topright[1], self.bottomright[1], self.bottomleft[1])
        maxY = max(self.topleft[1], self.topright[1], self.bottomright[1], self.bottomleft[1])

        newTopLeft = (minX, minY)
        newTopRight = (maxX, minY)
        newBottomRight = (maxX, maxY)
        newBottomLeft =  (minX, maxY)

        src = (self.topleft, self.topright, self.bottomright, self.bottomleft)
        points = (newTopLeft, newTopRight, newBottomRight, newBottomLeft)

        result = cv.CreateMat(3, 3, cv.CV_32FC1)
        cv.GetPerspectiveTransform(src, points, result)
        self.img = self.img.transformPerspective(result)

        self.topleft = newTopLeft
        self.topright = newTopRight
        self.bottomright = newBottomRight
        self.bottomleft = newBottomLeft

        self.img.save('images/temp-perspective.png')

    def cropImage(self, m1=10, m2=10, m3=10, m4=10):
        print "Cropping the image..."

        if self.topleft == None or self.topright == None or self.bottomright == None or self.bottomleft == None:
            print "You must first run find corners."
            return

        self.img = self.img.regionSelect(self.topleft[0]-m4, self.topleft[1]-m1, self.bottomright[0]+m2, self.bottomright[1]+m3)
        self.img = self.img.resize(w=500)
        self.img.save('images/temp-cropped.png')

    def findRegions(self):
        print "Finding the regions..."

        searchX = math.floor(self.img.width / 9)
        searchY = math.floor(self.img.height / 9)

        marginX = searchX * 0.3
        marginY = searchY * 0.3

        puzzle = [[(0,0) for x in range(9)] for y in range(9)]


        for t in range(1,10):
            print "Looking for", t,"..."
            mTemplate = SimpleCV.Image('template/' + str(t) + '.png')

            threshold = 5
            if t==1 or t==4 or t==7:
                threshold = 4
            elif t==2:
                threshold = 5
            elif t==5 or t==6 or t==9:
                threshold = 6
            elif t==3 or t==8:
                threshold = 9

            for i in range(9):
                posY = searchY*i

                for j in range(9):
                    posX = searchX*j

                    tlX = max(0, posX-marginX)
                    tlY = max(0, posY-marginY)
                    brX = min(self.img.width, posX+searchX+marginX)
                    brY = min(self.img.height, posY+searchY+marginY)

                    found = []
                    window = self.img.regionSelect(tlX, tlY, brX, brY)

                    for resize in range(-2,3):
                        t1 = mTemplate.resize(mTemplate.width+resize, mTemplate.height+resize)
                        found.append(window.findTemplate(t1, threshold=threshold))

                        t2 = mTemplate.resize(mTemplate.width+resize, mTemplate.height)
                        found.append(window.findTemplate(t2, threshold=threshold))

                        t3 = mTemplate.resize(mTemplate.width, mTemplate.height+resize)
                        found.append(window.findTemplate(t3, threshold=threshold))

                        template = t1
                        for shear in range(1,6,2):
                            t4 = template.invert()

                            src = ((0,0), (t4.width-1,0), (t4.width-1, t4.height-1), (0,t4.height-1))
                            points1 = ((0,shear), (t4.width-1,0), (t4.width-1, t4.height-1-shear), (0,t4.height-1))
                            points2 = ((0,0), (t4.width-1,shear), (t4.width-1, t4.height-1), (0,t4.height-1-shear))

                            result = cv.CreateMat(3, 3, cv.CV_32FC1)
                            cv.GetPerspectiveTransform(src, points1, result)
                            template1 = t4.transformPerspective(result)
                            template1 = template1.invert()
                            found.append(window.findTemplate(template1, threshold=threshold))

                            result = cv.CreateMat(3, 3, cv.CV_32FC1)
                            cv.GetPerspectiveTransform(src, points2, result)
                            template2 = t4.transformPerspective(result)
                            template2 = template2.invert()
                            found.append(window.findTemplate(template2, threshold=threshold))

                        for angle in range(-5,6,2):
                            t5 = template.invert()
                            t5 = t5.rotate(angle, fixed=False, point=(int(template.width/2), int(template.height/2)))
                            t5 = t5.invert()
                            found.append(window.findTemplate(t5, threshold=4))


                    found = [x for x in found if x]
                    if len(found) > 0:
                        current = puzzle[i][j]
                        if len(found) > current[0]:
                            puzzle[i][j] = (len(found), t)

                    #window.save('windows/' + str(i) + '-' + str(j) + '.png')

        tempString = ""

        print "\nThe puzzle:"
        for x in range(9):
            if x%3 == 0:
                    print ""
            for y in range(9):
                if y%3 == 0:
                    sys.stdout.write("| ")
                sys.stdout.write(str(puzzle[x][y][1]) + " ")
                tempString = tempString + str(puzzle[x][y][1])
            print "|"

        self.sudokuString = tempString

def main():

    if len(sys.argv) != 3:
        print ">python sudoku.py -auto image"
        print ">python sudoku.py -manual image"
        sys.exit()

    image = Sudoku(sys.argv[2])

    # PART ONE: THRESHOLD THE IMAGE
    image.threshold()

    # PART TWO: FIND THE CORNERS
    if sys.argv[1] == "-auto":
        image.findCorners()
    else:
        image.findCornersManually()

    # PART THREE: CORRECT THE PERSPECTIVE
    #  1. get the perspective transformation matrix using the four corners
    #  2. perform the perspective transformation
    image.correctPerspective()

    # PART FOUR: CROP THE IMAGE
    image.cropImage()

    # PART FOUR: FIND THE REGIONS
    image.findRegions()

    # PART FIVE: CALL THE SUDOKU SOLVER
    solved = sudokuSolver.solve(image.toString)
    print solved

if __name__ == '__main__':
    main()
