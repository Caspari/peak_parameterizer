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
#% description: Find false positives
#% guisection: Validation measurements
#%End
#%Flag
#% key: n
#% description: Find false negatives
#% guisection: Validation measurements
#%End
#%Flag
#% key: s
#% description: Summarize error values
#% guisection: Validation measurements
#%End

#%Option
#% key: dem
#% description: The input elevation map
#% gisprompt: old,cell,raster
#% required: yes
#%End
#%Option
#% key: peaks
#% description: A vector map of training peaks as points
#% gisprompt: old,vector
#% required: yes
#%End
#%Option
#% key: window_sizes
#% type: string
#% description: A list of integer window sizes separated by commas
#% required: yes
#% answer: 3, 5, 9, 19, 39, 69
#%End
#%Option
#% key: slope_thresholds
#% type: string
#% description: A list of slope thresholds separated by commas
#% required: yes
#% answer: 1, 2, 3, 4, 5, 6, 7, 8, 9, 10
#%End
#%Option
#% key: export_directory
#% type: string
#% description: The directory to export CSVs to.
#% required: yes
#% gisprompt: old,dbase,dbase
#%End

import os
import csv

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
                peak_vectors = 'p_' + peak_raster
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
        for peak_map in self.found_peaks:
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
            self.results.add_error(peak_map[0], 
                                   peak_map[1],
                                   'true positives', 
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
            self.results.add_error(peak_map[0], 
                                   peak_map[1],
                                   'false positives', 
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
            self.results.add_error(peak_map[0], 
                                   peak_map[1],
                                   'false negatives', 
                                   false_negatives_count)
    
class ResultsContainer(object):
    '''
    A data container with a three dimensional matrix.
    
    X: Window sizes
    Y: Slope thresholds
    Z: Error values
    
    The matrix is indexed using the following scheme:
    window[window_size][slope_threshold][error_value]
    
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
        # Initialize window list
        self.window = []
        for i in range(len(self.window_sizes)):
            # Append slope lists to windows
            self.window.append([])
            for j in range(len(slope_thresholds)):
                # Append error value lists to slope lists
                self.window[i].append([])
                for k in range(len(self.error_values)):
                    # Make entries for error values
                    self.window[i][j].append([])
    
    def add_error(self, 
                  window_size, 
                  slope_threshold,
                  error_type,
                  error_value):
        '''
        Adds the appropriate error value to the right position in the data 
        structure.
        '''
        
        # Find indices for window size, slope threshold and error value
        window_index = self.window_sizes.index(window_size)
        slope_index = self.slope_thresholds.index(slope_threshold)
        error_index = self.error_values.index(error_type)
        # Append error value to correct position in data structure
        self.window[window_index][slope_index][error_index] = error_value
    
class Exporter(object):
    '''
    Summarizes results and exports them to a specified format.
    '''
    
    def __init__(self, 
                 container, 
                 flags, 
                 options):
        self.container = container
        self.export_directory = options['export_directory']
        if not self.export_directory[-1] == '/':
            self.export_directory += '/'
        # Append error flags to error values list
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
        if 's' in self.error_values:
            self.error_values.remove('s')
            self.error_values.append('summarize')
        # Call export methods.
        for error_flag in self.error_values:
            export_path = (self.export_directory + error_flag + 
                           '.csv').replace(' ', '_')
            self.exportToCsv(error_flag, export_path)
            self.stdout(self.container)

    def summarize(self, tp, fp, fn):
        '''
        summarizes ResultContainer error values to error index.
        
        The error index calculated here is the 'sensitivity', i.e. the
        proportion of correctly identified peaks (true positive) to all existing
        peaks (true positive + false negative).
        (see http://en.wikipedia.org/wiki/Binary_classification)
        
        A different index form can be implemented in the future.
        
        Args: 
            tp: true positive count
            fp: false positive count
            fn: false negative count
        Returns:
            sensitivity value
        '''
        
        sensitivity = tp/(tp+fn) 
        return sensitivity
    
    def exportToCsv(self, errTag, export_path):
        ''' 
        Depending on id, exports error values from a ResultContainer to csv.
        Args:
            container: ResultContainer object which shall be exported
            errTag: Tag to indicate, which error or summary shall be exported.
                accepted strings:
                    'true positives',
                    'false positives',
                    'false negatives'
                    'summarize'
            export_path: path where file shall be created, plus FILENAME.csv
        '''
        
        # get indexes of error values in ResultContainer 
        tp_index = self.container.error_values.index('true positives')
        fp_index = self.container.error_values.index('false positives')
        fn_index = self.container.error_values.index('false negatives') 
        
        output_file = open(export_path, 'wb')
        csvWriter = csv.writer(output_file)

        # create header variable for labels
        header = container.slope_thresholds  
        # add 'threshold' text to labels
        for i in range(len(header)):
            header[i] = 'threshold_' + str(header[i])
        # append window size label to front of header list
        header.reverse()
        header.append('window_size')
        header.reverse()
        # write header
        csvWriter.writerow(header)
        
        # run through each window of ResultContainer
        for window in range(len(self.container.window)):
            errList = []  # set up list of error values for current window
            errList.append(container.window_sizes[window]) # window size in first row
            #  run through each threshold
            for threshold in range(len(self.container.window[window])):
                # if summary mode was selected, call summarize()
                if (errTag == 'summarize'): 
                    tp = self.container.window[window][threshold][tp_index]
                    fp = self.container.window[window][threshold][fp_index]
                    fn = self.container.window[window][threshold][fn_index]
                    summary = self.summarize(tp, fp, fn)
                    errList.append(summary)
                
                # else append error value to error list
                elif (errTag == 'true positives'): 
                    errList.append(self.container.window[window][threshold][tp_index])
                elif (errTag == 'false positives'): 
                    errList.append(self.container.window[window][threshold][fp_index])
                elif (errTag == 'false negatives'): 
                    errList.append(self.container.window[window][threshold][fn_index])
                else: raise(Exception)                
                
            csvWriter.writerow(errList) # write error vals for window to file
        
        output_file.close()  # close file path        
        return
    
    
    def stdout(self, container):
        '''
        Matrix of index of error vals as standard out for GRASS console
        
        Args:
            container: ResultContainer object which shall be exported
        '''
        self.container = container
          
        xlabel = 't h r e s h o l d'
        ylabel = 'w i n d o w'

        # get indexes of error values in ResultContainer 
        tp_index = container.error_values.index('true positives')
        fp_index = container.error_values.index('false positives')
        fn_index = container.error_values.index('false negatives') 

        # help function
        def setField(arg):
            '''Returns a string with certain fixed length, left justified'''
            if(isinstance(arg, float)):
                arg = round(arg, 2)         # round floating point numbers
            if(isinstance(arg, float)):
                arg = arg[:6]               # truncate strings 
            
            return str(arg).ljust(7)  # return string of length 7, filled with spaces 


        ## PRINTING ###
                        
        print xlabel.rjust(36)  # print x-label in first row
                   
        # print thresholds in second row as list with fixed spaces
        thresholds = container.slope_thresholds  # create variable to work with
        for x in range(len(thresholds)):
            thresholds[x] = setField(thresholds[x])  # set to correct field size
        thresholds.reverse()  # reverse threshold list
        thresholds.append('       ') # add seven spaces for row of window sizes
        thresholds.append('   ')  # three spaces for row of window label
        thresholds.reverse()  # and reverse back. Now the space is at the front
        print ''.join(x for x in thresholds)
          
        # prepare y-labels for printing. There will be one letter per row.
        ylabel = ylabel.split()  #separate in list
        ylabel.reverse()  # reverse --> letters will be popped from list
        
        # run through each window of ResultContainer
        for window in range(len(container.window)):
            errList = []  # set up list of summarized values for current window
            # append y-label letter, spaces if ylabels empty
            if(len(ylabel) > 0):
                errList. append(ylabel.pop())
            else:
                errList.append('   ')    
            
            window_size = container.window_sizes(window)  # extract window size
            errList.append(setField(str(window_size)))  # append window size
            
            #  run through each threshold, summarize and append to errList
            for threshold in range(len(container.window[window])):
                tp = container.window[window][threshold][tp_index]
                fp = container.window[window][threshold][fp_index]
                fn = container.window[window][threshold][fn_index]
                summary = self.summarize(tp, fp, fn)
                summary = setField(summary)  # format summary to correct length
                errList.append(summary)
                                          
            # print the summarized values for each threshold in current window
            print ''.join(x for x in errList)        
        
        return 
    

def main():
    # Initialize peak analyzer object
    peak_analyzer = PeakAnalyst(options, flags)
    
    # Find peaks using different windows
    print('Finding peaks')
    peak_analyzer.find_peaks()
    
    # Extract error values and write them to data container
    print('Extracting error values...')
    for error_value in peak_analyzer.error_values:
        peak_analyzer.evaluate_peaks(error_value)
    
    # Output error values
    print('Writing results to file...')
    output_writer = Exporter(peak_analyzer.results, 
                             flags, 
                             options)

if __name__ == '__main__':
    options, flags = grass.parser()
    main()
