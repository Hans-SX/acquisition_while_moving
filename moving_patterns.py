"""
Created on  Jun. 12, 2025

@author: Shih-Xian
"""
from abc import ABC, abstractmethod
from typing import List, Tuple
import time
import numpy as np
# from andor3 import Andor3
from pipython import GCSDevice
from pipython import pitools
from itertools import cycle


class MotionPatterns(ABC):
    @abstractmethod
    def _generate(self) -> np.array:
        pass
    
    @abstractmethod
    def pos_frames(self) -> dict:
        pass

class BigStepForward_SmallStepBack(MotionPatterns):
    def __init__(self, start:float, end:float, interval:float=0.5, pattern = np.array((2, -1))):
        self.start = start
        self.end = end
        self.interval = interval
        self.pattern = cycle(pattern)

        if start < 0 or start > end or end > 17:
            raise ValueError("The range of M-231.17 actuator is 0 - 17 mm.")
            
    def _generate(self):
        current = self.start
        pos = []
        while current <= self.end:
            pos.append(current)
            current = current + next(self.pattern) * self.interval
        
        pos = np.asarray(pos)
        if sum(pos < self.start) > 0 or sum(pos > self.end) > 0:
            raise ValueError("The pattern exceed range 0 - 17 mm.")
        return pos
    
    def pos_frames(self, interval=0.5, time_interval=100):
        pfdict = dict()
        pfdict['pos'] = self._generate()
        total_length = sum(abs(pfdict['pos'][1:] - pfdict['pos'][:-1]))
        time = int(total_length / interval)
        pfdict['frames'] = time * time_interval
        return pfdict
    
class SinusoidalForward(MotionPatterns):
    def __init__(self, start:float, end:float, npts:int, frequency:int=3, amp=3):
        # At least 60 npts would looks like a sinusodial, 90 npts would be better. 
        self.start = start
        self.end = end
        self.samples = np.linspace(start, end, npts)
        self.freq = frequency
        self.npts = npts
        self.amp = amp

        if start < 0 or start > end or end > 17:
            raise ValueError("The range of M-231.17 actuator is 0 - 17 mm.")

    def _generate(self):
        pos = self.amp * np.sin(2 * np.pi * self.freq * self.samples / self.end) + self.samples
        if sum(pos < self.start) > 0 or sum(pos > self.end) > 0:
            raise ValueError("The pattern exceed range 0 - 17 mm.")
        return pos
    
    def pos_frames(self, interval=0.5, time_interval=100):
        pfdict = dict()
        pfdict['pos'] = self._generate()
        total_length = sum(abs(pfdict['pos'][1:] - pfdict['pos'][:-1]))
        time = int(total_length / interval)
        pfdict['frames'] = time * time_interval
        return pfdict
    
def target_axials(x, n, stepsize):
    """
    x: the expected position
    n: 2*n + 1 will be the total examined positions
    """
    left_values = [x - i * stepsize for i in range(1, n+1)]
    right_values = [x + i * stepsize for i in range(1, n+1)]
    return left_values[::-1] + [x] + right_values
