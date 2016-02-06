from distutils.core import setup
import py2exe

includes = ["encodings", "encodings.*", "sip"]

options = {"py2exe":
    {"compressed": 1,
     "optimize": 2,
     "ascii": 1,
     "includes":includes,
     "bundle_files": 1
     }
    }
setup(options=options,zipfile=None,windows=[{"script": "Email My PC Launcher.py"}])  
