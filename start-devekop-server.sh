#!/bin/bash

source env/bin/activate
EXCHANGE_API_VERBOSE=true uvicorn main:app --reload