import tkinter

import cv2
import numpy as np
from tkinter import Label, Button, Tk, filedialog, colorchooser, Canvas
from PIL import ImageTk, Image

colour1 = (250, 161, 0)
colour2 = (0, 195, 184)
mathModeColour = (192, 0, 0)
import pygame

pygame.init()
screen = pygame.display.set_mode((900, 600), 0, 32)
pygame.display.set_caption('Oscilloscope Recolourer')
clock = pygame.time.Clock()

version = '0.1'


def get_opencv_img_res(opencv_image):
    height, width = opencv_image.shape[:2]
    return width, height


def convert_opencv_img_to_pygame(opencv_image):
    """
Convert OpenCV images for Pygame.

    see https://blanktar.jp/blog/2016/01/pygame-draw-opencv-image.html
    """
    opencv_image = opencv_image[:, :, ::-1]  # Since OpenCV is BGR and pygame is RGB, it is necessary to convert it.
    shape = opencv_image.shape[
            1::-1]  # OpenCV(height,width,Number of colors), Pygame(width, height)So this is also converted.
    pygame_image = pygame.image.frombuffer(opencv_image.tobytes(), shape, 'RGB')

    return pygame_image


def rgb_hack(rgb):
    return "#%02x%02x%02x" % rgb


colour1Position = (58, 123)
colour2Position = (30, 243)


def convertImageToColour(imgDirectory, measureList, trigMeasure):
    img = cv2.imread(imgDirectory)

    height = img.shape[0]
    width = img.shape[1]
    xOffset = 22
    yOffset = 26

    stopRed = (192, 0, 0)
    trigGreen = (194, 0, 0)

    grey = (238, 238, 238)

    # Fill selected lines with colours
    cv2.floodFill(img, None, colour1Position, colour1, loDiff=(20, 20, 20, 20), upDiff=(20, 20, 20, 20),
                  flags=cv2.FLOODFILL_FIXED_RANGE)
    cv2.floodFill(img, None, colour2Position, colour2, loDiff=(20, 20, 20, 20), upDiff=(20, 20, 20, 20),
                  flags=cv2.FLOODFILL_FIXED_RANGE)

    # Fill background colour with grey
    for x in range(xOffset - 2):
        for y in range(480):
            if not np.any(img[y, x] < 250):
                img[y, x] = grey

    for x in range(640):
        for y in range(yOffset - 2):
            if not np.any(img[y, x] < 250):
                img[y, x] = grey

    for x in range(640):
        for y in range(yOffset + 398, 480):
            if not np.any(img[y, x] < 250):
                img[y, x] = grey

    for x in range(xOffset + 498, 640):
        for y in range(480):
            if not np.any(img[y, x] < 250):
                img[y, x] = grey

    # Recolour measuring sections
    for i, num in enumerate(measureList):
        if num == 0:
            colour = (0, 0, 0)
        if num == 1:
            colour = colour1
        elif num == 2:
            colour = colour2
        elif num == 3:
            colour = mathModeColour

        for x in range(534, 626):
            for y in range(24 + 80 * i, 24 + 80 * i + 80):
                if (np.any(img[y, x] < 25)):
                    img[y, x] = colour

    # Recolour Ch1 voltage scale
    for x in range(0, 120):
        for y in range(428, 446):
            if (np.any(img[y, x] < 25)):
                img[y, x] = colour1

    # Recolour Ch2 voltage scale
    for x in range(130, 238):
        for y in range(428, 446):
            if (np.any(img[y, x] < 25)):
                img[y, x] = colour2

    # Recolour trigger section
    col = (0, 0, 0)
    if trigMeasure == 1:
        col = colour1
    elif trigMeasure == 2:
        col = colour2
    elif trigMeasure == 3:
        col = mathModeColour
    for x in range(460, 640):
        for y in range(428, 480):
            if (np.any(img[y, x] < 25)):
                img[y, x] = col
    # Recolour trigger arrow on RHS
    for y in range(yOffset, yOffset + 398):
        if np.all(img[y, 520]) < 25:
            for x in range(508, 522):
                for y2 in range(y - 10, y + 10):
                    if np.all(img[y2, x] < 25):
                        img[y2, x] = col


    # Recolour the voltage offset arrows on LHS

    for y in range(yOffset - 2, yOffset + 396):
        if (np.any(img[y, xOffset - 4] < 25)):
            if np.any(img[y + 7, 9] < 25):
                for x in range(0, 20):
                    for y2 in range(y - 10, y + 10):
                        if (np.any(img[y2, x] < 25)):
                            img[y2, x] = colour2
            elif np.any(img[y - 2, 7] < 25):
                for x in range(0, 20):
                    for y2 in range(y - 10, y + 10):
                        if (np.any(img[y2, x] < 25)):
                            img[y2, x] = colour1

    # Recolour the "trig'd" or "Stop" word at top of image
    modeColour = stopRed

    if (np.any(img[4, 202] < 25)):
        modeColour = trigGreen

    for x in range(200, 270):
        for y in range(24):
            if (np.any(img[y, x] < 25)):
                img[y, x] = modeColour

    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    return img


def writeText(string, coordx, coordy, fontSize, colour, center=True):
    # set the font to write with
    font = pygame.font.SysFont('calibri', fontSize)
    # (0, 0, 0) is black, to make black text
    text = font.render(string, True, colour)
    # get the rect of the text
    textRect = text.get_rect()
    # set the position of the text
    if center:
        textRect.center = (coordx, coordy)
    else:
        textRect.topleft = (coordx, coordy)
    screen.blit(text, textRect)


buttonList = ['Select Image', 'Colour 1', 'Colour 2', 'Math Mode Colour', 'Trig chan: ', 'Refresh', 'Save']
buttonRects = []
trigChannelVal = 0

measureModeRects = []
measureModeOptions = [0 for i in range(5)]

changePosRects = []
imgRects = []


def drawMenu(original, modified):
    global buttonList
    global buttonRects
    global measureModeOptions
    global measureModeRects
    global changePosRects

    buttonRects.clear()
    for i, button in enumerate(buttonList):
        rect = pygame.Rect(30, 30 + i * 65, 180, 60)
        buttonRects.append(rect)
        if i == 1:
            pygame.draw.rect(screen, colour1, rect, 2, 3)
            writeText(button, 30 + 90, 60 + i * 65, 15, colour1)
        elif i == 2:
            pygame.draw.rect(screen, colour2, rect, 2, 3)
            writeText(button, 30 + 90, 60 + i * 65, 15, colour2)
        elif i == 3:
            pygame.draw.rect(screen, mathModeColour, rect, 2, 3)
            writeText(button, 30 + 90, 60 + i * 65, 15, mathModeColour)
        elif i == 4:
            col = 'white'
            if trigChannelVal == 1:
                col = colour1
            elif trigChannelVal == 2:
                col = colour2
            elif trigChannelVal == 3:
                col = mathModeColour
            pygame.draw.rect(screen, col, rect, 2, 3)
            if trigChannelVal == 0:
                writeText(button + 'None', 30 + 90, 60 + i * 65, 15, col)
            elif trigChannelVal == 3:
                writeText(button + 'Math', 30 + 90, 60 + i * 65, 15, col)
            else:
                writeText(button + str(trigChannelVal), 30 + 90, 60 + i * 65, 15, col)
        else:
            pygame.draw.rect(screen, (255, 255, 255), rect, 2, 3)
            writeText(button, 30 + 90, 60 + i * 65, 15, 'white')

    measureModeRects.clear()
    for i, mode in enumerate(measureModeOptions):
        rect = pygame.Rect(360, 330 + i * 45, 80, 40)
        measureModeRects.append(rect)
        if mode == 1:
            pygame.draw.rect(screen, colour1, rect, 2, 3)
            writeText('1', 360 + 40, 350 + i * 45, 15, colour1)
        elif mode == 2:
            pygame.draw.rect(screen, colour2, rect, 2, 3)
            writeText('2', 360 + 40, 350 + i * 45, 15, colour2)
        elif mode == 3:
            pygame.draw.rect(screen, mathModeColour, rect, 2, 3)
            writeText('Math', 360 + 40, 350 + i * 45, 15, mathModeColour)
        else:
            pygame.draw.rect(screen, (255, 255, 255), rect, 2, 3)
            writeText('None', 360 + 40, 350 + i * 45, 15, 'white')

    imgRects.clear()
    smallOriginal = pygame.transform.scale(original, (640 * .6, 480 * .6))
    imgRects.append(screen.blit(smallOriginal, (450, 0)))
    smallModified = pygame.transform.scale(modified, (640 * .6, 480 * .6))
    imgRects.append(screen.blit(smallModified, (450, 300)))

    changePosRects.clear()
    rect = pygame.Rect(320, 30, 120, 40)
    writeText('Ch 1 pos: ' + str(colour1Position), 380, 50, 12, colour1)
    pygame.draw.rect(screen, colour1, rect, 2, 3)
    changePosRects.append(rect)
    rect = pygame.Rect(320, 80, 120, 40)
    writeText('Ch 2 pos: ' + str(colour2Position), 380, 100, 12, colour2)
    pygame.draw.rect(screen, colour2, rect, 2, 3)
    changePosRects.append(rect)

    writeText('Version ' + version, 10, 578, 12, 'white', center=False)


if __name__ == "__main__":

    myStr = 'US-maxVoltage'
    img = convertImageToColour(myStr + '.jpg', measureModeOptions, trigChannelVal,)
    originalImg = convert_opencv_img_to_pygame(cv2.imread(myStr + '.jpg'))

    changingPosVal = 0
    while True:

        for event in pygame.event.get():
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                pos = pygame.mouse.get_pos()
                if imgRects[0].collidepoint(pos):
                    changingPosVal = 0

                for i, b in enumerate(changePosRects):
                    if b.collidepoint(pos):
                        changingPosVal = i + 1

                for i, b in enumerate(buttonRects):
                    if b.collidepoint(pos):
                        root = tkinter.Tk()

                        if i == 0:  # Pressed load image
                            filename = filedialog.askopenfilename(
                                title='Open a file',
                                filetypes=(
                                    ('JPEGs', '*.jpg'),
                                    ('All files', '*.*')
                                ))
                            myStr = filename
                            img = convertImageToColour(myStr + '.jpg', measureModeOptions, trigChannelVal)
                            originalImg = convert_opencv_img_to_pygame(cv2.imread(myStr + '.jpg'))
                        if i == 1:  # Pressed colour 1
                            prevColour = colour1
                            colour1 = colorchooser.askcolor(title="Choose color")[0]
                            if colour1 == None:
                                colour1 = prevColour
                        if i == 2:  # Pressed colour 2
                            prevColour = colour2
                            colour2 = colorchooser.askcolor(title="Choose color")[0]
                            if colour2 == None:
                                colour2 = prevColour
                        if i == 3:  # Pressed math mode colour
                            mathModeColour = colorchooser.askcolor(title="Choose color")[0]
                        if i == 4:
                            trigChannelVal = (trigChannelVal + 1) % 4
                        if i == 5:  # Pressed refresh
                            img = convertImageToColour(myStr + '.jpg', measureModeOptions, trigChannelVal)
                            originalImg = convert_opencv_img_to_pygame(cv2.imread(myStr + '.jpg'))
                        if i == 6:  # Pressed save
                            filename = filedialog.asksaveasfilename(initialdir='/', title='Save File', filetypes=(
                                ('JPEG', '*.jpg'), ('All Files', '*.*')))
                            print(filename)
                            cv2.imwrite(filename + '.jpg', img)
                        root.destroy()
                for i, b in enumerate(measureModeRects):
                    if b.collidepoint(pos):
                        measureModeOptions[i] = (measureModeOptions[i] + 1) % 4
            if event.type == pygame.QUIT:
                pygame.quit()

        screen.fill((20, 20, 20))

        drawMenu(originalImg, convert_opencv_img_to_pygame(img))

        if changingPosVal == 1:
            pos = pygame.mouse.get_pos()
            pos = (int(max(20, min((pos[0] - 450) // .6, int(520)))), int(max(min(pos[1] // .6, 420), 20)))
            colour1Position = pos
        if changingPosVal == 2:
            pos = pygame.mouse.get_pos()
            pos = (int(max(20, min((pos[0] - 450) // .6, int(520)))), int(max(min(pos[1] // .6, 420), 20)))
            colour2Position = pos

        pygame.display.flip()
        clock.tick(16)
