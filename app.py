#!/usr/bin/env python
'''
https://github.com/jboynyc/cmus_app
'''
# =======================================================================
#   This program is free software: you can redistribute it and/or modify
#   it under the terms of the GNU Affero General Public License as
#   published by the Free Software Foundation, either version 3 of the
#   License, or (at your option) any later version.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU Affero General Public License for more details.
# =======================================================================


from optparse import OptionParser
from bottle import abort, post, request, response, route, run, view, static_file
from sh import cmus_remote, ErrorReturnCode_1
from os.path import expanduser
from pathlib import Path

@route('/')
@view('main')
def index():
    return {'host': settings['cmus_host']}


@post('/cmd')
def run_command():
    legal_commands = {'Play': 'player-play',
                      'Stop': 'player-stop',
                      'Next': 'player-next',
                      'Previous': 'player-prev',
                      'Increase Volume': 'vol +1%',
                      'Reduce Volume': 'vol -1%',
                      'Mute': 'vol 0',
                      'Refresh': 'refresh',
                      'Search Next': 'search-next',
                      'Search Prev': 'search-prev',
                      'Increase Seek': 'seek +1m',
                      'Reduce Seek': 'seek -1m',
                      'Toggle Amode': 'toogle aaa_mode',
                      'Toggle Continue': 'toogle continue',
                      'Toggle Play Library': 'toogle play_library',
                      'Toggle Play Sorted': 'toggle play_sorted',
                      'Toggle Repeat': 'toggle repeat',
                      'Toggle Repeat Current': 'toggle repeat_current',
                      'Toggle Show Remaining Time': 'toggle show_remaining_time',
                      'Toggle Shuffle': 'toggle shuffle',
                      'Playlist': 'view playlist',
                      'Tree': 'view tree',
                      'Queue': 'view queue',
                      'Sorted': 'view sorted',
                      'Browser': 'view browser',
                      'Filters': 'view filters',
                      'Settings': 'view Settings',
                      }
    command = request.POST.get('command', default=None)
    if command in legal_commands:
        try:
            out = Remote('-C', legal_commands[command])
            return {'result': out.exit_code, 'output': out.stdout.decode()}
        except ErrorReturnCode_1:
            abort(503, 'Cmus not running.')
    else:
        abort(400, 'Invalid command.')

@route('/playlist')
def get_playlist():
    home = expanduser("~")
    f = open(home+'/.config/cmus/playlist.pl')
    playlist = f.read()
    playlist = playlist.split('\n')
    return_playlist = []

    for play in playlist:
        play = play.split("/")
        play = play[-1]
        return_playlist.append(play)
    total = len(return_playlist)
    total = total - 1
    return {'playlist': return_playlist,
            'total': total
         }
@post('/play-music')
def play_music():
    music = request.POST.get('music', default=None)
    current = Path.cwd()
    try:
        out = Remote('-C', 'player-play '+str(current)+"/music/" + music)
        return {'result': out.exit_code, 'output': out.stdout.decode()}
    except ErrorReturnCode_1:
        abort(503, 'Cmus not running.')

@route('/status')
def get_status():
    try:
        out = Remote('-Q').stdout.decode().split('\n')
        r = {}
        play = out[0].split()[1]
        if play == 'playing':
            r['playing'] = True
        elif play == 'stopped':
            r['playing'] = False
        info = [i for i in out if i.startswith(('tag', 'set'))]
        for i in info:
            k, v = i.split()[1], i.split()[2:]
            if len(v):
                r[k] = ' '.join(v)
        return r
    except ErrorReturnCode_1:
        abort(503, 'Cmus not running.')


@route('/static/<file>')
def static(file):
    response.set_header('Cache-Control', 'max-age=604800')
    return static_file(file, root='static')


@route('/favicon.ico')
def favicon():
    response.set_header('Cache-Control', 'max-age=604800')
    return static_file('favicon.ico', root='static')

if __name__ == '__main__':
    option_parser = OptionParser()
    option_parser.add_option('-c', '--cmus-host', dest='cmus_host',
                             help='Name of cmus host.',
                             default='localhost')
    option_parser.add_option('-w', '--cmus-passwd', dest='cmus_passwd',
                             help='Cmus password.',
                             default='')
    option_parser.add_option('-a', '--app-host', dest='app_host',
                             help='Name of cmus_app host.',
                             default='0.0.0.0')
    option_parser.add_option('-p', '--app-port', dest='app_port',
                             help='Port cmus_app is listening on.',
                             default=8080)

    options, _ = option_parser.parse_args()

    settings = vars(options)
    Remote = cmus_remote.bake(['--server', settings['cmus_host'],
                               '--passwd', settings['cmus_passwd']])

    run(host=settings['app_host'], port=settings['app_port'])

