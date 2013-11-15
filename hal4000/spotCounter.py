#!/usr/bin/python
#
## @file
#
# Spot counter. This performs real time analysis of the frames from
# camera. It uses a fairly simple object finder. It's purpose is to
# provide the user with a rough idea of the quality of the data
# that they are taking.
#
# Hazen 08/13
#

import sys
from PyQt4 import QtCore, QtGui
import sip

import qtWidgets.qtAppIcon as qtAppIcon

import halLib.parameters as params

# Debugging.
import halLib.hdebug as hdebug

# The module that actually does the analysis.
import qtWidgets.qtSpotCounter as qtSpotCounter

## Counter
#
# Widget for keeping the various count displays up to date.
#
class Counter():

    ## __init__
    #
    # Initialize the counter object. This keeps track of the total
    # number of counts. One label is on the spot graph and the 
    # other label is on the image.
    #
    # @param q_label1 The first QLabel UI element.
    # @param q_label2 The second QLabel UI element.
    #
    def __init__(self, q_label1, q_label2):
        self.counts = 0
        self.q_label1 = q_label1
        self.q_label2 = q_label2
        self.updateCounts(0)

    ## getCounts
    #
    # Returns the total number of counts.
    #
    # @return Returns the total number of counts.
    #
    def getCounts(self):
        return self.counts

    ## reset
    #
    # Reset the counts to zero & update the labels.
    #
    def reset(self):
        self.counts = 0
        self.updateCounts(0)

    ## updateCounts
    #
    # Increments the number of counts by the number of objects
    # found in the most recent frame. Updates the labels accordingly.
    #
    # @param counts The number of objects in the frame that was analyzed.
    #
    def updateCounts(self, counts):
        self.counts += counts
        self.q_label1.setText(str(self.counts))
        self.q_label2.setText(str(self.counts))

## OfflineDriver
#
# Offline analysis driver widget. This is used to analyze saved films
# for the purpose of testing and evaluating the object finder.
#
class OfflineDriver(QtCore.QObject):

    ## __init__
    #
    # Initiailize the offline driver.
    #
    # @param spot_counter The spot counter GUI object.
    # @param data_file The data_file to analyze.
    # @param png_filename The png file to save the resulting image in.
    # @param parent (Optional) PyQt parent of this object.
    #
    def __init__(self, spot_counter, data_file, png_filename, parent = None):
        QtCore.QObject.__init__(self, parent)

        self.cur_frame = 0
        self.data_file = data_file
        self.png_filename = png_filename
        self.spot_counter = spot_counter

        [self.width, self.height, self.length] = data_file.filmSize()

        self.start_timer = QtCore.QTimer(self)
        self.start_timer.setSingleShot(True)
        self.start_timer.timeout.connect(self.startAnalysis)
        self.start_timer.setInterval(500)
        self.start_timer.start()

        self.spot_counter.imageProcessed.connect(self.nextImage)

    ## nextImage
    #
    # This is called when the spot counter finishes processing a frame. It
    # loads the next frame from the file and passes it to the spot counter.
    #
    def nextImage(self):
        if (self.cur_frame < self.length):
        #if (self.cur_frame < 5):
            np_data = data_file.loadAFrame(self.cur_frame)
            np_data = numpy.ascontiguousarray(np_data, dtype=numpy.int16)
            self.spot_counter.newFrame(frame.Frame(np_data.ctypes.data,
                                                   self.cur_frame,
                                                   self.width,
                                                   self.height,
                                                   "camera1",
                                                   True))
            self.cur_frame += 1
            if ((self.cur_frame % 100) == 0):
                print "Frame:", self.cur_frame, "(", self.length, ")"
        else:
            self.spot_counter.stopCounter()
            print "Finished Analysis"

    ## startAnalysis
    #
    # This starts the analysis. It is called after a 500 millisecond
    # delay to give PyQt a chance to get everything setup.
    #
    def startAnalysis(self):
        self.spot_counter.startCounter(self.png_filename)
        self.nextImage()

## QSpotGraph
#
# Spot Count Graphing Widget.
#
class QSpotGraph(QtGui.QWidget):

    ## __init__
    #
    # Create a spot graph object.
    #
    # @param x_size The x size (in pixels) of this widget.
    # @param y_size The y size (in pixels) of this widget.
    # @param y_min The graph's minimum value.
    # @param y_max The graph's maximum value.
    # @param parent (Optional) The PyQt parent of this object.
    #
    def __init__(self, x_size, y_size, y_min, y_max, parent = None):
        QtGui.QWidget.__init__(self, parent)
        self.range = y_max - y_min
        self.x_size = x_size
        self.y_size = y_size
        self.y_min = float(y_min)
        self.y_max = float(y_max)

        self.colors = [False]
        self.points_per_cycle = len(self.colors)
        self.x_points = 100

        self.x_scale = float(self.x_size)/float(self.x_points)
        self.y_scale = float(y_size)/5.0
        self.cycle = 0
        if self.points_per_cycle > 1:
            self.cycle = self.x_scale * float(self.points_per_cycle)

        self.data = []
        for i in range(self.x_points):
            self.data.append(0)

    ## changeYRange
    #
    # @param y_min (Optional) The new y minimum of the graph.
    # @param y_max (Optional) The new y maximum of the graph.
    #
    def changeYRange(self, y_min = None, y_max = None):
        if y_min:
            self.y_min = y_min
        if y_max:
            self.y_max = y_max
        self.range = self.y_max - self.y_min

    ## newParameters
    #
    # @param colors The colors to use for the points in the graph. This is based on the values specified in the shutter file.
    # @param total_points The total number of points in x.
    #
    def newParameters(self, colors, total_points):
        self.colors = colors
        self.points_per_cycle = len(colors)
        self.x_points = total_points

        self.x_scale = float(self.x_size)/float(self.x_points)
        self.cycle = 0
        if self.points_per_cycle > 1:
            self.cycle = self.x_scale * float(self.points_per_cycle)

        self.data = []
        for i in range(self.x_points):
            self.data.append(0)

        self.update()

    ## paintEvent
    #
    # Redraw the graph.
    #
    # @param event A PyQt event object.
    #
    def paintEvent(self, event):
        painter = QtGui.QPainter(self)

        # Background
        color = QtGui.QColor(255, 255, 255)
        painter.setPen(color)
        painter.setBrush(color)
        painter.drawRect(0, 0, self.x_size, self.y_size)

        # Draw lines in y to denote the start of each cycle, but only
        # if we have at least 2 points per cycle.
        #
        # Draw grid lines in x.
        if self.cycle:
            painter.setPen(QtGui.QColor(200, 200, 200))
            x = 0.0
            while x < float(self.x_size):
                ix = int(x)
                painter.drawLine(ix, 0, ix, self.y_size)
                x += self.cycle

            y = 0.0
            while y < float(self.y_size):
                iy = int(y)
                painter.drawLine(0, iy, self.x_size, iy)
                y += self.y_scale

        if (len(self.data)>0):
            # Lines
            painter.setPen(QtGui.QColor(0, 0, 0))
            x1 = int(self.x_scale * float(0))
            y1 = self.y_size - int((self.data[0] - self.y_min)/self.range * float(self.y_size))
            for i in range(len(self.data)-1):
                x2 = int(self.x_scale * float(i+1))
                y2 = self.y_size - int((self.data[i+1] - self.y_min)/self.range * float(self.y_size))
                painter.drawLine(x1, y1, x2, y2)
                x1 = x2
                y1 = y2

            # Points
            for i in range(len(self.data)):
                color = self.colors[i % self.points_per_cycle]
                qtcolor = 0
                if color:
                    qtcolor = QtGui.QColor(color[0], color[1], color[2])
                else:
                    qtcolor = QtGui.QColor(0, 0, 0)
                painter.setPen(QtGui.QColor(0, 0, 0))
#                painter.setPen(QtGui.QPen(QtGui.QColor(0, 0, 0),0))
                painter.setBrush(qtcolor)

                x = int(self.x_scale * float(i))
                y = self.y_size - int((self.data[i] - self.y_min)/self.range * float(self.y_size))
                if y < 0:
                    y = 0
                if y > self.y_size:
                    y = self.y_size
                painter.drawEllipse(x - 2, y - 2, 4, 4)

    ## updateGraph
    #
    # Updates the graph given a frame number and the number of spots in the frame.
    #
    # @param frame_index The frame number.
    # @param spots The number of spots in the frame.
    #
    def updateGraph(self, frame_index, spots):
        self.data[frame_index % self.x_points] = spots
        self.update()

## QImageGraph
#
# STORM image display widget.
#
class QImageGraph(QtGui.QWidget):

    ## __init__
    #
    # Create a STORM image display widget.
    #
    # @param x_size The x size of the widget in pixels.
    # @param y_size The y size of the widget in pixels.
    # @param flip_horizontal Flip the image horizontally.
    # @param flip_vertical Flip the image vertically.
    # @param parent The PyQt parent of this widget.
    #
    def __init__(self, x_size, y_size, flip_horizontal, flip_vertical, parent = None):
        QtGui.QWidget.__init__(self, parent)

        self.buffer = QtGui.QPixmap(x_size, y_size)
        self.flip_horizontal = flip_horizontal
        self.flip_vertical = flip_vertical
        self.x_size = x_size
        self.y_size = y_size

        self.colors = [False]
        self.points_per_cycle = len(self.colors)
        self.scale_bar_len = 1
        self.x_scale = 1.0
        self.y_scale = 1.0

    ## blank
    #
    # Resets the image to black.
    #
    def blank(self):
        painter = QtGui.QPainter(self.buffer)
        color = QtGui.QColor(0, 0, 0)
        painter.setPen(color)
        painter.setBrush(color)
        painter.drawRect(0, 0, self.x_size, self.y_size)
        self.update()

    ## newParameters
    #
    # Set new parameters.
    #
    # @param colors The colors to draw the pixels. This the same as for the image graph.
    # @param flip_horizontal Flip the image horizontally.
    # @param flip_vertical Flip the image vertically.
    # @param scale_bar_len The length of the image scale bar in pixels.
    # @param x_range The maximum x value of an object location.
    # @param y_range The maximum y value of an object location.
    #
    def newParameters(self, colors, flip_horizontal, flip_vertical, scale_bar_len, x_range, y_range):
        self.colors = colors
        self.flip_horizontal = flip_horizontal
        self.flip_vertical = flip_vertical
        self.points_per_cycle = len(colors)
        self.scale_bar_len = int(round(scale_bar_len))
        self.x_scale = float(self.x_size)/float(x_range)
        self.y_scale = float(self.y_size)/float(y_range)

        if (self.x_scale > self.y_scale):
            self.x_scale = self.y_scale
        else:
            self.y_scale = self.x_scale

        self.blank()

    ## paintEvent
    #
    # Redraw the image.
    # 
    # @param event A PyQt event object.
    #
    def paintEvent(self, event):
        # Draw the scale bar.
        painter = QtGui.QPainter(self.buffer)
        painter.setPen(QtGui.QColor(255, 255, 255))
        painter.setBrush(QtGui.QColor(255, 255, 255))
        painter.drawRect(5, 5, 5 + self.scale_bar_len, 5)

        # Mirror as necessary.
        #self.image = self.image.mirrored(self.flip_horizontal, self.flip_vertical)
            
        # Transfer to display.
        painter = QtGui.QPainter(self)
        painter.drawPixmap(0, 0, self.buffer)

    ## saveImage
    #
    # Saves the image in a file.
    #
    # @param filename The name of the file to save the image in.
    #
    def saveImage(self, filename):
        self.buffer.save(filename, "PNG", -1)

    ## updateImage
    #
    # Add the objects found in a frame to the image.
    #
    # @param index The frame number of the image.
    # @param x_locs The x locations of the objects.
    # @param y_locs The y locations of the objects.
    # @param spots The number of objects.
    #
    def updateImage(self, index, x_locs, y_locs, spots):
        painter = QtGui.QPainter(self.buffer)
        color = self.colors[index % self.points_per_cycle]
        if color:
            qtcolor = QtGui.QColor(color[0], color[1], color[2], 5)
            painter.setPen(qtcolor)
            for i in range(spots):
                ix = int(self.x_scale * x_locs[i])
                iy = int(self.y_scale * y_locs[i])
                #print ix, x_locs[i], iy, y_locs[i]
                painter.drawPoint(ix, iy)
            self.update()

## SpotCounter
#
# Spot Counter Dialog Box
#
class SpotCounter(QtGui.QDialog):
    imageProcessed = QtCore.pyqtSignal()

    ## __init__
    #
    # Create the spot counter dialog box.
    #
    # @param parameters The initial parameters.
    # @param single_camera Single camera setup or dual camera setup.
    # @param parent The PyQt parent of this dialog box.
    #
    @hdebug.debug
    def __init__(self, parameters, single_camera, parent = None):
        QtGui.QMainWindow.__init__(self, parent)

        self.counters = [False, False]
        self.filming = 0
        self.filenames = [False, False]
        self.image_graphs = [False, False]
        self.number_cameras = 1
        self.parameters = parameters
        self.spot_counter = False
        self.spot_graphs = [False, False]

        if parent:
            self.have_parent = True
        else:
            self.have_parent = False

        # UI setup.
        if single_camera:
            import qtdesigner.spotcounter_ui as spotCounterUi
        else:
            import qtdesigner.dualspotcounter_ui as spotCounterUi
            self.number_cameras = 2

        self.ui = spotCounterUi.Ui_Dialog()
        self.ui.setupUi(self)
        self.setWindowTitle(parameters.setup_name + " Spot Counter")
        self.setWindowIcon(qtAppIcon.QAppIcon())

        # Setup Counter objects.
        if single_camera:
            self.counters = [Counter(self.ui.countsLabel1, self.ui.countsLabel2)]
        else:
            self.counters = [Counter(self.ui.countsLabel1, self.ui.countsLabel2),
                             Counter(self.ui.countsLabel3, self.ui.countsLabel4)]

        # Setup spot counter.
        self.spot_counter = qtSpotCounter.QObjectCounter(parameters)
        self.spot_counter.imageProcessed.connect(self.updateCounts)

        # Setup spot counts graph(s).
        if (self.number_cameras == 1):
            parents = [self.ui.graphFrame]
        else:
            parents = [self.ui.graphFrame, self.ui.graphFrame2]

        for i in range(self.number_cameras):
            graph_w = parents[i].width() - 4
            graph_h = parents[i].height() - 4
            self.spot_graphs[i] = QSpotGraph(graph_w,
                                             graph_h,
                                             parameters.min_spots,
                                             parameters.max_spots,
                                             parent = parents[i])
            self.spot_graphs[i].setGeometry(2, 2, graph_w, graph_h)
            self.spot_graphs[i].show()

        # Setup STORM image(s).
        if (self.number_cameras == 1):
            parents = [self.ui.imageFrame]
        else:
            parents = [self.ui.imageFrame, self.ui.imageFrame2]

        for i in range(self.number_cameras):
            camera_params = parameters
            if hasattr(parameters, "camera" + str(i+1)):
                camera_params = getattr(parameters, "camera" + str(i+1))

            image_w = parents[i].width() - 4
            image_h = parents[i].height() - 4
            scale_bar_len = (parameters.scale_bar_len / parameters.nm_per_pixel) * \
                float(image_w) / float(camera_params.x_pixels * camera_params.x_bin)

            self.image_graphs[i] = QImageGraph(image_w,
                                               image_h,
                                               camera_params.flip_horizontal,
                                               camera_params.flip_vertical,
                                               parent = parents[i])
            self.image_graphs[i].setGeometry(2, 2, image_w, image_h)
            self.image_graphs[i].blank()
            self.image_graphs[i].show()

        # Connect signals.
        if self.have_parent:
            self.ui.okButton.setText("Close")
            self.ui.okButton.clicked.connect(self.handleOk)
        else:
            self.ui.okButton.setText("Quit")
            self.ui.okButton.clicked.connect(self.handleQuit)
        self.ui.maxSpinBox.valueChanged.connect(self.handleMaxChange)
        self.ui.minSpinBox.valueChanged.connect(self.handleMinChange)

        # Set modeless.
        self.setModal(False)

    ## closeEvent
    #
    # Handle close events. The event is ignored and the dialog box is simply
    # hidden if the dialog box has a parent.
    #
    # @param event A QEvent object.
    #
    @hdebug.debug
    def closeEvent(self, event):
        if self.have_parent:
            event.ignore()
            self.hide()
        else:
            self.quit()

    ## getCounts
    #
    # Returns the number of objects detected. If the movie is requested
    # by TCP/IP this number is passed back to the calling program.
    #
    @hdebug.debug
    def getCounts(self):
        return self.counters[0].getCounts()

    ## handleMaxChange
    #
    # Handles changing the maximum of the spot graph.
    #
    # @param new_max The new maximum.
    #
    @hdebug.debug
    def handleMaxChange(self, new_max):
        for i in range(self.number_cameras):
            self.spot_graphs[i].changeYRange(y_max = new_max)
        self.ui.minSpinBox.setMaximum(new_max - 10)
        self.parameters.max_spots = new_max

    ## handleMinChange
    #
    # Handles changing the minimum of the spot graph.
    #
    # @param new_min The new minimum.
    #
    @hdebug.debug
    def handleMinChange(self, new_min):
        for i in range(self.number_cameras):
            self.spot_graphs[i].changeYRange(y_min = new_min)
        self.ui.maxSpinBox.setMinimum(new_min + 10)
        self.parameters.max_spots = new_min

    ## handleOk
    #
    # Handles the close button, hides the dialog box.
    #
    # @param bool Dummy parameter.
    #
    @hdebug.debug
    def handleOk(self, bool):
        self.hide()

    ## handleQuit
    #
    # Handles the quit button, closes the dialog box.
    #
    # @param bool Dummy parameter.
    #
    @hdebug.debug
    def handleQuit(self, bool):
        self.close()

    ## newFrame
    #
    # Called when there is a new frame from the camera.
    #
    # @param frame A frame object.
    #
    def newFrame(self, frame):
        if self.spot_counter:
            self.spot_counter.newImageToCount(frame)

    ## newParameters
    #
    # Called when the parameters are changed. Updates the spot graphs
    # and image display with the new parameters.
    #
    # @param parameters A parameters object.
    # @param colors The colors to use for the different frames as specified by the shutter file.
    #
    @hdebug.debug
    def newParameters(self, parameters, colors):
        self.parameters = parameters

        self.spot_counter.newParameters(parameters)

        # Update counters, count graph(s) & STORM image(s).
        points_per_cycle = len(colors)
        total_points = points_per_cycle
        while total_points < 100:
            total_points += points_per_cycle

        for i in range(self.number_cameras):
            self.counters[i].reset()
            self.spot_graphs[i].newParameters(colors, total_points)

            camera_params = parameters
            if hasattr(parameters, "camera" + str(i+1)):
                camera_params = getattr(parameters, "camera" + str(i+1))
            scale_bar_len = (parameters.scale_bar_len / parameters.nm_per_pixel) * \
                float(self.image_graphs[i].width()) / float(camera_params.x_pixels * camera_params.x_bin)
            self.image_graphs[i].newParameters(colors,
                                               camera_params.flip_horizontal,
                                               camera_params.flip_vertical,
                                               scale_bar_len,
                                               camera_params.x_pixels / camera_params.x_bin,
                                               camera_params.y_pixels / camera_params.y_bin)

        # UI update.
        self.ui.maxSpinBox.setValue(parameters.max_spots)
        self.ui.minSpinBox.setValue(parameters.min_spots)

    ## updateCounts
    #
    # Called when the objects in a frame have been localized.
    #
    # @param which_camera This is one of "camera1" or "camera2"
    # @param frame_number The frame number of the frame that was analyzed.
    # @param x_locs The x locations of the objects that were found.
    # @param y_locs The y locations of the objects that were found.
    # @param spots The total number of spots that were found.
    #
    def updateCounts(self, which_camera, frame_number, x_locs, y_locs, spots):
        if (which_camera == "camera1"):
            self.spot_graphs[0].updateGraph(frame_number, spots)
            if self.filming:
                self.counters[0].updateCounts(spots)
                self.image_graphs[0].updateImage(frame_number, x_locs, y_locs, spots)
        elif (which_camera == "camera2"):
            self.spot_graphs[1].updateGraph(frame_number, spots)
            if self.filming:
                self.counters[1].updateCounts(spots)
                self.image_graphs[1].updateImage(frame_number, x_locs, y_locs, spots)
        else:
            print "spotCounter.update Unknown camera:", which_camera
        self.imageProcessed.emit()

    ## quit
    #
    # This does not do anything.
    #
    @hdebug.debug        
    def quit(self):
        pass

    ## shutDown
    #
    # Called when the program exits to stop the spot counter threads.
    #
    @hdebug.debug
    def shutDown(self):
        if self.spot_counter:
            self.spot_counter.shutDown()

    ## startCounter
    #
    # Called at the start of filming to reset the spot graphs and the
    # images. If name is not False then this is assumed to be root
    # filename to save the spot counter images in when filming is finished.
    #
    # @param name The root filename to save the images.
    #
    @hdebug.debug
    def startCounter(self, name):
        if self.spot_counter:
            for i in range(self.number_cameras):
                self.counters[i].reset()
                self.image_graphs[i].blank()
            self.filming = True
            self.filenames = [False, False]
            if name:
                if (self.number_cameras == 1):
                    self.filenames[0] = name + ".png"
                else:
                    self.filenames[0] = name + "_cam1.png"
                    self.filenames[1] = name + "_cam2.png"

    ## stopCounter
    #
    # Called at the end of filming.
    @hdebug.debug
    def stopCounter(self):
        self.filming = False
        if self.filenames[0]:
            for i in range(self.number_cameras):
                self.image_graphs[i].saveImage(self.filenames[i])


#
# Testing.
#
#   Load a movie file, analyze it & save the result.
#
if __name__ == "__main__":

    import numpy

    import camera.frame as frame

    # This file is available in the ZhuangLab storm-analysis project on github.
    import sa_library.datareader as datareader

    if (len(sys.argv) != 4):
        print "usage: <settings> <movie_in> <png_out>"
        exit()

    # Open movie & get size.
    data_file = datareader.inferReader(sys.argv[2])
    [width, height, length] = data_file.filmSize()

    # Start spotCounter as a stand-alone application.
    app = QtGui.QApplication(sys.argv)
    parameters = params.Parameters(sys.argv[1], is_HAL = True)
    parameters.setup_name = "offline"
    
    parameters.x_pixels = width
    parameters.y_pixels = height
    parameters.x_bin = 1
    parameters.y_bin = 1

    spotCounter = SpotCounter(parameters, True)
    spotCounter.newParameters(parameters, [[255,255,255]])

    # Start driver.
    driver = OfflineDriver(spotCounter, data_file, sys.argv[3])

    # Show window & start application.
    spotCounter.show()
    app.exec_()


#
# The MIT License
#
# Copyright (c) 2013 Zhuang Lab, Harvard University
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
#

