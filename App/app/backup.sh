#!/bin/bash
exec python3 manage.py dumpdata suite --format=json --indent=4 > backup/bd.json