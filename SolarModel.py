# -*- coding: utf-8 -*-
"""
Created on Fri Sep 16 21:29:51 2022

@author: Matt Dionne mjdionne@gmail.com
"""
import pandas as pd
import requests
import streamlit as st
import datetime
import numpy as np
import calendar
import altair as alt
from decimal import Decimal

dfJson = pd.DataFrame()
dfFixeddata = pd.DataFrame()
dfActivecase = pd.DataFrame()
dfCaseInputs = pd.DataFrame()


if 'caseIndex' not in st.session_state:
    st.session_state.caseIndex = 0

if 'collectionofCases' not in st.session_state:
    st.session_state.collectionofCases = []

if 'collectionofCaseData' not in st.session_state:
    st.session_state.collectionofCaseData = []

if 'caseCatalog' not in st.session_state:
        st.session_state.caseCatalog = []

if 'compareCaseIndex' not in st.session_state:
        st.session_state.compareCaseIndex = 0

if 'displayRunCase' not in st.session_state:
        st.session_state.displayRunCase = False

if 'displayViewCase' not in st.session_state:
        st.session_state.displayViewCase = False

if 'viewCaseIndex' not in st.session_state:
        st.session_state.viewCaseIndex = 0

#Setup the Streamlit Input

#Streamlit Main Area Setup
st.title('Texas Residential Solar Power System Modeling Tool')
tab1, tab2 = st.tabs(["Solar Power System Calculations", "NPV and Rate of Return Calculations"])

def ResetView():    
    if st.session_state.displayViewCase == True:
        return
    st.session_state.displayRunCase = True
    return

#Streamlit Sidebar Setup
st.sidebar.title('User Input')
caseName = st.sidebar.text_input('Case Name',value='Case 1',help='Enter a name for the modeled scenario', on_change=ResetView)
location = st.sidebar.selectbox('City',['Austin','Dallas','Houston','Midland','San Antonio'],index=2, on_change=ResetView)
avgMonthElecConsump = st.sidebar.number_input('Average Monthly Electricity Consumption (kwh)',min_value=0, max_value=20000,value=1500,step=100, on_change=ResetView)

#Solar System Input
with st.sidebar.expander("Solar System Description",expanded = True):
    dcSysSize = st.number_input('DC System Size (kW)',min_value=(0),max_value=(50),value=8, on_change=ResetView)

    moduleTypeChoices = {0: "Standard", 2: "Premium", 3: "Thin Film"}
    def format_func_mod(option):
        return moduleTypeChoices[option]
    moduleType = st.selectbox('Module Type',options=list(moduleTypeChoices.keys()),format_func=format_func_mod,index=0, on_change=ResetView)

    arrayTypeChoices = {0: "Fixed (open rack)", 1: "Fixed (roof mount)", 2: "1-Axis Tracking", 3: "1-Axis Backtracking", 4: "2-Axis Tracking"}
    def format_func_array(option):
        return arrayTypeChoices[option]
    arrayType = st.selectbox('Array Type',options=list(arrayTypeChoices.keys()),format_func=format_func_array,index=1, on_change=ResetView)

    sysLossSelect = st.checkbox('Advanced Loss Calc', on_change=ResetView)
    
    if sysLossSelect:
        soiling = st.number_input('Soiling (%)',min_value=(0.0),max_value=(100.0),value=2.0,step=0.1, on_change=ResetView)
        shading = st.number_input('Shading (%)',min_value=(0.0),max_value=(100.0),value=3.0,step=0.1, on_change=ResetView)
        snow = st.number_input('Snow (%)',min_value=(0.0),max_value=(100.0),value=0.0,step=0.1, on_change=ResetView)
        mismatch = st.number_input('Mismatch (%)',min_value=(0.0),max_value=(100.0),value=2.0,step=0.1, on_change=ResetView)
        wiring = st.number_input('Wiring (%)',min_value=(0.0),max_value=(100.0),value=2.0,step=0.1, on_change=ResetView)
        connections = st.number_input('Connections (%)',min_value=(0.0),max_value=(100.0),value=0.5,step=0.1, on_change=ResetView)
        initialDegradation = st.number_input('Inital Degradation',min_value=(0.0),max_value=(100.0),value=1.5,step=0.1, on_change=ResetView)
        nameplateRating = st.number_input('Nameplate Rating (%)',min_value=(0.0),max_value=(100.0),value=1.0,step=0.1, on_change=ResetView)
        age = st.number_input('Age (%)',min_value=(0.0),max_value=(100.0),value=0.0,step=0.1, on_change=ResetView)
        availability = st.number_input('Availability (%)',min_value=(0.0),max_value=(100.0),value=0.0,step=0.1, on_change=ResetView)
        systemLosses = (1-1*(1-soiling/100)*(1-shading/100)*(1-snow/100)*(1-mismatch/100)*(1-wiring/100)*(1-connections/100)*(1-initialDegradation/100)*(1-nameplateRating/100)*(1-age/100)*(1-availability/100))*100
        st.number_input('System Losses (%)',min_value=(0.0),max_value=(100.0),value=systemLosses,disabled=False, on_change=ResetView)       
    else:
        systemLosses = st.number_input('System Losses (%)',min_value=(0.0),max_value=(100.0),value=11.42, on_change=ResetView)
    
    tilt = st.number_input('Tilt (deg)',min_value=(0),max_value=(45),value=20, on_change=ResetView)
    azimuth = st.number_input('Azimuth (deg)',min_value=(0),max_value=(360),value=180, on_change=ResetView)

    selectAdvanced = st.checkbox("Show Advanced Input")
    if selectAdvanced:
        dcToACRatio = st.number_input('DC to AC Ratio',min_value=(0.1),max_value=(20.0),value=1.2, on_change=ResetView)
        inverterEff = st.number_input('Inverter Efficiency (%)',min_value=(0.1),max_value=(100.0),value=96.0, on_change=ResetView)
        groundCovRatio = st.number_input('Ground Coverage Ratio',min_value=(0.1),max_value=(1.0),value=0.4, on_change=ResetView)
    else:
        dcToACRatio = 1.2
        inverterEff = 96.0
        groundCovRatio = 0.4
#Battery System Setup
    batteryInstalled = st.checkbox("Include Battery?", on_change=ResetView)
    if batteryInstalled:
        batterySize = st.number_input('Battery Size (kwh)',min_value=(0.1), max_value=(500.0),value=13.5,step=0.1, on_change=ResetView)
        roundTripEff = st.number_input('Round Trip Efficiency (%)',min_value=(0.0),max_value=(100.0),value=92.5,step=0.1, on_change=ResetView)


#Electric Conctract Setup
with st.sidebar.expander("Electricity Plan Details",expanded = True):
    energyCharge = st.number_input('Energy Charge ($/kwh)',min_value=(0.00),max_value=(100.00),value=0.100,format="%.3f", on_change=ResetView)
    deliveryCharge = st.number_input('Delivery Charge ($/kwh)',min_value=(0.00),max_value=(100.00),value=0.04945,format="%.5f", on_change=ResetView)
    fixedDelCharge = st.number_input('Fixed Delivery Charge $/month',min_value=(0.0),max_value=(100.0),value=(4.39), on_change=ResetView)
    buyBackType = st.selectbox('Buy Back Type',('Net Credit','Real Time Market'), on_change=ResetView)
    touFeatures = st.selectbox('Plan Time-of-Use Features',('None','Free Nights','Free Weekends','Free Nights & Wk Ends','Reduced Cost Nights'),index=0, on_change=ResetView)
    if touFeatures == 'Free Nights':
        nightStart = st.time_input('Night Start Time', datetime.time(20,0), on_change=ResetView)
        nightEnd = st.time_input('Night End Time', datetime.time(6,0), on_change=ResetView)
    elif touFeatures == 'Free Weekends':
        wkDayTypeChoices = {0: "Monday", 1: "Tuesday", 2: "Wednesday", 3:"Thursday", 4:"Friday",5:"Saturday", 6: "Sunday", }
        def format_func_wkDay(option):
            return wkDayTypeChoices[option]
        wkendDayStart = st.selectbox('Weekend Start',options=list(wkDayTypeChoices.keys()),format_func=format_func_wkDay,index=4, on_change=ResetView)
        wkendDayEnd = st.selectbox('Weekend End', options=list(wkDayTypeChoices.keys()),format_func=format_func_wkDay,index=0, on_change=ResetView)
        wkendTimeStart = st.time_input('Weekend Start Time',datetime.time(20,0), on_change=ResetView)
        wkendTimeEnd = st.time_input('Weekend End Time', datetime.time(6,0), on_change=ResetView)
    elif touFeatures == 'Free Nights & Wk Ends':
        nightStart = st.time_input('Night Start Time', datetime.time(20,0), on_change=ResetView)
        nightEnd = st.time_input('Night End Time', datetime.time(6,0), on_change=ResetView)
        wkDayTypeChoices = {0: "Monday", 1: "Tuesday", 2: "Wednesday", 3:"Thursday", 4:"Friday",5:"Saturday", 6: "Sunday", }
        def format_func_wkDay(option):
            return wkDayTypeChoices[option]
        wkendDayStart = st.selectbox('Weekend Start',options=list(wkDayTypeChoices.keys()),format_func=format_func_wkDay,index=4, on_change=ResetView)
        wkendDayEnd = st.selectbox('Weekend End', options=list(wkDayTypeChoices.keys()),format_func=format_func_wkDay,index=0, on_change=ResetView)
        wkendTimeStart = st.time_input('Weekend Start Time',datetime.time(20,0), on_change=ResetView)
        wkendTimeEnd = st.time_input('Weekend End Time', datetime.time(6,0), on_change=ResetView)
    elif touFeatures == 'Reduced Cost Nights':
        nightEnergyCharge = st.number_input('Night Energy Charge ($/kwh)',min_value=(0.00),max_value=(100.00),value=0.100,format="%.3f", on_change=ResetView)
        nightStart = st.time_input('Night Start Time', datetime.time(20,0), on_change=ResetView)
        nightEnd = st.time_input('Night End Time', datetime.time(6,0), on_change=ResetView)
    elif touFeatures == 'None':
        nightStart = datetime.time(20,0)
        nightEnd = datetime.time(6,0)
        wkendDayStart = 'Friday'
        wkendDayEnd = 'Monday'
        wkendTimeStart = datetime.time(20,0)
 


#NREL request building
@st.cache
def GetNRELData(location, dcSysSize, moduleType, arrayType, systemLosses, tilt, azimuth, dcToACRatio, inverterEff, groundCovRatio):
    myAPIkey = "9zzEI7dNgn4vk8706ibfhr9XPbzn7eKXIGc3TgMp"
    df = pd.DataFrame()
    jsonRequestStr = "&address="+str(location)+"&system_capacity="+str(dcSysSize)+"&module_type="+str(moduleType)+"&array_type="+str(arrayType)+"&losses="+str(systemLosses)+"&tilt="+str(tilt)+"&azimuth="+str(azimuth)+"&dc_ac_ratio="+str(dcToACRatio)+"&gcr="+str(groundCovRatio)+"&inv_eff="+str(inverterEff)
    request = "https://developer.nrel.gov/api/pvwatts/v6.json?api_key="+myAPIkey+jsonRequestStr+"&timeframe=hourly"
    response = requests.get(request)
    df=pd.json_normalize(response.json(),max_level=1)
    return df

@st.cache
def RunCase(location, dcSysSize, moduleType, arrayType, systemLosses, tilt, azimuth, dcToACRatio, inverterEff, groundCovRatio, year, energyInf, panelDeg):
    global dfActivecase
    #fetch NREL solar data
    dfJson = GetNRELData(location, dcSysSize, moduleType, arrayType, systemLosses, tilt, azimuth, dcToACRatio, inverterEff, groundCovRatio)
    
    #fill index of the active case dataframe
    dfActivecase['Date']=pd.date_range("2022-01-01",periods=(365*24),freq="H")
    dfActivecase['MonthNum']=pd.DatetimeIndex(dfActivecase['Date']).month
    dfActivecase['DayNum']=pd.DatetimeIndex(dfActivecase['Date']).day
    dfActivecase['HourNum']=pd.DatetimeIndex(dfActivecase['Date']).hour
    dfActivecase['WeekDayNum']=pd.DatetimeIndex(dfActivecase['Date']).dayofweek
    
    #populate the monthly estimated electrical usage from historical data - using some Austin Energy data found
    dfResMonDelta = pd.DataFrame()
    #   Read in baked data that has the estimate delta to the annual average consumption on a monthly basis
    dfResMonDelta = pd.DataFrame(pd.read_csv('ResidentalMonthlyDelta2Mean.csv'))
    dfResMonDelta['Monthly Consumption'] = dfResMonDelta['Delta2YrlyMean']*avgMonthElecConsump+avgMonthElecConsump

    #Calculate estimated monthly power usage from annual average and populate active case dataframe
    dfResMonDelta = dfResMonDelta.set_index('MonthNum')
    dfActivecase['Monthly Pwr Consumption (kwh)'] = dfActivecase['MonthNum'].map(dfResMonDelta['Monthly Consumption'])
    
    #Calculate hourly power consumption from the location specific historical demand data (ERCOT only for now)
    #   Map the ERCOT zones to the cities in selection list
    ZoneMap = {
        "Houston":"COAST",
        "Austin":"SCENT",
        "Dallas":"NCENT",
        "San Antonio":"SCENT",
        "Midland":"FWEST"
    }
    ZoneLocation = ZoneMap[location]
    
    #   Read in the baked ERCOT historical data based on month and day of week averages
    dfERCOTHourly = pd.DataFrame()
    dfERCOTHourly = pd.DataFrame(pd.read_csv('ERCOT_Demand_NEW.csv'), columns=['Month','WeekDayNum','Day','Hour',ZoneLocation])
    #   Calculate the number of days in the month so that the user input monthly averages can be converted to hourly averages for hourly consumption estimate calculation
    dfERCOTHourly['MonthDays'] = pd.to_datetime(dfERCOTHourly['Month']).dt.daysinmonth
    #   Look up the monthly consumption data and apply it to all rows in that month for later calculation of hourly consumption
    dfERCOTHourly['Monthly Pwr Consumption (kwh)'] = dfERCOTHourly['Month'].map(dfResMonDelta['Monthly Consumption'])
    dfERCOTHourly[ZoneLocation] = 1 + dfERCOTHourly[ZoneLocation]
    dfERCOTHourly['Hourly Pwr Consumption (kwh)'] = dfERCOTHourly[ZoneLocation] * dfERCOTHourly['Monthly Pwr Consumption (kwh)'] / dfERCOTHourly['MonthDays'] / 24
    #   Merge the ERCOT Hourly by day of week data to the activecase dataframe to map the monthly day of week consumptions to a yearly datum
    #  - i.e. all weekdays in the same month have the same consumption profile
    #   drop the unused Month and Hour columns
    dfActivecase = pd.merge(dfActivecase,dfERCOTHourly[['Month','WeekDayNum','Hour','Hourly Pwr Consumption (kwh)']], left_on = ['MonthNum','WeekDayNum','HourNum'],right_on=['Month','WeekDayNum','Hour'])
    dfActivecase = dfActivecase.drop(['Month','Hour'], axis = 1)

    #Calculate the hourly solar power generation in kilowatts from the watt data output from the NREL request
    dfActivecase['Solar Gen (kw)'] = dfJson.iloc[0,dfJson.columns.get_loc("outputs.ac")]
    dfActivecase['Solar Gen (kw)'] = dfActivecase['Solar Gen (kw)'] / 1000

    #Calculate power saved from solar generation system - without considering battery
    conditions = [
        (dfActivecase['Solar Gen (kw)'] < dfActivecase['Hourly Pwr Consumption (kwh)']),
        (dfActivecase['Solar Gen (kw)'] > dfActivecase['Hourly Pwr Consumption (kwh)'])
    ]
    values = [dfActivecase['Solar Gen (kw)'], dfActivecase['Hourly Pwr Consumption (kwh)']]
    dfActivecase['Power Saved - Solar'] = np.select(conditions,values)
    
    #Calculate power sold back from solar generation system
    conditions = [
        (dfActivecase['Solar Gen (kw)'] > dfActivecase['Hourly Pwr Consumption (kwh)']),
        (dfActivecase['Solar Gen (kw)'] < dfActivecase['Hourly Pwr Consumption (kwh)'])
    ]
    values = [dfActivecase['Solar Gen (kw)'] - dfActivecase['Hourly Pwr Consumption (kwh)'], 0]
    dfActivecase['Power Sold - Solar'] = np.select(conditions,values)
    
    #If a battery system is installed: Calculate delta energy to battery, time series of battery storage energy, power saved, and power sold
    if batteryInstalled:
        #Calculate the hourly energy delta to battery
        conditions = [
        (dfActivecase['Power Sold - Solar'] > 0),
        (dfActivecase['Power Sold - Solar'] <= 0)
        ]
        values = [dfActivecase['Power Sold - Solar'], dfActivecase['Solar Gen (kw)'] - dfActivecase['Hourly Pwr Consumption (kwh)']]
        dfActivecase['Battery Delta Energy (kwh)'] = np.select(conditions,values)

        #Calculate the current energy storage in battery
        dfActivecase['Battery Storage'] = 0
        for i in range(1, len(dfActivecase)-1):
            if dfActivecase.loc[i-1,'Battery Storage'] + dfActivecase.loc[i,'Battery Delta Energy (kwh)'] <= 0:
                dfActivecase.loc[i,'Battery Storage'] = 0
            elif dfActivecase.loc[i-1,'Battery Storage'] + dfActivecase.loc[i,'Battery Delta Energy (kwh)'] < batterySize:
                dfActivecase.loc[i,'Battery Storage'] = dfActivecase.loc[i-1,'Battery Storage'] + (dfActivecase.loc[i,'Battery Delta Energy (kwh)'] * roundTripEff/100)
            elif dfActivecase.loc[i-1,'Battery Storage'] + dfActivecase.loc[i,'Battery Delta Energy (kwh)'] > batterySize:
                dfActivecase.loc[i,'Battery Storage'] = batterySize
        
        #Calculate power saved with solar + battery system
        conditions = [
        (dfActivecase['Battery Storage'] < dfActivecase['Battery Storage'].shift(1)),
        (dfActivecase['Battery Storage'] > dfActivecase['Battery Storage'].shift(1))
        ]
        values = [dfActivecase['Battery Storage'].shift(1).sub(dfActivecase['Battery Storage']), 0]
        dfActivecase['Power Saved - Battery'] = np.select(conditions,values)

        #Calculate power sold with solar + battery system
        conditions = [
            (dfActivecase['Battery Storage'].shift(1).add(dfActivecase['Battery Delta Energy (kwh)']) <= batterySize),
            (dfActivecase['Battery Storage'].shift(1).add(dfActivecase['Battery Delta Energy (kwh)']) > batterySize)
        ]
        values = [0, dfActivecase['Battery Storage'].shift(1).add(dfActivecase['Battery Delta Energy (kwh)']).sub(batterySize)]
        dfActivecase['Power Sold - Battery'] = np.select(conditions,values)

    #Calculate time of use (TOU) power saved if electrical plan features include
    dfActivecase['Pwr Saved - TOU'] = 0 # initialize power saved column to 0 for ease of future NPV calcs (always have the data available even if at 0)
    #Calculate TOU power if battery is installed - which needs to account for the power saved by the battery - but only if it has available energy.
    if batteryInstalled:
        if touFeatures == 'Free Nights' or touFeatures == 'Reduced Cost Nights':
            conditions = [
                ((dfActivecase['HourNum']>=nightStart.hour) | (dfActivecase['HourNum'] < nightEnd.hour) &
                    (dfActivecase['Battery Storage'] > dfActivecase['Hourly Pwr Consumption (kwh)'])),
                ((dfActivecase['HourNum']>=nightStart.hour) | (dfActivecase['HourNum'] < nightEnd.hour) &
                    (dfActivecase['Battery Storage'] <= dfActivecase['Hourly Pwr Consumption (kwh)']))
            ]
            value = [dfActivecase['Hourly Pwr Consumption (kwh)'].sub(dfActivecase['Power Saved - Solar']),
                dfActivecase['Hourly Pwr Consumption (kwh)'].sub(dfActivecase['Power Saved - Solar']).sub(dfActivecase['Power Saved - Battery'])
            ]
            dfActivecase['Pwr Saved - TOU'] = np.select(conditions,value)
        
        elif touFeatures == 'Free Weekends':
            dfActivecase['Week Day #'] = pd.DatetimeIndex(dfActivecase['Date']).weekday
            conditions = [
                ((dfActivecase['Week Day #'] == wkendDayStart) & (dfActivecase['HourNum']>=wkendTimeStart.hour)) |
                    (dfActivecase['Week Day #'] > wkendDayStart) |
                    (dfActivecase['Week Day #'] < wkendDayEnd) |
                    ((dfActivecase['Week Day #'] == wkendDayEnd) & (dfActivecase['HourNum']< wkendTimeEnd.hour) &
                    (dfActivecase['Battery Storage'] > dfActivecase['Hourly Pwr Consumption (kwh)'])),
                ((dfActivecase['Week Day #'] == wkendDayStart) & (dfActivecase['HourNum']>=wkendTimeStart.hour)) |
                    (dfActivecase['Week Day #'] > wkendDayStart) |
                    (dfActivecase['Week Day #'] < wkendDayEnd) |
                    ((dfActivecase['Week Day #'] == wkendDayEnd) & (dfActivecase['HourNum']< wkendTimeEnd.hour) &
                    (dfActivecase['Battery Storage'] <= dfActivecase['Hourly Pwr Consumption (kwh)'])),
            ]
            value = [dfActivecase['Hourly Pwr Consumption (kwh)'].sub(dfActivecase['Power Saved - Solar']),
                dfActivecase['Hourly Pwr Consumption (kwh)'].sub(dfActivecase['Power Saved - Solar']).sub(dfActivecase['Power Saved - Battery'])
            ]
            dfActivecase['Pwr Saved - TOU'] = np.select(conditions,value)
            dfActivecase.drop('Week Day #', axis=1, inplace = True)
        
        elif touFeatures == 'Free Nights & Wk Ends':
            dfActivecase['Week Day #'] = pd.DatetimeIndex(dfActivecase['Date']).weekday
            conditions = [
                ((dfActivecase['Week Day #'] == wkendDayStart) & (dfActivecase['HourNum']>=wkendTimeStart.hour)) |
                    (dfActivecase['Week Day #'] > wkendDayStart) |
                    (dfActivecase['Week Day #'] < wkendDayEnd) |
                    ((dfActivecase['Week Day #'] == wkendDayEnd) & (dfActivecase['HourNum']< wkendTimeEnd.hour)) |
                    ((dfActivecase['HourNum']>=nightStart.hour) | (dfActivecase['HourNum'] < nightEnd.hour) &
                    (dfActivecase['Battery Storage'] > dfActivecase['Hourly Pwr Consumption (kwh)'])),
                ((dfActivecase['Week Day #'] == wkendDayStart) & (dfActivecase['HourNum']>=wkendTimeStart.hour)) |
                    (dfActivecase['Week Day #'] > wkendDayStart) |
                    (dfActivecase['Week Day #'] < wkendDayEnd) |
                    ((dfActivecase['Week Day #'] == wkendDayEnd) & (dfActivecase['HourNum']< wkendTimeEnd.hour)) |
                    ((dfActivecase['HourNum']>=nightStart.hour) | (dfActivecase['HourNum'] < nightEnd.hour) &
                    (dfActivecase['Battery Storage'] <= dfActivecase['Hourly Pwr Consumption (kwh)'])),
            ]
            value = [dfActivecase['Hourly Pwr Consumption (kwh)'].sub(dfActivecase['Power Saved - Solar']),
                dfActivecase['Hourly Pwr Consumption (kwh)'].sub(dfActivecase['Power Saved - Solar']).sub(dfActivecase['Power Saved - Battery'])
            ]
            dfActivecase['Pwr Saved - TOU'] = np.select(conditions,value)
            dfActivecase.drop('Week Day #', axis=1, inplace = True)
    #Calculate TOU power saved if no battery - consumption - power saved with solar.
    else:
        if touFeatures == 'Free Nights' or touFeatures == 'Reduced Cost Nights':
            conditions = [
                ((dfActivecase['HourNum']>=nightStart.hour) | (dfActivecase['HourNum'] < nightEnd.hour)),
            ]
            value = [dfActivecase['Hourly Pwr Consumption (kwh)'].sub(dfActivecase['Power Saved - Solar'])]
            dfActivecase['Pwr Saved - TOU'] = np.select(conditions,value)
        
        elif touFeatures == 'Free Weekends':
            dfActivecase['Week Day #'] = pd.DatetimeIndex(dfActivecase['Date']).weekday
            conditions = [
                ((dfActivecase['Week Day #'] == wkendDayStart) & (dfActivecase['HourNum']>=wkendTimeStart.hour)) |
                (dfActivecase['Week Day #'] > wkendDayStart) |
                (dfActivecase['Week Day #'] < wkendDayEnd) |
                ((dfActivecase['Week Day #'] == wkendDayEnd) & (dfActivecase['HourNum']< wkendTimeEnd.hour))
            ]
            value = [dfActivecase['Hourly Pwr Consumption (kwh)'].sub(dfActivecase['Power Saved - Solar'])]
            dfActivecase['Pwr Saved - TOU'] = np.select(conditions,value)
            dfActivecase.drop('Week Day #', axis=1, inplace = True)
       
        elif touFeatures == 'Free Nights & Wk Ends':
            dfActivecase['Week Day #'] = pd.DatetimeIndex(dfActivecase['Date']).weekday
            conditions = [
                ((dfActivecase['Week Day #'] == wkendDayStart) & (dfActivecase['HourNum']>=wkendTimeStart.hour)) |
                (dfActivecase['Week Day #'] > wkendDayStart) |
                (dfActivecase['Week Day #'] < wkendDayEnd) |
                ((dfActivecase['Week Day #'] == wkendDayEnd) & (dfActivecase['HourNum']< wkendTimeEnd.hour)) |
                ((dfActivecase['HourNum']>=nightStart.hour) | (dfActivecase['HourNum'] < nightEnd.hour)),
            ]
            value = [dfActivecase['Hourly Pwr Consumption (kwh)'].sub(dfActivecase['Power Saved - Solar'])]
            dfActivecase['Pwr Saved - TOU'] = np.select(conditions,value)
            dfActivecase.drop('Week Day #', axis=1, inplace = True)
    
    #Calculate the value of power saved - either with just solar or solar + battery
    if batteryInstalled:
        dfActivecase['Power Saved Value'] = dfActivecase['Power Saved - Solar'].add(dfActivecase['Power Saved - Battery']) * (energyCharge + deliveryCharge)
    else:
        dfActivecase['Power Saved Value'] = dfActivecase['Power Saved - Solar'] * (energyCharge + deliveryCharge)
    
    #Calculate the vaolume of power sold
    if buyBackType == 'Net Credit':
        dfActivecase['Pwr Sold Value - Solar'] = dfActivecase['Power Sold - Solar'] * (energyCharge)
        if batteryInstalled:
            dfActivecase['Pwr Sold Value - Battery'] = dfActivecase['Power Sold - Battery'] * (energyCharge)
    else:
        #Import the real time market (RTM) pricing data developed from 2020 - 2022 ERCOT load zone RTM data
        dfActivecase['RTM Price'] = pd.DataFrame(pd.read_csv('RTMprices-Texas.csv'), columns=[location])
        dfActivecase['Pwr Sold Value - Solar'] = dfActivecase['RTM Price'].multiply(dfActivecase['Power Sold - Solar'])
        if batteryInstalled:
            dfActivecase['Pwr Sold Value - Battery'] = dfActivecase['RTM Price'].multiply(dfActivecase['Power Sold - Battery'])

        dfActivecase.drop('RTM Price', axis=1, inplace = True)

    #Summarize the Power Saved and Power Sold columns
    if batteryInstalled:
        dfActivecase['Power Sold Value'] = dfActivecase['Pwr Sold Value - Battery']
        dfActivecase['Power Saved'] = dfActivecase['Power Saved - Battery'] + dfActivecase['Power Saved - Solar']
        dfActivecase['Power Sold'] = dfActivecase['Power Sold - Battery']
        dfActivecase = dfActivecase.drop(['Pwr Sold Value - Solar','Pwr Sold Value - Battery'], axis =1)
        dfActivecase = dfActivecase.drop(['Power Saved - Solar','Power Saved - Battery'], axis = 1)
        dfActivecase = dfActivecase.drop(['Power Sold - Solar', 'Power Sold - Battery'], axis = 1)

    else:
        dfActivecase['Power Sold Value'] = dfActivecase['Pwr Sold Value - Solar']
        dfActivecase['Power Saved'] = dfActivecase['Power Saved - Solar']
        dfActivecase['Power Sold'] = dfActivecase['Power Sold - Solar']
        dfActivecase = dfActivecase.drop('Pwr Sold Value - Solar', axis =1)
        dfActivecase = dfActivecase.drop('Power Saved - Solar', axis = 1)
        dfActivecase = dfActivecase.drop('Power Sold - Solar', axis = 1)

    return dfActivecase

def CalcNPV ():
    year = 0
    return

def DisplayViewCase():
    st.session_state.displayViewCase = True
    caseLookup = st.session_state.viewChoice
    st.session_state.viewCaseIndex = st.session_state.caseCatalog.index(caseLookup)
    return


def DisplayCase (dfDisplayCase, caseIndex):
    dfResultDisp = pd.DataFrame()
    dfResultDisp = dfDisplayCase.groupby(['MonthNum'], as_index=False)[
        'Solar Gen (kw)','Power Saved','Power Sold','Power Sold Value', 'Power Saved Value'
        ].sum()
    d = dict(enumerate(calendar.month_abbr))
    dfResultDisp['Month'] = dfResultDisp['MonthNum'].map(d)
            
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric('Total Yearly Solar Power Generated',str(int(round(dfResultDisp['Solar Gen (kw)'].sum(),0)))+' kwh',delta=None)
        st.metric('Power Saved',str(int(round(dfResultDisp['Power Saved'].sum(),0)))+' kwh',delta=None)
        st.metric('Power Sold',str(int(round(dfResultDisp['Power Sold'].sum(),0)))+' kwh',delta=None)
    with col2:
        st.metric('Total Annual Savings',"$" + str(round(Decimal(
            dfResultDisp['Power Saved Value'].sum() + dfResultDisp['Power Sold Value'].sum()),2)),delta=None)
        st.metric('Value of Power Saved',"$" + str(round(Decimal(dfResultDisp['Power Saved Value'].sum()),2)),delta=None)
        st.metric('Value of Power Sold',"$" + str(round(Decimal(dfResultDisp['Power Sold Value'].sum()),2)),delta=None)
    with col3:
        st.metric('Average Monthly Savings',"$" + str(round(Decimal(
            (dfResultDisp['Power Saved Value'].sum() + dfResultDisp['Power Sold Value'].sum()) / 12),2)),delta=None)
                
    
    c = alt.Chart(dfResultDisp).mark_bar().encode(
        x=alt.X('Month',sort=dfResultDisp['MonthNum'].values),
        y='Solar Gen (kw)'
        )    

    st.altair_chart(c, use_container_width=True)
    #Prepare case inputs for display
    dfCaseInputs = pd.DataFrame([st.session_state.collectionofCaseData[caseIndex]])
    dfCaseDisplay = dfCaseInputs.transpose()
    dfCaseDisplay.index.rename('Input Parameters', inplace = True)
    dfCaseDisplay = dfCaseDisplay.rename(columns={0: 'User Inputs'})
    dfCaseDisplay.columns.name = dfCaseDisplay.index.name
    dfCaseDisplay.index.name = None

    st.write(dfCaseDisplay.to_html(), unsafe_allow_html = True)

    return


def RunCaseButton():
    st.session_state.displayViewCase = False
    caseData = {
        #'Case Number': st.session_state.caseIndex, #doesn't seem to be required at this time
        'Case Name': caseName,
        'City': location,
        'Annual Monthly Elec Usage (kwh)' : avgMonthElecConsump,
        'Solar System DC Size (kw)': dcSysSize,
        'Module Type': moduleType,
        'Array Type': arrayType,
        'System Losses (%)': systemLosses,
        'Tilt (deg)': tilt,
        'Azimuth (deg)' : azimuth,
        'Battery Installed' : batteryInstalled,
        'Energy Charge ($)': energyCharge,
        'Delivery Charge ($)' : deliveryCharge,
        'Buy Back Type' : buyBackType,
        'Time of Use Features' : touFeatures
    }
    
    #Check if the same case is being accidentlly run twice and skip the work
    if st.session_state.caseIndex > 0:
        if caseData == st.session_state.collectionofCaseData[st.session_state.caseIndex - 1]:           
            st.session_state.displayRunCase = True
            return

    #Check if case name is unique, if not warn, and all "-alt" to the case name
    if any(d['Case Name'] == caseData['Case Name'] for d in st.session_state.collectionofCaseData):
        st.warning("Case Name already exists, please give a unique Case Name")
        st.session_state.displayRunCase = True
        return

    st.session_state.collectionofCaseData.append(caseData)
    st.session_state.caseCatalog = [x['Case Name'] for x in st.session_state.collectionofCaseData]
    dfActivecase = RunCase(location, dcSysSize, moduleType, arrayType, systemLosses, tilt, azimuth, dcToACRatio, inverterEff, groundCovRatio, 1, 1, 1)
    st.session_state.collectionofCases.append(dfActivecase)
    #DisplayCase(st.session_state.collectionofCases[st.session_state.caseIndex], (st.session_state.caseIndex)) 
    st.session_state.caseIndex += 1
    st.session_state.displayRunCase = True


with tab1: #Tab 1 is the solar system main calculation tab where results on the base solar power system are shown
    
    col1, col2, col3 = st.columns(3)
    with col1:
        runcasebutton = st.button('Run Case',on_click=RunCaseButton)
    with col2:
        #If more than one case run, show select box for view case
        if len(st.session_state.collectionofCases) > 1:
            #If a case is run, display the case just ran
            if st.session_state.displayRunCase:
                displayIndexLookup = st.selectbox('View Case',pd.DataFrame(st.session_state.caseCatalog),
                    index = int(st.session_state.caseIndex - 1), on_change=DisplayViewCase,key = 'viewChoice'
                    )
            #If a view case was chosen, display view case
            if st.session_state.displayViewCase:
                st.selectbox('View Case',pd.DataFrame(st.session_state.caseCatalog),
                    index = int(st.session_state.viewCaseIndex), on_change=DisplayViewCase,key = 'viewChoice'
                    )

    with col3:
        #If more than one case run, show compare box for view case
        if len(st.session_state.collectionofCases) > 1:
            #Remove current view case from list of compare cases
            compareCatalog = st.session_state.caseCatalog.copy()
            
            if st.session_state.displayRunCase:
                for i in range(len(compareCatalog)):
                    if compareCatalog[i] == st.session_state.caseCatalog[st.session_state.caseIndex - 1]:
                        del compareCatalog[i]
                        break
            if st.session_state.displayViewCase:
                for i in range(len(compareCatalog)):
                    if compareCatalog[i] == st.session_state.caseCatalog[st.session_state.viewCaseIndex]:
                        del compareCatalog[i]
                        break

            while st.session_state.compareCaseIndex >= len(compareCatalog):
                st.session_state.compareCaseIndex -= 1

            compareIndexLookup = st.selectbox('Case to Compare',pd.DataFrame(compareCatalog),
                index = int(st.session_state.compareCaseIndex), on_change=ResetView, key ='compareChoice')
            st.session_state.compareCaseIndex = st.session_state.caseCatalog.index(compareIndexLookup)
               
    if st.session_state.displayRunCase & (len(st.session_state.collectionofCases) > 0):
        DisplayCase(st.session_state.collectionofCases[st.session_state.caseIndex - 1], (st.session_state.caseIndex - 1))
        st.session_state.displayRunCase = False

    if st.session_state.displayViewCase & (len(st.session_state.collectionofCases) > 0):
        DisplayCase(st.session_state.collectionofCases[st.session_state.viewCaseIndex], (st.session_state.viewCaseIndex))
        
        
with tab2: #Tab2 is for the NPV inputs and to calculate and display NPV data

    foo=1
#    runNPV = st.button("Run NPV and Rate of Return Calc")