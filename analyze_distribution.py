import os, sys, csv, getopt

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy import stats
from scipy import nanmedian

np.set_printoptions(precision=3)

def main(argv):
    inputfile = ''
    outputfile = ''
    try:
        opts, args = getopt.getopt(argv,"hi:o:",["ifile=","ofile="])
    except getopt.GetoptError:
        print('plot_distribution.py -i <inputfile.csv> -o <outputfile.csv>')
        sys.exit(2)
    for opt, arg in opts:
        if opt == '-h':
            print('test.py -i <inputfile.csv> -o <outputfile.csv>')
            sys.exit()
        elif opt in ("-i", "--ifile"):
            inputfile = arg
        elif opt in ("-o", "--ofile"):
            outputfile = arg
    
    results = analyse_data(inputfile)
    save_file(results, inputfile, outputfile)

def analyse_data(input_file):
    df = pd.read_csv(input_file)
    labels = df['board_size'].unique()
    to_write = []

    for l in labels:
        rows_values = df.loc[(df.board_size == l)]
        step_values = rows_values.loc[rows_values.solved == 'yes'].steps_taken.values 
        if not len(step_values):
            to_write.append([l, input_file[:-4], len(rows_values), 0, 0, 0, 0, 0, 0, 0])
        else:
            analys = stats.describe(step_values)
            median = nanmedian(step_values)
            percentile = [analys[1][0], np.percentile(step_values,25), np.percentile(step_values,50), np.percentile(step_values,75),analys[1][1]]
            to_write.append([l, input_file[:-4], len(rows_values), analys[0], round(np.mean(step_values),3)] + percentile)
    return to_write

def save_file(to_write, in_file_name, out_file_name):
    if not os.path.isfile(out_file_name):
        with open(out_file_name, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(["map_size", "heuristic_type", "sample_size", "solved_map", 'mean', "min", "25%", 'median', '75%', 'max'])
            for line in to_write:
                writer.writerow(line)
    else:
        with open(out_file_name, 'a') as f:
            writer = csv.writer(f)
            for line in to_write:
                writer.writerow(line)

if __name__ == "__main__":
   main(sys.argv[1:])
