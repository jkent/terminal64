#!/bin/sh
set -e

if [ ! -e venv ]; then
    python -m venv venv
    venv/bin/python -m pip install -e .
fi

app=$1
shift
venv/bin/$app "$@"
