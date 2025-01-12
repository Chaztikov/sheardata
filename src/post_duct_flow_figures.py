#!/usr/bin/env python3

# Copyright (C) 2020-2021 Andrew Trettel
#
# SPDX-License-Identifier: MIT

import sheardata as sd
import sqlite3
import sys
import numpy as np
from uncertainties import ufloat
from uncertainties import unumpy as unp

import matplotlib as mpl
mpl.use("pgf")
import matplotlib.pylab as plt
import gfx
mpl.rcParams.update( gfx.rc_custom_preamble() )

conn   = sqlite3.connect( sys.argv[1] )
cursor = conn.cursor()
cursor.execute( "PRAGMA foreign_keys = ON;" )

# Intersection of
# - Stations in duct flow experimental studies
# - Stations in 2D series in cylindrical coordinates with elliptical
#   geometries
# - Stations that are fully-developed (next station is the previous station)
# - Stations that have points with smooth walls
# - Stations that have an aspect ratio of 1.0
# - Stations that have bulk Mach numbers between 0.0 and 0.3
# - Stations that have the bulk Reynolds number
# - Stations that have the quantity of interest

class DuctType:
    geometry          = None
    coordinate_system = None
    min_aspect_ratio  = None
    max_aspect_ratio  = None
    laminar_constant  = None

    def __init__( self, geometry, coordinate_system, min_aspect_ratio, \
                  max_aspect_ratio, laminar_constant ):
        self.geometry          =   str(geometry)
        self.coordinate_system =   str(coordinate_system)
        self.min_aspect_ratio  = float(min_aspect_ratio)
        self.max_aspect_ratio  = float(max_aspect_ratio)
        self.laminar_constant  = float(laminar_constant)

duct_types = {}
duct_types["channel"] = DuctType( sd.RECTANGULAR_GEOMETRY, sd.RECTANGULAR_COORDINATE_SYSTEM, 7.0, float("inf"), 24.0 )
duct_types["pipe"]    = DuctType(  sd.ELLIPTICAL_GEOMETRY, sd.CYLINDRICAL_COORDINATE_SYSTEM, 1.0,          1.0, 16.0 )

max_inner_layer_roughness_height = 1.0
min_bulk_mach_number = 0.0
max_bulk_mach_number = 0.8
min_outer_layer_development_length = 50.0
min_center_line_to_wall_temperature_ratio = 0.9
max_center_line_to_wall_temperature_ratio = 1.1

for duct_type in duct_types:
    for quantity in [ sd.Q_BULK_TO_CENTER_LINE_VELOCITY_RATIO,
                                 sd.Q_FANNING_FRICTION_FACTOR, ]:
        fig = plt.figure()
        ax  = fig.add_subplot( 1, 1, 1 )

        all_stations = []

        ax.set_xscale( "log", nonposx="clip" )
        if ( quantity == sd.Q_FANNING_FRICTION_FACTOR ):
            ax.set_yscale( "log", nonposy="clip" )

        bulk_reynolds_number_bounds = None
        quantity_values_bounds      = None
        y_label        = None
        filename_label = None
        quantity_label = None
        if ( quantity == sd.Q_BULK_TO_CENTER_LINE_VELOCITY_RATIO ):
            bulk_reynolds_number_bounds = ( 1.00e+3, 1.00e+5, )

            quantity_values_bounds = ( 1.0/2.0, 0.85, )
            if ( duct_type == "channel" ):
                quantity_values_bounds = ( 2.0/3.0, 1.0, )

            y_label        = r"$\frac{U_b}{U_c}$"
            filename_label = "velocity-ratios"
            quantity_label = "Bulk-to-center-line velocity ratio"
        elif ( quantity == sd.Q_FANNING_FRICTION_FACTOR ):
            bulk_reynolds_number_bounds = ( 1.00e+1, 1.00e+6, )
            quantity_values_bounds      = ( 1.00e-3, 1.00e-1, )

            y_label        = r"$f = \frac{2 \tau_w}{\rho U_b^2}$"
            filename_label = "fanning-friction-factor"
            quantity_label = "Fanning friction factor"

            laminar_bulk_reynolds_number = np.linspace(
                bulk_reynolds_number_bounds[0],
                2.0e+3,
                gfx.page_size.max_elements(),
            )
            laminar_fanning_friction_factor = duct_types[duct_type].laminar_constant / laminar_bulk_reynolds_number

            ax.plot(
                laminar_bulk_reynolds_number,
                laminar_fanning_friction_factor,
                clip_on=True,
                zorder=1,
            )

        ax.set_xlim( bulk_reynolds_number_bounds )
        ax.set_ylim(      quantity_values_bounds )

        gfx.label_axes(
            ax,
            r"$\mathrm{Re}_b = U_b D_H / \nu$",
            y_label
        )

        for study_type in [ sd.DIRECT_NUMERICAL_SIMULATION_STUDY_TYPE,
                                           sd.EXPERIMENTAL_STUDY_TYPE, ]:
            if ( quantity == sd.Q_BULK_TO_CENTER_LINE_VELOCITY_RATIO ):
                cursor.execute(
                """
                SELECT identifier
                FROM stations
                WHERE study IN (
                    SELECT identifier
                    FROM studies
                    WHERE flow_class=? AND study_type=?
                )
                INTERSECT
                SELECT identifier
                FROM stations
                WHERE series IN (
                    SELECT identifier
                    FROM series
                    WHERE number_of_dimensions=? AND coordinate_system=? AND geometry=?
                )
                INTERSECT
                SELECT identifier
                FROM stations
                WHERE previous_streamwise_station=next_streamwise_station
                INTERSECT
                SELECT station
                FROM points
                WHERE identifier IN (
                    SELECT point
                    FROM point_values
                    WHERE quantity=? AND point_value<? AND outlier=0
                )
                INTERSECT
                SELECT station
                FROM station_values
                WHERE quantity=? AND station_value>=? AND station_value<=? AND outlier=0
                INTERSECT
                SELECT station
                FROM station_values
                WHERE quantity=? AND station_value>=? AND station_value<? AND outlier=0
                INTERSECT
                SELECT station
                FROM station_values
                WHERE quantity=? AND station_value>=? AND outlier=0
                INTERSECT
                SELECT station
                FROM points
                WHERE point_label=? AND identifier IN (
                    SELECT point
                    FROM point_values
                    WHERE quantity=? AND point_value>=? AND point_value<=? AND outlier=0
                )
                INTERSECT
                SELECT station
                FROM station_values
                WHERE quantity=? AND outlier=0
                INTERSECT
                SELECT station
                FROM station_values
                WHERE quantity=? AND outlier=0
                ORDER BY identifier;
                """,
                (
                    sd.DUCT_FLOW_CLASS,
                    study_type,
                    int(2),
                    duct_types[duct_type].coordinate_system,
                    duct_types[duct_type].geometry,
                    sd.Q_INNER_LAYER_ROUGHNESS_HEIGHT,
                    max_inner_layer_roughness_height,
                    sd.Q_ASPECT_RATIO,
                    duct_types[duct_type].min_aspect_ratio,
                    duct_types[duct_type].max_aspect_ratio,
                    sd.Q_BULK_MACH_NUMBER,
                    min_bulk_mach_number,
                    max_bulk_mach_number,
                    sd.Q_OUTER_LAYER_DEVELOPMENT_LENGTH,
                    min_outer_layer_development_length,
                    sd.WALL_POINT_LABEL,
                    sd.Q_CENTER_LINE_TO_WALL_TEMPERATURE_RATIO,
                    min_center_line_to_wall_temperature_ratio,
                    max_center_line_to_wall_temperature_ratio,
                    sd.Q_BULK_REYNOLDS_NUMBER,
                    quantity,
                )
                )
            elif ( quantity == sd.Q_FANNING_FRICTION_FACTOR ):
                cursor.execute(
                """
                SELECT identifier
                FROM stations
                WHERE study IN (
                    SELECT identifier
                    FROM studies
                    WHERE flow_class=? AND study_type=?
                )
                INTERSECT
                SELECT identifier
                FROM stations
                WHERE series IN (
                    SELECT identifier
                    FROM series
                    WHERE number_of_dimensions=? AND coordinate_system=? AND geometry=?
                )
                INTERSECT
                SELECT identifier
                FROM stations
                WHERE previous_streamwise_station=next_streamwise_station
                INTERSECT
                SELECT station
                FROM points
                WHERE identifier IN (
                    SELECT point
                    FROM point_values
                    WHERE quantity=? AND point_value<? AND outlier=0
                )
                INTERSECT
                SELECT station
                FROM station_values
                WHERE quantity=? AND station_value>=? AND station_value<=? AND outlier=0
                INTERSECT
                SELECT station
                FROM station_values
                WHERE quantity=? AND station_value>=? AND station_value<? AND outlier=0
                INTERSECT
                SELECT station
                FROM station_values
                WHERE quantity=? AND station_value>=? AND outlier=0
                INTERSECT
                SELECT station
                FROM points
                WHERE point_label=? AND identifier IN (
                    SELECT point
                    FROM point_values
                    WHERE quantity=? AND point_value>=? AND point_value<=? AND outlier=0
                )
                INTERSECT
                SELECT station
                FROM station_values
                WHERE quantity=? AND outlier=0
                INTERSECT
                SELECT station
                FROM points
                WHERE point_label=? AND identifier IN (
                    SELECT point
                    FROM point_values
                    WHERE quantity=? AND outlier=0
                )
                ORDER BY identifier;
                """,
                (
                    sd.DUCT_FLOW_CLASS,
                    study_type,
                    int(2),
                    duct_types[duct_type].coordinate_system,
                    duct_types[duct_type].geometry,
                    sd.Q_INNER_LAYER_ROUGHNESS_HEIGHT,
                    max_inner_layer_roughness_height,
                    sd.Q_ASPECT_RATIO,
                    duct_types[duct_type].min_aspect_ratio,
                    duct_types[duct_type].max_aspect_ratio,
                    sd.Q_BULK_MACH_NUMBER,
                    min_bulk_mach_number,
                    max_bulk_mach_number,
                    sd.Q_OUTER_LAYER_DEVELOPMENT_LENGTH,
                    min_outer_layer_development_length,
                    sd.WALL_POINT_LABEL,
                    sd.Q_CENTER_LINE_TO_WALL_TEMPERATURE_RATIO,
                    min_center_line_to_wall_temperature_ratio,
                    max_center_line_to_wall_temperature_ratio,
                    sd.Q_BULK_REYNOLDS_NUMBER,
                    sd.WALL_POINT_LABEL,
                    quantity,
                )
                )

            stations = []
            for result in cursor.fetchall():
                stations.append( str(result[0]) )
                all_stations.append( str(result[0]) )

            bulk_reynolds_number_array = []
            quantity_values_array      = []
            for station in stations:
                bulk_reynolds_number_array.append( sd.get_station_value(
                    cursor,
                    station,
                    sd.Q_BULK_REYNOLDS_NUMBER,
                    averaging_system=sd.UNWEIGHTED_AVERAGING_SYSTEM,
                ) )

                if ( quantity == sd.Q_BULK_TO_CENTER_LINE_VELOCITY_RATIO ):
                    quantity_values_array.append( sd.get_station_value(
                        cursor,
                        station,
                        quantity,
                        averaging_system=sd.UNWEIGHTED_AVERAGING_SYSTEM,
                    ) )
                elif ( quantity == sd.Q_FANNING_FRICTION_FACTOR ):
                    quantity_values_array.append( sd.get_labeled_value(
                        cursor,
                        station,
                        quantity,
                        sd.WALL_POINT_LABEL,
                        averaging_system=sd.UNWEIGHTED_AVERAGING_SYSTEM,
                    ) )

            bulk_reynolds_number = np.array( bulk_reynolds_number_array )
            quantity_values      = np.array(      quantity_values_array )

            study_order = 2
            marker_type = "o"
            if ( study_type == sd.DIRECT_NUMERICAL_SIMULATION_STUDY_TYPE ):
                marker_type = "d"
                study_order = 3

            ax.errorbar(
                unp.nominal_values( bulk_reynolds_number  ),
                unp.nominal_values( quantity_values ),
                unp.std_devs( quantity_values ),
                marker=marker_type,
                linestyle="",
                elinewidth=gfx.error_bar_width,
                clip_on=( quantity == sd.Q_FANNING_FRICTION_FACTOR ),
                zorder=study_order,
            )

        ########################################
        fig.savefig( "figure-{:s}-flow-{:s}.pgf".format(
            duct_type,
            filename_label,
        ) )
        fig.clear()
        plt.close( fig )

        with open( "caption-{:s}-flow-{:s}.tex.tmp".format( \
                   duct_type, filename_label ), "w" ) as f:
            short_caption = "{:s} for fully-developed, incompressible {:s} \
                             flow as a function of the bulk Reynolds \
                             number.".format(
                quantity_label,
                duct_type,
            )

            f.write( r"\caption[" )
            f.write( short_caption )
            f.write( r"]{" )
            f.write( short_caption+"  " )

            f.write( "{:d} series in total".format(
                len(all_stations),
            ) )

            studies = sd.count_studies( all_stations )
            i_study = 0
            if ( len(studies) != 0 ):
                f.write( ": " )
            for key in sorted(studies.items()):
                study = str(key[0])
                f.write( r"\texttt{" )
                f.write( "{:s}".format(
                    sd.make_readable_identifier( study ),
                ) )
                f.write( r"}" )
                f.write( ", {:d} series".format(
                    studies[study],
                ) )
                i_study += 1
                if ( i_study != len(studies) ):
                    f.write( "; " )

            f.write( r".}" )

conn.commit()
conn.close()
