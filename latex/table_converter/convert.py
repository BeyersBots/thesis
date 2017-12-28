#!/usr/bin/python
import csv
import sys
import os

f = open(sys.argv[1], 'rU')
f2 = open(os.path.splitext(sys.argv[1])[0]+'.tex', 'w')
f2.truncate()
reader = csv.reader(f)

writer = csv.writer(f2, delimiter='&',quotechar='', quoting=csv.QUOTE_NONE)
firstline = next(reader)
num_columns = len(firstline)

f2.write('\\begin{table}[h!]\n\centering\n\caption{Add caption}\n')
f2.write('\t\\begin{tabular}{')
f2.write('|c'*num_columns)
f2.write('|')
f2.write('}\n\t\t\hline\n')

f2.write('\t\t')
f2.write('\\thead{')
f2.write('} & \\thead{'.join(firstline))
f2.write('} \\\\\n\t\t\hline\n')
for row in reader:
	f2.write('\t\t')
	f2.write(' & '.join(row))
	#writer.writerow(row)
	f2.write(' \\\\')
	f2.write('\n\t\t\hline\n')

f2.write('\t\end{tabular}\n\label{addlabel}\n\end{table}')
	
f.close()
f2.close()
