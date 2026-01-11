import os
from song import Song

files = filter(lambda x: len(x) >= 6 and x[-6:] == ".fasta", os.listdir(os.getcwd()))

total_songs = {}
total_songs_with_chords = {}
for path in files:
    total_songs[path] = 0
    total_songs_with_chords[path] = 0
    with open(path, 'r') as f:
        songs = Song.load_from_fasta(f.read())
    for song in songs:
        has_chords = False
        total_songs[path] += 1
        for paragraph in song.paragraphs:
            if any([chord_line != "" for chord_line in paragraph.chords.split("\n")]):
                total_songs_with_chords[path] += 1
                break

total_songs["---------------\nTOTAL"]=sum(total_songs.values())
total_songs_with_chords["---------------\nTOTAL"]=sum(total_songs_with_chords.values())

for path, chords, total in zip(total_songs.keys(), total_songs_with_chords.values(), total_songs.values()):
    print(f"{path}: {chords}/{total}")
