#!/usr/bin/python3

import site
import os

src = "{}/smartserver".format(os.path.dirname(__file__))
dest = "{}/smartserver".format(site.getsitepackages()[0])

if not os.path.exists(dest):
    os.symlink(src, dest)
