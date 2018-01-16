#! /usr/bin/env python

#This program is free software: you can redistribute it and/or modify
#it under the terms of the GNU General Public License as published by
#the Free Software Foundation, either version 3 of the License, or
#(at your option) any later version.
#
#This program is distributed in the hope that it will be useful,
#but WITHOUT ANY WARRANTY; without even the implied warranty of
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#GNU General Public License for more details.
#
#You should have received a copy of the GNU General Public License
#along with this program.  If not, see <http://www.gnu.org/licenses/>.

# Author: Giacomo Mirabassi <giacomo@mirabassi.it>
# Version: 0.2

import sys
import os
import re
from distutils.spawn import find_executable

import subprocess
import math

import inkex
import simpletransform

inkex.localize()

class JPEGExport(inkex.Effect):

    def __init__(self):
        """Init the effect library and get options from gui."""
        inkex.Effect.__init__(self)

        self.OptionParser.add_option("--path",    action="store", type="string",  dest="path",    default="",        help="")
        self.OptionParser.add_option("--bgcol",   action="store", type="string",  dest="bgcol",   default="#ffffff", help="")
        self.OptionParser.add_option("--quality", action="store", type="int",     dest="quality", default="90",      help="")
        self.OptionParser.add_option("--density", action="store", type="int",     dest="density", default="90",      help="")
        self.OptionParser.add_option("--page",    action="store", type="inkbool", dest="page",    default=False,     help="")
        self.OptionParser.add_option("--fast",    action="store", type="inkbool", dest="fast",    default=True,      help="")

    def effect(self):
        """get selected item coords and call command line command to export as a png"""
        # The user must supply a directory to export:
        if not self.options.path:
            inkex.errormsg(_('Please indicate a file name and path to export the jpg.'))
            exit()
        if not os.path.basename(self.options.path):
            inkex.errormsg(_('Please indicate a file name.'))
            exit()
        if not os.path.dirname(self.options.path):
            inkex.errormsg(_('Please indicate a directory other than your system\'s base directory.'))
            exit()
          
        # Test if the directory exists:
        if not os.path.exists(os.path.dirname(self.options.path)):
            inkex.errormsg(_('The directory "%s" does not exist.') % os.path.dirname(self.options.path))
            exit()

        outfile=self.options.path
        curfile = self.args[-1]
        
        # Test if color is valid
        _rgbhexstring = re.compile(r'#[a-fA-F0-9]{6}$')
        if not _rgbhexstring.match(self.options.bgcol):
            inkex.errormsg(_('Please indicate the background color like this: \"#abc123\" or leave the field empty for white.'))
            exit()

        bgcol = self.options.bgcol

        if self.options.page == False:
            if len(self.selected) == 0:
                inkex.errormsg(_('Please select something.'))
                exit()

            coords=self.processSelected()
            self.exportArea(int(coords[0]),int(coords[1]),int(coords[2]),int(coords[3]),curfile,outfile,bgcol)

        elif self.options.page == True:
            self.exportPage(curfile,outfile,bgcol)

    def processSelected(self):
        """Iterate trough nodes and find the bounding coordinates of the selected area"""
        startx=None
        starty=None
        endx=None
        endy=None
        nodelist=[]
        root=self.document.getroot();
        toty=self.getUnittouu(root.attrib['height'])
        scale = self.getUnittouu('1px')
        props=['x', 'y', 'width', 'height']

        for id in self.selected:
            if self.options.fast == True:  # uses simpletransform
                nodelist.append(self.getElementById(id))
            else:  # uses command line
                rawprops=[]
                for prop in props:
                    command=("inkscape", "--without-gui", "--query-id", id, "--query-"+prop, self.args[-1])
                    proc=subprocess.Popen(command,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
                    proc.wait()
                    rawprops.append(math.ceil(self.getUnittouu(proc.stdout.read())))
                nodeEndX = rawprops[0] + rawprops[2]
                nodeStartY = toty - rawprops[1] - rawprops[3]
                nodeEndY = toty - rawprops[1]

                if rawprops[0] < startx or startx is None:
                    startx = rawprops[0]

                if nodeStartY < starty or starty is None:
                    starty = nodeStartY

                if nodeEndX > endx or endx is None:
                    endx = nodeEndX

                if nodeEndY > endy or endy is None:
                    endy = nodeEndY
        

        if self.options.fast == True:  # uses simpletransform
            bbox = simpletransform.computeBBox(nodelist)
            startx = math.ceil(bbox[0])
            endx = math.ceil(bbox[1])
            h = -bbox[2] + bbox[3]
            starty = toty - math.ceil(bbox[2]) -h
            endy = toty - math.ceil(bbox[2])

        coords = [startx / scale, starty / scale, endx / scale, endy / scale]
        return coords

    def exportArea(self, x0, y0, x1, y1, curfile, outfile, bgcol):
        tmp = self.getTmpPath()
        command="inkscape -a %s:%s:%s:%s -d %s -e \"%sjpinkexp.png\" -b \"%s\" %s" % (x0, y0, x1, y1, self.options.density, tmp, bgcol, curfile)

        p = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return_code = p.wait()
        f = p.stdout
        err = p.stderr

        self.tojpeg(outfile)

    def exportPage(self, curfile, outfile, bgcol):
        tmp = self.getTmpPath()
        command = "inkscape -C -d %s -e \"%sjpinkexp.png\" -b\"%s\" %s" % (self.options.density, tmp,bgcol, curfile)

        p = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return_code = p.wait()
        f = p.stdout
        err = p.stderr

        self.tojpeg(outfile)


    def tojpeg(self,outfile):
        tmp = self.getTmpPath()
        if os.name == 'nt':
	        outfile = outfile.encode('string-escape')

        # set the ImageMagick command to run based on what's installed
        if find_executable('magick'):
            command = "magick -quality %s -density %s \"%sjpinkexp.png\" \"%s\" " % (self.options.quality, self.options.density, tmp, outfile)
        elif find_executable('convert'): 
            command = "convert \"%sjpinkexp.png\" -quality %s -density %s \"%s\" " % (tmp, self.options.quality, self.options.density, outfile)
        else:
            inkex.errormsg(_('ImageMagick does not appear to be installed.'))
            exit()
            
        p = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return_code = p.wait()
        f = p.stdout
        err = p.stderr

    def getTmpPath(self):
        """Define the temporary folder path depending on the operating system"""
        if os.name == 'nt':
            return 'C:\\WINDOWS\\Temp\\'
        else:
            return '/tmp/'

    def getUnittouu(self, param):
        try:
            return inkex.unittouu(param)

        except AttributeError:
            return self.unittouu(param)

def _main():
    e = JPEGExport()
    e.affect()
    exit()

if __name__=="__main__":
    _main()
