#! /usr/bin/python

import sys
import re

if len(sys.argv) != 3:
    print("Usage: transpose.py <half-steps> <chord sequence>\nExample: transpose.py +4 \"C D e\"")
    exit(-1)

valid_chord_regex = r'^[a-hA-H](#|b)?[a-zA-Z0-9]*'
chord_name_regex = r'^[a-hA-H](#|b)?'

def chordname_split(chordname: str):
    if re.match(valid_chord_regex, chordname) is None:
        raise ValueError(f"{chordname} is not a valid chord name")
    match = re.match(chord_name_regex, chordname)
    return chordname[match.span()[0]:match.span()[1]], chordname[match.span()[1]:]

note_steps = {"c": 0, "d": 2, "e": 4, "f": 5, "g": 7, "a": 9, "b": 10, "h": 11}

def note_to_chromatic_scale(note: str):
    note = note.lower()
    step = note_steps[note[0]]
    if len(note) == 2:
        if note[1] == "#":
            step += 1
        elif note[1] == "b":
            step -= 1
    return step

step_notes = "c c# d d# e f f# g g# a b h".split(" ")

def chromatic_scale_to_note(step: int):
    return step_notes[step%12]

def note_transpose(note: str, steps: int):
    step = note_to_chromatic_scale(note)
    step += steps
    new_note = chromatic_scale_to_note(step)
    if note[0].isupper():
        new_note = new_note.upper()
    return new_note


steps = int(sys.argv[1])
chords = sys.argv[2].split(" ")


try:
    transposed = []
    for chord in chords:
        note, type = chordname_split(chord)
        transposed.append(note_transpose(note, steps) + type)
    print(" ".join(transposed))
except Exception as e:
    print("Error:", e)

