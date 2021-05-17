"""
Dealing with data saving on CAMP

We want to transfer data from experimental setup to camp in an automatic and organised fashion. We will most likely
do that in steps:

- step 1: transfer data from acquisition computers.
 We have different computers and we want to be sure to be able to clean up space. So step one is to find the data and
 transfer it in the relevant folder. We will also add the data pieces to flexilims

- step 2: link things together
 Once everything is on CAMP we need to make sure that we have all the data we need and update flexilims wherever needed
"""

from .datasets import Dataset
from .camera import Camera
from .harp_data import HarpData

Dataset.SUBCLASSES['camera'] = Camera
Dataset.SUBCLASSES['harp'] = HarpData

