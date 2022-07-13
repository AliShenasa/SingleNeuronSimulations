# Cleans SWC files
# Input: SWC file
# Output: Cleaned SWC file
# 
# To run use: python CleanSWC -i file.swc -o cleanfile.swc
# where -i is the input file
# and -o is the output filename
# 
# SWC files from neuprint ocassionally have segments that have no parents.
# Most SWC interpreters require there to be only 1 segment with no parents.
# This scripts assumes if a segment is not the first one without a parent, then its parent is the previous segment.

import argparse

def parseSWCLine(line):
    """
    Parses data line in SWC file. Not for blank or comment lines
    Returns Dictionary with data from the line
    """
    splitline = line.split()
    dataDict = {'idx' : int(splitline[0]),
                'segtype' : int(splitline[1]),
                'xpos' : float(splitline[2]),
                'ypos' : float(splitline[3]),
                'zpos' : float(splitline[4]),
                'radius' : float(splitline[5]),
                'parentidx' : int(splitline[6])}
    return dataDict

def formatnum(num):
    """Remove trailing zeros from a float"""
    return str(num).rstrip('0').rstrip('.')

def writeSWCLine(dataDict, outfile):
    """Given a dict of data for a line and a file, writes the line to the file"""
    lineformat = "{idx} {segtype} {xpos} {ypos} {zpos} {radius} {parentidx}\n"
    lineout = lineformat.format(idx = dataDict['idx'], 
                                segtype = dataDict['segtype'],
                                xpos = formatnum(dataDict['xpos']),
                                ypos = formatnum(dataDict['ypos']),
                                zpos = formatnum(dataDict['zpos']),
                                radius = formatnum(dataDict['radius']),
                                parentidx = dataDict['parentidx'])
    outfile.write(lineout)


def cleanSWC(swcfile, outfilename):
    """Cleans input swc file and saves it to output file"""
    rootSeen = False
    with open(swcfile) as swcfile, open(outfilename, 'w') as outfile:
        for line in swcfile:
            stripline = line.strip()
            if (stripline == "") or (stripline[0] == "#"): # ignore blank and comment lines
                outfile.write(line)
                continue

            lineData = parseSWCLine(line)
            if (lineData['parentidx'] == -1) and (not rootSeen):
                rootSeen = True
                writeSWCLine(lineData, outfile)
                continue
            
            if (lineData['parentidx'] == -1) and (rootSeen):
                lineData['parentidx'] = lineData['idx'] - 1
                writeSWCLine(lineData, outfile)

            else:
                writeSWCLine(lineData, outfile)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--input', '-i', type=str, action='store', help='input file')
    parser.add_argument('--output', '-o', type=str, action='store', help='output file')
    args = parser.parse_args()
    infilename = args.input
    outfilename = args.output

    cleanSWC(infilename, outfilename)


if __name__ == "__main__":
    main()