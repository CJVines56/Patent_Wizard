# Chop up the XML into the three primary sections of Abstract, Description, and Claims.         #
# These sections are separated by a starting and ending line of text, as is the entire patent.  #
#                                                                                               #
# For the patent itself, it will lead with <us-patent-application - followed by some patent     #
# information, and then end with </us-patent-application>. The slash indicates the end of a     #
# section.                                                                                      #
#                                                                                               #
# These are <abstract>, <description>, and <claims> respectively.                               #
# <abstract id="abstract"> will be followed by <p id="p-0001" num="0000">(abstract text) on the #
# next line. id= and num= indicate attributes read from XML. id is for referencing within a     #
# section, it is an id number. num= is the number of a paragraph.                               #

# There's a lot of junk in the text, not applicable sections, figure descriptions, etc.         #

# 10/15/2025 Revised extract, now extracts into chunks preemptively based on sections in xml    #
# chunking.py is now REDUNDANT?                                                                 #
# EXTRACT WILL ALSO NEED TO EXTRACT METADATA LIKE CPC CODE AND DOC NUMBER                       #
# Takes in exactly ONE xml file                                                                 #
from lxml import etree
from pathlib import Path

def extract_text(xml_path):

    # Check for proper XML path, plus error message
    try:
        tree = etree.parse(xml_path)        # Check for proper xml
        root = tree.getroot()               # Find root of xml
    except etree.XMLSyntaxError as e:
        print(f"XML parsing failed: {e}")   # Error message
        return []                           # return an empty list (no chunks)

    def clean_text(path):
        # Given an input path, finds the root associated with that path,
        # then clean all text by removing whitespace
        parts = root.xpath(path)
        return " ".join(t.strip() for t in parts if t.strip())

    # List of chunks
    chunks = []

    # Extract the text from the abstract section of xml
    abstract_text = clean_text("//abstract//text()")

    # append that to the list of chunks under abstract
    if abstract_text:
        chunks.append(("abstract", abstract_text))

    ## PUT PARAGRAPH NUMBER ##
    ## LABEL IMPORTANT FIELDS EARLY IN DESCRIPTION ##
    # Iterate through each "p" labeled section in xml (paragraph)
    for para in root.xpath("//description//p"):
        # Clean the text, then append to list of chunks under description
        desc_text = " ".join(t.strip() for t in para.xpath(".//text()") if t.strip())
        if desc_text:
            chunks.append(("description", desc_text))

    # Exact same process as for the description
    for claim in root.xpath("//claims//claim"):
        claim_text = " ".join(t.strip() for t in claim.xpath(".//text()") if t.strip())
        if claim_text:
            chunks.append(("claim", claim_text))

    # Will return a list of tuples, each tuple containing the chunk label and then chunk text
    return chunks
# Old extract - extracts and puts evering as one large string of text, separating sections by newlines.

'''
from lxml import etree


def extract_text(xml_path):

    # Check for proper XML path, plus error message
    try:
        tree = etree.parse(xml_path)        # Check for proper xml
        root = tree.getroot()               # Find root of xml
    except etree.XMLSyntaxError as e:
        print(f"XML parsing failed: {e}")   # Error message
        return []                           # return an empty list (no chunks)

    def clean_text(path):
        # Given an input path, finds the root associated with that path,
        # then clean all text by removing whitespace
        parts = root.xpath(path)
        return " ".join(t.strip() for t in parts if t.strip())

    # Extract the text from each section
    abstract_text = clean_text("//abstract//text()")
    description_text = clean_text("//description//text()")
    claims_text = clean_text("//claims//text()")

    # Connect all sections into 3 large paragraphs separated by two newlines
    combined_text = "\n\n".join(
        section for section in [abstract_text, description_text, claims_text] if section
    )
    #print(combined_text)
    return combined_text
'''

# Initial testing extract
'''
# Load in the XML to be extracted from, then identify "root" element. "us-patent-application"   #
# in this case.                                                                                 #
#tree = etree.parse()
#root = tree.getroot()
#print(root.tag)  # Test

# First extract the abstract from the XML. root.xpath searches through xml documents in its own #
# unique way. // will search for an element in the xml. After //, you can specify a section.    #
# "abstract" will specify the section named "abstract". //text() will then return all text in   #
# the abstract section. Then we just clean up the extracted text.                               #
abstract = root.xpath("//abstract//text()")
abstract_text = " ".join(abstract).strip()
#print(abstract_text) # Test

# Now we extract description, and it's done the exact same way.                                 #
# IT APPEARS SOME SECTIONS ARE EMPTY, MAYBE CREATE A WAY OF OMITTING THEM?                      #
description = root.xpath("//description//text()")
description_text = " ".join(description).strip()
#print(description_text)  # Test

# Claims are the exact same as well.                                                            #
claims = root.xpath("//claims//text()")
claims_text = " ".join(claims).strip()
# Short loop will iterate through text and remove whitespace.
#claims_text = " ".join(
#    t.strip() for t in root.xpath("//claims//text()") if t.strip()
#)
print(claims_text)
'''
