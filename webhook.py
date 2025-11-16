#!/usr/bin/env python
# -*- coding: utf-8 -*-
# webhook.py

import requests
import json
import config
import database
import discord

class Webhook:

    def __init__(self, url):
        self.url = url

    def send_message(self, message):
        requests.post(self.url, data=json.dumps({"content": message}), headers={"Content-Type": "application/json"})
