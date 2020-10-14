#!/bin/bash
coverage erase && coverage run -m unittest discover && coverage html && coverage report
