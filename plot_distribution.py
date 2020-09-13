import sys, getopt
import csv
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

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

   df = pd.read_csv(inputfile)
   analyse_data_by_size_and_result(df)

def analyse_data_by_size_and_result(df):
   labels = df['board_size'].unique()
   solved, unsolved = [], []

   for l in labels:
      solved.append(len(df.loc[(df['board_size'] == l) & (df['solved'] == 'yes')]))
      unsolved.append(len(df.loc[(df['board_size'] == l) & (df['solved'] == 'no')]))

   x = np.arange(len(labels))  # the label locations
   width = 0.35  # the width of the bars

   fig, ax = plt.subplots()
   rects1 = ax.bar(x - width/2, solved, width, label='Solved')
   rects2 = ax.bar(x + width/2, unsolved, width, label='Unsolved')

   # Add some text for labels, title and custom x-axis tick labels, etc.
   ax.set_ylabel('Number of solvement')
   ax.set_title('Scores by board size and solve result')
   ax.set_xticks(x)
   ax.set_xticklabels(labels)
   ax.legend()

   autolabel(rects1, ax)
   autolabel(rects2, ax)

   fig.tight_layout()

   plt.show()

def autolabel(rects, ax):
   """Attach a text label above each bar in *rects*, displaying its height."""
   for rect in rects:
      height = rect.get_height()
      ax.annotate('{}'.format(height),
                  xy=(rect.get_x() + rect.get_width() / 2, height),
                  xytext=(0, 3),  # 3 points vertical offset
                  textcoords="offset points",
                  ha='center', va='bottom')

if __name__ == "__main__":
   main(sys.argv[1:])
