# Splunk-Appinspect w/ API
Splunk Appinspect Docker build with API

### Docker usage:
docker run -d -p 5000:5000 doctorruin/splunk-appinspect

### API usage:

#### List
    GET /list
    
    Implementation Notes:
        This endpoint returns stdout of CLI list. Allows tag filtering. 
    
    Parameters:
    Use any combination of groups, checks, or tags to list the groups, checks, and tags, respectively. Use version to see the version of AppInspect currently running.
    list_type       checks, groups, tags, version , help
    included_tags   tag ref: http://dev.splunk.com/view/appinspect/SP-CAAAFB2
    excluded_tags   tag ref: http://dev.splunk.com/view/appinspect/SP-CAAAFB2
    
    Example Usage:
    curl localhost:5000/list?list_type=version
    
    curl localhost:5000/list?list_type=checks&list_type=groups

    Appinspect Doc:
    http://dev.splunk.com/view/appinspect/SP-CAAAFAM#scr
    
#### Lnspect
    POST /inspect
    
    Implementation Notes:
        This endpoint returns stdout or json of CLI app inspect. Allows tag filtering.
        Splunk AppInspect's inspect command:

        Runs in test mode by default.
        Writes the failures at the end of an inspection.
        Writes a result summary at the end of an inspection.
        Sends all output to stdout unless specified otherwise - json=true
    
    Parameters:
    mode        test(default), precert
    json        true //returns report in json format, otherwise stdout
    included_tags   accepts multiple values. tag ref: http://dev.splunk.com/view/appinspect/SP-CAAAFB2
    excluded_tags   accepts multiple values. tag ref: http://dev.splunk.com/view/appinspect/SP-CAAAFB2
    
    Example Usage:
    curl 'localhost:5000/inspect?mode=precert&included_tags=cloud&included_tags=manual' -F 'app_package@myapp.tar.gz'
    
    curl 'localhost:5000/inspect?json=true' -F 'app_package@myapp.tar.gz'

    Appinspect Doc:
    http://dev.splunk.com/view/appinspect/SP-CAAAFAM#scr
    
### Tags

Tag Reference: http://dev.splunk.com/view/appinspect/SP-CAAAFB2

#### Filtering on multiple tags
You can append additional instances of the --included-tags and --excluded-tags command options to add more filtering.

#### Filtering precedence
The --included-tags option will always take precedence over the --excluded-tags option.

// This will show only groups and checks with the appapproval tag
splunk-appinspect list groups checks --included-tags appapproval --excluded-tags appapproval