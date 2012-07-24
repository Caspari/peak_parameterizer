#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
##############################################################################
#
# SCRIPT: peak_parameters.py
# AUTHOR(S): Nico Caspari & Daniel Lee
# PURPOSE: Identifies peaks using the methodology in r.param.scale and
# compares them to a list of peaks entered by the user.
# Advanced GIS (Dr. C. Reudenbach).
#
##############################################################################

class GeoObject(object):
    '''
    A geographical object that finds peaks according to specified parameters
    and compares them with a validation data set.
    '''
    
    return

class ResultsContainer(object):
    '''
    A data container with a three dimensional matrix.
    X: Window sizes
    Y: Slope thresholds
    Z: Error values
    The matrix is indexed using the following scheme:
    matrix[window_size][slope_threshold][error_value]
    Parallel lists (window_sizes, slope_thresholds, error_values) serve as axes.
    '''
    
    return

class Exporter(object):
    '''
    Summarizes results and exports them to a specified format.
    '''
    
    return

def main():
    window_sizes = [3, 5, 9, 19, 39, 69]
    slope_thresholds = range(1, 11)
    error_values = ['false positive',
                    'true negative',
                    'false negative']
    
    # Find peaks using different windows
    # 3x3, 5x5, 9x9, 19x19, 39x39, 69x69
        # For each window, iterate with slope threshold 1-10
    
    # Extract peaks and convert them to vectors
    
    # Produce matrices for each method normalized for the number of peaks
    # Contains query for vectors and peak points
        # True positives
        # False positives
        # False negatives
    return

if __name__ == '__main__':
    main()