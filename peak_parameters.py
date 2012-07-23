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
        self.results = results
        # Set region to raster
        grass.run_command('g.region', rast=self.dem)
        return
    
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
        
        # TODO: Use this as a model for the window / slope counters
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
            self.write_to_results('true positives', 
                                  peak_map[0],
                                  peak_map[1],
                                  true_positives_count)
            pass
        return
    
    
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
            # TODO: Get this to also send the proper window and slope
            self.write_to_results('false positives',
                                  peak_map[0],
                                  peak_map[1], 
                                  false_positives_count)
            pass
        return
    
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
            self.write_to_results('false negatives',
                                  peak_map[0],
                                  peak_map[1], 
                                  false_negatives_count)
            pass
        return
    
    # TODO: Get this working.
    def write_to_results(self, 
                         error_value,
                         window_size,
                         slope_threshold, 
                         value):
        '''
        Writes a specified error value to the correct field in the data 
        container object.
        '''
        
        # Find out which error value is needed and write it to object 
        if error_value == 'true_positives':
            self.write_true_positives(window_size,
                                      slope_threshold,
                                      value)
        return

    def write_true_positives(self, 
                             window_size,
                             slope_threshold,
                             value):
        '''
        Writes true positives to the results container.
        '''
        
        # Append window size to results container if needed
        # Append slope threshold to results container if needed
        # Append true positives field to results container if needed
        if not 'true positives' in self.results.error_values:
            self.results.error_values.append('true positives')
        # Find position of true positives field
        # Append true positives value to proper window and slope
        self.write_true_positives(value)
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
    options = {'window_sizes'     : '3, 5, 9, 19, 39, 69',
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
