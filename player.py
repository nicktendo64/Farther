import pafy
from omxplayer.player import OMXPlayer, OMXPlayerDeadError
from interval import *
import urllib.request
import json


STATUS_URL = "http://dabney.caltech.edu:27036/status"
VIDEO = False # TODO: auto-detect if an HDMI is plugged in

player = None
stop_time = 0

url_cache = {}
def get_player_url(id):
    if id not in url_cache:
        video = pafy.new("https://youtube.com/watch?v=" + id)
        if VIDEO:
            target = video.getbest()
        else:
            target = video.getbestaudio()
        url_cache[id] = target.url
    return url_cache[id]

def prep_queue():
    f = urllib.request.urlopen(STATUS_URL)
    data = json.load(f)
    to_download = set(data["queue"])
    if data.get("current") is not None:
        to_download.add(data["current"])
    for id in to_download:
        get_player_url(id) # ensure we have a player url for everybody in the queue
set_interval(prep_queue, 10)

def play(id, start_time=0):
    print("play requested for {}, starting at {}".format(id, start_time))

    play_url = get_player_url(id)

    args = ["-o", "both"] if VIDEO else ["-o", "local"]
    if start_time != 0:
        seconds = start_time
        hours = seconds // 3600
        seconds -= 3600 * hours
        minutes = seconds // 60
        seconds -= 60 * minutes
        timestamp = "{}:{}:{}".format(hours, minutes, seconds)
        args += ["--pos", timestamp]

    global player
    if player is None:
        player = OMXPlayer(play_url, args=args)

def stop():
    global player
    global stop_time

    if player is not None:
        try:
            stop_time = player.position()
        except OMXPlayerDeadError:
            stop_time = 0

        tmp = player
        player = None
        tmp.quit() # mark player as dead before we block on quitting it

def stop_if_done():
    if player is None:
        return False
    elif player._process is None or player._process.poll() is not None:
        # TODO: this seems to be the how OMXPlayer internally detects whether a
        # player is done, but a try-catech may work better
        stop()
        return True
    return False

def get_time():
    if player is None:
        return stop_time
    else:
        return player.position()
