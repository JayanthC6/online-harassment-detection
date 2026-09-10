import torch
from captum.attr._utils.common import _format_baseline

try:
    _format_baseline(torch.zeros(1, 256, 768), torch.zeros(1, 256, 768))
    print("Same shape works!")
except Exception as e:
    print("Error:", e)

try:
    _format_baseline(torch.zeros(1, 256, 768), torch.zeros(2, 256, 768))
    print("Broadcast works!")
except Exception as e:
    print("Error:", e)

try:
    _format_baseline(torch.zeros(2, 256, 768), torch.zeros(1, 256, 768))
    print("Wrong broadcast works!")
except Exception as e:
    print("Error:", e)
