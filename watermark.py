#!/usr/bin/env python3

"""
Requirements:
(1) sudo apt install pdftk -y
(2) pip3 install reportlab
(3) create a directory name "marked"

Sample usage: python3 watermark.py email@up.edu.ph
"""

from reportlab.pdfgen.canvas import Canvas
from reportlab.lib.units import cm, inch
import datetime 
from reportlab.lib.colors import red
import os,sys
import subprocess

text="This copy is part of the bulk request by "+ sys.argv[1] +" authorized by the ICS Library Committee. DO NOT DISTRIBUTE. "+str(datetime.datetime.now())

canvas = Canvas("watermark", pagesize=(8.5 * inch, 11 * inch))
canvas.rotate(90)
canvas.setFont("Times-Roman", 10)
canvas.setFillColor(red)
canvas.drawString(1*cm, -1.5*cm, text)
canvas.save()

files = [f for f in os.listdir('.') if os.path.isfile(f)]
files = filter(lambda f: f.endswith(('.pdf','.PDF')), files)
i=1
for f in files:
    print(f)
    subprocess.call('pdftk '+ f + ' background watermark output marked/'+str(i)+'.pdf',shell=True)
    i=i+1
