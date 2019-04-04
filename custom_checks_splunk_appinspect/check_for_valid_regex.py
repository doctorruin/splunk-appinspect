# import splunk_appinspect !!IMPORTANT!!
import splunk_appinspect
import re

# Docstring to explain the check
"""
Check EXTRACT regex for PCRE compile. Des not run extraction tests, 
just for valid PCRE regex.
"""


# Specify Tags associated with check. This check will be included with any of these tags are specified

@splunk_appinspect.tags("appapproval", "regex")
@splunk_appinspect.cert_version(min='1.6.1')  # Specify the version of Splunk AppInspect you're adding to.
def check_for_valid_regex(app, reporter):
    """
    Look for EXTRACT regex in props.conf and make sure they can compile.
    """

    # Check if default directory exists using the splunk appinspect directory_exists method with the app object
    if app.directory_exists('default'):
        # Check file_exists method
        if app.file_exists('default', 'props.conf'):

            # search_for_patters to return tuples that meet certain patterns, in this case the extract line
            prop_file = app.search_for_patterns(['EXTRACT-.+'], basedir="default")

            # iterate over the returned tuples that match EXTRACT if not NULL
            if prop_file:
                # we are setting up to output manual check message once, no matter how many invalid regexs are found
                not_regex = 0
                for e in prop_file:

                    # get group object that has extract pattern
                    extract = e[1].group()

                    # Get [<regex>|<regex> in <src_field>] after the = sign of EXTRACT-<class>=
                    extract_val = extract.rsplit('=', 1)[1]
                    # get regex, will get if there is "in <src_field>"
                    regex = extract_val.rsplit("in", 1)[0]
                    # check if regex is valid
                    is_regex = is_regex_valid(regex)

                    # if regex is not valid or did not exist in the first place
                    if not is_regex:
                        not_regex = 1
                        # Get info from the original tuple, syntax "dir/file:num"
                        extract_info = e[0]
                        # get filename
                        filename = extract_info.rsplit(':', 1)[0]
                        # get line number
                        line_number = extract_info.rsplit(':', 1)[1]

                        # get 'EXTRACT-<class>'
                        extract_prefix = extract.rsplit('=', 1)[0]
                        # get class name
                        extract_class = extract_prefix.rsplit('-', 1)[1]

                        # create message to provide info about invalid regex using values extracted above
                        reporter_output = ("Bad syntax for REGEX. "
                                           " File: {}\n"
                                           " Line: {} \n"
                                           " Class: {} \n"
                                           " Regex: {} ").format(filename,
                                                                 line_number,
                                                                 extract_class,
                                                                 regex)
                        # use reporter object to provide fail status and output info
                        reporter.fail(reporter_output)
                        # also output this type of check requires a human to validate
                        manual_check_message = 'Check regex for syntax errors'
                if not_regex:
                    reporter.manual_check(manual_check_message)

# method to validate regex
# noinspection PyBroadException
def is_regex_valid(regex):
    # if null, then no regex was in EXTRACT-<class>
    if not regex:
        return False
    try:
        re.compile(regex)
        return True
    except:
        return False
