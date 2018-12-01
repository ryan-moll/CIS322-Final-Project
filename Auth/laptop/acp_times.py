import arrow

def open_time(control_dist_km, brevet_dist_km, brevet_start_time):
    if control_dist_km > brevet_dist_km:                                            # If the control distance exceeds the total brevet distance but by a safe amount
        control_dist_km = brevet_dist_km                                            # Just use the total brevet distance for the calculation
    control_open_time = 0                                                           # Open time to be returned. Unit is hours.
    alt_distance = control_dist_km                                                  # Keep track of difference in distance
    open_dict = {200:34, 400:32, 600:30, 1000:28, 1300:26}                          # Key = distance boundaries, Value = max speed
    last_distance = 0                                                               # Store the last used distance boundary
    while control_dist_km > 0:                                                      # While there is still distance left to calculate
        for distance in open_dict:                                                  # Loop through all of the possible distances
            if control_dist_km > distance:                                          # If the distance is larger than current distance boundary
                control_open_time += (distance-last_distance)/open_dict[distance]   # Add the size of that distance boundary divided by its speed to the finish time
                alt_distance -= (distance-last_distance)                            # Save the remainder
                last_distance = distance                                            # Store the current key for the next loop
            else:                                                                   # Distance is between the current boundary and last boundary. Last time our loop will run
                control_open_time += alt_distance/open_dict[distance]               # Add the remaining distance divided by the speed of the current distance boundary
                control_dist_km = 0                                                 # Set control distance to 0 to break the while loop
                break                                                               # No distance left. Leave the for loop
    hours = int(control_open_time)                                                  # Retrieve the integer of control_open_time as the hour value
    minutes = int((control_open_time*60)%60)                                        # Multiply the decemal by 60 to get the fraction of an hour and mod to reurn that value in minutes
    seconds = int((control_open_time*3600)%60)                                      # Get the seconds value
    date_time = arrow.get(brevet_start_time, 'YYYY-MM-DD HH:mm')                    # Create an arrow object based on the given start time
    date_time = date_time.shift(hours=+hours, minutes=+minutes)                     # Shift the start time by hours and minutes
    date_time = date_time.replace(tzinfo='US/Pacific')                              # Change the timezone to PST
    if seconds >= 30:                                                               # If there are more than 30 seconds in the remainder
        date_time = date_time.shift(minutes=+1)                                     # Round up the start time to the nearest minute
    return date_time.isoformat()


def close_time(control_dist_km, brevet_dist_km, brevet_start_time):
    if control_dist_km > brevet_dist_km:                                            # If the control distance exceeds the total brevet distance but by a safe amount
        control_dist_km = brevet_dist_km                                            # Just use the total brevet distance for the calculation
    special_dict = {1000:4500, 600:2400, 400:1620, 300:1200, 200:810}               # Special cases: End distance and corrosponding shift in seconds
    control_close_time = 0                                                          # Close time to be returned. Unit is hours.
    alt_distance = control_dist_km                                                  # Keep track of difference in distance
    temp = control_dist_km                                                          # Save control distance for later
    close_dict = {600:15, 1000:11.428, 1300:13.333}                                 # Key = distance boundaries, Value = max speed
    last_distance = 0                                                               # Store the last used distance boundary
    while control_dist_km > 0:                                                      # While there is still distance left to calculate
        for distance in close_dict:                                                 # Loop through all of the possible distances
            if control_dist_km > distance:                                          # If the distance is larger than current distance boundary
                control_close_time += (distance-last_distance)/close_dict[distance] # Add the size of that distance boundary divided by its speed to the finish time
                alt_distance -= (distance-last_distance)                            # Save the remainder
                last_distance = distance                                            # Store the current key for the next loop
            else:                                                                   # Distance is between the current boundary and last boundary. Last time our loop will run
                control_close_time += alt_distance/close_dict[distance]             # Add the remaining distance divided by the speed of the current distance boundary
                control_dist_km = 0                                                 # Set control distance to 0 to break the while loop
                break                                                               # No distance left. Leave the for loop
    hours = int(control_close_time)                                                 # Retrieve the integer of control_close_time as the hour value
    minutes = int((control_close_time*60)%60)                                       # Multiply the decemal by 60 to get the fraction of an hour and mod to reurn that value in minutes
    seconds = int((control_close_time*3600)%60)                                     # Get the seconds value
    if temp == 0:                                                                   # If the given checkpoint distance is 0
        hours = 1                                                                   # Shift close time by an hour
    if temp == brevet_dist_km:                                                      # If the checkpoint is at the end of the course
        hours = seconds = 0                                                         # Ignore the calculations we did and-
        minutes = special_dict[brevet_dist_km]                                      # use the special case times provided by ACP.
    date_time = arrow.get(brevet_start_time, 'YYYY-MM-DD HH:mm')                    # Create an arrow object based on the given start time
    date_time = date_time.shift(hours=+hours, minutes=+minutes)                     # Shift the start time by hours and minutes
    date_time = date_time.replace(tzinfo='US/Pacific')                              # Change the timezone to PST
    if seconds >= 30:                                                               # If there are more than 30 seconds in the remainder
        date_time = date_time.shift(minutes=+1)                                     # Round up the start time to the nearest minute
    return date_time.isoformat()
