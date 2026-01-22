from typing import List
from math import ceil
import argparse
import glob
import os
import re

from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A5
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

from song import Song, Paragraph


pdfmetrics.registerFont(TTFont('Garamond-Bold', 'EBGaramond-Bold.ttf'))
pdfmetrics.registerFont(TTFont('NotoSerif', 'NotoSerif-Regular.ttf'))
pdfmetrics.registerFont(TTFont('NotoSerif-SemiBold', 'NotoSerif-SemiBold.ttf'))
pdfmetrics.registerFont(TTFont('NotoSerif-Light', 'NotoSerif-Light.ttf'))
pdfmetrics.registerFont(TTFont('NotoSerif-LightItalic', 'NotoSerif-LightItalic.ttf'))

class FontConfig:
    def __init__(self, font_name: str, font_size: float):
        self.name = font_name
        self.size = font_size

class CompilationConfig:
    page_size = A5
    font_title = FontConfig("Garamond-Bold", 15)
    font_author = FontConfig("NotoSerif-Light", 9)
    font_lyrics = FontConfig("NotoSerif", 9)
    font_chords = FontConfig("NotoSerif-SemiBold", 9)
    font_comment = FontConfig("NotoSerif-LightItalic", 8)
    
    max_title_width = 280
    title_author_spacing_x = 5
    title_author_spacing_y = 15

    min_top_margin = 40
    min_bottom_margin = 20
    preferred_top_margin = 100
    preferred_bottom_margin = 40
    min_title_padding = 10
    optimal_title_padding = 40

    chorus_x_offset = 20

    line_spacing = 11
    chord_gap = 20
    min_chord_x = A5[0]*0.6
    par_gap = 12

    page_bind_offset = 20

config = CompilationConfig()

class TitleParams:
    def __init__(self,
                 title: str,
                 author: str | None,
                 title_xoffset: float,
                 author_xoffset: float,
                 author_yoffset: float):
        self.title = title
        self.author = author
        self.title_xoffset = title_xoffset
        self.author_xoffset = author_xoffset
        self.author_yoffset = author_yoffset
        self.bottom_border = author_yoffset


class ParBlock:
    def __init__(self,
                 lyrics_lines: List[str],
                 chords_lines: List[str],
                 lyrics_width: float,
                 chords_width: float,
                 total_height: float,
                 x_offset: float):
        self.lyrics_lines = lyrics_lines
        self.chords_lines = chords_lines
        self.lyrics_width = lyrics_width
        self.chords_width = chords_width
        self.total_width = lyrics_width+chords_width+config.chord_gap
        self.total_height = total_height
        self.x_offset = x_offset
    
    def __repr__(self):
        return f"Paragraph: {' '.join(self.lyrics_lines)[:25]}...\nwidth: {self.total_width}, height: {self.total_height}"


class BlockPlacement:
    def __init__(self,
                 title_y: float,
                 pars_x: float,
                 pars_y_list: List[float],
                 chords_x_list: List[float],
                 title_params: TitleParams,
                 parblocks: List[ParBlock]):
        self.title_y = title_y
        self.pars_x = pars_x
        self.pars_y_list = pars_y_list
        self.chords_x_list = chords_x_list
        self.title_params = title_params
        self.parblocks = parblocks


def parse_song_lyrics(song: Song):
    '''Generates ParBlock objects with known dimensions'''
    parblocks = [] 
    for paragraph in song.paragraphs:
        lyrics_lines = paragraph.lyrics.split("\n")
        chords_lines = performChordStrReplacements(paragraph.chords).split("\n")
        lyrics_width = 0
        chords_width = 0
        for line, chord in zip(lyrics_lines, chords_lines):
            lyrics_width = max(lyrics_width, pdfmetrics.stringWidth(line, config.font_lyrics.name, config.font_lyrics.size))
            chords_width = max(chords_width, pdfmetrics.stringWidth(chord, config.font_chords.name, config.font_chords.size))
        
        x_offset = config.chorus_x_offset if paragraph.type == "chorus" else 0
        lyrics_width += x_offset
        parblocks.append(ParBlock(lyrics_lines, chords_lines, lyrics_width, chords_width, len(lyrics_lines) * config.line_spacing, x_offset))
    return parblocks


def compute_title_params(song: Song):
    '''Computes the placement of title and author labels within the header'''
    title_width = pdfmetrics.stringWidth(song.title, config.font_title.name, config.font_title.size)
    if song.author is None:
        return TitleParams(song.title, None, -0.5*title_width, 0, 0)
    author_width = pdfmetrics.stringWidth(song.author, config.font_author.name, config.font_author.size)
    total_width = title_width + author_width + config.title_author_spacing_x
    if total_width <= config.max_title_width and author_width < 0.5 * title_width:
        # Title and author next to each other
        return TitleParams(song.title, song.author, -0.5*total_width, -0.5*total_width + title_width + config.title_author_spacing_x, 0)
    else:
        # Title on top, author at the bottom
        return TitleParams(song.title, song.author, -0.5*title_width, -0.5*author_width, config.title_author_spacing_y)
        

def compute_block_placement(pars: List[ParBlock], title: TitleParams):
    # ---------------
    # | top_margin
    # | total_title_height
    # | title_padding
    # | total_text_height
    # | bottom_margin
    # ---------------


    total_text_height = sum(par.total_height for par in pars) + (len(pars) - 1) * config.par_gap
    total_title_height = config.font_title.size + title.bottom_border
    content_height = total_text_height + total_title_height
    content_height_limit = config.page_size[1] - config.min_top_margin - config.min_bottom_margin - config.min_title_padding
    if content_height > content_height_limit:
        # Lyrics too long: need to split to multiple pages
        middle_par = ceil(0.5 * len(pars))
        empty_title = TitleParams("", None, 0, 0, 0)
        return [
            *compute_block_placement(pars[:middle_par], title),
            *compute_block_placement(pars[middle_par:], empty_title)]
    title_padding = config.page_size[1] - config.preferred_bottom_margin - config.preferred_top_margin - content_height 
    title_padding = max(config.min_title_padding, min(config.optimal_title_padding, title_padding))
    total_content_height = content_height + title_padding

    total_margin = (config.page_size[1] - total_content_height)
    top_margin = 0.4 * total_margin
    bottom_margin = 0.6 * total_margin
    top_margin = max(config.min_top_margin, top_margin)

    title_y = top_margin

    # Compute y positions of each paragraph
    par_y = [0 for _ in range(len(pars))]
    par_y[0] = top_margin + total_title_height + title_padding
    for i in range(1, len(pars)):
        par_y[i] = par_y[i-1] + pars[i-1].total_height + config.par_gap

    # Compute x position that ensures centering
    max_width = max(par.total_width for par in pars) 
    par_x = 0.5*(config.page_size[0]-max_width)
    chords_x_list = [config.min_chord_x for _ in range(len(pars))]
    for i in range(len(pars)):
        chords_x = par_x + pars[i].lyrics_width + config.chord_gap
        if chords_x > chords_x_list[i]:
            chords_x_list[i] = chords_x


    return [BlockPlacement(title_y, par_x, par_y, chords_x_list, title, pars)]


def print_to_canvas(placement: BlockPlacement, canvas: canvas, page_number: int | None = None, x_offset: float = 0.0):
    title = placement.title_params
    pars = placement.parblocks
    W, H = config.page_size
    canvas.setFont(config.font_title.name, config.font_title.size)
    canvas.drawString(W/2 + x_offset + title.title_xoffset, placement.title_y, title.title)
    if title.author is not None:
        canvas.setFont(config.font_author.name, config.font_author.size)
        canvas.drawString(W/2 + x_offset + title.author_xoffset, placement.title_y + title.author_yoffset, title.author)
    
    for chords_x, y, par in zip(placement.chords_x_list, placement.pars_y_list, pars):
        canvas.setFont(config.font_lyrics.name, config.font_lyrics.size)
        for i, line in enumerate(par.lyrics_lines):
            drawStringOrComment(placement.pars_x + par.x_offset + x_offset, y + i * config.line_spacing, config.font_lyrics, line, canvas)
        canvas.setFont(config.font_chords.name, config.font_chords.size)
        for i, line in enumerate(par.chords_lines):
            drawStringOrComment(chords_x + x_offset, y + i * config.line_spacing, config.font_chords, line, canvas)
    
    if page_number is not None:
        canvas.setFont(config.font_chords.name, config.font_chords.size)
        canvas.drawCentredString(W/2 + x_offset, H - 25, str(page_number))

    canvas.showPage()


def performChordStrReplacements(chords: str):
    chords = chords.replace("+", "₊")
    chords = chords.replace("sus2", "₂")
    chords = chords.replace("sus4", "₄")
    chords = chords.replace("7", "₇")
    chords = chords.replace("add9", "₉")
    return chords
    

def drawStringOrComment(x: float, y: float, font: FontConfig, line: str, canvas: canvas):
    strings = []
    types = []
    last_idx = 0
    for match in re.finditer(r'\[[^\[\]]*\]', line):
        if match.span()[0] > last_idx:
            strings.append(line[last_idx:match.span()[0]])
            types.append(0)
        strings.append(line[match.span()[0]+1:match.span()[1]-1])
        types.append(1)
        last_idx = match.span()[1]
    strings.append(line[last_idx:len(line)])
    types.append(0)
    
    for string, type in zip(strings, types):
        if type == 0:
            selected_font = font
        else:
            selected_font = config.font_comment
        
        canvas.setFont(selected_font.name, selected_font.size)
        canvas.drawString(x, y, string)
        x += pdfmetrics.stringWidth(string, selected_font.name, selected_font.size)
        





def compile_single_song(song: Song):
    parblocks = parse_song_lyrics(song)
    titleblock = compute_title_params(song)
    placements = compute_block_placement(parblocks, titleblock)
    return placements




def compile(songs: Song | List[Song], output_path: str):
    c = canvas.Canvas(output_path, config.page_size, bottomup=False)
    if not type(songs) == list:
        songs = [songs]
    placements = []
    for song in songs:
        placements.append(compile_single_song(song))

    # Ensure that two-page songs always start from even pages
    page_number = 1
    for i in range(len(placements)):
        pages = len(placements[i])
        if page_number % 2 == 1:
            if len(placements[i]) > 1:
                swap = placements[i]
                placements[i] = placements[i-1]
                placements[i-1] = swap
        page_number += pages

    page_number = 1
    for group in placements:
        for placement in group:
            x_offset = config.page_bind_offset
            if page_number % 2 == 0:
                x_offset = -x_offset
            print_to_canvas(placement, c, page_number, x_offset)
            page_number += 1
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
                with open(filename, 'r', encoding='utf-8') as f:
                    songs = Song.load_from_fasta(f.read())
                    all_songs.extend(songs)

    if not all_songs:
        print("No songs found. Check your file paths.")
        return
    
    all_songs.sort(key=lambda x: x.title)

    # selected_song = []
    # for song in all_songs:
    #     if song.title.lower().startswith("niemanie"):
    #         selected_song.append(song)
    # all_songs = selected_song


    compile(all_songs, args.output)
    print(f"Successfully created {args.output}")

if __name__ == "__main__":
    main()