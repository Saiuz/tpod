from meanshift import CamShift
from opticalflow import OpticalFlow
from bidirectionaloptflow import BidirectionalOptFlow
from backgroundsubtract import BackgroundSubtract
from templatematching import TemplateMatch, BidirectionalTemplateMatch
from correlationtracking import CorrelationTracking

#online = {"Mean Shift": MeanShift}
online = {
#    "Optical Flow": OpticalFlow,    
    "Correlation": CorrelationTracking,
    "camshift": CamShift,    
#    "Background Subtraction":BackgroundSubtract,
#    "Template": TemplateMatch,
}

bidirectional = {
#    "Optical Flow": BidirectionalOptFlow,
#    "Template": BidirectionalTemplateMatch
}

multiobject = {}
