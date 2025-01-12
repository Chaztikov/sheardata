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

flow_class   = sd.DUCT_FLOW_CLASS
year         = 1932
study_number = 1

study_identifier = sd.add_study(
    cursor,
    flow_class=flow_class,
    year=year,
    study_number=study_number,
    study_type=sd.EXPERIMENTAL_STUDY_TYPE,
)

sd.add_source( cursor, study_identifier, "NikuradseJ+1932+deu+JOUR",    1 )
sd.add_source( cursor, study_identifier, "NikuradseJ+1933+deu+JOUR",    1 )
sd.add_source( cursor, study_identifier, "RobertsonJM+1957+eng+CPAPER", 2 )
sd.add_source( cursor, study_identifier, "LindgrenER+1965+eng+RPRT",    2 )
sd.add_source( cursor, study_identifier, "BeattieDRH+1995+eng+CPAPER",  2 )
sd.add_source( cursor, study_identifier, "HagerWH+2008+eng+JOUR",       2 )
sd.add_source( cursor, study_identifier, "LaVioletteM+2017+eng+JOUR",   2 )

conn.commit()
conn.close()
