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

flow_class    = sd.DUCT_FLOW_CLASS
year          = 1914
study_number  = 1

study_identifier = sd.add_study(
    cursor,
    flow_class=flow_class,
    year=year,
    study_number=study_number,
    study_type=sd.EXPERIMENTAL_STUDY_TYPE,
)

sd.add_source( cursor, study_identifier, "StantonTE+1914+eng+JOUR", 1 )
sd.add_source( cursor, study_identifier, "ObotNT+1988+eng+JOUR",    2 )

development_length_note = sd.add_note(
    cursor,
    "../data/{:s}/note_development_length.tex".format( study_identifier ),
)

mass_density_note = sd.add_note(
    cursor,
    "../data/{:s}/note_mass_density.tex".format( study_identifier ),
)

class Pipe:
    diameter                       = None
    distance_between_pressure_taps = None
    material                       = None

    # p. 202
    #
    # \begin{quote}
    # The length of ``leading in'' pipe, of the same diameter as the
    # experimental portion, through which the fluid passed before any
    # observations of its velocity or pressure were made, varied from 90 to 140
    # diameters, as it was considered that this length was sufficient both to
    # enable any irregularities in the distribution of velocity to die away, or
    # any stream-line motion at the inlet to break up, before the measurements
    # were taken.
    # \end{quote}
    #
    # For the sake of simplicity, assume that the development length is the
    # minimum of these.  It is long enough that its precise value does not
    # matter.
    def outer_layer_development_length( self ):
        return sd.sdfloat(90.0)

    def development_length( self ):
        return diameter * self.outer_layer_development_length()

    def __init__( self, diameter, distance_between_pressure_taps, material ):
        self.diameter = sd.sdfloat(diameter)
        if ( distance_between_pressure_taps == 0.0 ):
            self.distance_between_pressure_taps = None
        else:
            self.distance_between_pressure_taps = distance_between_pressure_taps
        self.material = str(material)

# Pipe 12A
#
# p. 202
#
# \begin{quote}
# For very accurate comparison the surfaces of the tubes should have been
# precisely geometrically similar, as regards roughness, but as this condition
# could not be fulfilled, the experiments were all made on commercially
# smooth-drawn brass pipes.
# \end{quote}
#
# However, this only appears to be the case for most of the experiments.  Some
# were conducted using steel pipes.  One experiment using air and all of the
# experiments with thick oil are using steel pipes.
#
# p. 209
#
# \begin{quote}
# As a matter of interest the results of a series of observations of the
# surface fraction of this oil, when flowing through a steel pipe 10.1 cm.
# diameter at speeds varying from 5 to 60 cm. per second, are given in Table
# IV. and are also plotted in fig. 3.
# \end{quote}
#
# Pipe 12A on p. 224 is not in the table on p. 207.  It is possible that this
# pipe is a brass pipe, but unfortunately the test length is not specified.

pipes = {}
pipes_filename = "../data/{:s}/pipes.csv".format( study_identifier )
with open( pipes_filename, "r" ) as pipes_file:
    pipes_reader = csv.reader(
        pipes_file,
        delimiter=",",
        quotechar='"', \
        skipinitialspace=True,
    )
    next(pipes_reader)
    for pipes_row in pipes_reader:
        pipes[str(pipes_row[0])] = Pipe(
            float(pipes_row[1]) * 1.0e-2,
            float(pipes_row[2]) * 1.0e-2,
              str(pipes_row[3]),
        )

# p. 203
#
# \begin{quote}
# The form of the tilting manometer used for the estimation of both the surface
# friction and the axial velocity, is that devised by Dr. A. P.  Chattock and
# has been previously described.†  For the purpose of the present paper it is
# sufficient to state that in this manometer a pressure difference of the order
# of 0.003 mm. of water can be detected, which is well within the limits of
# sensitivity required in these experiments.  As the fall of pressure in these
# pipes varied from 0.5 to 150,000 mm. of water, other manometers were required
# for the higher pressures, and for this purpose water or mercury U-tubes were
# used for the intermediate pressures, and the Bourdon pressure gauges for the
# highest pressures.
# \end{quote}
#
# The footnote lists two papers that should contain more information about the
# manometers used.
#
# This appears to be the only information given about the uncertainty of the
# experiments.  It is less useful than it appears, since according to the table
# on page 207, different manometers and gauges were used seemingly at random,
# making it unclear where the cutoff for "higher pressures" really is.
#
# Moreover, just as in the 1911 case, the uncertainties produced after
# propagating this from the pressure measurements to the velocities and shear
# stresses are many orders of magnitude too small.  Therefore it is difficult
# to estimate the uncertainties of these measurements.

# Set 1: velocity ratio data
series_number = 0
ratio_filename = "../data/{:s}/bulk_and_maximum_velocities.csv".format( study_identifier )
with open( ratio_filename, "r" ) as ratio_file:
    ratio_reader = csv.reader(
        ratio_file,
        delimiter=",",
        quotechar='"', \
        skipinitialspace=True,
    )
    next(ratio_reader)
    for ratio_row in ratio_reader:
        series_number += 1

        # Series 49, the one with the bulk velocity of 115.5 cm/s, appears to
        # be a turbulent value at a laminar Reynolds number.
        outlier = True if series_number == 49 else False

        bulk_velocity    = sd.sdfloat(ratio_row[0]) * 1.0e-2
        maximum_velocity = sd.sdfloat(ratio_row[1]) * 1.0e-2
        working_fluid    =        str(ratio_row[2])
        pipe             =        str(ratio_row[3])

        diameter                       = pipes[pipe].diameter
        distance_between_pressure_taps = pipes[pipe].distance_between_pressure_taps
        development_length             = pipes[pipe].development_length()
        outer_layer_development_length = pipes[pipe].outer_layer_development_length()

        # The velocity ratio experiments do not give the test conditions like
        # the temperature.  Graphical extraction from figure 1 reveals that the
        # kinematic viscosity used there is consistent with the value around
        # 15°C.
        #
        # These values were extracted graphically from figure 1 and averaged to
        # a single value.
        #
        # TODO: Calculate the density values rather than just assuming them.
        temperature = sd.sdfloat( 15.0 + sd.ABSOLUTE_ZERO )
        dynamic_viscosity   = None
        kinematic_viscosity = None
        mass_density        = None
        if ( working_fluid == "Water" ):
            mass_density        = sd.liquid_water_mass_density( temperature )
            dynamic_viscosity   = sd.liquid_water_dynamic_viscosity( temperature )
            kinematic_viscosity = dynamic_viscosity / mass_density
        elif ( working_fluid == "Air" ):
            mass_density        = sd.ideal_gas_mass_density( temperature )
            dynamic_viscosity   = sd.sutherlands_law_dynamic_viscosity( temperature )
            kinematic_viscosity = dynamic_viscosity / mass_density

        Re_bulk = bulk_velocity * diameter / kinematic_viscosity

        volumetric_flow_rate = 0.25 * math.pi * diameter**2.0 * bulk_velocity

        speed_of_sound = sd.sdfloat("inf")
        if ( working_fluid == "Air" ):
            speed_of_sound = sd.ideal_gas_speed_of_sound( temperature )
        elif ( working_fluid == "Water" ):
            speed_of_sound = sd.liquid_water_speed_of_sound( temperature )
        Ma_bulk = bulk_velocity / speed_of_sound

        series_identifier = sd.add_series(
            cursor,
            flow_class=flow_class,
            year=year,
            study_number=study_number,
            series_number=series_number,
            number_of_dimensions=2,
            coordinate_system=sd.CYLINDRICAL_COORDINATE_SYSTEM,
        )

        if ( working_fluid == "Air" ):
            sd.add_air_components( cursor, series_identifier )
        elif ( working_fluid == "Water" ):
            sd.add_working_fluid_component(
                cursor,
                series_identifier,
                sd.WATER_LIQUID,
            )

        sd.update_series_geometry(
            cursor,
            series_identifier,
            sd.ELLIPTICAL_GEOMETRY
        )

        sd.set_series_value( cursor, series_identifier, sd.Q_DISTANCE_BETWEEN_PRESSURE_TAPS, distance_between_pressure_taps, )

        station_number = 1
        station_identifier = sd.add_station(
            cursor,
            flow_class=flow_class,
            year=year,
            study_number=study_number,
            series_number=series_number,
            station_number=station_number,
        )

        sd.mark_station_as_periodic( cursor, station_identifier )

        sd.set_station_value( cursor, station_identifier, sd.Q_HYDRAULIC_DIAMETER,                 diameter,                                                                                               )
        sd.set_station_value( cursor, station_identifier, sd.Q_DEVELOPMENT_LENGTH,                 development_length,               measurement_techniques=[sd.MT_ASSUMPTION], notes=[development_length_note], )
        sd.set_station_value( cursor, station_identifier, sd.Q_OUTER_LAYER_DEVELOPMENT_LENGTH,     outer_layer_development_length,   measurement_techniques=[sd.MT_ASSUMPTION], notes=[development_length_note], )
        sd.set_station_value( cursor, station_identifier, sd.Q_ASPECT_RATIO,                       1.0,                                                                                                    )
        sd.set_station_value( cursor, station_identifier, sd.Q_BULK_VELOCITY,                      bulk_velocity,                    averaging_system=sd.BOTH_AVERAGING_SYSTEMS,                                             outlier=outlier, )
        sd.set_station_value( cursor, station_identifier, sd.Q_BULK_TO_CENTER_LINE_VELOCITY_RATIO, bulk_velocity / maximum_velocity, averaging_system=sd.BOTH_AVERAGING_SYSTEMS, measurement_techniques=[sd.MT_CALCULATION], outlier=outlier, )
        sd.set_station_value( cursor, station_identifier, sd.Q_BULK_REYNOLDS_NUMBER,               Re_bulk,                          averaging_system=sd.BOTH_AVERAGING_SYSTEMS, measurement_techniques=[sd.MT_CALCULATION], outlier=outlier, )
        sd.set_station_value( cursor, station_identifier, sd.Q_BULK_MACH_NUMBER,                   Ma_bulk,                          averaging_system=sd.BOTH_AVERAGING_SYSTEMS, measurement_techniques=[sd.MT_CALCULATION], outlier=outlier, )
        sd.set_station_value( cursor, station_identifier, sd.Q_VOLUMETRIC_FLOW_RATE,               volumetric_flow_rate,             averaging_system=sd.BOTH_AVERAGING_SYSTEMS,                                             outlier=outlier, )

        n_points = 2
        for point_number in [1, n_points]:
            point_label = None
            if ( point_number == 1 ):
                point_label = sd.WALL_POINT_LABEL
            elif ( point_number == n_points ):
                point_label = sd.CENTER_LINE_POINT_LABEL

            point_identifier = sd.add_point(
                cursor,
                flow_class=flow_class,
                year=year,
                study_number=study_number,
                series_number=series_number,
                station_number=station_number,
                point_number=point_number,
                point_label=point_label,
            )

        # Measurement techniques for flow rate and center-line velocities
        #
        # p. 203
        #
        # \begin{quote}
        # To measure the velocity of the current, one of two methods was used
        # according to convenience.  By one method the total quantity of fluid
        # passing through the pipe in a given time was either weighed directly,
        # or passed through a water-meter or a gas-holder, which had been
        # designed for the purpose of the experiments and carefully calibrated.
        # By the other method the velocity at the axis of the pipe was
        # estimated by measuring the difference of pressure between that in a
        # small Pitot tube facing the current and placed in the axis of the
        # pipe and that in a small hole in the wall of the pipe.
        # \end{quote}
        #
        # Page 207 contains a table of global parameters listing the
        # measurement techniques for different series of measurements.
        # However, the flow rate measurement technique varies for different
        # pipes and often 2 or more measurement techniques were used in an
        # unclear manner for a given pipe.
        #
        # In addition to that, the paper contains no information on the
        # uncertainty of the flow rate measuremnt.
        mt_velocity = sd.MT_IMPACT_TUBE

        for label in [ sd.WALL_POINT_LABEL, sd.CENTER_LINE_POINT_LABEL ]:
            sd.set_labeled_value( cursor, station_identifier, sd.Q_MASS_DENSITY,        label, mass_density,        averaging_system=sd.BOTH_AVERAGING_SYSTEMS, measurement_techniques=[sd.MT_CALCULATION], )
            sd.set_labeled_value( cursor, station_identifier, sd.Q_DYNAMIC_VISCOSITY,   label, dynamic_viscosity,   averaging_system=sd.BOTH_AVERAGING_SYSTEMS, measurement_techniques=[sd.MT_CALCULATION], )
            sd.set_labeled_value( cursor, station_identifier, sd.Q_KINEMATIC_VISCOSITY, label, kinematic_viscosity, averaging_system=sd.BOTH_AVERAGING_SYSTEMS, measurement_techniques=[sd.MT_CALCULATION], )
            sd.set_labeled_value( cursor, station_identifier, sd.Q_TEMPERATURE,         label, temperature,         averaging_system=sd.BOTH_AVERAGING_SYSTEMS, measurement_techniques=[sd.MT_ASSUMPTION],  )
            sd.set_labeled_value( cursor, station_identifier, sd.Q_SPEED_OF_SOUND,      label, speed_of_sound,      averaging_system=sd.BOTH_AVERAGING_SYSTEMS, measurement_techniques=[sd.MT_ASSUMPTION],  )

        for quantity in [ sd.Q_ROUGHNESS_HEIGHT,
                          sd.Q_INNER_LAYER_ROUGHNESS_HEIGHT,
                          sd.Q_OUTER_LAYER_ROUGHNESS_HEIGHT, ]:
            sd.set_labeled_value(
                cursor,
                station_identifier,
                quantity,
                sd.WALL_POINT_LABEL,
                sd.sdfloat(0.0),
                measurement_techniques=[sd.MT_ASSUMPTION],
            )

        sd.set_labeled_value( cursor, station_identifier, sd.Q_STREAMWISE_VELOCITY,    sd.WALL_POINT_LABEL,        sd.sdfloat( 0.0, 0.0 ),            averaging_system=sd.BOTH_AVERAGING_SYSTEMS, )
        sd.set_labeled_value( cursor, station_identifier, sd.Q_STREAMWISE_VELOCITY,    sd.CENTER_LINE_POINT_LABEL, maximum_velocity,                  averaging_system=sd.BOTH_AVERAGING_SYSTEMS, measurement_techniques=[mt_velocity], outlier=outlier,)
        sd.set_labeled_value( cursor, station_identifier, sd.Q_TRANSVERSE_COORDINATE,  sd.WALL_POINT_LABEL,        sd.sdfloat( 0.5*diameter.n, 0.0 ), averaging_system=sd.BOTH_AVERAGING_SYSTEMS, )
        sd.set_labeled_value( cursor, station_identifier, sd.Q_TRANSVERSE_COORDINATE,  sd.CENTER_LINE_POINT_LABEL, 0.0,                               averaging_system=sd.BOTH_AVERAGING_SYSTEMS, )
        sd.set_labeled_value( cursor, station_identifier, sd.Q_DISTANCE_FROM_WALL,     sd.WALL_POINT_LABEL,        sd.sdfloat( 0.0, 0.0 ),            averaging_system=sd.BOTH_AVERAGING_SYSTEMS, )
        sd.set_labeled_value( cursor, station_identifier, sd.Q_DISTANCE_FROM_WALL,     sd.CENTER_LINE_POINT_LABEL, 0.5*diameter,                      averaging_system=sd.BOTH_AVERAGING_SYSTEMS, )
        sd.set_labeled_value( cursor, station_identifier, sd.Q_OUTER_LAYER_COORDINATE, sd.WALL_POINT_LABEL,        sd.sdfloat( 0.0, 0.0 ),            averaging_system=sd.BOTH_AVERAGING_SYSTEMS, )
        sd.set_labeled_value( cursor, station_identifier, sd.Q_OUTER_LAYER_COORDINATE, sd.CENTER_LINE_POINT_LABEL, 1.0,                               averaging_system=sd.BOTH_AVERAGING_SYSTEMS, )

        sd.set_labeled_value( cursor, station_identifier, sd.Q_HEAT_FLUX,                             sd.WALL_POINT_LABEL, sd.sdfloat( 0.0, 0.0 ), averaging_system=sd.BOTH_AVERAGING_SYSTEMS, measurement_techniques=[sd.MT_ASSUMPTION], )
        sd.set_labeled_value( cursor, station_identifier, sd.Q_CENTER_LINE_TO_WALL_TEMPERATURE_RATIO, sd.WALL_POINT_LABEL, sd.sdfloat( 1.0, 0.0 ), averaging_system=sd.BOTH_AVERAGING_SYSTEMS, measurement_techniques=[sd.MT_ASSUMPTION], )
        sd.set_labeled_value( cursor, station_identifier, sd.Q_WALL_TO_RECOVERY_TEMPERATURE_RATIO,    sd.WALL_POINT_LABEL, sd.sdfloat( 1.0, 0.0 ), averaging_system=sd.BOTH_AVERAGING_SYSTEMS, measurement_techniques=[sd.MT_ASSUMPTION], )

# Set 2: wall shear stress data
shear_stress_filename = "../data/{:s}/wall_shear_stress_measurements.csv".format( study_identifier )
with open( shear_stress_filename, "r" ) as shear_stress_file:
    shear_stress_reader = csv.reader(
        shear_stress_file,
        delimiter=",",
        quotechar='"', \
        skipinitialspace=True,
    )
    next(shear_stress_reader)
    for shear_stress_row in shear_stress_reader:
        series_number += 1

        bulk_velocity                 = sd.sdfloat(shear_stress_row[0]) * 1.0e-2
        wall_shear_stress             = sd.sdfloat(shear_stress_row[1]) * 1.0e-1
        fanning_friction_factor       = sd.sdfloat(shear_stress_row[2]) * 2.0
        Re_bulk                       = sd.sdfloat(shear_stress_row[3])
        temperature                   = sd.sdfloat(shear_stress_row[4]) + sd.ABSOLUTE_ZERO
        working_fluid                 =        str(shear_stress_row[5])
        pipe                          =        str(shear_stress_row[6])

        diameter                       = pipes[pipe].diameter
        distance_between_pressure_taps = pipes[pipe].distance_between_pressure_taps
        development_length             = pipes[pipe].development_length()
        outer_layer_development_length = pipes[pipe].outer_layer_development_length()

        mass_density        = 2.0 * wall_shear_stress / ( fanning_friction_factor * bulk_velocity**2.0 )
        kinematic_viscosity = bulk_velocity * diameter / Re_bulk
        dynamic_viscosity   = mass_density * kinematic_viscosity

        volumetric_flow_rate = 0.25 * math.pi * diameter**2.0 * bulk_velocity

        friction_velocity    = ( wall_shear_stress / mass_density )**0.5
        viscous_length_scale = kinematic_viscosity / friction_velocity
        Re_tau               = 0.5 * diameter / viscous_length_scale

        outlier = False
        current_notes = []
        if ( working_fluid == "Air" and pipe == "S" ):
            outlier = True
            current_notes = [mass_density_note]

        series_identifier = sd.add_series(
            cursor,
            flow_class=flow_class,
            year=year,
            study_number=study_number,
            series_number=series_number,
            number_of_dimensions=2,
            coordinate_system=sd.CYLINDRICAL_COORDINATE_SYSTEM,
            outlier=outlier,
        )

        if ( working_fluid == "Air" ):
            sd.add_air_components( cursor, series_identifier )
        elif ( working_fluid == "Water" ):
            sd.add_working_fluid_component(
                cursor,
                series_identifier,
                sd.WATER_LIQUID,
            )
        elif ( working_fluid == "Thick oil" ):
            sd.set_working_fluid_name(
                cursor,
                series_identifier,
                "Stanton and Pannell thick oil",
            )

        # Without knowing precisely what "thick oil" is it is difficult to
        # assume anything else.
        speed_of_sound_measurement_technique = sd.MT_ASSUMPTION
        speed_of_sound = sd.sdfloat("inf")
        if ( working_fluid == "Air" ):
            speed_of_sound = sd.ideal_gas_speed_of_sound( temperature )
            speed_of_sound_measurement_technique = sd.MT_CALCULATION
        elif ( working_fluid == "Water" ):
            speed_of_sound = sd.liquid_water_speed_of_sound( temperature )
            speed_of_sound_measurement_technique = sd.MT_CALCULATION
        Ma_bulk = bulk_velocity     / speed_of_sound
        Ma_tau  = friction_velocity / speed_of_sound

        sd.update_series_geometry(
            cursor,
            series_identifier,
            sd.ELLIPTICAL_GEOMETRY
        )

        if ( distance_between_pressure_taps != None ):
            sd.set_series_value(
                cursor,
                series_identifier,
                sd.Q_DISTANCE_BETWEEN_PRESSURE_TAPS,
                distance_between_pressure_taps,
            )

        station_number = 1
        station_identifier = sd.add_station(
            cursor,
            flow_class=flow_class,
            year=year,
            study_number=study_number,
            series_number=series_number,
            station_number=station_number,
            outlier=outlier,
        )

        sd.mark_station_as_periodic( cursor, station_identifier )

        sd.set_station_value( cursor, station_identifier, sd.Q_DEVELOPMENT_LENGTH,             development_length,             measurement_techniques=[sd.MT_ASSUMPTION], notes=[development_length_note], )
        sd.set_station_value( cursor, station_identifier, sd.Q_OUTER_LAYER_DEVELOPMENT_LENGTH, outer_layer_development_length, measurement_techniques=[sd.MT_ASSUMPTION], notes=[development_length_note], )
        sd.set_station_value( cursor, station_identifier, sd.Q_HYDRAULIC_DIAMETER,             diameter,                                                                                                     outlier=outlier, )
        sd.set_station_value( cursor, station_identifier, sd.Q_ASPECT_RATIO,                   1.0,                                                                                                          outlier=outlier, )
        sd.set_station_value( cursor, station_identifier, sd.Q_BULK_VELOCITY,                  bulk_velocity,        averaging_system=sd.BOTH_AVERAGING_SYSTEMS,                                             outlier=outlier, )
        sd.set_station_value( cursor, station_identifier, sd.Q_BULK_REYNOLDS_NUMBER,           Re_bulk,              averaging_system=sd.BOTH_AVERAGING_SYSTEMS, measurement_techniques=[sd.MT_CALCULATION], outlier=outlier, )
        sd.set_station_value( cursor, station_identifier, sd.Q_BULK_MACH_NUMBER,               Ma_bulk,              averaging_system=sd.BOTH_AVERAGING_SYSTEMS, measurement_techniques=[sd.MT_CALCULATION], outlier=outlier, )
        sd.set_station_value( cursor, station_identifier, sd.Q_VOLUMETRIC_FLOW_RATE,           volumetric_flow_rate, averaging_system=sd.BOTH_AVERAGING_SYSTEMS,                                             outlier=outlier, )

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

        for quantity in [ sd.Q_ROUGHNESS_HEIGHT,
                          sd.Q_INNER_LAYER_ROUGHNESS_HEIGHT,
                          sd.Q_OUTER_LAYER_ROUGHNESS_HEIGHT, ]:
            sd.set_labeled_value(
                cursor,
                station_identifier,
                quantity,
                sd.WALL_POINT_LABEL,
                sd.sdfloat(0.0),
                measurement_techniques=[sd.MT_ASSUMPTION],
                outlier=outlier,
            )

        # Wall shear stress measurement technique
        #
        # p. 203
        #
        # \begin{quote}
        # To determine the amount of the surface friction two small holes were
        # made in the walls of the experimental portion of the pipe, one at
        # each extremity, at a known distance apart, and connected to a tilting
        # manometer.  \ldots  In this way the fall of pressure along a given
        # length of the pipe was determined, and from the known diameter of the
        # pipe the surface friction per unit area was calculated.
        # \end{quote}
        mt_wall_shear_stress = sd.MT_MOMENTUM_BALANCE

        sd.set_labeled_value( cursor, station_identifier, sd.Q_MASS_DENSITY,                          sd.WALL_POINT_LABEL, mass_density,                      averaging_system=sd.BOTH_AVERAGING_SYSTEMS,                                                                outlier=outlier, notes=current_notes, )
        sd.set_labeled_value( cursor, station_identifier, sd.Q_DYNAMIC_VISCOSITY,                     sd.WALL_POINT_LABEL, dynamic_viscosity,                 averaging_system=sd.BOTH_AVERAGING_SYSTEMS,                                                                outlier=outlier,                    )
        sd.set_labeled_value( cursor, station_identifier, sd.Q_KINEMATIC_VISCOSITY,                   sd.WALL_POINT_LABEL, kinematic_viscosity,               averaging_system=sd.BOTH_AVERAGING_SYSTEMS,                                                                outlier=outlier,                    )
        sd.set_labeled_value( cursor, station_identifier, sd.Q_TEMPERATURE,                           sd.WALL_POINT_LABEL, temperature,                       averaging_system=sd.BOTH_AVERAGING_SYSTEMS,                                                                outlier=outlier,                    )
        sd.set_labeled_value( cursor, station_identifier, sd.Q_SPEED_OF_SOUND,                        sd.WALL_POINT_LABEL, speed_of_sound,                    averaging_system=sd.BOTH_AVERAGING_SYSTEMS, measurement_techniques=[speed_of_sound_measurement_technique], outlier=outlier,                    )
        sd.set_labeled_value( cursor, station_identifier, sd.Q_STREAMWISE_VELOCITY,                   sd.WALL_POINT_LABEL, sd.sdfloat( 0.0,            0.0 ), averaging_system=sd.BOTH_AVERAGING_SYSTEMS,                                                                outlier=outlier,                    )
        sd.set_labeled_value( cursor, station_identifier, sd.Q_TRANSVERSE_COORDINATE,                 sd.WALL_POINT_LABEL, sd.sdfloat( 0.5*diameter.n, 0.0 ), averaging_system=sd.BOTH_AVERAGING_SYSTEMS,                                                                outlier=outlier,                    )
        sd.set_labeled_value( cursor, station_identifier, sd.Q_DISTANCE_FROM_WALL,                    sd.WALL_POINT_LABEL, sd.sdfloat( 0.0,            0.0 ), averaging_system=sd.BOTH_AVERAGING_SYSTEMS,                                                                outlier=outlier,                    )
        sd.set_labeled_value( cursor, station_identifier, sd.Q_OUTER_LAYER_COORDINATE,                sd.WALL_POINT_LABEL, sd.sdfloat( 0.0,            0.0 ), averaging_system=sd.BOTH_AVERAGING_SYSTEMS,                                                                outlier=outlier,                    )
        sd.set_labeled_value( cursor, station_identifier, sd.Q_SHEAR_STRESS,                          sd.WALL_POINT_LABEL, wall_shear_stress,                 averaging_system=sd.BOTH_AVERAGING_SYSTEMS, measurement_techniques=[mt_wall_shear_stress],                 outlier=outlier,                    )
        sd.set_labeled_value( cursor, station_identifier, sd.Q_FANNING_FRICTION_FACTOR,               sd.WALL_POINT_LABEL, fanning_friction_factor,           averaging_system=sd.BOTH_AVERAGING_SYSTEMS, measurement_techniques=[mt_wall_shear_stress],                 outlier=outlier,                    )
        sd.set_labeled_value( cursor, station_identifier, sd.Q_FRICTION_VELOCITY,                     sd.WALL_POINT_LABEL, friction_velocity,                 averaging_system=sd.BOTH_AVERAGING_SYSTEMS, measurement_techniques=[sd.MT_CALCULATION],                    outlier=outlier,                    )
        sd.set_labeled_value( cursor, station_identifier, sd.Q_VISCOUS_LENGTH_SCALE,                  sd.WALL_POINT_LABEL, viscous_length_scale,              averaging_system=sd.BOTH_AVERAGING_SYSTEMS, measurement_techniques=[sd.MT_CALCULATION],                    outlier=outlier,                    )
        sd.set_labeled_value( cursor, station_identifier, sd.Q_FRICTION_REYNOLDS_NUMBER,              sd.WALL_POINT_LABEL, Re_tau,                            averaging_system=sd.BOTH_AVERAGING_SYSTEMS, measurement_techniques=[sd.MT_CALCULATION],                    outlier=outlier,                    )
        sd.set_labeled_value( cursor, station_identifier, sd.Q_SEMI_LOCAL_FRICTION_REYNOLDS_NUMBER,   sd.WALL_POINT_LABEL, Re_tau,                            averaging_system=sd.BOTH_AVERAGING_SYSTEMS, measurement_techniques=[sd.MT_CALCULATION],                    outlier=outlier,                    )
        sd.set_labeled_value( cursor, station_identifier, sd.Q_FRICTION_MACH_NUMBER,                  sd.WALL_POINT_LABEL, Ma_tau,                            averaging_system=sd.BOTH_AVERAGING_SYSTEMS, measurement_techniques=[sd.MT_CALCULATION],                    outlier=outlier,                    )
        sd.set_labeled_value( cursor, station_identifier, sd.Q_HEAT_FLUX,                             sd.WALL_POINT_LABEL, sd.sdfloat( 0.0, 0.0 ),            averaging_system=sd.BOTH_AVERAGING_SYSTEMS, measurement_techniques=[sd.MT_ASSUMPTION],                                                         )
        sd.set_labeled_value( cursor, station_identifier, sd.Q_INNER_LAYER_HEAT_FLUX,                 sd.WALL_POINT_LABEL, sd.sdfloat( 0.0, 0.0 ),            averaging_system=sd.BOTH_AVERAGING_SYSTEMS, measurement_techniques=[sd.MT_ASSUMPTION],                                                         )
        sd.set_labeled_value( cursor, station_identifier, sd.Q_CENTER_LINE_TO_WALL_TEMPERATURE_RATIO, sd.WALL_POINT_LABEL, sd.sdfloat( 1.0, 0.0 ),            averaging_system=sd.BOTH_AVERAGING_SYSTEMS, measurement_techniques=[sd.MT_ASSUMPTION],                                                         )
        sd.set_labeled_value( cursor, station_identifier, sd.Q_WALL_TO_RECOVERY_TEMPERATURE_RATIO,    sd.WALL_POINT_LABEL, sd.sdfloat( 1.0, 0.0 ),            averaging_system=sd.BOTH_AVERAGING_SYSTEMS, measurement_techniques=[sd.MT_ASSUMPTION],                                                         )
        sd.set_labeled_value( cursor, station_identifier, sd.Q_FRICTION_TEMPERATURE,                  sd.WALL_POINT_LABEL, sd.sdfloat( 0.0, 0.0 ),            averaging_system=sd.BOTH_AVERAGING_SYSTEMS, measurement_techniques=[sd.MT_ASSUMPTION],                                                         )

conn.commit()
conn.close()
