import cv2 as cv
import numpy as np
import time

def nothing(x):
    pass

# ---------------- BASIC CAPTURE PART ----------------

cap = cv.VideoCapture(0)
cv.namedWindow('frame')

fourcc = cv.VideoWriter_fourcc(*'XVID')

switch = '0 : OFF \n1 : ON'
cv.createTrackbar(switch, 'frame', 0, 1, nothing)

fps = 30
size = (int(cap.get(cv.CAP_PROP_FRAME_WIDTH)),
        int(cap.get(cv.CAP_PROP_FRAME_HEIGHT)))

out = cv.VideoWriter("cervix.avi", fourcc, fps, size)

success, frame = cap.read()
numFramesRemaining = 10 * fps - 1

while success and numFramesRemaining > 0:
    cv.imshow("frame", frame)

    out.write(frame)

    s = cv.getTrackbarPos(switch, 'frame')

    if s == 1:
        frame[:] = [0, 255, 0]  # Example effect

    success, frame = cap.read()
    numFramesRemaining -= 1

    if cv.waitKey(25) == 27:
        break

out.release()
cap.release()
cv.destroyWindow("frame")


# ---------------- CAPTURE MANAGER CLASS ----------------

class CaptureManager(object):

    def __init__(self, channel, previewWindowManager=None, shouldMirrorPreview=False):
        self.previewWindowManager = previewWindowManager
        self.shouldMirrorPreview = shouldMirrorPreview

        self._capture = cv.VideoCapture(channel)
        self._enteredFrame = False
        self._frame = None

        self._imageFilename = None
        self._videoFilename = None
        self._videoEncoding = None
        self._videoWriter = None

        self._startTime = None
        self._framesElapsed = 0
        self._fpsEstimate = None

    @property
    def frame(self):
        if self._enteredFrame and self._frame is None:
            success, self._frame = self._capture.retrieve()
        return self._frame

    @property
    def isWritingImage(self):
        return self._imageFilename is not None

    @property
    def isWritingVideo(self):
        return self._videoFilename is not None

    def writeImage(self, filename):
        self._imageFilename = filename

    def startWritingVideo(self, filename, encoding=cv.VideoWriter_fourcc(*'MJPG')):
        self._videoFilename = filename
        self._videoEncoding = encoding

    def stopWritingVideo(self):
        self._videoFilename = None
        self._videoEncoding = None
        self._videoWriter = None

    def enterFrame(self):
        if self._capture is not None:
            self._enteredFrame = self._capture.grab()

    def exitFrame(self):
        if self.frame is None:
            self._enteredFrame = False
            return

        if self._framesElapsed == 0:
            self._startTime = time.time()
        else:
            timeElapsed = time.time() - self._startTime
            self._fpsEstimate = self._framesElapsed / timeElapsed
        self._framesElapsed += 1

        if self.previewWindowManager:
            frameToShow = np.fliplr(self._frame).copy() if self.shouldMirrorPreview else self._frame
            self.previewWindowManager.show(frameToShow)

        if self.isWritingImage:
            cv.imwrite(self._imageFilename, self._frame)
            self._imageFilename = None

        self._writeVideoFrame()

        self._frame = None
        self._enteredFrame = False

    def _writeVideoFrame(self):
        if not self.isWritingVideo:
            return

        if self._videoWriter is None:
            fps = self._capture.get(cv.CAP_PROP_FPS)

            if fps <= 0.0:
                if self._framesElapsed < 20:
                    return
                fps = self._fpsEstimate

            size = (int(self._capture.get(cv.CAP_PROP_FRAME_WIDTH)),
                    int(self._capture.get(cv.CAP_PROP_FRAME_HEIGHT)))

            self._videoWriter = cv.VideoWriter(
                self._videoFilename, self._videoEncoding, fps, size
            )

        self._videoWriter.write(self._frame)


# ---------------- WINDOW MANAGER ----------------

class WindowManager(object):

    def __init__(self, windowName, keypressCallback=None):
        self.keypressCallback = keypressCallback
        self._windowName = windowName
        self._isWindowCreated = False

    @property
    def isWindowCreated(self):
        return self._isWindowCreated

    def createWindow(self):
        cv.namedWindow(self._windowName)
        self._isWindowCreated = True

    def show(self, frame):
        cv.imshow(self._windowName, frame)

    def destroyWindow(self):
        cv.destroyWindow(self._windowName)
        self._isWindowCreated = False

    def processEvents(self):
        keycode = cv.waitKey(1)
        if self.keypressCallback and keycode != -1:
            self.keypressCallback(keycode & 0xFF)


# ---------------- MAIN APPLICATION ----------------

class CervicalCancer(object):

    def __init__(self):
        self._windowManager = WindowManager('AIR labs Diagnostics', self.keyInterrupt)
        self._captureManager = CaptureManager(0, self._windowManager, True)

    def main(self):
        self._windowManager.createWindow()

        while self._windowManager.isWindowCreated:
            self._captureManager.enterFrame()
            self._captureManager.exitFrame()
            self._windowManager.processEvents()

    def keyInterrupt(self, keycode):
        if keycode == 32:  # Space
            self._captureManager.writeImage('testshot.png')
        elif keycode == 9:  # Tab
            if not self._captureManager.isWritingVideo:
                self._captureManager.startWritingVideo('testcast.avi')
            else:
                self._captureManager.stopWritingVideo()
        elif keycode == 27:  # Escape
            self._windowManager.destroyWindow()


if __name__ == '__main__':
    cancer = CervicalCancer()
    cancer.main()