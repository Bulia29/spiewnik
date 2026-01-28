import os
import locale
from song import Song

try:
    locale.setlocale(locale.LC_COLLATE, 'pl_PL.UTF-8')
except locale.Error:
    print("Locale not supported on this system.")

files = filter(lambda x: len(x) >= 6 and x[-6:] == ".fasta", os.listdir(os.getcwd()))

songs = []

for path in files:
    with open(path, 'r') as f:
        loaded_songs = Song.load_from_fasta(f.read())
        song: Song
        for song in loaded_songs:
            songs.append({"title": song.title, "author": song.author, "file": path})

songs.sort(key=lambda x: locale.strxfrm(x["title"]))

print("# Śpiewnik.fasta")

print("Wersja pdf do pobrania dostępna pod linkiem: https://github.com/Bulia29/spiewnik/releases/")

print(f"Zawarte piosenki ({len(songs)}):")

for song in songs:
    author = f' – {song["author"]}' if song["author"] is not None else ""
    print(f' - **{song["title"]}**{author}\t*({song["file"]})*')


print("\n### TODO:")

with open("todo.md", "r") as file:
    print(file.read())