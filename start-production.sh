#!/bin/bash

source env/bin/activate
gunicorn -k uvicorn.workers.UvicornWorker main:app