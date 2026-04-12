#!/usr/bin/env bash
gunicorn level_sensor.wsgi:application