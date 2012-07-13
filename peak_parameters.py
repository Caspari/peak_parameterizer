#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
##############################################################################
#
# SCRIPT:       peak_parameters.py
# AUTHOR(S):    Nico Caspari & Daniel Lee
# PURPOSE:      Identifies peaks using the methodology in r.param.scale and
#               compares them to a list of peaks entered by the user.
#               Advanced GIS (Dr. C. Reudenbach).
#
##############################################################################

# TODO: Write GUI.
# Inputs: DEM, peak points.

import grass.script as grass

class PeakAnalyst(object):
    '''
    A geographical object that finds peaks according to specified parameters
    and compares them with a validation data set.
    '''
    
    def __init__(self, 
                 options,
                 flags,
                 results):
        '''
        Initializes peak analyst with the window sizes and slope thresholds to
        be used in the analysis. Adjusts regional settings to match rasters
        to be analyzed. Inputs are received and parsed from GUI.
        
        Inputs:
            window_sizes: int list
            slope_thresholds: int list
            flags: dictionary of binary values.
                   t - true positives
                   f - false negatives
                   n - false negatives
            dem: string (name of GRASS elevation model to be analyzed. Must be
                         in same mapset)
            peaks: string (name of GRASS vector points showing peaks. Later,
                           this could be expanded to allow the use of polygons
                           as peaks)
            results: results container object
        '''
        
        # TODO: Parse this
        # The input is a string of integers divided by commas. Split it into
        # a list and convert all values to integers.
        self.window_sizes = options['window_sizes']
        # Repeat procedure as above.
        self.slope_thresholds = options['slope_thresholds']
        # TODO: Parse flags from GUI for error values.
        # flags.values() == [True, True, True]
        self.error_values = []
        for error_flag in flags.keys():
            if flags[error_flag]:
                self.error_values.append(error_flag)
        # Replace error values from flags with readable strings
        if 't' in self.error_values:
            self.error_values.remove('t')
            self.error_values.append('true positives')
        if 'f' in self.error_values:
            self.error_values.remove('f')
            self.error_values.append('false positives')
        if 'n' in self.error_values:
            self.error_values.remove('n')
            self.error_values.append('false negatives')
        self.dem = options['dem']
        self.peaks = ['peaks']
        self.results = results
        # TODO: Set up regional settings with grass.region()
        # Set region to raster
        return
    
    def find_peaks(self):
        '''
        Performs morphometric analyses for all specified window sizes and slope
        thresholds, then extracts all areas classified as peaks and converts
        them into vector areas.
        '''
        
        self.found_peaks = []
        # TODO: Get this running.
        for window in self.window_sizes:
            for slope_threshold in self.slope_thresholds:
                # Use r.param.scale to produce peak maps.
                # Use r.reclass to extract the peaks as rasters.
                # Use r.to.vect to turn the peaks into areas.
                # Add the vector peak map to self.found_peaks[]
                # Delete the geomorphometry map and raster peak map.
                pass
        
        pass
    
    def evaluate_peaks(self, error_value):
        '''
        Calls an evaluation method that compares training peaks with identified
        peaks.
        '''
        
        # If-else query to find out which method to call
        if error_value == 'true positives':
            self.true_positives()
        elif error_value == 'false positives':
            self.false_positives
        elif error_value == 'false negatives':
            pass
        return
    
    def true_positives(self):
        '''
        Count classified peak areas that contain a training peak and write 
        number to results container.
        '''
        
        # TODO: Get this working.
        for peak_map in self.found_peaks:
            # Use v.select to find peak areas containing peak points.
            # Count features in the extracted map and call write_to_results()
            pass
        return
    
    def false_positives(self):
        '''
        Count classified peak areas that do not contain a training peak and 
        write number to results container.
        '''
        
        # TODO: Get this working.
        for peak_map in self.found_peaks:
            # Use v.select to find peak areas that do not contain training peaks
            # Count features in the extracted map and call write_to_results()
            pass
        return
    
    def false_negatives(self):
        '''
        Count training peaks that are not contained in a classified peak area
        and write number to results container.
        '''
        
        # TODO: Get this working.
        for peak_map in self.found_peaks:
            # Use v.select to find training peaks that do not overlap with
            # peak areas.
            # Count features in the extracted map and call write_to_results()
            pass
        return
    
    # TODO: Get this working.
    def write_to_results(self, error_value, value):
        '''
        Writes a specified error value to the correct field in the data 
        container object.
        '''
        
        return
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
    
    def __init__(self):
        '''
        Initializes axes and data matrix.
        '''
        
        self.window_sizes = []
        self.slope_thresholds = []
        self.error_values = []
        self.window_size = []
        self.slope_threshold = []
        self.error_value = []
        return
    
    return

class Exporter(object):
    '''
    Summarizes results and exports them to a specified format.
    '''
    
    return

def main():
    # Override GUI inputs
    # Window sizes: 3x3, 5x5, 9x9, 19x19, 39x39, 69x69
    options = {'window_sizes'     : ['3, 5, 9, 19, 39, 69'],
               # For each window, iterate with slope threshold 1-10
               'slope_thresholds' : str(range(1, 11))[1:-1]}
    # Error values. t = true positives, f = false positives, n = false negatives
    flags = {'f' : True,
             't' : True,
             'n' : True}
    
    # Initialize data container and peak analyzer object
    results = ResultsContainer()
    peak_analyzer = PeakAnalyst(options, flags, results)
    
    # Find peaks using different windows
    peak_analyzer.find_peaks()
    
    # Extract peaks and convert them to vectors
    for error_value in peak_analyzer.error_values:
        peak_analyzer.evaluate_peaks(error_value)
    
    return

if __name__ == '__main__':
    # TODO: Turn GUI parsing back on.
    #options, flags = grass.parser()
    main()
