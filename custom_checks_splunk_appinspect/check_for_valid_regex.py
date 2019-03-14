import splunk_appinspect
import re

"""
Check EXTRACT regex for PCRE compile. Des not run extraction tests, 
just for valid PCRE regex.
"""


@splunk_appinspect.tags("regex")
@splunk_appinspect.cert_version(min='1.6.1')  # Specify the version of Splunk AppInspect you're adding to.
def check_for_valid_regex(app, reporter):
    """
    Look for EXTRACT regex in props.conf and make sure they can compile.
    """

    if app.directory_exists('default'):
        if app.file_exists('default', 'props.conf'):
            prop_file = app.search_for_patterns(['EXTRACT-.+'], basedir="default")

            if prop_file:
                for e in prop_file:
                    extract = e[1].group()
                    extract_info = e[0]
                    filename = extract_info.rsplit(':', 1)[0]
                    line_number = extract_info.rsplit(':', 1)[1]

                    # extract_line is equal to 'EXTRACT-<class>'
                    extract_line = extract.rsplit('=', 1)[0]
                    extract_class = extract_line.rsplit('-', 1)[1]
                    extract_val = extract.rsplit('=', 1)[1]

                    regex = extract_val.rsplit("in", 1)[0]
                    is_regex = is_regex_valid(regex)

                    if not is_regex:
                        reporter_output = ("Bad syntax for PCRE. "
                                           " File: {}\n"
                                           " Line: {} \n"
                                           " Class: {} \n"
                                           " Regex: {} ").format(filename,
                                                                 line_number,
                                                                 extract_class,
                                                                 regex)

                        reporter.fail(reporter_output)
                        reporter.manual_check('Check regex for syntax errors')


def is_regex_valid(regex):
    if not regex:
        return False
    try:
        re.compile(regex)
        return True
    except:
        return False
