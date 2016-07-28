import requests
from text_processing import TEXT_END_MARKERS
from text_processing import TEXT_START_MARKERS
from text_processing import LEGALESE_END_MARKERS
from text_processing import LEGALESE_START_MARKERS
import os

def download_raw(url):
    local_filename = "rawTexts/" + url.split('/')[-1]
    # NOTE the stream=True parameter
    r = requests.get(url, stream=True)
    with open(local_filename, 'wb') as f:
        for chunk in r.iter_content(chunk_size=1024):
            if chunk: # filter out keep-alive new chunks
                f.write(chunk)
                #f.flush() commented by recommendation from J.F.Sebastian
    return local_filename

def process_raw(text):

    lines = text.splitlines()
    sep = str(os.linesep)

    out = []
    i = 0
    footer_found = False
    ignore_section = False

    for line in lines:
        reset = False

        if i <= 600:
            # Check if the header ends here
            if any(line.startswith(token) for token in TEXT_START_MARKERS):
                reset = True

            # If it's the end of the header, delete the output produced so far.
            # May be done several times, if multiple lines occur indicating the
            # end of the header
            if reset:
                out = []
                continue

        if i >= 100:
            # Check if the footer begins here
            if any(line.startswith(token) for token in TEXT_END_MARKERS):
                footer_found = True

            # If it's the beginning of the footer, stop output
            if footer_found:
                break

        if any(line.startswith(token) for token in LEGALESE_START_MARKERS):
            ignore_section = True
            continue
        elif any(line.startswith(token) for token in LEGALESE_END_MARKERS):
            ignore_section = False
            continue

        if not ignore_section:
            out.append(line.rstrip(sep))
            i += 1

    return sep.join(out)

if __name__ == '__main__':
    """Populate the book ids list with the ones we will be scraping
    for now, just looking at lewis carrol complete works
    11 = Alice's Adventures in Wonderland
    """
    book_ids = [
        11
    ]

    for book in book_ids:
        url = "http://www.gutenberg.org/cache/epub/"+str(book)+"/pg"+str(book)+".txt"
        raw_text_file = download_raw(url)
        with open(raw_text_file, "r") as f:
            text = f.read()
            processed_text = process_raw(text)
            with open("clean/" +str(book)+".txt", "wb") as g:
                g.write(processed_text)
