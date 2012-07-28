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
    
    def summarize(self):
        '''summarizes ResultContainer error values to error index.'''
        return
    
    def exportToCsv(self, container, id, exportpath):
        ''' 
        Depending on id, exports error values from a ResultContainer to csv.
        Args:
            container: ResultContainer object which shall be exported
            id: error value or summary to be exported
                0 = 'false positive',
                1 = 'true negative',
                2 = 'false negative'
                3 = summarized index
            exportpath: path where file shall be created, plus FILENAME.csv
        '''
        self.container = container
        self.id = id
        self.exportpath = exportpath
        
        # could test the integrity of cointainer file: 
        # isinstance(container, ResultContainer)  
        
        file = open(self.exportpath, "wb")
        csvWriter = csv.writer(file)

        # run through each window of ResultContainer
        for window in range(0, len(container.matrix)):
            errList = []  # set up list of error values for current window
            #  run through each threshold
            for threshold in range(0, len(container.matrix[window])):
                # append error values to error list
                errList.append(container.matrix[window][threshold][self.id])
                
            csvWriter.writerow(errList) # write error vals for window to file
        
        file.close()  # close file path        
        return
    
    
    def stdout(self):
        '''somehow create standard out for GRASS console''' 
        
        # z.B. feste Leerzeichenzahl -> 8-len(str(Zahl)) Leerzeichen
        
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
