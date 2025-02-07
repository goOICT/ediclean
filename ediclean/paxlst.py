"""
This module checks if a given file or data is valid UN/EDIFACT PAXLST
by checking for the existence of specific segments.
"""
import os
import logging
import re
import sys

logging.basicConfig()
logging.getLogger().setLevel(logging.INFO)


def is_paxlst(data):
    """ Checks if a chunk of data is valid PAXLST """

    # mandatory EDIFACT segments
    edifact = ["UNB", "UNH", "UNT", "UNZ"]

    # mandatory PAXLST segments
    paxlst = ["ATT", "BGM", "CNT", "DOC", "NAD", "NAT", "TDT", "UNE", "UNG"]

    # for logging purposes only
    edifact_segments_missing = []
    for edifact_segment in edifact:
        if edifact_segment not in data:
            edifact_segments_missing.append(edifact_segment)

    paxlst_segments_missing = []
    for paxlst_segment in paxlst:
        if paxlst_segment not in data:
            paxlst_segments_missing.append(paxlst_segment)

    # check if all mandatory EDIFACT segments are present
    if all(x in data for x in edifact):
        # check if all mandatory PAXLST segments are present
        if all(x in data for x in paxlst):
            # attempt to clean PAXLST file
            return True
        else:
            logging.error(
                "Not a valid PAXLST message. Segments missing: %s",
                str(paxlst_segments_missing))
            return False

    else:
        logging.error('Not a valid EDIFACT message. Segments missing: %s',
                      str(edifact_segments_missing))
        return False


def clean(data):
    """ Cleans PAXLST data from unnecessary headers and footers. """
    # trim new lines
    data = data.replace('\n', '').replace('\r', '')

    # trim hex characters
    data = re.sub(r'[^\x00-\x7f]', r'', data)

    if is_paxlst(data):

        # Service String Advice
        service_string_advice = "UNA"

        # Interchange Trailer; end of message segment
        interchange_trailer = "UNZ"

        # length of the SSA string according to PAXLST spec
        service_string_advice_length = 6

        # check if Service String Advice present
        if service_string_advice in data:

            # trim Default Service Characters
            default_service_characters = data[
                data.index(service_string_advice) +
                len(service_string_advice):data.index(service_string_advice) +
                len(service_string_advice) + service_string_advice_length]

            # Segment Terminator
            segment_terminator = default_service_characters[5]

            # beginning of PAXLST message
            # trim everything before SSA string
            data = data[data.index(service_string_advice):]

            # end of PAXLST message
            # the PAXLST message ends after the Segment Terminator or the Interchange Trailer
            # i.e. UNZ...’ <-
            data = data[:data.index(segment_terminator,
                                    data.index(interchange_trailer)) + 1]

            # add newlines to increase readability
            paxlst = data.replace(segment_terminator,
                                  segment_terminator + "\n")

            # logging.info (paxlst)
            return paxlst

        # Service String Advice absent
        else:
            # assume default SSA: ":+.? '"
            segment_terminator = "'"

            # In case the Service String Advice("UNA") is missing,
            # the message starts with the Interchange Header("UNB")
            interchange_header = "UNB"

            data = data[data.index(interchange_header):]

            # end of PAXLST message
            # the PAXLST message ends after the Segment Terminator or the Interchange Trailer
            # i.e. UNZ...’ <-
            data = data[:data.index(segment_terminator,
                                    data.index(interchange_trailer)) + 1]

            # add newlines to increase readability
            paxlst = data.replace(segment_terminator,
                                  segment_terminator + "\n")

            # logging.info (paxlst)
            return paxlst

    else:
        return False


def cleanfile(filename):
    """ Wrapper around the 'clean' function. """

    if os.path.isfile(filename):
        with open(filename, 'r') as file:
            filecontent = file.read()
            return clean(filecontent)
    else:
        logging.error("File does not exist: %s", filename)


def cleandir(source_dir, target_dir):
    """ Cleans all files within source_dir and copies them into target_dir. """

    if not os.path.isdir(source_dir):
        logging.error("Source directory not found: %s", source_dir)
        sys.exit()

    if not os.path.isdir(target_dir):
        logging.error("Target directory not found: %s", source_dir)
        sys.exit()

    for root, dirs, files in os.walk(source_dir):
        for file in sorted(files):
            target_content = cleanfile(os.path.join(root, file))

            if target_content:
                target = open(os.path.join(target_dir, file), "w")
                target.write(target_content)
                target.close()
                logging.info("Cleaned %s", os.path.join(target_dir, file))
            else:
                sys.exit()
