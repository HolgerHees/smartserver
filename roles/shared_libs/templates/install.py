#!/usr/bin/python3

import site
import os

src = "{}/smartserver".format(os.path.dirname(__file__))

site_packages = site.getsitepackages()
site_packages.sort()

for dir in site_packages:
    
    if not os.path.exists(dir):
        continue
    
    dest = "{}/smartserver".format(dir)

    if not os.path.exists(dest):
        os.symlink(src, dest)
        
    break
