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
year         = 1947
study_number = 1

study_identifier = sd.add_study(
    cursor,
    flow_class=flow_class,
    year=year,
    study_number=study_number,
    study_type=sd.EXPERIMENTAL_STUDY_TYPE,
)

sd.add_source( cursor, study_identifier, "HuebscherRG+1947+eng+JOUR", 1 )

# Duct dimensions
#
# p. 128
#
# \begin{quote}
# The first part of the paper gives the results of an experimental
# investigation using three ducts of different forms but each of 8 in.
# equivalent diameter.  The duct sizes were 8 in. ID round, 8 in. square and
# 4.5 in. by 36 in. rectangular (8:1 aspect ratio).  Air velocities used ranged
# from 300 to 9310 fpm.
# \end{quote}

class Duct:
    aspect_ratio = None
    length       = None

    def __init__( self, aspect_ratio, length ):
        self.aspect_ratio = float(aspect_ratio)
        self.length       = float(length)

ducts = {}
globals_filename = "../data/{:s}/globals.csv".format( study_identifier )
with open( globals_filename, "r" ) as globals_file:
    globals_reader = csv.reader(
        globals_file,
        delimiter=",",
        quotechar='"', \
        skipinitialspace=True,
    )
    next(globals_reader)
    for globals_row in globals_reader:
        ducts[str(globals_row[0])] = Duct(
            float(globals_row[1]),
            float(globals_row[2]),
        )

series_number = 0
for duct in ducts:
    duct_globals_filename = "../data/{:s}/{:s}_duct_globals.csv".format(
        study_identifier,
        duct.lower(),
    )
    with open( duct_globals_filename, "r" ) as duct_globals_file:
        duct_globals_reader = csv.reader(
            duct_globals_file,
            delimiter=",",
            quotechar='"', \
            skipinitialspace=True,
        )
        next(duct_globals_reader)
        for duct_globals_row in duct_globals_reader:
            series_number += 1

            originators_identifier = "{:s} duct {:d}".format(
                duct,
                int(duct_globals_row[0]),
            )
            temperature                   = ( float(duct_globals_row[2]) - 32.0 ) / 1.8 + 273.15
            mass_density                  = float(duct_globals_row[4]) * 0.45359237 / 0.3048**3.0
            bulk_velocity_value           = float(duct_globals_row[5]) * 0.3048 / 60.0
            hydraulic_diameter            = float(duct_globals_row[6]) * 0.0254
            Re_bulk_value                 = float(duct_globals_row[10])
            fanning_friction_factor_value = float(duct_globals_row[11]) / 4.0

            # Uncertainty of wall shear stress measurements
            #
            # p. 129
            #
            # \begin{quote}
            # The maximum sensitivity of the five gages was $\pm 0.02$ in. of
            # water, with an accuracy within this value over the entire range.
            # \end{quote}
            #
            # Assume a uniform distribution.
            wall_shear_stress_value = 0.5 * mass_density * bulk_velocity_value**2.0 * fanning_friction_factor_value
            wall_shear_stress_uncertainty = 1000.0 * 9.81 * ( 0.02 * 0.0254 )
            wall_shear_stress = ufloat( wall_shear_stress_value, wall_shear_stress_uncertainty )

            # Uncertainty of flow rate measurements
            #
            # p. 128
            #
            # \begin{quote}
            # The estimated error in any flow measurement due to all sources,
            # including the assumption of constant nozzle coefficient, did not
            # exceed $\pm 2$ percent.
            # \end{quote}
            #
            # Assume a uniform distribution.
            bulk_velocity_uncertainty = 0.02 * bulk_velocity_value / 3.0**2.0
            bulk_velocity = ufloat( bulk_velocity_value, bulk_velocity_uncertainty )

            fanning_friction_factor = 2.0 * wall_shear_stress / ( mass_density * bulk_velocity**2.0 )

            kinematic_viscosity = bulk_velocity * hydraulic_diameter / Re_bulk_value
            dynamic_viscosity   = mass_density * kinematic_viscosity
            Re_bulk             = bulk_velocity * hydraulic_diameter / kinematic_viscosity

            # TODO: Correct these assumptions later.
            speed_of_sound = ( 1.4 * 287.058 * temperature )**0.5
            Ma_bulk        = bulk_velocity / speed_of_sound

            series_identifier = sd.add_series(
                cursor,
                flow_class=flow_class,
                year=year,
                study_number=study_number,
                series_number=series_number,
                number_of_dimensions=2,
                coordinate_system=sd.CYLINDRICAL_COORDINATE_SYSTEM,
            )

            sd.add_air_components( cursor, series_identifier )

            if ( duct == "Round" ):
                sd.update_series_geometry(
                    cursor,
                    series_identifier,
                    sd.ELLIPTICAL_GEOMETRY
                )
            else:
                sd.update_series_geometry(
                    cursor,
                    series_identifier,
                    sd.RECTANGULAR_GEOMETRY
                )

            station_number = 1
            station_identifier = sd.add_station(
                cursor,
                flow_class=flow_class,
                year=year,
                study_number=study_number,
                series_number=series_number,
                station_number=station_number,
                originators_identifier=originators_identifier,
            )

            sd.mark_station_as_periodic( cursor, station_identifier )

            sd.set_station_value(
                cursor,
                station_identifier,
                sd.HYDRAULIC_DIAMETER_QUANTITY,
                hydraulic_diameter,
            )

            sd.set_station_value(
                cursor,
                station_identifier,
                sd.ASPECT_RATIO_QUANTITY,
                ducts[duct].aspect_ratio,
            )

            # p. 128
            #
            # \begin{quote}
            # The mean air velocity was determined from the measurement of the
            # air quantity and the duct area.  \ldots  Air quantity was
            # measured by the use of five cast aluminum nozzles made
            # approximately to ASME log-radius, low-ratio proportions and
            # equiped with throat static taps.  \ldots  The nozzles were
            # calibrated in place by impact tube traverses at the throat over
            # the full flow range.
            # \end{quote}
            sd.set_station_value(
                cursor,
                station_identifier,
                sd.BULK_VELOCITY_QUANTITY,
                bulk_velocity,
                averaging_system=sd.UNWEIGHTED_AVERAGING_SYSTEM,
                measurement_technique=sd.IMPACT_TUBE_MEASUREMENT_TECHNIQUE,
            )

            sd.set_station_value(
                cursor,
                station_identifier,
                sd.BULK_REYNOLDS_NUMBER_QUANTITY,
                Re_bulk,
                averaging_system=sd.UNWEIGHTED_AVERAGING_SYSTEM,
                measurement_technique=sd.CALCULATION_MEASUREMENT_TECHNIQUE
            )

            sd.set_station_value(
                cursor,
                station_identifier,
                sd.BULK_MACH_NUMBER_QUANTITY,
                Ma_bulk,
                averaging_system=sd.UNWEIGHTED_AVERAGING_SYSTEM,
                measurement_technique=sd.CALCULATION_MEASUREMENT_TECHNIQUE
            )

            # This set of data only considers wall quantities.
            point_number = 1
            point_identifier = sd.add_point(
                cursor,
                flow_class=flow_class,
                year=year,
                study_number=study_number,
                series_number=series_number,
                station_number=station_number,
                point_number=point_number,
                point_label=sd.WALL_POINT_LABEL,
            )

            # TODO: Correct this assumption later.
            #
            # Duct material
            #
            # p. 128
            #
            # \begin{quote}
            # The three ducts were fabricated from 16 gage galvanized sheet
            # metal to provide the necessary rigidity against deflection.
            # \end{quote}
            #
            # p. 129
            #
            # \begin{quote}
            # The internal roughness of all three ducts was typical of
            # galvanized iron, very little roughness was contributed by the
            # joints.  The hydraulic roughness magnitude cannot be measured
            # geometrically but can be deduced from the test results.
            # \end{quote}
            for quantity in [ sd.ROUGHNESS_HEIGHT_QUANTITY,
                              sd.INNER_LAYER_ROUGHNESS_HEIGHT_QUANTITY,
                              sd.OUTER_LAYER_ROUGHNESS_HEIGHT_QUANTITY, ]:
                sd.set_labeled_value(
                    cursor,
                    station_identifier,
                    quantity,
                    sd.WALL_POINT_LABEL,
                    0.0,
                    measurement_technique=sd.ASSUMPTION_MEASUREMENT_TECHNIQUE,
                )

            sd.set_labeled_value(
                cursor,
                station_identifier,
                sd.MASS_DENSITY_QUANTITY,
                sd.WALL_POINT_LABEL,
                mass_density,
                averaging_system=sd.UNWEIGHTED_AVERAGING_SYSTEM,
            )

            sd.set_labeled_value(
                cursor,
                station_identifier,
                sd.KINEMATIC_VISCOSITY_QUANTITY,
                sd.WALL_POINT_LABEL,
                kinematic_viscosity,
                averaging_system=sd.UNWEIGHTED_AVERAGING_SYSTEM,
            )

            sd.set_labeled_value(
                cursor,
                station_identifier,
                sd.DYNAMIC_VISCOSITY_QUANTITY,
                sd.WALL_POINT_LABEL,
                dynamic_viscosity,
                averaging_system=sd.UNWEIGHTED_AVERAGING_SYSTEM,
            )

            sd.set_labeled_value(
                cursor,
                station_identifier,
                sd.TEMPERATURE_QUANTITY,
                sd.WALL_POINT_LABEL,
                temperature,
                averaging_system=sd.UNWEIGHTED_AVERAGING_SYSTEM,
            )

            sd.set_labeled_value(
                cursor,
                station_identifier,
                sd.SPEED_OF_SOUND_QUANTITY,
                sd.WALL_POINT_LABEL,
                speed_of_sound,
                averaging_system=sd.UNWEIGHTED_AVERAGING_SYSTEM,
                measurement_technique=sd.ASSUMPTION_MEASUREMENT_TECHNIQUE,
            )

            sd.set_labeled_value(
                cursor,
                station_identifier,
                sd.STREAMWISE_VELOCITY_QUANTITY,
                sd.WALL_POINT_LABEL,
                ufloat( 0.0, 0.0 ),
                averaging_system=sd.UNWEIGHTED_AVERAGING_SYSTEM,
            )

            sd.set_labeled_value(
                cursor,
                station_identifier,
                sd.DISTANCE_FROM_WALL_QUANTITY,
                sd.WALL_POINT_LABEL,
                ufloat( 0.0, 0.0 ),
                averaging_system=sd.UNWEIGHTED_AVERAGING_SYSTEM,
            )

            sd.set_labeled_value(
                cursor,
                station_identifier,
                sd.OUTER_LAYER_COORDINATE_QUANTITY,
                sd.WALL_POINT_LABEL,
                ufloat( 0.0, 0.0 ),
                averaging_system=sd.UNWEIGHTED_AVERAGING_SYSTEM,
            )

            # p. 129
            wall_shear_stress_measurement_technique = sd.PRESSURE_DROP_MEASUREMENT_TECHNIQUE

            sd.set_labeled_value(
                cursor,
                station_identifier,
                sd.SHEAR_STRESS_QUANTITY,
                sd.WALL_POINT_LABEL,
                wall_shear_stress,
                averaging_system=sd.UNWEIGHTED_AVERAGING_SYSTEM,
                measurement_technique=wall_shear_stress_measurement_technique,
            )

            sd.set_labeled_value(
                cursor,
                station_identifier,
                sd.FANNING_FRICTION_FACTOR_QUANTITY,
                sd.WALL_POINT_LABEL,
                fanning_friction_factor,
                averaging_system=sd.UNWEIGHTED_AVERAGING_SYSTEM,
                measurement_technique=wall_shear_stress_measurement_technique,
            )

conn.commit()
conn.close()

# p. 132
#
# \begin{quote}
# Two traverses at opposite ends of the round duct indicated
# different velocity profiles, the centerline velocity at the
# downstream end was 6.6 percent higher than at the upstream end
# for a mean velocity of 9310 fpm.
# \end{quote}
