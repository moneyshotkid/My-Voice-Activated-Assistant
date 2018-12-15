#!/usr/bin/env python3
# Copyright 2017 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Run a recognizer using the Google Assistant Library with button support.

The Google Assistant Library has direct access to the audio API, so this Python
code doesn't need to record audio. Hot word detection "OK, Google" is supported.

It is available for Raspberry Pi 2/3 only; Pi Zero is not supported.
"""

import logging
import platform
import sys
import threading
import subprocess
import requests
import webbrowser
#import smtplib
import time
#import imaplib
#import email
from requests.auth import HTTPDigestAuth
from imap_tools import MailBox

import aiy.assistant.auth_helpers
from aiy.assistant.library import Assistant
import aiy.voicehat
import aiy.audio
from google.assistant.library.event import EventType

ORG_EMAIL   = ""
FROM_EMAIL  = "" + ORG_EMAIL
FROM_PWD    = ""
SMTP_SERVER = ""
SMTP_PORT   = 993
HTTP_USER=""
HTTP_PASS=""
HTTP_URL_PORT=""


logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s:%(name)s:%(message)s"
)


class MyAssistant(object):

    """An assistant that runs in the background.

    The Google Assistant Library event loop blocks the running thread entirely.
    To support the button trigger, we need to run the event loop in a separate
    thread. Otherwise, the on_button_pressed() method will never get a chance to
    be invoked.
    """

    def __init__(self):
        self._task = threading.Thread(target=self._run_task)
        """self._audio= aiy.audio();"""
        self._can_start_conversation = False
        self._assistant = None

    def start(self):
        """Starts the assistant.

        Starts the assistant event loop and begin processing events.
        """
        self._task.start()

    def read_mail(self):
        mailbox = MailBox(SMTP_SERVER)
        mailbox.login(FROM_EMAIL,FROM_PWD)
        frommail=""
        for msg in mailbox.fetch('(RECENT)',10):
            frommail=frommail+str(msg.from_)
        return frommail



    def power_off_pi():
        aiy.audio.say('Good bye!')
        subprocess.call('sudo shutdown now', shell=True)


    def reboot_pi():
        aiy.audio.say('See you in a bit!')
        subprocess.call('sudo reboot', shell=True)


    def say_ip():
        ip_address = subprocess.check_output("hostname -I | cut -d' ' -f1", shell=True)
        aiy.audio.say('My IP address is %s' % ip_address.decode('utf-8'))

    def _run_task(self):
        credentials = aiy.assistant.auth_helpers.get_assistant_credentials()
        with Assistant(credentials) as assistant:
            self._assistant = assistant
            for event in assistant.start():
                self._process_event(event)

    def _process_event(self, event):
        status_ui = aiy.voicehat.get_status_ui()
        if event.type == EventType.ON_START_FINISHED:
            status_ui.status('ready')
            self._can_start_conversation = True
            # Start the voicehat button trigger.
            aiy.voicehat.get_button().on_press(self._on_button_pressed)
            if sys.stdout.isatty():
                print('Say "OK, Google" or press the button, then speak. '
                      'Press Ctrl+C to quit...')

        elif event.type == EventType.ON_CONVERSATION_TURN_STARTED:
            self._can_start_conversation = False
            status_ui.status('listening')

        elif event.type == EventType.ON_RECOGNIZING_SPEECH_FINISHED and event.args:   
            print('You said:', event.args['text'])
            text = event.args['text'].lower()
            if text == 'power off':
                self._assistant.stop_conversation()
                aiy.audio.say('Good bye!')
                subprocess.call('sudo shutdown now', shell=True)
            elif text == 'remote infrared on':
                self._assistant.stop_conversation()
                aiy.audio.say('Turning Remote I R on')
                r = requests.get('http://HTTP_URL_PORT/light1on')
                print(r.status_code)
            elif text == 'read mail':
                self._assistant.stop_conversation()
                email=self.read_mail()
                #aiy.audio.say(email)
                print(email)
            elif text == 'what are my options':
                self._assistant.stop_conversation()
                aiy.audio.say('Your options are, power off, reboot, i p adddress, your master is, remote infrared on, remote infrared off, and play my music. to control your camera you can say, move camera outside, move camera inside, move up, move down, move left, move right, infrared on, infrared off, send camera home ')
            elif text == 'remote infrared off':
                self._assistant.stop_conversation()
                aiy.audio.say('Turning Remote I R off')
                r = requests.get('http://HTTP_URL_PORT/light1off')
                print(r.status_code)
            elif text == 'infrared off':
                self._assistant.stop_conversation()
                aiy.audio.say('Turning Off IR')
                r = requests.get('http://HTTP_URL_PORT/hy-cgi/irctrl.cgi?cmd=setinfrared&infraredstatus=close&cmd=setircutctrl', auth=HTTPDigestAuth(HTTP_USER,HTTP_PASS))
                print(r.status_code)
                #webbrowser.open('http://HTTP_USER:HTTP_PASS@HTTP_URL_PORT/hy-cgi/irctrl.cgi?cmd=setinfrared&infraredstatus=close&cmd=setircutctrl')
            elif text == 'play my music':
                self._assistant.stop_conversation()
                aiy.audio.say('okay this will take a second as i bypass google and play your music')
                webbrowser.open('https://www.youtube.com/watch?v=TpGS9dOlx74&list=PL1BD30F94EB438CD5')
            elif text == 'move camera outside':
                self._assistant.stop_conversation()
                aiy.audio.say('showing you outside')
                r = requests.get('http://HTTP_URL_PORT/hy-cgi/ptz.cgi?cmd=preset&act=goto&number=7',auth=HTTPDigestAuth(HTTP_USER,HTTP_PASS))
                #webbrowser.open('http://HTTP_USER:HTTP_PASS@HTTP_URL_PORT/hy-cgi/ptz.cgi?cmd=preset&act=goto&number=7')
                print(r.status_code)
            elif text == 'move camera inside':
                self._assistant.stop_conversation()
                aiy.audio.say('showing you inside')
                r = requests.get('http://HTTP_URL_PORT/hy-cgi/ptz.cgi?cmd=preset&act=goto&number=1', auth=HTTPDigestAuth(HTTP_USER,HTTP_PASS))
                print(r.status_code)
                #webbrowser.open('http://HTTP_USER:HTTP_PASS@HTTP_URL_PORT/hy-cgi/ptz.cgi?cmd=preset&act=goto&number=1')
##Camera PTZ Control
            elif text == 'move left':
                self._assistant.stop_conversation()
                r = requests.get('http://HTTP_URL_PORT/hy-cgi/ptz.cgi?cmd=ptzctrl&act=left', auth=HTTPDigestAuth(HTTP_USER,HTTP_PASS))
                r = requests.get('http://HTTP_URL_PORT/hy-cgi/ptz.cgi?cmd=ptzctrl&act=stop', auth=HTTPDigestAuth(HTTP_USER,HTTP_PASS))
                print(r.status_code)
                #webbrowser.open('http://HTTP_USER:HTTP_PASS@HTTP_URL_PORT/hy-cgi/ptz.cgi?cmd=preset&act=goto&number=1')  
            elif text == 'move right':
                self._assistant.stop_conversation()
                r = requests.get('http://HTTP_URL_PORT/hy-cgi/ptz.cgi?cmd=ptzctrl&act=right', auth=HTTPDigestAuth(HTTP_USER,HTTP_PASS))
                r = requests.get('http://HTTP_URL_PORT/hy-cgi/ptz.cgi?cmd=ptzctrl&act=stop', auth=HTTPDigestAuth(HTTP_USER,HTTP_PASS))
                print(r.status_code)
                #webbrowser.open('http://HTTP_USER:HTTP_PASS@HTTP_URL_PORT/hy-cgi/ptz.cgi?cmd=preset&act=goto&number=1')  
            elif text == 'move down':
                self._assistant.stop_conversation()
                r = requests.get('http://HTTP_URL_PORT/hy-cgi/ptz.cgi?cmd=ptzctrl&act=down', auth=HTTPDigestAuth(HTTP_USER,HTTP_PASS))
                r = requests.get('http://HTTP_URL_PORT/hy-cgi/ptz.cgi?cmd=ptzctrl&act=stop', auth=HTTPDigestAuth(HTTP_USER,HTTP_PASS))
                print(r.status_code)
                #webbrowser.open('http://HTTP_USER:HTTP_PASS@HTTP_URL_PORT/hy-cgi/ptz.cgi?cmd=preset&act=goto&number=1')  
            elif text == 'move up':
                self._assistant.stop_conversation()
                r = requests.get('http://HTTP_URL_PORT/hy-cgi/ptz.cgi?cmd=ptzctrl&act=up', auth=HTTPDigestAuth(HTTP_USER,HTTP_PASS))
                r = requests.get('http://HTTP_URL_PORT/hy-cgi/ptz.cgi?cmd=ptzctrl&act=stop', auth=HTTPDigestAuth(HTTP_USER,HTTP_PASS))
                print(r.status_code)
                #webbrowser.open('http://HTTP_USER:HTTP_PASS@HTTP_URL_PORT/hy-cgi/ptz.cgi?cmd=preset&act=goto&number=1')
            elif text == 'send camera home':
                self._assistant.stop_conversation()
                r = requests.get('http://HTTP_URL_PORT/hy-cgi/ptz.cgi?cmd=ptzctrl&act=home', auth=HTTPDigestAuth(HTTP_USER,HTTP_PASS))
                r = requests.get('http://HTTP_URL_PORT/hy-cgi/ptz.cgi?cmd=ptzctrl&act=stop', auth=HTTPDigestAuth(HTTP_USER,HTTP_PASS))
                aiy.audio.say('Camera Returned to home position')
                print(r.status_code)
                #webbrowser.open('http://HTTP_USER:HTTP_PASS@HTTP_URL_PORT/hy-cgi/ptz.cgi?cmd=preset&act=goto&number=1')    
            elif text == 'infrared on':
                self._assistant.stop_conversation()
                aiy.audio.say('Turning On IR')
                r = requests.get('http://HTTP_URL_PORT/hy-cgi/irctrl.cgi?cmd=setinfrared&infraredstatus=auto&cmd=setircutctrl&cmd=setirparams&irparams=100', auth=HTTPDigestAuth(HTTP_USER,HTTP_PASS))
                print(r.status_code)
                #webbrowser.open('http://HTTP_USER:HTTP_PASS@HTTP_URL_PORT/hy-cgi/irctrl.cgi?cmd=setinfrared&infraredstatus=auto&cmd=setircutctrl&cmd=setirparams&irparams=100')
            elif text == 'your master':
                self._assistant.stop_conversation()
                aiy.audio.say('Nick you are my master')
                self._assistant.start_conversation()
            elif text == 'reboot':
                self._assistant.stop_conversation()
                aiy.audio.say('See you in a bit!')
                subprocess.call('sudo reboot', shell=True)
            elif text == 'ip address':
                self._assistant.stop_conversation()
                ip_address = subprocess.check_output("hostname -I | cut -d' ' -f1", shell=True)
                aiy.audio.say('My IP address is %s' % ip_address.decode('utf-8'))

        elif event.type == EventType.ON_END_OF_UTTERANCE:
            status_ui.status('thinking')

        elif (event.type == EventType.ON_CONVERSATION_TURN_FINISHED
              or event.type == EventType.ON_CONVERSATION_TURN_TIMEOUT
              or event.type == EventType.ON_NO_RESPONSE):
            status_ui.status('ready')
            self._can_start_conversation = True

        elif event.type == EventType.ON_ASSISTANT_ERROR and event.args and event.args['is_fatal']:
            sys.exit(1)

    def _on_button_pressed(self):
        # Check if we can start a conversation. 'self._can_start_conversation'
        # is False when either:
        # 1. The assistant library is not yet ready; OR
        # 2. The assistant library is already in a conversation.
        if self._can_start_conversation:
            self._assistant.start_conversation()


def main():
    if platform.machine() == 'armv6l':
        print('Cannot run hotword demo on Pi Zero!')
        exit(-1)
    MyAssistant().start()


if __name__ == '__main__':
    main()
