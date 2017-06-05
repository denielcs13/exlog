#!/usr/bin/env gnuplot

load("common.cfg")

set output "press-epley.jpg"

set style line 1 linewidth 2
set style fill solid 0.25 border

set y2tics

set title "Press Epley and Wilks"

plot \
     csvdir."weekly.csv" using date:press_epley with lines title "press epley",\
     csvdir."weekly.csv" using date:press_epley_wilks with lines axis x1y2 title "press wilks",\
