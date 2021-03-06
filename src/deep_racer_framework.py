#
# DeepRacer Framework
#
# Version 1.0
#

import math


# -------------------------------------------------------------------------------
#
# CONSTANTS
#
# -------------------------------------------------------------------------------

class ParamNames:
    ALL_WHEELS_ON_TRACK = "all_wheels_on_track"
    CLOSEST_WAYPOINTS = "closest_waypoints"
    DISTANCE_FROM_CENTER = "distance_from_center"
    IS_CRASHED = "is_crashed"
    IS_LEFT_OF_CENTER = "is_left_of_center"
    IS_OFFTRACK = "is_offtrack"
    IS_REVERSED = "is_reversed"
    HEADING = "heading"
    PROGRESS = "progress"
    PROJECTION_DISTANCE = "projection_distance"
    SPEED = "speed"
    STEERING_ANGLE = "steering_angle"
    STEPS = "steps"
    TRACK_LENGTH = "track_length"
    TRACK_WIDTH = "track_width"
    WAYPOINTS = "waypoints"
    X = "x"
    Y = "y"
    CLOSEST_OBJECTS = "closest_objects"
    OBJECTS_DISTANCE = "objects_distance"
    OBJECTS_DISTANCE_FROM_CENTER = "objects_distance_from_center"
    OBJECTS_HEADING = "objects_heading"
    OBJECTS_LEFT_OF_CENTER = "objects_left_of_center"
    OBJECTS_LOCATION = "objects_location"
    OBJECTS_SPEED = "objects_speed"
    OBJECT_IN_CAMERA = "object_in_camera"


class RealWorld:
    STEPS_PER_SECOND = 15
    CAR_WIDTH = 0.21


# -------------------------------------------------------------------------------
#
# GEOMETRY
#
# -------------------------------------------------------------------------------

def get_distance_between_points(first, second):
    (x1, y1) = first
    (x2, y2) = second

    x_diff = x2 - x1
    y_diff = y2 - y1

    return math.sqrt(x_diff * x_diff + y_diff * y_diff)


def get_bearing_between_points(start, finish):
    (start_x, start_y) = start
    (finish_x, finish_y) = finish

    direction_in_radians = math.atan2(finish_y - start_y, finish_x - start_x)
    return math.degrees(direction_in_radians)


def get_angle_in_proper_range(angle):
    if angle >= 180:
        return angle - 360
    elif angle <= -180:
        return 360 + angle
    else:
        return angle


def get_turn_between_directions(current, required):
    difference = required - current
    return get_angle_in_proper_range(difference)


# -------------------------------------------------------------------------------
#
# WAYPOINT INFO CACHE
#
# -------------------------------------------------------------------------------

class ProcessedWaypoint:
    def __init__(self, point):
        (self.x, self.y) = point


def get_processed_waypoints(waypoints):
    processed_waypoints = []
    for w in waypoints:
        processed_waypoints.append(ProcessedWaypoint(w))
    return processed_waypoints


# -------------------------------------------------------------------------------
#
# REMEMBER A PREVIOUS STEP IN THIS EPISODE
#
# -------------------------------------------------------------------------------

class HistoricStep:
    def __init__(self, framework, previous_step):
        self.action_speed = framework.action_speed
        self.action_steering_angle = framework.action_steering_angle
        self.closest_waypoint_id = framework.closest_waypoint_id

        self.action_sequence_length = 1
        if previous_step:
            if (previous_step.action_speed == self.action_speed and
                    previous_step.action_steering_angle == self.action_steering_angle):
                self.action_sequence_length = previous_step.action_sequence_length + 1

# -------------------------------------------------------------------------------
#
# FRAMEWORK
#
# -------------------------------------------------------------------------------

class Framework:
    def __init__(self, params):
        # Real PRIVATE variables set here
        self._processed_waypoints = get_processed_waypoints(params[ParamNames.WAYPOINTS])
        self._history = []

        # Definitions only of variables to use in your reward method, real values are set during process_params()
        self.x = 0.0
        self.y = 0.0
        self.all_wheels_on_track = True
        self.previous_waypoint_id = 0
        self.previous_waypoint_x = 0.0
        self.previous_waypoint_y = 0.0
        self.next_waypoint_id = 0
        self.next_waypoint_x = 0.0
        self.next_waypoint_y = 0.0
        self.closest_waypoint_id = 0
        self.closest_waypoint_x = 0.0
        self.closest_waypoint_y = 0.0
        self.distance_from_closest_waypoint = 0.0
        self.distance_from_center = 0.0
        self.distance_from_edge = 0.0
        self.distance_from_extreme_edge = 0.0
        self.is_left_of_center = False
        self.is_right_of_center = False
        self.is_crashed = False
        self.is_off_track = False
        self.is_reversed = False
        self.steps = 0
        self.is_final_step = False
        self.progress = 0.0
        self.predicted_lap_time = 0.0
        self.waypoints = []
        self.track_length = 0.0
        self.track_width = 0.0
        self.action_speed = 0.0
        self.action_steering_angle = 0.0
        self.action_sequence_length = 0
        self.is_steering_left = False
        self.is_steering_right = False
        self.is_steering_straight = False
        self.heading = 0.0

        # Derived ideas :
        #
        #                 action_sequence_length
        #                 true_bearing    (from previous step history)
        #                 track_speed  &  progress_speed   (from previous step history)
        #                 skew    (difference between true_bearing and heading)
        #                 is_skidding   / is_spinning   / is_skidding_left    / is_skidding_right
        #                 has_skidded  / has_spun   (has is_skidding or is_spinning been True any time this episode?)
        #
        # projection_distance - WHAT'S THIS????
        #

    def process_params(self, params):
        self.x = float(params[ParamNames.X])
        self.y = float(params[ParamNames.Y])

        self.all_wheels_on_track = bool(params[ParamNames.ALL_WHEELS_ON_TRACK])

        self.previous_waypoint_id = int(params[ParamNames.CLOSEST_WAYPOINTS][0])
        self.previous_waypoint_x, self.previous_waypoint_y = params[ParamNames.WAYPOINTS][self.previous_waypoint_id]
        self.next_waypoint_id = int(params[ParamNames.CLOSEST_WAYPOINTS][1])
        self.next_waypoint_x, self.next_waypoint_y = params[ParamNames.WAYPOINTS][self.next_waypoint_id]

        distance_to_previous_waypoint = get_distance_between_points((self.x, self.y), params[ParamNames.WAYPOINTS][self.previous_waypoint_id])
        distance_to_next_waypoint = get_distance_between_points((self.x, self.y), params[ParamNames.WAYPOINTS][self.next_waypoint_id])
        if distance_to_previous_waypoint < distance_to_next_waypoint:
            self.closest_waypoint_id = self.previous_waypoint_id
            self.closest_waypoint_x = self.previous_waypoint_x
            self.closest_waypoint_y = self.previous_waypoint_y
            self.distance_from_closest_waypoint = distance_to_previous_waypoint
        else:
            self.closest_waypoint_id = self.next_waypoint_id
            self.closest_waypoint_x = self.next_waypoint_x
            self.closest_waypoint_y = self.next_waypoint_y
            self.distance_from_closest_waypoint = distance_to_next_waypoint

        self.distance_from_center = float(params[ParamNames.DISTANCE_FROM_CENTER])
        self.distance_from_edge = float(max(0.0, params[ParamNames.TRACK_WIDTH] / 2 - self.distance_from_center))
        self.distance_from_extreme_edge =\
            float(max(0.0, (params[ParamNames.TRACK_WIDTH] + RealWorld.CAR_WIDTH) / 2 - self.distance_from_center))

        self.is_left_of_center = bool(params[ParamNames.IS_LEFT_OF_CENTER])
        self.is_right_of_center = not self.is_left_of_center

        self.is_crashed = bool(params[ParamNames.IS_CRASHED])
        self.is_off_track = bool(params[ParamNames.IS_OFFTRACK])
        self.is_reversed = bool(params[ParamNames.IS_REVERSED])

        self.steps = int(round(params[ParamNames.STEPS]))
        self.progress = float(params[ParamNames.PROGRESS])
        self.is_final_step = self.progress == 100.0 or self.is_crashed or self.is_off_track or self.is_reversed
        if self.progress > 0:
            self.predicted_lap_time = round(100 / self.progress * self.steps / RealWorld.STEPS_PER_SECOND, 2)
        else:
            self.predicted_lap_time = 0.0

        self.waypoints = params[ParamNames.WAYPOINTS]
        self.track_length = params[ParamNames.TRACK_LENGTH]
        self.track_width = params[ParamNames.TRACK_WIDTH]

        self.action_speed = params[ParamNames.SPEED]
        self.action_steering_angle = params[ParamNames.STEERING_ANGLE]

        self.is_steering_straight = abs(self.action_steering_angle) < 0.01
        self.is_steering_left = self.action_steering_angle > 0 and not self.is_steering_straight
        self.is_steering_right = self.action_steering_angle < 0 and not self.is_steering_straight

        #
        # Record history
        #

        if self.steps <= 2 and len(self._history) > 2:
            self._history = []

        if self._history:
            previous_step = self._history[-1]
        else:
            previous_step = None

        this_step = HistoricStep(self, previous_step)
        self._history.append(this_step)

        #
        # Calculations that use the history
        #

        self.action_sequence_length = this_step.action_sequence_length


    def print_debug(self):
        #print("x, y                    ", round(self.x, 3), round(self.y, 3))
        #print("all_wheels_on_track     ", self.all_wheels_on_track)
        #print("previous_waypoint_id    ", self.previous_waypoint_id)
        #print("previous_waypoint_x, y  ", round(self.previous_waypoint_x, 3), round(self.previous_waypoint_y, 3))
        #print("next_waypoint_id        ", self.next_waypoint_id)
        #print("next_waypoint_x, y      ", round(self.next_waypoint_x, 3), round(self.next_waypoint_y, 3))
        #print("closest_waypoint_id     ", self.closest_waypoint_id)
        #print("closest_waypoint_x, y   ", round(self.closest_waypoint_x, 3), round(self.closest_waypoint_y, 3))
        #print("distance_from_closest_waypoint ", round(self.distance_from_closest_waypoint, 2))
        print("distance_from_center    ", round(self.distance_from_center, 2))
        print("distance_from_edge      ", round(self.distance_from_edge, 2))
        print("distance_from_extreme_edge     ", round(self.distance_from_extreme_edge, 2))
        print("is_left/right_of_center ", self.is_left_of_center, self.is_right_of_center)
        print("is_crashed / reversed   ", self.is_crashed, self.is_reversed)
        print("is_off_track            ", self.is_off_track)
        print("steps, is_final_step    ", self.steps, self.is_final_step)
        print("predicted_lap_time      ", round(self.predicted_lap_time, 2))
        print("progress                ", round(self.progress, 2))
        #print("waypoints  (SIZE)       ", len(self.waypoints))
        #print("track_length, width     ", round(self.track_length, 2), round(self.track_width, 2))
        print("action_speed            ", round(self.action_speed, 2))
        print("action_steering_angle   ", round(self.action_steering_angle, 1))
        print("action_sequence_length  ", self.action_sequence_length)
        print("is_steering_left/right  ", self.is_steering_left, self.is_steering_right)
        print("is_steering_straight    ", self.is_steering_straight)




# -------------------------------------------------------------------------------
#
# REWARD FUNCTION MASTER WRAPPER
#
# -------------------------------------------------------------------------------

def reward_function(params):
    global framework_global
    if not framework_global:
        framework_global = Framework(params)
    framework_global.process_params(params)
    raw_reward = float(get_reward(framework_global))
    if raw_reward > 0:
        return raw_reward
    else:
        tiny_reward = 0.0001
        print("WARNING - Invalid reward " + str(raw_reward) + " replaced with " + str(tiny_reward))
        return tiny_reward


framework_global = None


# -------------------------------------------------------------------------------
#
# YOUR REWARD FUNCTION GOES HERE ... ... ... ...
#
# -------------------------------------------------------------------------------

def get_reward(framework: Framework):
    framework.print_debug()
    return framework.steps * 2
