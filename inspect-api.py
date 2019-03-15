import os
import subprocess
import json
import datetime
from flask import Flask, request, jsonify
from werkzeug.utils import secure_filename
from subprocess import PIPE
from waitress import serve

# global variables
UPLOAD_FOLDER = '/home/splunk/'
ALLOWED_EXTENSIONS = {'tar', 'spl', 'gz'}
d = datetime.datetime.now().strftime("%Y%m%d%H%M%S")

# App flask init.
app = Flask(__name__)
app.secret_key = os.urandom(24)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


# function to check for allowed files
def allowed_file(name_of_file):
    # extracting file type and checking against allowed files list
    return '.' in name_of_file and \
           name_of_file.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


# get actual filename for reading and writing
def filename(name_of_file):
    return name_of_file.rsplit('.', 2)[0].lower()


# check to make sure requests includes a valid uploaded file
def check_if_file(requests_file):
    if 'app_package' not in requests_file:
        raise InvalidUsage('No file uploaded', status_code=410)
    file = requests_file['app_package']
    if file.filename == '':
        raise InvalidUsage('Filename is null', status_code=410)
    if file and allowed_file(file.filename):
        return file


# function to check if args are valid cor command, and if not create Invalid Usage message
def check_args(method_args, command):
    # valid list command option
    list_cmd = ['groups', 'checks', 'tags']
    # valid inspect command options
    inspect_cmd = ['mode', 'included_tags', 'excluded_tags', 'json']
    # instantiate vars
    is_true = 0
    bad_arg = ''
    valid_args = None
    if method_args:
        for a in method_args:
            if command == 'list':
                if a in list_cmd:
                    is_true += 1
                else:
                    is_true -= 1
                    bad_arg += a + " "
                    valid_args = list_cmd
            elif command == 'inspect':
                if a in inspect_cmd:
                    is_true += 1
                else:
                    is_true -= 1
                    bad_arg += a + " "
                    valid_args = inspect_cmd
        if is_true == len(method_args):
            return True
        else:
            raise InvalidUsage('Error: invalid arguments: ' + bad_arg + ' | valid args are: ' + json.dumps(valid_args),
                               status_code=410)
    raise InvalidUsage('Use appropriate arguments', status_code=410)


# read file from os and load as json
def file_read(filename_wout_ext):
    with open(UPLOAD_FOLDER + filename_wout_ext + '_inspect-out_' + str(d) + '.txt') as json_file:
        data = json.load(json_file)
        return data


# run subprocess to interact with splunk-appinspect
def return_subprocess(sub_cmd, proc_type):
    if proc_type == 'popen':
        sub_proc = subprocess.Popen(sub_cmd, stdout=PIPE, stderr=PIPE)
        (out, err) = sub_proc.communicate()
        return out
    elif proc_type == 'call':
        fnull = open(os.devnull, 'w')
        subprocess.call(sub_cmd, stdout=fnull, stderr=fnull)


class InvalidUsage(Exception):
    status_code = 400

    def __init__(self, message, status_code=None, payload=None):
        Exception.__init__(self)
        self.message = message
        if status_code is not None:
            self.status_code = status_code
        self.payload = payload

    def to_dict(self):
        rv = dict(self.payload or ())
        rv['message'] = self.message
        return rv


class Subcmd:

    def __init__(self, ext=None):
        cmd = ['splunk-appinspect']

        if not ext:
            raise ValueError('Specify a splunk-appinspect command')
        self.cmd = cmd
        self.cmd.extend(ext)

    def extend(self, extendcmd):
        self.cmd.extend(extendcmd)


@app.route('/test', methods=['GET'])
def test_api():
    if request.method == 'GET':
        sub_cmd = Subcmd(['list'])
        sub_cmd.extend(['checks'])
        return json.dumps(sub_cmd.cmd)


@app.route('/list', methods=['GET'])
def appinspect_list():
    if request.method == 'GET':
        # get arguements for list command
        list_args = request.args.getlist('list_type')
        # check to make sure arguments are valid
        if check_args(list_args, 'list'):
            is_included_tags = request.args.getlist('included_tags')
            is_excluded_tags = request.args.getlist('excluded_tags')

            sub_cmd = Subcmd(['list'])

            # extend sub_cmd if args are present
            if list_args:
                sub_cmd.extend(list_args)
            if is_included_tags:
                sub_cmd.extend(['--included-tags'])
                sub_cmd.extend(is_included_tags)
            if is_excluded_tags:
                sub_cmd.extend(['--excluded-tags'])
                sub_cmd.extend([is_excluded_tags])

            try:
                # run subprocess with args and return them
                cmd_out = return_subprocess(sub_cmd.cmd, 'popen')
            except subprocess.CalledProcessError as e:
                raise InvalidUsage(e, status_code=500)

            return cmd_out

    raise InvalidUsage('GET malformed', status_code=410)


@app.route('/inspect', methods=['POST'])
def upload_file():
    if request.method == 'POST':
        # check if requests file is is uploaded
        file = check_if_file(request.files)
        # secure the file
        filename_w_ext = secure_filename(file.filename)
        # get filename without extension
        filename_wout_ext = filename(filename_w_ext)
        # save the file to the container
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename_w_ext))

        # create subcmd obj
        sub_cmd = Subcmd(['inspect'])
        # add the file to be inspected to teh cmd
        sub_cmd.extend([UPLOAD_FOLDER + filename_w_ext])

        inspect_list = []

        # create inspect list from different args that inspect can take
        for arg in request.args:
            inspect_list.append(arg)

        # check to make sure args are valid
        if inspect_list:
            if check_args(inspect_list, 'inspect'):

                is_mode = request.args.get('mode')
                is_json = request.args.get('json')
                is_included_tags = request.args.getlist('included_tags')
                is_excluded_tags = request.args.getlist('excluded_tags')

                # if args exist, extend sub_cmd with appropriate flags
                if is_json == 'true':
                    sub_cmd.extend(['--output-file', UPLOAD_FOLDER + filename_wout_ext + '_inspect-out_' + str(d) + '.txt',
                                    '--data-format', 'json'])
                if is_mode:
                    sub_cmd.extend(['--mode'])
                    sub_cmd.extend([is_mode])
                if is_included_tags:
                    sub_cmd.extend(['--included-tags'])
                    sub_cmd.extend(is_included_tags)
                if is_excluded_tags:
                    sub_cmd.extend(['--excluded-tags'])
                    sub_cmd.extend(is_excluded_tags)

                # add custom check directory to include in splunk-appinspect
                sub_cmd.extend(['--custom-checks-dir', UPLOAD_FOLDER + 'custom_checks_splunk_appinspect/'])

                # try subprocess cmd
                try:
                    if is_json == 'true':
                        return_subprocess(sub_cmd.cmd, 'call')
                        data = file_read(filename_wout_ext)
                        resp = jsonify(data)
                        resp.status_code = 200
                    else:
                        inspect = return_subprocess(sub_cmd.cmd, 'popen')
                        resp = inspect

                except subprocess.CalledProcessError as e:
                    raise InvalidUsage(e, status_code=500)
                return resp
        else:
            inspect = return_subprocess(sub_cmd.cmd, 'popen')
            resp = inspect
            return resp
    else:
        raise InvalidUsage('Method must be POST', status_code=410)


@app.route('/version', methods=['GET'])
def appinspect_version():
    if request.method == 'GET':
        sub_cmd = Subcmd(['list'])
        sub_cmd.extend(['version'])
        inspect = return_subprocess(sub_cmd.cmd, 'popen')
        return inspect


@app.errorhandler(InvalidUsage)
def handle_invalid_usage(error):
    response = jsonify(error.to_dict())
    response.status_code = error.status_code
    return response


if __name__ == '__main__':
    serve(app, host='0.0.0.0', port=5000)
