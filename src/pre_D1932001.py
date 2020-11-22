#!/usr/bin/env python3

# Copyright (C) 2020 Andrew Trettel
#
# This file is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free Software
# Foundation, either version 3 of the License, or (at your option) any later
# version.
#
# This file is distributed in the hope that it will be useful, but WITHOUT ANY
# WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR
# A PARTICULAR PURPOSE.  See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along with
# this file.  If not, see <https://www.gnu.org/licenses/>.

import csv
import math
import sqlite3
import sheardata as sd
import sys
from uncertainties import ufloat
from uncertainties import unumpy as unp

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