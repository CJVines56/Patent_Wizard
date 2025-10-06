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
#                                                                                               #

