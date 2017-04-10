#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print 'Usage: check_textgrid.py vad.TextGrid'
        sys.exit(1)

    if (sys.argv[1] == "-"):
        fin = sys.stdin
    else:
        fin = open(sys.argv[1], 'r')

    line = 0
    total_xmax = 0
    voice_num = 0
    interval_num = 0
    wav_info = fin.read().splitlines()
    for info in wav_info:
        line += 1
        if info.startswith("xmax"):
            total_xmax = float(info.split()[-1])
        if info.lstrip().startswith("xmax"):
            if total_xmax != float(info.split()[-1]):
                print "line %d xmax error" % line
                sys.exit(1)
        if info.lstrip().startswith("intervals: size"):
            interval_num = int(info.split()[-1])
            voice_num = interval_num/2
            break

    last_xmax = 0
    last_text = "v"
    voice_index = 0
    interval_index = 0
    intervals_info = wav_info[line:line + interval_num*4]
    for i in xrange(0, len(intervals_info), 4):
        line += 4
        interval_index += 1

        xmin = float(intervals_info[i+1].split()[-1])
        xmax = float(intervals_info[i+2].split()[-1])
        if xmin != last_xmax:
            print "line %d xmin error" % (line-2)
            sys.exit(1)
        if xmax <= xmin:
            print "line %d xmax error" % (line-1)
            sys.exit(1)
        last_xmax = xmax

        text = intervals_info[i+3].split('=')[-1].strip().replace('"', '')
        if text == last_text:
            print "line %d text error" % (line)
            sys.exit(1)
        if text == 'v':
            voice_index += 1
            last_text = text
        elif text == '':
            last_text = text
            continue
        else:
            print "line %d text error" % (line)
            sys.exit(1)

    if voice_index != voice_num:
        print "voice number is wrong"
        sys.exit(1)
    if interval_index != interval_num:
        print "voice number is wrong"
        sys.exit(1)
    if total_xmax != last_xmax:
        print "line %d xmax error" % (line-1)
        sys.exit(1)

    print "Your TextGrid is OK."
    fin.close()
