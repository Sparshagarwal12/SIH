#!/usr/bin/env python
# coding: utf-8

# In[2]:


import os
import datetime as dt
try:
    from importlib import reload
except ImportError:
    try:
        from imp import reload
    except ImportError:
        pass

import numpy as np
import pandas as pd
import warnings

from pvlib import atmosphere
from pvlib.tools import datetime_to_djd, djd_to_datetime


# In[8]:


NS_PER_HR = 1.e9 * 3600.


# In[9]:


def get_solarposition(time, latitude, longitude,
                      altitude=None, pressure=None,
                      method='nrel_numpy',
                      temperature=12, **kwargs):

    if altitude is None and pressure is None:
        altitude = 0.
        pressure = 101325.
    elif altitude is None:
        altitude = atmosphere.pres2alt(pressure)
    elif pressure is None:
        pressure = atmosphere.alt2pres(altitude)

    method = method.lower()
    if isinstance(time, dt.datetime):
        time = pd.DatetimeIndex([time, ])

    if method == 'nrel_c':
        ephem_df = spa_c(time, latitude, longitude, pressure, temperature,
                         **kwargs)
    elif method == 'nrel_numba':
        ephem_df = spa_python(time, latitude, longitude, altitude,
                              pressure, temperature,
                              how='numba', **kwargs)
    elif method == 'nrel_numpy':
        ephem_df = spa_python(time, latitude, longitude, altitude,
                              pressure, temperature,
                              how='numpy', **kwargs)
    elif method == 'pyephem':
        ephem_df = pyephem(time, latitude, longitude,
                           altitude=altitude,
                           pressure=pressure,
                           temperature=temperature, **kwargs)
    elif method == 'ephemeris':
        ephem_df = ephemeris(time, latitude, longitude, pressure, temperature,
                             **kwargs)
    else:
        raise ValueError('Invalid solar position method')

    return ephem_df


# In[10]:


def spa_c(time, latitude, longitude, pressure=101325, altitude=0,
          temperature=12, delta_t=67.0,
          raw_spa_output=False):

    # Added by Rob Andrews (@Calama-Consulting), Calama Consulting, 2014
    # Edited by Will Holmgren (@wholmgren), University of Arizona, 2014
    # Edited by Tony Lorenzo (@alorenzo175), University of Arizona, 2015

    try:
        from pvlib.spa_c_files.spa_py import spa_calc
    except ImportError:
        raise ImportError('Could not import built-in SPA calculator. ' +
                          'You may need to recompile the SPA code.')

    # if localized, convert to UTC. otherwise, assume UTC.
    try:
        time_utc = time.tz_convert('UTC')
    except TypeError:
        time_utc = time

    spa_out = []

    for date in time_utc:
        spa_out.append(spa_calc(year=date.year,
                                month=date.month,
                                day=date.day,
                                hour=date.hour,
                                minute=date.minute,
                                second=date.second,
                                time_zone=0,  # date uses utc time
                                latitude=latitude,
                                longitude=longitude,
                                elevation=altitude,
                                pressure=pressure / 100,
                                temperature=temperature,
                                delta_t=delta_t
                                ))

    spa_df = pd.DataFrame(spa_out, index=time)

    if raw_spa_output:
        # rename "time_zone" from raw output from spa_c_files.spa_py.spa_calc()
        # to "timezone" to match the API of pvlib.solarposition.spa_c()
        return spa_df.rename(columns={'time_zone': 'timezone'})
    else:
        dfout = pd.DataFrame({'azimuth': spa_df['azimuth'],
                              'apparent_zenith': spa_df['zenith'],
                              'apparent_elevation': spa_df['e'],
                              'elevation': spa_df['e0'],
                              'zenith': 90 - spa_df['e0']})

        return dfout


def _spa_python_import(how):
    """Compile spa.py appropriately"""

    from pvlib import spa

    # check to see if the spa module was compiled with numba
    using_numba = spa.USE_NUMBA

    if how == 'numpy' and using_numba:
        # the spa module was compiled to numba code, so we need to
        # reload the module without compiling
        # the PVLIB_USE_NUMBA env variable is used to tell the module
        # to not compile with numba
        warnings.warn('Reloading spa to use numpy')
        os.environ['PVLIB_USE_NUMBA'] = '0'
        spa = reload(spa)
        del os.environ['PVLIB_USE_NUMBA']
    elif how == 'numba' and not using_numba:
        # The spa module was not compiled to numba code, so set
        # PVLIB_USE_NUMBA so it does compile to numba on reload.
        warnings.warn('Reloading spa to use numba')
        os.environ['PVLIB_USE_NUMBA'] = '1'
        spa = reload(spa)
        del os.environ['PVLIB_USE_NUMBA']
    elif how != 'numba' and how != 'numpy':
        raise ValueError("how must be either 'numba' or 'numpy'")

    return spa


# In[11]:


def spa_python(time, latitude, longitude,
               altitude=0, pressure=101325, temperature=12, delta_t=67.0,
               atmos_refract=None, how='numpy', numthreads=4, **kwargs):

    # Added by Tony Lorenzo (@alorenzo175), University of Arizona, 2015

    lat = latitude
    lon = longitude
    elev = altitude
    pressure = pressure / 100  # pressure must be in millibars for calculation

    atmos_refract = atmos_refract or 0.5667

    if not isinstance(time, pd.DatetimeIndex):
        try:
            time = pd.DatetimeIndex(time)
        except (TypeError, ValueError):
            time = pd.DatetimeIndex([time, ])

    unixtime = np.array(time.astype(np.int64)/10**9)

    spa = _spa_python_import(how)

    delta_t = delta_t or spa.calculate_deltat(time.year, time.month)

    app_zenith, zenith, app_elevation, elevation, azimuth, eot = spa.solar_position(
        unixtime, lat, lon, elev, pressure, temperature, delta_t, atmos_refract, numthreads)

    result = pd.DataFrame({'apparent_zenith': app_zenith, 'zenith': zenith,
                           'apparent_elevation': app_elevation,
                           'elevation': elevation, 'azimuth': azimuth,
                           'equation_of_time': eot},
                          index=time)

    return result


# In[12]:


def sun_rise_set_transit_spa(times, latitude, longitude, how='numpy',
                             delta_t=67.0, numthreads=4):

    # Added by Tony Lorenzo (@alorenzo175), University of Arizona, 2015

    lat = latitude
    lon = longitude

    # times must be localized
    if times.tz:
        tzinfo = times.tz
    else:
        raise ValueError('times must be localized')

    # must convert to midnight UTC on day of interest
    utcday = pd.DatetimeIndex(times.date).tz_localize('UTC')
    unixtime = np.array(utcday.astype(np.int64)/10**9)

    spa = _spa_python_import(how)

    delta_t = delta_t or spa.calculate_deltat(times.year, times.month)

    transit, sunrise, sunset = spa.transit_sunrise_sunset(
        unixtime, lat, lon, delta_t, numthreads)

    # arrays are in seconds since epoch format, need to conver to timestamps
    transit = pd.to_datetime(transit*1e9, unit='ns', utc=True).tz_convert(
        tzinfo).tolist()
    sunrise = pd.to_datetime(sunrise*1e9, unit='ns', utc=True).tz_convert(
        tzinfo).tolist()
    sunset = pd.to_datetime(sunset*1e9, unit='ns', utc=True).tz_convert(
        tzinfo).tolist()

    return pd.DataFrame(index=times, data={'sunrise': sunrise,
                                           'sunset': sunset,
                                           'transit': transit})


# In[13]:


def _ephem_convert_to_seconds_and_microseconds(date):
    # utility from unreleased PyEphem 3.6.7.1
    """Converts a PyEphem date into seconds"""
    microseconds = int(round(24 * 60 * 60 * 1000000 * date))
    seconds, microseconds = divmod(microseconds, 1000000)
    seconds -= 2209032000  # difference between epoch 1900 and epoch 1970
    return seconds, microseconds


# In[14]:


def _ephem_to_timezone(date, tzinfo):
    # utility from unreleased PyEphem 3.6.7.1
    """"Convert a PyEphem Date into a timezone aware python datetime"""
    seconds, microseconds = _ephem_convert_to_seconds_and_microseconds(date)
    date = dt.datetime.fromtimestamp(seconds, tzinfo)
    date = date.replace(microsecond=microseconds)
    return date


# In[15]:


def _ephem_setup(latitude, longitude, altitude, pressure, temperature,
                 horizon):
    import ephem
    # initialize a PyEphem observer
    obs = ephem.Observer()
    obs.lat = str(latitude)
    obs.lon = str(longitude)
    obs.elevation = altitude
    obs.pressure = pressure / 100.  # convert to mBar
    obs.temp = temperature
    obs.horizon = horizon

    # the PyEphem sun
    sun = ephem.Sun()
    return obs, sun


# In[16]:


def sun_rise_set_transit_ephem(times, latitude, longitude,
                               next_or_previous='next',
                               altitude=0,
                               pressure=101325,
                               temperature=12, horizon='0:00'):

    try:
        import ephem
    except ImportError:
        raise ImportError('PyEphem must be installed')

    # times must be localized
    if times.tz:
        tzinfo = times.tz
    else:
        raise ValueError('times must be localized')

    obs, sun = _ephem_setup(latitude, longitude, altitude,
                            pressure, temperature, horizon)
    # create lists of sunrise and sunset time localized to time.tz
    if next_or_previous.lower() == 'next':
        rising = obs.next_rising
        setting = obs.next_setting
        transit = obs.next_transit
    elif next_or_previous.lower() == 'previous':
        rising = obs.previous_rising
        setting = obs.previous_setting
        transit = obs.previous_transit
    else:
        raise ValueError("next_or_previous must be either 'next' or" +
                         " 'previous'")

    sunrise = []
    sunset = []
    trans = []
    for thetime in times:
        thetime = thetime.to_pydatetime()
        # pyephem drops timezone when converting to its internal datetime
        # format, so handle timezone explicitly here
        obs.date = ephem.Date(thetime - thetime.utcoffset())
        sunrise.append(_ephem_to_timezone(rising(sun), tzinfo))
        sunset.append(_ephem_to_timezone(setting(sun), tzinfo))
        trans.append(_ephem_to_timezone(transit(sun), tzinfo))

    return pd.DataFrame(index=times, data={'sunrise': sunrise,
                                           'sunset': sunset,
                                           'transit': trans})


# In[17]:


def pyephem(time, latitude, longitude, altitude=0, pressure=101325,
            temperature=12, horizon='+0:00'):

    # Written by Will Holmgren (@wholmgren), University of Arizona, 2014
    try:
        import ephem
    except ImportError:
        raise ImportError('PyEphem must be installed')

    # if localized, convert to UTC. otherwise, assume UTC.
    try:
        time_utc = time.tz_convert('UTC')
    except TypeError:
        time_utc = time

    sun_coords = pd.DataFrame(index=time)

    obs, sun = _ephem_setup(latitude, longitude, altitude,
                            pressure, temperature, horizon)

    # make and fill lists of the sun's altitude and azimuth
    # this is the pressure and temperature corrected apparent alt/az.
    alts = []
    azis = []
    for thetime in time_utc:
        obs.date = ephem.Date(thetime)
        sun.compute(obs)
        alts.append(sun.alt)
        azis.append(sun.az)

    sun_coords['apparent_elevation'] = alts
    sun_coords['apparent_azimuth'] = azis

    # redo it for p=0 to get no atmosphere alt/az
    obs.pressure = 0
    alts = []
    azis = []
    for thetime in time_utc:
        obs.date = ephem.Date(thetime)
        sun.compute(obs)
        alts.append(sun.alt)
        azis.append(sun.az)

    sun_coords['elevation'] = alts
    sun_coords['azimuth'] = azis

    # convert to degrees. add zenith
    sun_coords = np.rad2deg(sun_coords)
    sun_coords['apparent_zenith'] = 90 - sun_coords['apparent_elevation']
    sun_coords['zenith'] = 90 - sun_coords['elevation']

    return sun_coords


# In[18]:


def ephemeris(time, latitude, longitude, pressure=101325, temperature=12):

    Latitude = latitude
    Longitude = -1 * longitude

    Abber = 20 / 3600.
    LatR = np.radians(Latitude)

    # the SPA algorithm needs time to be expressed in terms of
    # decimal UTC hours of the day of the year.

    # if localized, convert to UTC. otherwise, assume UTC.
    try:
        time_utc = time.tz_convert('UTC')
    except TypeError:
        time_utc = time

    # strip out the day of the year and calculate the decimal hour
    DayOfYear = time_utc.dayofyear
    DecHours = (time_utc.hour + time_utc.minute/60. + time_utc.second/3600. +
                time_utc.microsecond/3600.e6)

    # np.array needed for pandas > 0.20
    UnivDate = np.array(DayOfYear)
    UnivHr = np.array(DecHours)

    Yr = np.array(time_utc.year) - 1900
    YrBegin = 365 * Yr + np.floor((Yr - 1) / 4.) - 0.5

    Ezero = YrBegin + UnivDate
    T = Ezero / 36525.

    # Calculate Greenwich Mean Sidereal Time (GMST)
    GMST0 = 6 / 24. + 38 / 1440. + (
        45.836 + 8640184.542 * T + 0.0929 * T ** 2) / 86400.
    GMST0 = 360 * (GMST0 - np.floor(GMST0))
    GMSTi = np.mod(GMST0 + 360 * (1.0027379093 * UnivHr / 24.), 360)

    # Local apparent sidereal time
    LocAST = np.mod((360 + GMSTi - Longitude), 360)

    EpochDate = Ezero + UnivHr / 24.
    T1 = EpochDate / 36525.

    ObliquityR = np.radians(
        23.452294 - 0.0130125 * T1 - 1.64e-06 * T1 ** 2 + 5.03e-07 * T1 ** 3)
    MlPerigee = 281.22083 + 4.70684e-05 * EpochDate + 0.000453 * T1 ** 2 + (
        3e-06 * T1 ** 3)
    MeanAnom = np.mod((358.47583 + 0.985600267 * EpochDate - 0.00015 *
                       T1 ** 2 - 3e-06 * T1 ** 3), 360)
    Eccen = 0.01675104 - 4.18e-05 * T1 - 1.26e-07 * T1 ** 2
    EccenAnom = MeanAnom
    E = 0

    while np.max(abs(EccenAnom - E)) > 0.0001:
        E = EccenAnom
        EccenAnom = MeanAnom + np.degrees(Eccen)*np.sin(np.radians(E))

    TrueAnom = (
        2 * np.mod(np.degrees(np.arctan2(((1 + Eccen) / (1 - Eccen)) ** 0.5 *
                                         np.tan(np.radians(EccenAnom) / 2.), 1)), 360))
    EcLon = np.mod(MlPerigee + TrueAnom, 360) - Abber
    EcLonR = np.radians(EcLon)
    DecR = np.arcsin(np.sin(ObliquityR)*np.sin(EcLonR))

    RtAscen = np.degrees(np.arctan2(np.cos(ObliquityR)*np.sin(EcLonR),
                                    np.cos(EcLonR)))

    HrAngle = LocAST - RtAscen
    HrAngleR = np.radians(HrAngle)
    HrAngle = HrAngle - (360 * ((abs(HrAngle) > 180)))

    SunAz = np.degrees(np.arctan2(-np.sin(HrAngleR),
                                  np.cos(LatR)*np.tan(DecR) -
                                  np.sin(LatR)*np.cos(HrAngleR)))
    SunAz[SunAz < 0] += 360

    SunEl = np.degrees(np.arcsin(
        np.cos(LatR) * np.cos(DecR) * np.cos(HrAngleR) +
        np.sin(LatR) * np.sin(DecR)))

    SolarTime = (180 + HrAngle) / 15.

    # Calculate refraction correction
    Elevation = SunEl
    TanEl = pd.Series(np.tan(np.radians(Elevation)), index=time_utc)
    Refract = pd.Series(0, index=time_utc)

    Refract[(Elevation > 5) & (Elevation <= 85)] = (
        58.1/TanEl - 0.07/(TanEl**3) + 8.6e-05/(TanEl**5))

    Refract[(Elevation > -0.575) & (Elevation <= 5)] = (
        Elevation *
        (-518.2 + Elevation*(103.4 + Elevation*(-12.79 + Elevation*0.711))) +
        1735)

    Refract[(Elevation > -1) & (Elevation <= -0.575)] = -20.774 / TanEl

    Refract *= (283/(273. + temperature)) * (pressure/101325.) / 3600.

    ApparentSunEl = SunEl + Refract

    # make output DataFrame
    DFOut = pd.DataFrame(index=time_utc)
    DFOut['apparent_elevation'] = ApparentSunEl
    DFOut['elevation'] = SunEl
    DFOut['azimuth'] = SunAz
    DFOut['apparent_zenith'] = 90 - ApparentSunEl
    DFOut['zenith'] = 90 - SunEl
    DFOut['solar_time'] = SolarTime
    DFOut.index = time

    return DFOut


# In[19]:


def calc_time(lower_bound, upper_bound, latitude, longitude, attribute, value,
              altitude=0, pressure=101325, temperature=12, horizon='+0:00',
              xtol=1.0e-12):

    try:
        import scipy.optimize as so
    except ImportError:
        raise ImportError('The calc_time function requires scipy')

    obs, sun = _ephem_setup(latitude, longitude, altitude,
                            pressure, temperature, horizon)

    def compute_attr(thetime, target, attr):
        obs.date = thetime
        sun.compute(obs)
        return getattr(sun, attr) - target

    lb = datetime_to_djd(lower_bound)
    ub = datetime_to_djd(upper_bound)

    djd_root = so.brentq(compute_attr, lb, ub,
                         (value, attribute), xtol=xtol)

    return djd_to_datetime(djd_root)


# In[20]:


def pyephem_earthsun_distance(time):

    import ephem

    sun = ephem.Sun()
    earthsun = []
    for thetime in time:
        sun.compute(ephem.Date(thetime))
        earthsun.append(sun.earth_distance)

    return pd.Series(earthsun, index=time)


# In[21]:


def nrel_earthsun_distance(time, how='numpy', delta_t=67.0, numthreads=4):

    if not isinstance(time, pd.DatetimeIndex):
        try:
            time = pd.DatetimeIndex(time)
        except (TypeError, ValueError):
            time = pd.DatetimeIndex([time, ])

    unixtime = np.array(time.astype(np.int64)/10**9)

    spa = _spa_python_import(how)

    delta_t = delta_t or spa.calculate_deltat(time.year, time.month)

    dist = spa.earthsun_distance(unixtime, delta_t, numthreads)

    dist = pd.Series(dist, index=time)

    return dist


def _calculate_simple_day_angle(dayofyear, offset=1):

    return (2. * np.pi / 365.) * (dayofyear - offset)


# In[22]:


def equation_of_time_spencer71(dayofyear):

    day_angle = _calculate_simple_day_angle(dayofyear)
    # convert from radians to minutes per day = 24[h/day] * 60[min/h] / 2 / pi
    eot = (1440.0 / 2 / np.pi) * (
        0.0000075 +
        0.001868 * np.cos(day_angle) - 0.032077 * np.sin(day_angle) -
        0.014615 * np.cos(2.0 * day_angle) - 0.040849 * np.sin(2.0 * day_angle)
    )
    return eot


# In[23]:


def equation_of_time_pvcdrom(dayofyear):

    # day angle relative to Vernal Equinox, typically March 22 (day number 81)
    bday = _calculate_simple_day_angle(
        dayofyear) - (2.0 * np.pi / 365.0) * 80.0
    # same value but about 2x faster than Spencer (1971)
    return 9.87 * np.sin(2.0 * bday) - 7.53 * np.cos(bday) - 1.5 * np.sin(bday)


# In[24]:


def declination_spencer71(dayofyear):

    day_angle = _calculate_simple_day_angle(dayofyear)
    return (
        0.006918 -
        0.399912 * np.cos(day_angle) + 0.070257 * np.sin(day_angle) -
        0.006758 * np.cos(2. * day_angle) + 0.000907 * np.sin(2. * day_angle) -
        0.002697 * np.cos(3. * day_angle) + 0.00148 * np.sin(3. * day_angle)
    )


# In[25]:


def declination_cooper69(dayofyear):

    day_angle = _calculate_simple_day_angle(dayofyear)
    dec = np.deg2rad(23.45 * np.sin(day_angle + (2.0 * np.pi / 365.0) * 285.0))
    return dec


# In[26]:


def solar_azimuth_analytical(latitude, hourangle, declination, zenith):

    numer = (np.cos(zenith) * np.sin(latitude) - np.sin(declination))
    denom = (np.sin(zenith) * np.cos(latitude))

    # cases that would generate new NaN values are safely ignored here
    # since they are dealt with further below
    with np.errstate(invalid='ignore', divide='ignore'):
        cos_azi = numer / denom

    # when zero division occurs, use the limit value of the analytical
    # expression
    cos_azi = np.where(np.isclose(
        denom,    0.0, rtol=0.0, atol=1e-8),  1.0, cos_azi)

    # when too many round-ups in floating point math take cos_azi beyond
    # 1.0, use 1.0
    cos_azi = np.where(np.isclose(
        cos_azi,  1.0, rtol=0.0, atol=1e-8),  1.0, cos_azi)
    cos_azi = np.where(np.isclose(
        cos_azi, -1.0, rtol=0.0, atol=1e-8), -1.0, cos_azi)

    # when NaN values occur in input, ignore and pass to output
    with np.errstate(invalid='ignore'):
        sign_ha = np.sign(hourangle)

    return sign_ha * np.arccos(cos_azi) + np.pi


# In[27]:


def solar_zenith_analytical(latitude, hourangle, declination):

    return np.arccos(
        np.cos(declination) * np.cos(latitude) * np.cos(hourangle) +
        np.sin(declination) * np.sin(latitude)
    )


# In[28]:


def hour_angle(times, longitude, equation_of_time):

    naive_times = times.tz_localize(None)  # naive but still localized
    # hours - timezone = (times - normalized_times) - (naive_times - times)
    hrs_minus_tzs = 1 / NS_PER_HR * (
        2 * times.astype(np.int64) - times.normalize().astype(np.int64) -
        naive_times.astype(np.int64))
    # ensure array return instead of a version-dependent pandas <T>Index
    return np.asarray(
        15. * (hrs_minus_tzs - 12.) + longitude + equation_of_time / 4.)


# In[29]:


def _hour_angle_to_hours(times, hourangle, longitude, equation_of_time):
    """converts hour angles in degrees to hours as a numpy array"""
    naive_times = times.tz_localize(None)  # naive but still localized
    tzs = 1 / NS_PER_HR * (
        naive_times.astype(np.int64) - times.astype(np.int64))
    hours = (hourangle - longitude - equation_of_time / 4.) / 15. + 12. + tzs
    return np.asarray(hours)


# In[30]:


def _local_times_from_hours_since_midnight(times, hours):
    """
    converts hours since midnight from an array of floats to localized times
    """
    tz_info = times.tz  # pytz timezone info
    naive_times = times.tz_localize(None)  # naive but still localized
    # normalize local, naive times to previous midnight and add the hours until
    # sunrise, sunset, and transit
    return pd.DatetimeIndex(
        (naive_times.normalize().astype(np.int64) +
         (hours * NS_PER_HR).astype(np.int64)).astype('datetime64[ns]'),
        tz=tz_info)


# In[31]:


def _times_to_hours_after_local_midnight(times):
    """convert local pandas datetime indices to array of hours as floats"""
    times = times.tz_localize(None)
    hrs = 1 / NS_PER_HR * (
        times.astype(np.int64) - times.normalize().astype(np.int64))
    return np.array(hrs)


# In[32]:


def sun_rise_set_transit_geometric(times, latitude, longitude, declination,
                                   equation_of_time):
    latitude_rad = np.radians(latitude)  # radians
    sunset_angle_rad = np.arccos(-np.tan(declination) * np.tan(latitude_rad))
    sunset_angle = np.degrees(sunset_angle_rad)  # degrees
    # solar noon is at hour angle zero
    # so sunrise is just negative of sunset
    sunrise_angle = -sunset_angle
    sunrise_hour = _hour_angle_to_hours(
        times, sunrise_angle, longitude, equation_of_time)
    sunset_hour = _hour_angle_to_hours(
        times, sunset_angle, longitude, equation_of_time)
    transit_hour = _hour_angle_to_hours(times, 0, longitude, equation_of_time)
    sunrise = _local_times_from_hours_since_midnight(times, sunrise_hour)
    sunset = _local_times_from_hours_since_midnight(times, sunset_hour)
    transit = _local_times_from_hours_since_midnight(times, transit_hour)
    return sunrise, sunset, transit


# In[33]:


# res = get_solarposition(5, 40.7719472, -73.9735199)
# # print(res)

# # using list
# l = res.values.tolist()[0]
# # print(l)

# apparent_zenith = l[0]
# zenith = l[1]
# apparent_elevation = l[2]
# elevation = l[3]
# azimuth = l[4]
# equation_of_time = l[5]

# print([apparent_zenith, zenith, apparent_elevation,
#        elevation, azimuth, equation_of_time])

# print('\n\n')
# # using dictionary

# d = res.to_dict()
# # print(d)
# dic = {k: list(v.values())[0] for k, v in d.items()}
# # print(dic)

# for k, v in d.items():
#     print(k, '=', v)
