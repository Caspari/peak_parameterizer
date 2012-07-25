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

#%Module
#% label: Peak parameterizer
#% description: A tool to find parameters for finding peaks based on a training data set.
#% keywords: raster, terrain, peaks, morphometry
#%End

#%Flag
#% key: t
#% description: Find true positives
#% guisection: Validation measurements
#%End

#%Flag
#% key: f
#% description: Find false negatives
#% guisection: Validation measurements
#%End

#%Flag
#% key: n
#% description: Find false negatives
#% guisection: Validation measurements
#%End

#%Option
#% key: dem
#% type: old,cell,raster
#% description: The input elevation map
#% required: yes
#%End

#%Option
#% key: peaks
#% description: A vector map of training peaks as points
#% type: old,vector
#% required: yes
#%End

#%Option
#% key: window_sizes
#% type: string
#% description: A list of integer window sizes separated by commas
#% required: yes
#% answer: '3, 5, 9, 19, 39, 69'
#% guisection: Parameters
#%End

#%Option
#% key: slope_thresholds
#% type: string
#% description: A list of slope thresholds separated by commas
#% required: yes
#% answer: '1, 2, 3, 4, 5, 6, 7, 8, 9, 10'
#% guisection: Parameters
#%End

import os

import grass.script as grass

class PeakAnalyst(object):
    '''
    A geographical object that finds peaks according to specified parameters
    and compares them with a validation data set.
    '''
    
    def __init__(self, 
                 options,
                 flags):
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
        
        # The input is a string of integers divided by commas. Split it into
        # a list and convert all values to integers.
        self.window_sizes = options['window_sizes'].split(',')
        for i in range(len(self.window_sizes)):
            self.window_sizes[i] = int(self.window_sizes[i])
        # Repeat procedure as above.
        self.slope_thresholds = options['slope_thresholds'].split(',')
        for i in range(len(self.slope_thresholds)):
            self.slope_thresholds[i] = int(self.slope_thresholds[i])
        # Append error flags to error values list
        self.error_values = []
        for error_flag in flags.keys():
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
        self.peaks = options['peaks']
        # Set region to raster
        grass.run_command('g.region', rast=self.dem)
        # Initialize results container
        self.results = ResultsContainer(self.window_sizes,
                                        self.slope_thresholds,
                                        self.error_values)
    
    def find_peaks(self):
        '''
        Performs morphometric analyses for all specified window sizes and slope
        thresholds, then extracts all areas classified as peaks and converts
        them into vector areas.
        '''
        
        # Make reclass table that eliminates all features except for peaks
        reclass_rules = '.tmp_reclass.txt'
        with open(reclass_rules, 'w') as reclass:
            reclass.write('0 thru 5 = NULL\n' + 
                          '* = *\n' + 
                          'end\n')
        self.found_peaks = []
        for window in self.window_sizes:
            for slope_threshold in self.slope_thresholds:
                # Use r.param.scale to produce peak maps.
                feature_map = str(window) + '_' + str(slope_threshold)
                grass.run_command('r.param.scale',
                                  input=self.dem,
                                  output=feature_map,
                                  s_tol=slope_threshold,
                                  size=window,
                                  param='feature')
                # Use r.reclass to extract the peaks as rasters.
                peak_raster = feature_map + '_peaks'
                grass.run_command('r.reclass',
                                  input=feature_map,
                                  output=peak_raster,
                                  rules=reclass_rules)
                # Use r.to.vect to turn the peaks into areas.
                peak_vectors = peak_raster
                grass.run_command('r.to.vect',
                                  input=peak_raster,
                                  output=peak_vectors,
                                  feature='area')
                # Add the window, slope threshold and vector peak map to list 
                # of found peaks
                self.found_peaks.append([window, slope_threshold, peak_vectors])
                # Delete the geomorphometry map and raster peak map.
                for raster in [feature_map, peak_raster]:
                    grass.run_command('g.remove',
                                      rast=raster)
        # Delete reclass table
        os.remove(reclass_rules)
    
    def evaluate_peaks(self, error_value):
        '''
        Calls an evaluation method that compares training peaks with identified
        peaks.
        '''
        
        # If-else query to find out which method to call
        if error_value == 'true positives':
            self.true_positives()
        elif error_value == 'false positives':
            self.false_positives()
        elif error_value == 'false negatives':
            self.false_negatives()
    
    def true_positives(self):
        '''
        Count classified peak areas that contain a training peak and write 
        number to results container.
        '''
        
        true_positives = 'true_positives'
        
        # peak_map contains [window, slope, map]
        for peak_map in range(len(self.found_peaks)):
            # Find peak areas containing peak points.
            grass.run_command('v.select',
                              ainput=peak_map[2],
                              binput=self.peaks,
                              output=true_positives)
            # Count features in the extracted map and call write_to_results()
            true_positives_count = len(grass.read_command('v.db.select',
                                                          map=true_positives,
                                                          column='cat',
                                                          flags='c').splitlines())
            grass.run_command('g.remove',
                              vect=true_positives)
            # Send results to results container object
            self.results.add_error('true positives', 
                                         peak_map[0], 
                                         peak_map[1], 
                                         true_positives_count)
    
    def false_positives(self):
        '''
        Count classified peak areas that do not contain a training peak and 
        write number to results container.
        '''
        
        false_positives = 'false_positives'
        for peak_map in self.found_peaks:
            # Find peak areas that do not contain training peaks
            grass.run_command('v.select',
                              ainput=peak_map[2],
                              binput=self.peaks,
                              output=false_positives,
                              operator='disjoint')
            # Count features in the extracted map and call write_to_results()
            false_positives_count = len(grass.read_command('v.db.select',
                                                           map=false_positives,
                                                           column='cat',
                                                           flags='c').splitlines())
            grass.run_command('g.remove',
                              vect=false_positives)
            self.results.add_error('false positives', 
                                         peak_map[0], 
                                         peak_map[1], 
                                         false_positives_count)
    
    def false_negatives(self):
        '''
        Count training peaks that are not contained in a classified peak area
        and write number to results container.
        '''
        
        false_negatives = 'false_negatives'
        for peak_map in self.found_peaks:
            # Find training peaks that do not overlap with peak areas.
            grass.run_command('v.select',
                              ainput=self.peaks,
                              binput=peak_map[2],
                              output=false_negatives,
                              operator='disjoint')
            # Count features in the extracted map and call write_to_results()
            false_negatives_count = len(grass.read_command('v.db.select',
                                                           map=false_negatives,
                                                           column='cat',
                                                           flags='c').splitlines())
            grass.run_command('g.remove',
                              vect=false_negatives)
            self.results.add_error('false negatives', 
                                         peak_map[0], 
                                         peak_map[1], 
                                         false_negatives_count)
    
# TODO: Finish this class.
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
    
    def __init__(self,
                 window_sizes,
                 slope_thresholds,
                 error_values):
        '''
        Initializes axes and data matrix.
        '''
        
        self.window_sizes = window_sizes
        self.slope_thresholds = slope_thresholds
        self.error_values = error_values
        # TODO: Have this lists be initialized here.
        # Initialize window list
        self.window_size = []
        for i in range(len(self.window_sizes)):
            # Append slope lists to windows
            self.window_size.append([])
            for j in range(len(slope_thresholds)):
                # Append error value lists to slope lists
                self.window_size[i].append([])
                for k in range(len(self.error_values):
                    # Make entries for error values
                    self.window_size[i][j].append([])
    
    def add_error(self, 
                  error_type, 
                  window_size, 
                  slope_threshold,
                  error_value):
        '''
        Adds the appropriate error value to the right position in the data 
        structure.
        '''
        
        if not window_size in self.window_sizes:
            self.add_window_size(window_size)
        
        # If it does, check if the slope threshold's in it
        # If so, check if the error value is in it
        # If so, replace the error value
        # If not, write what needs to be written
        # If error type is already in error_values, note its position.
        if error_type in self.results.error_values:
            # Note position
            pass
        else:
            # Otherwise add it.
            pass
        # Repeat for window size
        # Repeat for slope threshold
        # Append error value to correct position in data structure
    
    def add_window_size(self, window_size):
        '''
        Adds and initializes window size to window size list. Adds window size
        to window size index.
        '''
        
        pass
    
    def add_slope_threshold(self, slope_threshold):
        '''
        Adds and initializes slope threshold to slope threshold lists in all
        existing windows. Adds slope threshold to slope threshold index.
        '''
        
        pass

    def add_error_value(self, error_value):
        '''
        Adds and initializes error value to error value lists in all
        existing slope thresholds. Adds error value to error value index.
        '''
        
        pass

class Exporter(object):
    '''
    Summarizes results and exports them to a specified format.
    '''
    
    return

def main():
    # Override GUI inputs
    # Window sizes: 3x3, 5x5, 9x9, 19x19, 39x39, 69x69
    options = {'window_sizes'     : '3, 5, 9, 19, 39, 69',
               # For each window, iterate with slope threshold 1-10
               'slope_thresholds' : str(range(1, 11))[1:-1]}
    # Error values. t = true positives, f = false positives, n = false negatives
    flags = {'f' : True,
             't' : True,
             'n' : True}
    
    # Initialize peak analyzer object
    peak_analyzer = PeakAnalyst(options, flags)
    
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
