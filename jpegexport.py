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
# Version: 0.1

import sys
sys.path.append('/usr/share/inkscape/extensions')

import subprocess
import math
import re

import inkex

class JPEGExport(inkex.Effect):
	def __init__(self):
		"""init the effetc library and get options from gui"""
		inkex.Effect.__init__(self)

		self.OptionParser.add_option("--path",action="store", type="string", dest="path", default="~",help="")
		self.OptionParser.add_option("--bgcol",action="store",type="string",dest="bgcol",default="",help="")
		

	def effect(self):
		"""get selected item coords and call command line command to export as a png"""

		if len(self.selected)==0:
			sys.stderr.write('Please select something.')
			exit()

		coords=self.processSelected()
		outfile=self.options.path
		curfile = self.args[-1]
		bgcol = self.options.bgcol
		command="inkscape -a %s:%s:%s:%s -e \"/tmp/jpinkexp.png\" -b \"%s\" %s" % (int(coords[0]), int(coords[1]), int(coords[2]), int(coords[3]),bgcol,curfile)

		p = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
		return_code = p.wait()
		f = p.stdout
		err = p.stderr

		command="convert -quality 100 -density 90 /tmp/jpinkexp.png %s" % (outfile)

		p = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
		return_code = p.wait()
		f = p.stdout
		err = p.stderr


	def processSelected(self):
		"""Iterate trough nodes and find the bounding coordinates of the selected area"""
		startx=None
		starty=None
		endx=None
		endy=None

		root=self.document.getroot();

		toty=inkex.unittouu(root.attrib['height'])
		
		props=['x','y','width','height']
		
		for id in self.selected:
			
			rawprops=[]

			for prop in props:
				

				command=("inkscape", "--without-gui", "--query-id", id, "--query-"+prop,self.args[-1])
				proc=subprocess.Popen(command,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
				proc.wait()
				rawprops.append(math.ceil(inkex.unittouu(proc.stdout.read())))

			nodeEndX=rawprops[0]+rawprops[2]
			nodeStartY=toty-rawprops[1]-rawprops[3]
			nodeEndY=toty-rawprops[1]


			if rawprops[0] < startx or startx==None: 
				startx=rawprops[0]

			if  nodeStartY < starty or starty == None:
				starty = nodeStartY

			
			if nodeEndX > endx or endx == None:
				endx = nodeEndX

			if nodeEndY > endy or endy == None:
				endy = nodeEndY


		coords=[startx,starty,endx,endy]
		return coords

def _main():
	e=JPEGExport()
	e.affect()

if __name__=="__main__":
	_main()
