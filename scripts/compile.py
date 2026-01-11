from typing import List
import argparse
import glob
import os

from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A5
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

from song import Song, Paragraph


pdfmetrics.registerFont(TTFont('Garamond-Bold', 'EBGaramond-Bold.ttf'))
pdfmetrics.registerFont(TTFont('NotoSerif', 'NotoSerif-Regular.ttf'))
pdfmetrics.registerFont(TTFont('NotoSerif-SemiBold', 'NotoSerif-SemiBold.ttf'))
pdfmetrics.registerFont(TTFont('NotoSerif-Light', 'NotoSerif-Light.ttf'))

def compile_single_song(song: Song, c: canvas):
    if len(song.paragraphs) == 0:
        print(f"Skipping song {song.title} due to empty lyrics.")
        return
    print(f"Compiling song {song.title}...")
    W, H = A5

    # Draw title
    title_height = 46
    title_font = "Garamond-Bold"
    author_font = "NotoSerif-Light"

    width = 0
    title_width = pdfmetrics.stringWidth(song.title, title_font, 14)
    width += title_width
    if song.author is not None:
        width += 6 + pdfmetrics.stringWidth(song.author, author_font, 10)
    c.setFont(title_font, 14)
    c.drawString((W-width)/2, H - 32, song.title)
    if song.author is not None:
        c.setFont(author_font, 10)
        c.drawString((W-width)/2 + title_width + 6, H - 32, song.author)

    # Draw lyrics
    font = "NotoSerif"
    chordfont = "NotoSerif-SemiBold"
    fontsize = 9.5
    
    linespacing = 1.2 * fontsize
    par_gap_size = 15
    chorus_offset = 20
    chord_gap = 15
    min_right_margin = 20
    min_left_margin = 20

    max_text_height = H - title_height
    text_height = (len(song.paragraphs) - 1) * par_gap_size + sum([len(p.lyrics.split("\n")) for p in song.paragraphs]) * linespacing
    h_offset = (max_text_height - text_height - 40) / 2
    h_offset = max(0, min(30, h_offset))
    h_offset += title_height + 1*linespacing

    h_size = 0
    lyrics_widths = []
    chords_widths = []
    # Compute maximum widths of each paragraph
    for paragraph in song.paragraphs:
        lines = paragraph.lyrics.split("\n")
        chords = paragraph.chords.split("\n")
        maxtextlen = 0
        maxchordlen = 0
        # Calculate maximum
        for line, chord in zip(lines, chords):
            textlen = pdfmetrics.stringWidth(line, font, fontsize)
            if paragraph.type == 'chorus':
                textlen += chorus_offset
            maxtextlen = max(maxtextlen, textlen)
            chordlen = pdfmetrics.stringWidth(chord.replace("7", "₇"), chordfont, fontsize)
            maxchordlen = max(maxchordlen, chordlen)
        lyrics_widths.append(maxtextlen)
        chords_widths.append(maxchordlen)

    # Draw paragraph
    chord_offset = max(chords_widths)
    max_line_width = chord_offset + chord_gap + max(lyrics_widths)
    h_size = 0
    total_margin = W - max_line_width
    left_margin = max(min_left_margin, total_margin/2)
    right_margin = max(min_right_margin, total_margin/2)
    for paragraph in song.paragraphs:
        lines = paragraph.lyrics.split("\n")
        chords = paragraph.chords.split("\n")
        text_offset = chorus_offset if paragraph.type == "chorus" else 0
        for i in range(len(lines)):
            c.setFont(font, fontsize)
            c.drawString(left_margin + text_offset, H - h_offset - h_size - i*linespacing, lines[i])
            c.setFont(chordfont, fontsize)
            c.drawString(W - right_margin - chord_offset, H - h_offset - h_size - i*linespacing, chords[i].replace("7", "₇"))
        h_size += len(lines) * linespacing + par_gap_size
        
    c.showPage()





def compile(songs: Song | List[Song], output_path: str):
    c = canvas.Canvas(output_path, A5)
    if not type(songs) == list:
        songs = [songs]
    for song in songs:
        compile_single_song(song, c)
    c.save()
    print(f"Saved output to {output_path}.")



def main():
    parser = argparse.ArgumentParser(
        description="Compile song files (.fasta) into a pdf file."
    )
    
    # nargs='+' collects 1 or more arguments into a list
    parser.add_argument(
        'input_files', 
        nargs='+', 
        help="Path to .fasta files. Supports wildcards (e.g., songs/*.fasta)"
    )
    
    parser.add_argument(
        '-o', '--output', 
        default='pdf/Śpiewnik.pdf',
        help="Output filename (default: pdf/Śpiewnik.pdf)"
    )

    args = parser.parse_args()

    all_songs = []
    
    # Process each filename provided
    for pattern in args.input_files:
        # glob.glob handles cases where the shell might not expand the *
        for filename in glob.glob(pattern):
            if os.path.isfile(filename):
                print(f"Reading {filename}...")
                with open(filename, 'r', encoding='utf-8') as f:
                    songs = Song.load_from_fasta(f.read())
                    all_songs.extend(songs)

    if not all_songs:
        print("No songs found. Check your file paths.")
        return
    
    all_songs.sort(key=lambda x: x.title)

    compile(all_songs, args.output)
    print(f"Successfully created {args.output}")

if __name__ == "__main__":
    main()