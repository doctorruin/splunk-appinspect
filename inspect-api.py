import os
import subprocess
import json
import datetime
from flask import Flask, request, jsonify
from werkzeug.utils import secure_filename
from subprocess import PIPE
from waitress import serve

UPLOAD_FOLDER = '/home/splunk/'
ALLOWED_EXTENSIONS = {'tar', 'spl', 'gz'}
d = datetime.datetime.now().strftime("%Y%m%d%H%M%S")

app = Flask(__name__)
app.secret_key = os.urandom(24)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


def allowed_file(name_of_file):
    return '.' in name_of_file and \
           name_of_file.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


# get actual filename for reading and writing
def filename(name_of_file):
    return name_of_file.rsplit('.', 2)[0].lower()


def read_json(inspect_out):
    with open(inspect_out) as f:
        data = json.load(f)
    return data


def check_if_file(requests_file):
    if 'app_package' not in requests_file:
        raise InvalidUsage('No file uploaded', status_code=410)
    file = requests_file['app_package']
    if file.filename == '':
        raise InvalidUsage('Filename is null', status_code=410)
    if file and allowed_file(file.filename):
        return file


def check_args(method_args, command):
    list_cmd = {'groups', 'checks', 'tags', 'version', 'help'}
    inspect_cmd = {'mode', 'included-tags', 'excluded-tags'}
    is_true = 0
    bad_arg = ''
    if method_args:
        for a in method_args:
            if command == 'list':
                if a in list_cmd:
                    is_true += 1
                else:
                    is_true -= 1
                    bad_arg += a + " "
            elif command == 'inspect':
                if a in inspect_cmd:
                    is_true += 1
                else:
                    is_true -= 1
                    bad_arg += a + " "
        if is_true == len(method_args):
            return True
        else:
            raise InvalidUsage('Error: Missing argument \'list-type\': ' + bad_arg, status_code=410)
    raise InvalidUsage('Use appropriate arguments', status_code=410)


def file_read(filename_wout_ext):
    with open(UPLOAD_FOLDER + filename_wout_ext + '_inspect-out_' + str(d) + '.txt') as json_file:
        data = json.load(json_file)
        return data


@app.route('/inspect', methods=['POST'])
def upload_file():
    if request.method == 'POST':
        file = check_if_file(request.files)
        filename_w_ext = secure_filename(file.filename)
        filename_wout_ext = filename(filename_w_ext)
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename_w_ext))
        sub_cmd = ['splunk-appinspect', 'inspect', UPLOAD_FOLDER + filename_w_ext]
        is_mode = request.args.get('mode')
        is_json = request.args.get('json')
        is_included_tags = request.args.getlist('included_tags')
        is_excluded_tags = request.args.getlist('excluded_tags')

        if is_json == 'true':
            sub_cmd.extend(['--output-file', UPLOAD_FOLDER + filename_wout_ext + '_inspect-out_' + str(d) + '.txt',
                            '--data-format', 'json'])
        if is_mode:
            sub_cmd.append('--mode')
            sub_cmd.append(is_mode)
        if is_included_tags:
            sub_cmd.append('--included-tags')
            sub_cmd.extend(is_included_tags)
        if is_excluded_tags:
            sub_cmd.append('--excluded-tags')
            sub_cmd.extend(is_excluded_tags)

        try:
            if is_json == 'true':
                fnull = open(os.devnull, 'w')
                subprocess.call(sub_cmd, stdout=fnull, stderr=fnull)
                data = file_read(filename_wout_ext)
                resp = jsonify(data)
                resp.status_code = 200
            else:
                inspect = subprocess.Popen(sub_cmd, stdout=PIPE, stderr=PIPE)
                (out, err) = inspect.communicate()
                resp = out

        except subprocess.CalledProcessError as e:
            raise InvalidUsage(e, status_code=500)
        return resp
    else:
        raise InvalidUsage('Method must be POST', status_code=410)


@app.route('/list', methods=['GET'])
def appinspect_list():
    if request.method == 'GET':
        if check_args(request.args.getlist('list_type'), 'list'):
            list_args = request.args.getlist('list_type')
            sub_cmd = ['splunk-appinspect', 'list']
            is_included_tags = request.args.getlist('included_tags')
            is_excluded_tags = request.args.getlist('excluded_tags')

            if 'help' in list_args:
                sub_cmd.append('--help')
            else:
                sub_cmd.extend(list_args)

            if is_included_tags:
                sub_cmd.append('--included-tags')
                sub_cmd.extend(request.args.getlist('included_tags'))
            if is_excluded_tags:
                sub_cmd.append('--excluded-tags')
                sub_cmd.extend(request.args.getlist('excluded_tags'))

            inspect = subprocess.Popen(sub_cmd,
                                       stdout=PIPE, stderr=PIPE)
            (out, err) = inspect.communicate()

            return out

    raise InvalidUsage('GET malformed', status_code=410)


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


@app.errorhandler(InvalidUsage)
def handle_invalid_usage(error):
    response = jsonify(error.to_dict())
    response.status_code = error.status_code
    return response


if __name__ == '__main__':
    serve(app, host='0.0.0.0', port=5000)
