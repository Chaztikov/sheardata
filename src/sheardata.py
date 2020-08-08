#!/usr/bin/env python3

# Copyright (C) 2020 Andrew Trettel
# 
# This file is licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.  You may
# obtain a copy of the License at <http://www.apache.org/licenses/LICENSE-2.0>.
# 
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.  See the
# License for the specific language governing permissions and limitations under
# the License.

import sqlite3

EXPERIMENTAL_DATA_TYPE = "E"
NUMERICAL_DATA_TYPE    = "N"

BOUNDARY_LAYER_CLASS     = "B"
WALL_BOUNDED_FLOW_CLASS  = "C"
DUCT_FLOW_CLASS          = "D"
EXTERNAL_FLOW_CLASS      = "E"
FREE_SHEAR_FLOW_CLASS    = "F"
ISOTROPIC_FLOW_CLASS     = "G"
HOMOGENEOUS_FLOW_CLASS   = "H"
INTERNAL_FLOW_CLASS      = "I"
FREE_JET_CLASS           = "J"
WALL_JET_CLASS           = "K"
MIXING_LAYER_CLASS       = "M"
INHOMOGENEOUS_FLOW_CLASS = "N"
RELATIVE_MOTION_CLASS    = "R"
SHEAR_LAYER_CLASS        = "S"
FLOW_CLASS               = "U"
WAKE_CLASS               = "W"

SOLID_PHASE  = "S"
LIQUID_PHASE = "L"
GAS_PHASE    = "G"
PLASMA_PHASE = "P"
MULTIPHASE   = "M"

AIR_WORKING_FLUID   = "132259-10-0"
WATER_WORKING_FLUID =   "7732-18-5"

RECTANGULAR_COORDINATES = "XYZ"

ELLIPTICAL_GEOMETRY = "E"
POLYGONAL_GEOMETRY  = "P"

LAMINAR_REGIME      = "L"
TRANSITIONAL_REGIME = "U"
TURBULENT_REGIME    = "T"

_DEFAULT_PROFILE_IDENTIFIER = "S9999001001001"

_DISCRETE_GLOBALS_TABLE       =      "discrete_globals"
_DIMENSIONAL_GLOBALS_TABLE    =   "dimensional_globals"
_DIMENSIONLESS_GLOBALS_TABLE  = "dimensionless_globals"
_DIMENSIONLESS_PROFILES_TABLE = "dimensionless_profiles"

_UNWEIGHTED_PREFIX       = "uw_"
_DENSITY_WEIGHTED_PREFIX = "dw_"
_VALUE_POSTFIX           = "_n"
_UNCERTAINTY_POSTFIX     = "_s"

def identify_case( flow_class, year, case_number, readable=False ):
    separator = ""
    if ( readable ):
        separator = "-"

    return "{:1s}{:s}{:4d}{:s}{:3d}".format(
        str(flow_class),
        str(separator),
        int(year),
        str(separator),
        int(case_number),
    ).replace(" ","0")

def identify_series( flow_class, year, case_number, series_number, \
                     readable=False ):
    separator = ""
    if ( readable ):
        separator = "-"

    return "{:s}{:s}{:3d}".format(
        identify_case( flow_class, year, case_number, readable=readable, ),
        str(separator),
        int(series_number),
    ).replace(" ","0")

def identify_profile( flow_class, year, case_number, series_number, \
                      profile_number, readable=False ):
    separator = ""
    if ( readable ):
        separator = "-"

    return "{:s}{:s}{:3d}".format(
        identify_series(
            flow_class, year, case_number, series_number, readable=readable,
        ),
        str(separator),
        int(profile_number),
    ).replace(" ","0")

def identify_point( flow_class, year, case_number, series_number, \
                    profile_number, point_number, readable=False ):
    separator = ""
    if ( readable ):
        separator = "-"

    return "{:s}{:s}{:4d}".format(
        identify_profile(
            flow_class, year, case_number, series_number, profile_number, \
            readable=readable,
        ),
        str(separator),
        int(point_number),
    ).replace(" ","0")

def sanitize_identifier( identifier ):
    return identifier.replace("-","")

class ShearLayer:
    _database           = None
    _profile_identifier = None

    def __repr__( self ):
        return self.profile_identifier( readable=False )

    def __str__( self ):
        return self.profile_identifier( readable=True )

    def _connection( self ):
        connection = sqlite3.connect( self._database )
        cursor = connection.cursor()
        return connection, cursor

    def _table_exists( self, table ):
        connection, cursor = self._connection()

        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
            ( str(table), ),
        )
        answer = cursor.fetchone()
        connection.close()
        if ( answer == None ):
            return False
        else:
            return True

    def _table_and_variable_exists( self, table, variable ):
        if ( self._table_exists(table) ):
            connection, cursor = self._connection()
            cursor.execute(
                "PRAGMA table_info("+table+")",
            )
            for column in cursor.fetchall():
                if ( variable == column[1] ):
                    connection.close()
                    return True
            connection.close()
        return False

    def _set_integer( self, table, variable, value ):
        assert( self._table_and_variable_exists(table,variable) )
        connection, cursor = self._connection()
        cursor.execute(
            "UPDATE "+table+" SET "+variable+"=? WHERE profile_identifier=?",
            ( int(value), self._profile_identifier, ),
        )
        connection.commit()
        connection.close()

    def _get_integer( self, table, variable ):
        assert( self._table_and_variable_exists(table,variable) )
        connection, cursor = self._connection()
        cursor.execute(
            "SELECT "+variable+" FROM "+table+" WHERE profile_identifier=?",
            ( self._profile_identifier, ),
        )
        answer = cursor.fetchone()[0]
        connection.close()
        if ( answer == None ):
            return answer
        else:
            return int(answer)

    def _set_string( self, table, variable, value ):
        assert( self._table_and_variable_exists(table,variable) )
        connection, cursor = self._connection()
        cursor.execute(
            "UPDATE "+table+" SET "+variable+"=? WHERE profile_identifier=?",
            ( str(value), self._profile_identifier, ),
        )
        connection.commit()
        connection.close()

    def _get_string( self, table, variable ):
        assert( self._table_and_variable_exists(table,variable) )
        connection, cursor = self._connection()
        cursor.execute(
            "SELECT "+variable+" FROM "+table+" WHERE profile_identifier=?",
            ( self._profile_identifier, ),
        )
        answer = cursor.fetchone()[0]
        connection.close()
        if ( answer == None ):
            return answer
        else:
            return str(answer)

    def case_identifier( self, readable=False ):
        if ( readable ):
            return identify_case(
                self.flow_class(),
                self.year(),
                self.case_number(),
                readable=True,
            )
        else:
            return self._get_string(
                _DISCRETE_GLOBALS_TABLE,
                "case_identifier",
            )

    def set_case_identifier( self, case_identifier ):
        self._set_string(
            _DISCRETE_GLOBALS_TABLE,
            "case_identifier",
            case_identifier,
        )

    def case_number( self ):
        return self._get_integer(
            _DISCRETE_GLOBALS_TABLE,
            "case_number",
        )

    def set_case_number( self, case_number ):
        self._set_integer(
            _DISCRETE_GLOBALS_TABLE,
            "case_number",
            case_number,
        )

    def coordinate_system( self ):
        return self._get_string(
            _DISCRETE_GLOBALS_TABLE,
            "coordinate_system",
        )

    def set_coordinate_system( self, coordinate_system ):
        self._set_string(
            _DISCRETE_GLOBALS_TABLE,
            "coordinate_system",
            coordinate_system,
        )

    def data_type( self ):
        return self._get_string(
            _DISCRETE_GLOBALS_TABLE,
            "data_type",
        )

    def set_data_type( self, data_type ):
        self._set_string(
            _DISCRETE_GLOBALS_TABLE,
            "data_type",
            data_type,
        )

    def flow_class( self ):
        return self._get_string(
            _DISCRETE_GLOBALS_TABLE,
            "flow_class",
        )

    def set_flow_class( self, flow_class ):
        self._set_string(
            _DISCRETE_GLOBALS_TABLE,
            "flow_class",
            flow_class,
        )

    def number_of_dimensions( self ):
        return self._get_integer(
            _DISCRETE_GLOBALS_TABLE,
            "number_of_dimensions",
        )

    def set_number_of_dimensions( self, number_of_dimensions ):
        self._set_integer(
            _DISCRETE_GLOBALS_TABLE,
            "number_of_dimensions",
            number_of_dimensions,
        )

    def number_of_points( self ):
        return self._get_integer(
            _DISCRETE_GLOBALS_TABLE,
            "number_of_points",
        )

    def set_number_of_points( self, number_of_points ):
        self._set_integer(
            _DISCRETE_GLOBALS_TABLE,
            "number_of_points",
            number_of_points,
        )

    def originators_identifier( self ):
        return self._get_string(
            _DISCRETE_GLOBALS_TABLE,
            "originators_identifier",
        )

    def set_originators_identifier( self, originators_identifier ):
        self._set_string(
            _DISCRETE_GLOBALS_TABLE,
            "originators_identifier",
            originators_identifier,
        )

    def profile_identifier( self, readable=False ):
        if ( readable ):
            return identify_profile(
                self.flow_class(),
                self.year(),
                self.case_number(),
                self.series_number(),
                self.profile_number(),
                readable=True,
            )
        else:
            return self._profile_identifier

    def profile_number( self ):
        return self._get_integer(
            _DISCRETE_GLOBALS_TABLE,
            "profile_number",
        )

    def set_profile_number( self, profile_number ):
        self._set_integer(
            _DISCRETE_GLOBALS_TABLE,
            "profile_number",
            profile_number,
        )

    def regime( self ):
        return self._get_string(
            _DISCRETE_GLOBALS_TABLE,
            "regime",
        )

    def set_regime( self, regime ):
        self._set_string(
            _DISCRETE_GLOBALS_TABLE,
            "regime",
            regime,
        )

    def series_identifier( self, readable=False ):
        if ( readable ):
            return identify_series(
                self.flow_class(),
                self.year(),
                self.case_number(),
                self.series_number(),
                readable=True,
            )
        else:
            return self._get_string(
                _DISCRETE_GLOBALS_TABLE,
                "series_identifier",
            )

    def set_series_identifier( self, series_identifier ):
        self._set_string(
            _DISCRETE_GLOBALS_TABLE,
            "series_identifier",
            series_identifier,
        )

    def series_number( self ):
        return self._get_integer(
            _DISCRETE_GLOBALS_TABLE,
            "series_number",
        )

    def set_series_number( self, series_number ):
        self._set_integer(
            _DISCRETE_GLOBALS_TABLE,
            "series_number",
            series_number,
        )

    # Stations
    #
    # These functions return profile identifiers.  The function to set the
    # stations accepts both profile identifiers and shear layer objects.
    #
    # TODO: add option to selectors for readable output.
    def previous_streamwise_station( self ):
        return self._get_string(
            _DISCRETE_GLOBALS_TABLE,
            "previous_streamwise_station",
        )

    def next_streamwise_station( self ):
        return self._get_string(
            _DISCRETE_GLOBALS_TABLE,
            "next_streamwise_station",
        )

    def previous_spanwise_station( self ):
        return self._get_string(
            _DISCRETE_GLOBALS_TABLE,
            "previous_spanwise_station",
        )

    def next_spanwise_station( self ):
        return self._get_string(
            _DISCRETE_GLOBALS_TABLE,
            "next_spanwise_station",
        )

    # TODO: This function should check to ensure that a profile marked as the
    # previous station has the current profile as its next station.
    def set_stations( self,
                      previous_streamwise=None,
                      next_streamwise=None,
                      previous_spanwise=None,
                      next_spanwise=None, ):
        if ( previous_streamwise != None ):
            self._set_string(
                _DISCRETE_GLOBALS_TABLE,
                "previous_streamwise_station",
                sanitize_identifier( str(previous_streamwise) ),
            )

        if ( next_streamwise != None ):
            self._set_string(
                _DISCRETE_GLOBALS_TABLE,
                "next_streamwise_station",
                sanitize_identifier( str(next_streamwise) ),
            )

        if ( previous_spanwise != None ):
            self._set_string(
                _DISCRETE_GLOBALS_TABLE,
                "previous_spanwise_station",
                sanitize_identifier( str(previous_spanwise) ),
            )

        if ( next_spanwise != None ):
            self._set_string(
                _DISCRETE_GLOBALS_TABLE,
                "next_spanwise_station",
                sanitize_identifier( str(next_spanwise) ),
            )

    def working_fluid( self ):
        return self._get_string(
            _DISCRETE_GLOBALS_TABLE,
            "working_fluid",
        )

    def working_fluid_phase( self ):
        return self._get_string(
            _DISCRETE_GLOBALS_TABLE,
            "working_fluid_phase",
        )

    def set_working_fluid( self, fluid, phase=GAS_PHASE ):
        self._set_string(
            _DISCRETE_GLOBALS_TABLE,
            "working_fluid",
            fluid,
        )

        self._set_string(
            _DISCRETE_GLOBALS_TABLE,
            "working_fluid_phase",
            phase,
        )

    def year( self ):
        return self._get_integer(
            _DISCRETE_GLOBALS_TABLE,
            "year",
        )

    def set_year( self, year ):
        self._set_integer(
            _DISCRETE_GLOBALS_TABLE,
            "year",
            year,
        )

    def __init__( self,                             \
                  database,                         \
                  profile_identifier=None,          \
                  flow_class=SHEAR_LAYER_CLASS,     \
                  year=None,                        \
                  case_number=None,                 \
                  series_number=None,               \
                  profile_number=None,              \
                  data_type=EXPERIMENTAL_DATA_TYPE, \
                  number_of_points=0,               \
                  number_of_dimensions=2, ):
        self._database = database
        if ( profile_identifier == None and case_number != None ):
            self._profile_identifier = identify_profile(
                flow_class,
                year,
                case_number, 
                series_number,
                profile_number,
                readable=False,
            )

            connection = sqlite3.connect( self._database )
            cursor = connection.cursor()

            cursor.execute(
            """
            SELECT profile_identifier FROM discrete_globals WHERE profile_identifier=?
            LIMIT 1
            """,
            ( self._profile_identifier, ) )

            if ( cursor.fetchone() == None ):
                cursor.execute( "INSERT INTO discrete_globals DEFAULT VALUES" )

                cursor.execute(
                """
                UPDATE discrete_globals SET profile_identifier=?
                WHERE profile_identifier=?
                """,
                (
                    self._profile_identifier,
                    _DEFAULT_PROFILE_IDENTIFIER,
                )
                )

                connection.commit()
                cursor.close()
                connection.close()

                self.set_flow_class( flow_class )
                self.set_year( year )
                self.set_case_number( case_number )
                self.set_series_number( series_number )
                self.set_profile_number( profile_number )
                self.set_data_type( data_type )
                self.set_number_of_points( number_of_points )
                self.set_number_of_dimensions( number_of_dimensions )

                self.set_case_identifier(
                    identify_case(
                        self.flow_class(),
                        self.year(),
                        self.case_number(),
                        readable=False,
                    ),
                )
                self.set_series_identifier(
                    identify_series(
                        self.flow_class(),
                        self.year(),
                        self.case_number(),
                        self.series_number(),
                        readable=False,
                    ),
                )
        elif ( profile_identifier != None ):
            self._profile_identifier = sanitize_identifier(profile_identifier)

class FreeShearFlow(ShearLayer):
    def __init__( self,                             \
                  database,                         \
                  profile_identifier=None,          \
                  flow_class=FREE_SHEAR_FLOW_CLASS, \
                  year=None,                        \
                  case_number=None,                 \
                  series_number=None,               \
                  profile_number=None,              \
                  data_type=EXPERIMENTAL_DATA_TYPE, \
                  number_of_points=0,               \
                  number_of_dimensions=2, ):
        super().__init__( database,                                  \
                          profile_identifier=profile_identifier,     \
                          flow_class=flow_class,                     \
                          year=year,                                 \
                          case_number=case_number,                   \
                          series_number=series_number,               \
                          profile_number=profile_number,             \
                          data_type=data_type,                       \
                          number_of_points=number_of_points,         \
                          number_of_dimensions=number_of_dimensions, )

class WallBoundedFlow(ShearLayer):
    def __init__( self,                               \
                  database,                           \
                  profile_identifier=None,            \
                  flow_class=WALL_BOUNDED_FLOW_CLASS, \
                  year=None,                          \
                  case_number=None,                   \
                  series_number=None,                 \
                  profile_number=None,                \
                  data_type=EXPERIMENTAL_DATA_TYPE,   \
                  number_of_points=0,                 \
                  number_of_dimensions=2, ):
        super().__init__( database,                                  \
                          profile_identifier=profile_identifier,     \
                          flow_class=flow_class,                     \
                          year=year,                                 \
                          case_number=case_number,                   \
                          series_number=series_number,               \
                          profile_number=profile_number,             \
                          data_type=data_type,                       \
                          number_of_points=number_of_points,         \
                          number_of_dimensions=number_of_dimensions, )

class FreeJet(FreeShearFlow):
    def __init__( database,                         \
                  cursor,                           \
                  profile_identifier=None,          \
                  flow_class=FREE_JET_CLASS,        \
                  year=None,                        \
                  case_number=None,                 \
                  series_number=None,               \
                  profile_number=None,              \
                  data_type=EXPERIMENTAL_DATA_TYPE, \
                  number_of_points=0,               \
                  number_of_dimensions=2, ):
        super().__init__( database,                                  \
                          profile_identifier=profile_identifier,     \
                          flow_class=flow_class,                     \
                          year=year,                                 \
                          case_number=case_number,                   \
                          series_number=series_number,               \
                          profile_number=profile_number,             \
                          data_type=data_type,                       \
                          number_of_points=number_of_points,         \
                          number_of_dimensions=number_of_dimensions, )

class MixingLayer(FreeShearFlow):
    def __init__( self,                             \
                  database,                         \
                  profile_identifier=None,          \
                  flow_class=MIXING_LAYER_CLASS,    \
                  year=None,                        \
                  case_number=None,                 \
                  series_number=None,               \
                  profile_number=None,              \
                  data_type=EXPERIMENTAL_DATA_TYPE, \
                  number_of_points=0,               \
                  number_of_dimensions=2, ):
        super().__init__( database,                                  \
                          profile_identifier=profile_identifier,     \
                          flow_class=flow_class,                     \
                          year=year,                                 \
                          case_number=case_number,                   \
                          series_number=series_number,               \
                          profile_number=profile_number,             \
                          data_type=data_type,                       \
                          number_of_points=number_of_points,         \
                          number_of_dimensions=number_of_dimensions, )

class Wake(FreeShearFlow):
    def __init__( self,                             \
                  database,                         \
                  profile_identifier=None,          \
                  flow_class=WAKE_CLASS,            \
                  year=None,                        \
                  case_number=None,                 \
                  series_number=None,               \
                  profile_number=None,              \
                  data_type=EXPERIMENTAL_DATA_TYPE, \
                  number_of_points=0,               \
                  number_of_dimensions=2, ):
        super().__init__( database,                                  \
                          profile_identifier=profile_identifier,     \
                          flow_class=flow_class,                     \
                          year=year,                                 \
                          case_number=case_number,                   \
                          series_number=series_number,               \
                          profile_number=profile_number,             \
                          data_type=data_type,                       \
                          number_of_points=number_of_points,         \
                          number_of_dimensions=number_of_dimensions, )

class ExternalFlow(WallBoundedFlow):
    def __init__( self,                             \
                  database,                         \
                  profile_identifier=None,          \
                  flow_class=EXTERNAL_FLOW_CLASS,   \
                  year=None,                        \
                  case_number=None,                 \
                  series_number=None,               \
                  profile_number=None,              \
                  data_type=EXPERIMENTAL_DATA_TYPE, \
                  number_of_points=0,               \
                  number_of_dimensions=2, ):
        super().__init__( database,                                  \
                          profile_identifier=profile_identifier,     \
                          flow_class=flow_class,                     \
                          year=year,                                 \
                          case_number=case_number,                   \
                          series_number=series_number,               \
                          profile_number=profile_number,             \
                          data_type=data_type,                       \
                          number_of_points=number_of_points,         \
                          number_of_dimensions=number_of_dimensions, )

class InternalFlow(WallBoundedFlow):
    def geometry( self ):
        return self._get_string(
            _DISCRETE_GLOBALS_TABLE,
            "geometry",
        )

    def number_of_sides( self ):
        return self._get_integer(
            _DISCRETE_GLOBALS_TABLE,
            "number_of_sides",
        )

    def set_geometry( self, geometry, number_of_sides=4 ):
        self._set_string(
            _DISCRETE_GLOBALS_TABLE,
            "geometry",
            geometry,
        )

        if ( geometry == POLYGONAL_GEOMETRY ):
            self._set_integer(
                _DISCRETE_GLOBALS_TABLE,
                "number_of_sides",
                number_of_sides,
            )

    def __init__( self,                             \
                  database,                         \
                  profile_identifier=None,          \
                  flow_class=INTERNAL_FLOW_CLASS,   \
                  year=None,                        \
                  case_number=None,                 \
                  series_number=None,               \
                  profile_number=None,              \
                  data_type=EXPERIMENTAL_DATA_TYPE, \
                  number_of_points=0,               \
                  number_of_dimensions=2, ):
        super().__init__( database,                                  \
                          profile_identifier=profile_identifier,     \
                          flow_class=flow_class,                     \
                          year=year,                                 \
                          case_number=case_number,                   \
                          series_number=series_number,               \
                          profile_number=profile_number,             \
                          data_type=data_type,                       \
                          number_of_points=number_of_points,         \
                          number_of_dimensions=number_of_dimensions, )


class BoundaryLayer(ExternalFlow):
    def __init__( self,                             \
                  database,                         \
                  profile_identifier=None,          \
                  flow_class=BOUNDARY_LAYER_CLASS,  \
                  year=None,                        \
                  case_number=None,                 \
                  series_number=None,               \
                  profile_number=None,              \
                  data_type=EXPERIMENTAL_DATA_TYPE, \
                  number_of_points=0,               \
                  number_of_dimensions=2, ):
        super().__init__( database,                                  \
                          profile_identifier=profile_identifier,     \
                          flow_class=flow_class,                     \
                          year=year,                                 \
                          case_number=case_number,                   \
                          series_number=series_number,               \
                          profile_number=profile_number,             \
                          data_type=data_type,                       \
                          number_of_points=number_of_points,         \
                          number_of_dimensions=number_of_dimensions, )

class WallJet(ExternalFlow):
    def __init__( self,                             \
                  database,                         \
                  profile_identifier=None,          \
                  flow_class=WALL_JET_CLASS,        \
                  year=None,                        \
                  case_number=None,                 \
                  series_number=None,               \
                  profile_number=None,              \
                  data_type=EXPERIMENTAL_DATA_TYPE, \
                  number_of_points=0,               \
                  number_of_dimensions=2, ):
        super().__init__( database,                                  \
                          profile_identifier=profile_identifier,     \
                          flow_class=flow_class,                     \
                          year=year,                                 \
                          case_number=case_number,                   \
                          series_number=series_number,               \
                          profile_number=profile_number,             \
                          data_type=data_type,                       \
                          number_of_points=number_of_points,         \
                          number_of_dimensions=number_of_dimensions, )

class DuctFlow(InternalFlow):
    def __init__( self,                             \
                  database,                         \
                  profile_identifier=None,          \
                  flow_class=DUCT_FLOW_CLASS,       \
                  year=None,                        \
                  case_number=None,                 \
                  series_number=None,               \
                  profile_number=None,              \
                  data_type=EXPERIMENTAL_DATA_TYPE, \
                  number_of_points=0,               \
                  number_of_dimensions=2, ):
        super().__init__( cursor,
                          profile_identifier=profile_identifier,     \
                          flow_class=flow_class,                     \
                          year=year,                                 \
                          case_number=case_number,                   \
                          series_number=series_number,               \
                          profile_number=profile_number,             \
                          data_type=data_type,                       \
                          number_of_points=number_of_points,         \
                          number_of_dimensions=number_of_dimensions, )

class FlowWithRelativeMotion(InternalFlow):
    def __init__( self,                             \
                  database,                         \
                  profile_identifier=None,          \
                  flow_class=RELATIVE_MOTION_CLASS, \
                  year=None,                        \
                  case_number=None,                 \
                  series_number=None,               \
                  profile_number=None,              \
                  data_type=EXPERIMENTAL_DATA_TYPE, \
                  number_of_points=0,               \
                  number_of_dimensions=2, ):
        super().__init__( database,                                  \
                          profile_identifier=profile_identifier,     \
                          flow_class=flow_class,                     \
                          year=year,                                 \
                          case_number=case_number,                   \
                          series_number=series_number,               \
                          profile_number=profile_number,             \
                          data_type=data_type,                       \
                          number_of_points=number_of_points,         \
                          number_of_dimensions=number_of_dimensions, )

def create_empty_database( filename ):
    connection = sqlite3.connect( filename )
    cursor = connection.cursor()

    cursor.execute(
    "CREATE TABLE "+_DISCRETE_GLOBALS_TABLE+" ("+
    """
    profile_identifier TEXT NOT NULL UNIQUE DEFAULT "S9999001001001",
    series_identifier TEXT NOT NULL DEFAULT "S9999001001",
    case_identifier TEXT NOT NULL DEFAULT "S9999001",
    flow_class TEXT NOT NULL DEFAULT "S",
    year INTEGER NOT NULL DEFAULT 9999,
    case_number INTEGER NOT NULL DEFAULT 1,
    series_number INTEGER NOT NULL DEFAULT 1,
    profile_number INTEGER NOT NULL DEFAULT 1,
    data_type TEXT NOT NULL DEFAULT "E",
    number_of_points INTEGER NOT NULL DEFAULT 0,
    number_of_dimensions INTEGER NOT NULL DEFAULT 2,
    originators_identifier TEXT DEFAULT NULL,
    working_fluid TEXT DEFAULT NULL,
    working_fluid_phase TEXT DEFAULT NULL,
    coordinate_system TEXT DEFAULT NULL,
    geometry TEXT DEFAULT NULL,
    number_of_sides INTEGER DEFAULT NULL,
    previous_streamwise_station TEXT_DEFAULT_NULL,
    next_streamwise_station TEXT_DEFAULT_NULL,
    previous_spanwise_station TEXT_DEFAULT_NULL,
    next_spanwise_station TEXT_DEFAULT_NULL,
    regime TEXT DEFAULT NULL,
    trip_present INTEGER DEFAULT NULL
    )
    """
    )

    for postfix in [ _VALUE_POSTFIX, _UNCERTAINTY_POSTFIX ]:
        cursor.execute(
        "CREATE TABLE "+_DIMENSIONAL_GLOBALS_TABLE+postfix+" ("+
        """
        profile_identifier TEXT NOT NULL UNIQUE DEFAULT "S9999001001001",
        origin_streamwise_coordinate REAL DEFAULT NULL,
        origin_transverse_coordinate REAL DEFAULT NULL,
        origin_spanwise_coordinate REAL DEFAULT NULL,
        streamwise_wall_curvature REAL DEFAULT NULL,
        spanwise_wall_curvature REAL DEFAULT NULL,
        roughness_height REAL DEFAULT NULL,
        characteristic_width REAL DEFAULT NULL,
        characteristic_height REAL DEFAULT NULL,
        cross_sectional_area REAL DEFAULT NULL,
        wetted_perimeter REAL DEFAULT NULL,
        hydraulic_diameter REAL DEFAULT NULL,
        streamwise_trip_location REAL DEFAULT NULL
        )
        """,
        )

        for prefix in [ _UNWEIGHTED_PREFIX, _DENSITY_WEIGHTED_PREFIX ]:
            cursor.execute(
            "CREATE TABLE "+prefix+_DIMENSIONAL_GLOBALS_TABLE+postfix+" ("+
            """
            profile_identifier TEXT NOT NULL UNIQUE DEFAULT "S9999001001001",
            bulk_dynamic_viscosity REAL DEFAULT NULL,
            bulk_kinematic_viscosity REAL DEFAULT NULL,
            bulk_mass_density REAL DEFAULT NULL,
            bulk_pressure REAL DEFAULT NULL,
            bulk_specific_isobaric_heat_capacity REAL DEFAULT NULL,
            bulk_speed_of_sound REAL DEFAULT NULL,
            bulk_streamwise_velocity REAL DEFAULT NULL,
            bulk_temperature REAL DEFAULT NULL,
            bulk_transverse_velocity REAL DEFAULT NULL,
            center_line_dynamic_viscosity REAL DEFAULT NULL,
            center_line_kinematic_viscosity REAL DEFAULT NULL,
            center_line_mass_density REAL DEFAULT NULL,
            center_line_pressure REAL DEFAULT NULL,
            center_line_specific_isobaric_heat_capacity REAL DEFAULT NULL,
            center_line_speed_of_sound REAL DEFAULT NULL,
            center_line_streamwise_velocity REAL DEFAULT NULL,
            center_line_temperature REAL DEFAULT NULL,
            center_line_transverse_velocity REAL DEFAULT NULL,
            clauser_thickness REAL DEFAULT NULL,
            compressible_displacement_thickness REAL DEFAULT NULL,
            compressible_momentum_thickness REAL DEFAULT NULL,
            edge_dynamic_viscosity REAL DEFAULT NULL,
            edge_kinematic_viscosity REAL DEFAULT NULL,
            edge_mass_density REAL DEFAULT NULL,
            edge_pressure REAL DEFAULT NULL,
            edge_specific_isobaric_heat_capacity REAL DEFAULT NULL,
            edge_speed_of_sound REAL DEFAULT NULL,
            edge_streamwise_velocity REAL DEFAULT NULL,
            edge_temperature REAL DEFAULT NULL,
            edge_transverse_velocity REAL DEFAULT NULL,
            edge_velocity_gradient REAL DEFAULT NULL,
            friction_velocity REAL DEFAULT NULL,
            friction_temperature REAL DEFAULT NULL,
            incompressible_displacement_thickness REAL DEFAULT NULL,
            incompressible_momentum_thickness REAL DEFAULT NULL,
            left_hand_side_of_momentum_integral REAL DEFAULT NULL,
            mass_flow_rate REAL DEFAULT NULL,
            maximum_dynamic_viscosity REAL DEFAULT NULL,
            maximum_kinematic_viscosity REAL DEFAULT NULL,
            maximum_mass_density REAL DEFAULT NULL,
            maximum_pressure REAL DEFAULT NULL,
            maximum_specific_isobaric_heat_capacity REAL DEFAULT NULL,
            maximum_speed_of_sound REAL DEFAULT NULL,
            maximum_streamwise_velocity REAL DEFAULT NULL,
            maximum_temperature REAL DEFAULT NULL,
            maximum_transverse_velocity REAL DEFAULT NULL,
            minimum_dynamic_viscosity REAL DEFAULT NULL,
            minimum_kinematic_viscosity REAL DEFAULT NULL,
            minimum_mass_density REAL DEFAULT NULL,
            minimum_pressure REAL DEFAULT NULL,
            minimum_specific_isobaric_heat_capacity REAL DEFAULT NULL,
            minimum_speed_of_sound REAL DEFAULT NULL,
            minimum_streamwise_velocity REAL DEFAULT NULL,
            minimum_temperature REAL DEFAULT NULL,
            minimum_transverse_velocity REAL DEFAULT NULL,
            reservoir_pressure REAL DEFAULT NULL,
            reservoir_speed_of_sound REAL DEFAULT NULL,
            reservoir_temperature REAL DEFAULT NULL,
            right_hand_side_of_momentum_integral REAL DEFAULT NULL,
            streamwise_pressure_gradient REAL DEFAULT NULL,
            viscous_length_scale REAL DEFAULT NULL,
            wall_dynamic_viscosity REAL DEFAULT NULL,
            wall_kinematic_viscosity REAL DEFAULT NULL,
            wall_mass_density REAL DEFAULT NULL,
            wall_pressure REAL DEFAULT NULL,
            wall_shear_stress REAL DEFAULT NULL,
            wall_specific_isobaric_heat_capacity REAL DEFAULT NULL,
            wall_speed_of_sound REAL DEFAULT NULL,
            wall_streamwise_velocity REAL DEFAULT NULL,
            wall_temperature REAL DEFAULT NULL,
            wall_transverse_velocity REAL DEFAULT NULL,
            ninety_nine_percent_velocity_boundary_layer_thickness REAL DEFAULT NULL,
            ninety_nine_percent_temperature_boundary_layer_thickness REAL DEFAULT NULL
            )
            """,
            )

            cursor.execute(
            "CREATE TABLE "+prefix+_DIMENSIONLESS_GLOBALS_TABLE+postfix+" ("+
            """
            profile_identifier TEXT NOT NULL UNIQUE DEFAULT "S9999001001001",
            bulk_heat_capacity_ratio REAL DEFAULT NULL,
            bulk_mach_number REAL DEFAULT NULL,
            bulk_prandtl_number REAL DEFAULT NULL,
            center_line_heat_capacity_ratio REAL DEFAULT NULL,
            center_line_mach_number REAL DEFAULT NULL,
            center_line_prandtl_number REAL DEFAULT NULL,
            dimensionless_wall_heat_flux REAL DEFAULT NULL,
            edge_heat_capacity_ratio REAL DEFAULT NULL,
            edge_mach_number REAL DEFAULT NULL,
            edge_prandtl_number REAL DEFAULT NULL,
            edge_reynolds_number_based_on_displacement_thickness REAL DEFAULT NULL,
            edge_reynolds_number_based_on_momentum_thickness REAL DEFAULT NULL,
            equilibrium_parameter REAL DEFAULT NULL,
            freestream_turbulence_intensity REAL DEFAULT NULL,
            friction_factor REAL DEFAULT NULL,
            friction_mach_number REAL DEFAULT NULL,
            friction_reynolds_number REAL DEFAULT NULL,
            heat_transfer_coefficient REAL DEFAULT NULL,
            maximum_heat_capacity_ratio_ REAL DEFAULT NULL,
            maximum_mach_number REAL DEFAULT NULL,
            maximum_prandtl_number REAL DEFAULT NULL,
            minimum_heat_capacity_ratio_ REAL DEFAULT NULL,
            minimum_mach_number REAL DEFAULT NULL,
            minimum_prandtl_number REAL DEFAULT NULL,
            recovery_factor REAL DEFAULT NULL,
            semi_local_friction_reynolds_number REAL DEFAULT NULL,
            skin_friction_coefficient REAL DEFAULT NULL,
            wall_heat_capacity_ratio REAL DEFAULT NULL,
            wall_mach_number REAL DEFAULT NULL,
            wall_prandtl_number REAL DEFAULT NULL
            )
            """,
            )

    connection.commit()
    connection.close()
