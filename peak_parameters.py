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

    import csv
    
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
            fn: false negative count
        Returns:
            sensitivity value
        '''
        sensitivity = tp/(tp+fn) 
        return sensitivity
    
    def exportToCsv(self, container, errTag, exportpath):
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
            exportpath: path where file shall be created, plus FILENAME.csv
        '''
        self.container = container
        self.errTag = errTag
        self.exportpath = exportpath
 
        # get indexes of error values in ResultContainer 
        tp_index = container.error_values.index('true positives')
        fp_index = container.error_values.index('false positives')
        fn_index = container.error_values.index('false negatives') 
        
        file = open(self.exportpath, 'wb')
        csvWriter = csv.writer(file)

        # run through each window of ResultContainer
        for window in range(len(container.window)):
            errList = []  # set up list of error values for current window
            #  run through each threshold
            for threshold in range(len(container.window[window])):
                # if summary mode was selected, call summarize()
                if (self.errTag == 'summarize'): 
                    tp = container.window[window][threshold][tp_index]
                    fp = container.window[window][threshold][fp_index]
                    fn = container.window[window][threshold][fn_index]
                    summary = self.summarize(tp, fp, fn)
                    errList.append(summary)
                
                # else append error value to error list
                elif (self.errTag == 'true positives'): 
                    errList.append(container.window[window][threshold][tp_index])
                elif (self.errTag == 'false positives'): 
                    errList.append(container.window[window][threshold][fp_index])
                elif (self.errTag == 'false negatives'): 
                    errList.append(container.window[window][threshold][fn_index])
                else: raise(Exception)                
                
            csvWriter.writerow(errList) # write error vals for window to file
        
        file.close()  # close file path        
        return
    
    
    def stdout(self):
        '''somehow create standard out for GRASS console''' 
        # feste Breite auf 80 Zeichen
        # oben in die Ecke: window/threshold
        # z.B. feste Leerzeichenzahl -> 8-len(str(Zahl)) Leerzeichen
        # Oder: Methode r.just, z.B. : entry += value.rjust(7)

        
        
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
