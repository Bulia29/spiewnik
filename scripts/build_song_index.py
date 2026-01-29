import os
from song import Song
from compile import sort_songs

files = filter(lambda x: len(x) >= 6 and x[-6:] == ".fasta", os.listdir(os.getcwd()+"/songs"))
result = ''
result += '{'
result += '"paths":'
result += str(['songs/' + path for path in files]).replace("'", '"')
result += '}'

with open("song_manifest.json", "w") as file:
    file.write(result)