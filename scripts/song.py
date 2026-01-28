import re
from typing import List

class Paragraph:
    def __init__(self, type: str, lyrics: str, chords: str):
        self.type = type
        self.lyrics = lyrics 
        self.chords = chords
    
    def __repr__(self):
        return(f"Paragraph:\ntype={self.type}\nlyrics:\n{self.lyrics}\nchords:\n{self.chords}\n")

class Song:
    def __init__(self, title: str, author: str, paragraphs: List[Paragraph]):
        self.title = title
        self.author = author
        self.paragraphs = paragraphs

    def __repr__(self) -> str:
        data = ""
        data += f"> {self.title}"
        if self.author is not None:
            data += f" | {self.author}"
        data += f"\n\n"
        for paragraph in self.paragraphs:
            lyrics_lines = paragraph.lyrics.split("\n")
            chords_lines = paragraph.chords.split("\n")
            max_line_len = 0
            for line in lyrics_lines:
                if len(line) > max_line_len:
                    max_line_len = len(line)
            for lyrics_line, chords_line in zip(lyrics_lines, chords_lines):
                lyric = lyrics_line if len(lyrics_line) > 0 else "-"
                chords = f" | {chords_line}" if chords_line != "" else ""
                data += f"{' '*8 if paragraph.type == 'chorus' else ''}{lyric.ljust(max_line_len+4)}{chords}\n"
            data += "\n"
        return data
    
    def load_from_fasta(data: str) -> List['Song']:
        songs = []

        datalines = data.split("\n")
        data = "\n".join(filter(lambda x: not x.strip().startswith("#"), datalines))

        blocks = data.split(">")

        if len(blocks) <= 1: # There are no songs in the file
            return songs

        for block in blocks[1:]:
            first_line = block.split("\n")[0]
            if "|" in first_line:
                title, author = [value.strip() for value in first_line.split("|")]
            else:
                title, author = first_line.strip(), None

            paragraphs = []
            lyrics_lines = "\n".join(block.strip().split("\n")[1:]).lstrip("\n")
            single_paragraph_blocks = lyrics_lines.split("\n\n")
            for block in single_paragraph_blocks:
                if block == "":
                    continue
                lines = block.split("\n")
                paragraph_type = "chorus" if re.match(r'\s', lines[0]) else "verse"
                lyrics, chords = [], []
                for line in lines:
                    if "|" in line:
                        text, chord = line.split("|")
                        lyrics.append(text.strip())
                        chords.append(chord.strip())
                    else:
                        lyrics.append(line.strip())
                        chords.append("")
                for i in range(len(lyrics)):
                    if lyrics[i] == "-":
                        lyrics[i] = ""
                lyrics = "\n".join(lyrics)
                chords = "\n".join(chords)
                paragraphs.append(Paragraph(paragraph_type, lyrics, chords))

            songs.append(Song(title, author, paragraphs))
            
        return songs
    

    
        
    


if __name__=="__main__":
    with open("turystyczne.fasta", "r") as file:
        songs = Song.load_from_fasta(file.read())
        print(len(songs))


