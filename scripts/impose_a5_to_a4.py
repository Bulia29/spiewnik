from pypdf import PdfReader, PdfWriter, PageObject, Transformation
from reportlab.lib.pagesizes import A4


def impose(input_path, output_path):
    reader = PdfReader(input_path)
    writer = PdfWriter()

    pages = list(reader.pages)
    while len(pages) % 4 !=0:
        pages.append(PageObject.create_blank_page(width=pages[0].mediabox.width, height=pages[0].mediabox.height))
    
    num_pages = len(pages)
    num_sheets = num_pages // 2

    order = []
    for i in range(num_sheets):
        if i % 2 == 0:
            # Front side of the sheet
            order.append(pages[num_pages - 1 - i]) # Left
            order.append(pages[i])                 # Right
        else:
            # Back side of the sheet
            order.append(pages[i])                 # Left
            order.append(pages[num_pages - 1 - i]) # Right

    for i in range(0, len(reader.pages), 2):
        new_page = PageObject.create_blank_page(width=A4[1], height=A4[0])
        p1 = order[i]
        p1.add_transformation(Transformation().translate(tx=0, ty=0))

        p2 = order[i+1]
        p2.add_transformation(Transformation().translate(tx=A4[1]/2, ty=0))
        p2.mediabox.bottom_left = (A4[1]/2, 0)
        p2.mediabox.upper_right = (A4[1], A4[0])

        new_page.merge_page(p1)
        new_page.merge_page(p2)

        writer.add_page(new_page)
    
    with open(output_path, "wb") as file:
        writer.write(file)
    

if __name__=="__main__":
    impose("pdf/Śpiewnik.pdf", "pdf/Śpiewnik-printableA4.pdf")