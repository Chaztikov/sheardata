#!/usr/bin/env python3

# Copyright (C) 2020-2021 Andrew Trettel
#
# SPDX-License-Identifier: MIT

import csv
import math
import sqlite3
import sheardata as sd
import sys

conn   = sqlite3.connect( sys.argv[1] )
cursor = conn.cursor()
cursor.execute( "PRAGMA foreign_keys = ON;" )

flow_class   = sd.BOUNDARY_LAYER_FLOW_CLASS
year         = 1940
study_number = 1

study_identifier = sd.add_study(
    cursor,
    flow_class=flow_class,
    year=year,
    study_number=study_number,
    study_type=sd.EXPERIMENTAL_STUDY_TYPE,
)

sd.add_source( cursor, study_identifier, "SchultzGrunowF+1940+deu+JOUR", 1 )

reynolds_number_typo_note = sd.add_note(
    cursor,
    "../data/{:s}/note_reynolds_number_typo.tex".format( study_identifier ),
)

station_1_outlier_note = sd.add_note(
    cursor,
    "../data/{:s}/note_station_1_outlier.tex".format( study_identifier ),
)

velocity_measurement_technique_note = sd.add_note(
    cursor,
    "../data/{:s}/note_velocity_measurement_technique.tex".format( study_identifier ),
)

conn.commit()
conn.close()
