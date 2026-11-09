"""
Pytest configuration and early DLL pre-initialization for ShieldAI test suite.
"""
import os
import sys

# On Windows with Python 3.12, torch must load its runtime libraries (libiomp5md, c10)
# before numpy, scipy, or scikit-learn load conflicting OpenMP/MKL DLLs.
try:
    import torch
except Exception as _e:
    pass

