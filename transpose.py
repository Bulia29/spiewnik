#! /usr/bin/python

import sys

if len(sys.argv) != 3:
    print("Usage: transpose.py <half-steps> <chord sequence>\nExample: transpose.py +4 \"C D e\"")
    exit(-1)

steps = int(sys.argv[1])
chords = sys.argv[2].split(" ")

order = "c c# d d# e f f# g g# a b h".split(" ")

transposed = []

for chord in chords:
    chord_idx = order.index(chord.lower()) + steps % len(order)
    if chord_idx < 0:
        chord_idx += len(order)
    if chord_idx >= len(order):
        chord_idx -= len(order)
    transposed_chord = order[chord_idx]
    if chord[0].isupper():
        transposed_chord = transposed_chord.upper()
    transposed.append(transposed_chord)

print(" ".join(transposed))