from distutils.core import setup
import os, sys

if "bdist_wininst" in sys.argv:  WININST = True
else:  WININST = False

#icons = ["CoopSim/icons/" + entry for entry in os.listdir("CoopSim/icons")]
#docs = ["CoopSim/docs/CoopSim_Doc/" + entry for entry in os.listdir("CoopSim/docs/CoopSim_Doc")]
allfiles = []
for r,d,f in os.walk("CoopSim"):
    head, tail = os.path.split(r)
    if tail != "big_images" and tail != "small_images":
      if WININST:
          allfiles.append(("lib/"+r, [r + "/" + file for file in f]))
      else:
          allfiles.append(("lib/"+r, [r + "/" + file for file in f if file != "CoopSim_Doc.pdf"]))

setup(name="CoopSim",
      version="0.9.9 beta 2",
      description="Computer Simulation of the Evolution of Cooperation",
      author="Eckhart Arnold",
      license="LGPL",
      url="http://www.eckhartarnold.de/apppages/coopsim.html",
      author_email="eckhart_arnold@hotmail.com",
      #packages=["CoopSim", "CoopSim.PyPlotter", "CoopSim.PopulationDynamics"],
      scripts = ["CoopSim/coopsim"],
      # data_files = [("icons", icons), ("docs/CoopSim_Doc", docs)]
      data_files = allfiles
      )
