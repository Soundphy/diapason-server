"""
Diapason RESTful API.
"""
import inspect
from io import BytesIO

from flask import Flask
from flask import abort
from flask import request
from flask import jsonify
from flask import send_file

import numpy
from numpy import linspace,sin,pi,int16
from scipy.io import wavfile

from diapason import note_frequency
from diapason import generate_wav
from diapason.dub import convert_wav


app = Flask('Diapason')


def list_routes(app, starting=''):
    output = []
    for rule in app.url_map.iter_rules():
        if rule.endpoint.startswith('_'):
            continue
        if not str(rule).startswith(starting):
            continue
        output.append(dict(
            name=rule.endpoint,
            rule=rule.rule,
            methods=','.join(rule.methods),
            doc=inspect.getdoc(app.view_functions[rule.endpoint])
        ))
    return output


def error_information(error):
    info = {}
    info['code'] = error.code
    info['name'] = error.name
    if error.response:
        info['response'] = error.response
    if error.description:
        info['description'] = error.description
    return jsonify(error=info), error.code


@app.errorhandler(400)
def handle_400(error):
    return error_information(error)


@app.errorhandler(404)
def handle_404(error):
    return error_information(error)


@app.route('/')
def root():
    versions = dict(v0=request.url+'v0')
    return jsonify(title='Diapason RESTful API', versions=versions)


@app.route('/v0')
def routes():
    return jsonify(routes=list_routes(app, '/v0'))


@app.route('/v0/reverse/<string:query>')
def reverse(query):
    """
    Return the reversed query string provided (for testing purposes).
    """
    return jsonify(reverse=query[::-1])


@app.route('/v0/<note>')
def get(note):
    """
    Get a note.
    """
    coding_format = request.args.get('format', 'wav')
    rate = int(request.args.get('rate', 44100))
    duration = float(request.args.get('duration', 2))
    octave = int(request.args.get('octave', 4))

    mimetype = 'audio/' + coding_format

    if '.' in note:
        note = note.split('.')[0]

    note = note.upper()
    frequency = note_frequency(note, octave)
    note = generate_wav(frequency, duration, rate)

    if coding_format != 'wav':
        note = convert_wav(note, coding_format=coding_format,
                           **request.args.to_dict())

    # valid MP3 file (MPEG version 2).
    # 48 kbps
    # 16000 Hz.

    return send_file(note, mimetype=mimetype,
                     # For developing purposes only
                     add_etags=False, cache_timeout=0)


@app.route('/<path:path>', methods=['GET', 'POST'])
def _catch_all(path):
    abort(404, 'Requested API call does not exist')


if __name__ == '__main__':
    app.run(host='localhost', port=5000, threaded=True, debug=True)