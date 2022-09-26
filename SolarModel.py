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

dfJson = pd.DataFrame()
dfFixeddata = pd.DataFrame()
dfActivecase = pd.DataFrame()

#Setup the Streamlit Input

#Streamlit Main Area Setup
st.title('Texas Residential Solar Power System Modelling Tool')
tab1, tab2 = st.tabs(["Solar Power System Calculations", "NPV and Rate of Return Calculations"])

with tab1: #Tab 1 is the solar system main calculation tab where results on the base solar power system are shown

    runcasebutton = st.button('Run Case')

    #Streamlit Sidebar Setup
    st.sidebar.title('User Input')
    st.sidebar.text_input('Case Name',value='Case 1',help='Enter a name for the modelled scenario')
    location = st.sidebar.selectbox('City',['Austin','Dallas','Houston','Midland','San Antonio'],index=2)
    avgMonthElecConsump = st.sidebar.number_input('Average Monthly Electricity Consumption (kwh)',min_value=0, max_value=20000,value=1500,step=100)

    #Solar System Input
    with st.sidebar.expander("Solar System Description",expanded = True):
        dcSysSize = st.number_input('DC System Size (kW)',min_value=(0),max_value=(50),value=8)
    
        moduleTypeChoices = {0: "Standard", 2: "Premium", 3: "Thin Film"}
        def format_func_mod(option):
            return moduleTypeChoices[option]
        moduleType = st.selectbox('Module Type',options=list(moduleTypeChoices.keys()),format_func=format_func_mod,index=0)
    
        arrayTypeChoices = {0: "Fixed (open rack)", 1: "Fixed (roof mount)", 2: "1-Axis Tracking", 3: "1-Axis Backtracking", 4: "2-Axis Tracking"}
        def format_func_array(option):
            return arrayTypeChoices[option]
        arrayType = st.selectbox('Array Type',options=list(arrayTypeChoices.keys()),format_func=format_func_array,index=1)
    
        sysLossSelect = st.checkbox('Advanced Loss Calc')
        
        if sysLossSelect:
            soiling = st.number_input('Soiling (%)',min_value=(0.0),max_value=(100.0),value=2.0,step=0.1)
            shading = st.number_input('Shading (%)',min_value=(0.0),max_value=(100.0),value=3.0,step=0.1)
            snow = st.number_input('Snow (%)',min_value=(0.0),max_value=(100.0),value=0.0,step=0.1)
            mismatch = st.number_input('Mismatch (%)',min_value=(0.0),max_value=(100.0),value=2.0,step=0.1)
            wiring = st.number_input('Wiring (%)',min_value=(0.0),max_value=(100.0),value=2.0,step=0.1)
            connections = st.number_input('Connections (%)',min_value=(0.0),max_value=(100.0),value=0.5,step=0.1)
            initialDegradation = st.number_input('Inital Degradation',min_value=(0.0),max_value=(100.0),value=1.5,step=0.1)
            nameplateRating = st.number_input('Nameplate Rating (%)',min_value=(0.0),max_value=(100.0),value=1.0,step=0.1)
            age = st.number_input('Age (%)',min_value=(0.0),max_value=(100.0),value=0.0,step=0.1)
            availability = st.number_input('Availability (%)',min_value=(0.0),max_value=(100.0),value=0.0,step=0.1)
            systemLosses = (1-1*(1-soiling/100)*(1-shading/100)*(1-snow/100)*(1-mismatch/100)*(1-wiring/100)*(1-connections/100)*(1-initialDegradation/100)*(1-nameplateRating/100)*(1-age/100)*(1-availability/100))*100
            st.number_input('System Losses (%)',min_value=(0.0),max_value=(100.0),value=systemLosses,disabled=False)       
        else:
            systemLosses = st.number_input('System Losses (%)',min_value=(0.0),max_value=(100.0),value=11.42)
        
        tilt = st.number_input('Tilt (deg)',min_value=(0),max_value=(45),value=20)
        azimuth = st.number_input('Azimuth (deg)',min_value=(0),max_value=(360),value=180)

        selectAdvanced = st.checkbox("Show Advanced Input")
        if selectAdvanced:
            dcToACRatio = st.number_input('DC to AC Ratio',min_value=(0.1),max_value=(20.0),value=1.2)
            inverterEff = st.number_input('Inverter Efficiency (%)',min_value=(0.1),max_value=(100.0),value=96.0)
            groundCovRatio = st.number_input('Ground Coverage Ratio',min_value=(0.1),max_value=(1.0),value=0.4)
        else:
            dcToACRatio = 1.2
            inverterEff = 96.0
            groundCovRatio = 0.4
    #Battery System Setup
        batteryInstalled = st.checkbox("Include Battery?")
        if batteryInstalled:
            batterySize = st.number_input('Battery Size (kwh)',min_value=(0.1), max_value=(500.0),value=13.5,step=0.1)
            roundTripEff = st.number_input('Round Trip Efficiency (%)',min_value=(0.0),max_value=(100.0),value=92.5,step=0.1)


    #Electric Conctract Setup
    with st.sidebar.expander("Electricity Plan Details",expanded = True):
        energyCharge = st.number_input('Energy Charge ($/kwh)',min_value=(0.00),max_value=(100.00),value=0.100,format="%.3f")
        deliveryCharge = st.number_input('Delivery Charge ($/kwh)',min_value=(0.00),max_value=(100.00),value=0.04945,format="%.5f")
        fixedDelCharge = st.number_input('Fixed Delivery Charge $/month',min_value=(0.0),max_value=(100.0),value=(4.39))
        buyBackType = st.selectbox('Buy Back Type',('Net Credit','Real Time Market'))
        touFeatures = st.selectbox('Plan Time-of-Use Features',('None','Free Nights','Free Weekends','Free Nights & Wk Ends','Reduced Cost Nights'),index=0)
        if touFeatures == 'Free Nights':
            nightStart = st.time_input('Night Start Time', datetime.time(20,0))
            nightEnd = st.time_input('Night End Time', datetime.time(6,0))
        elif touFeatures == 'Free Weekends':
            wkDayTypeChoices = {0: "Monday", 1: "Tuesday", 2: "Wednesday", 3:"Thursday", 4:"Friday",5:"Saturday", 6: "Sunday", }
            def format_func_wkDay(option):
                return wkDayTypeChoices[option]
            wkendDayStart = st.selectbox('Weekend Start',options=list(wkDayTypeChoices.keys()),format_func=format_func_wkDay,index=4)
            wkendDayEnd = st.selectbox('Weekend End', options=list(wkDayTypeChoices.keys()),format_func=format_func_wkDay,index=0)
            wkendTimeStart = st.time_input('Weekend Start Time',datetime.time(20,0))
            wkendTimeEnd = st.time_input('Weekend End Time', datetime.time(6,0))
        elif touFeatures == 'Free Nights & Wk Ends':
            nightStart = st.time_input('Night Start Time', datetime.time(20,0))
            nightEnd = st.time_input('Night End Time', datetime.time(6,0))
            wkDayTypeChoices = {0: "Monday", 1: "Tuesday", 2: "Wednesday", 3:"Thursday", 4:"Friday",5:"Saturday", 6: "Sunday", }
            def format_func_wkDay(option):
                return wkDayTypeChoices[option]
            wkendDayStart = st.selectbox('Weekend Start',options=list(wkDayTypeChoices.keys()),format_func=format_func_wkDay,index=4)
            wkendDayEnd = st.selectbox('Weekend End', options=list(wkDayTypeChoices.keys()),format_func=format_func_wkDay,index=0)
            wkendTimeStart = st.time_input('Weekend Start Time',datetime.time(20,0))
            wkendTimeEnd = st.time_input('Weekend End Time', datetime.time(6,0))
        elif touFeatures == 'Reduced Cost Nights':
            nightEnergyCharge = st.number_input('Night Energy Charge ($/kwh)',min_value=(0.00),max_value=(100.00),value=0.100,format="%.3f")
            nightStart = st.time_input('Night Start Time', datetime.time(20,0))
            nightEnd = st.time_input('Night End Time', datetime.time(6,0))
        elif touFeatures == 'None':
            nightStart = datetime.time(20,0)
            nightEnd = datetime.time(6,0)
            wkendDayStart = 'Friday'
            wkendDayEnd = 'Monday'
            wkendTimeStart = datetime.time(20,0)
 
#with tab2: #Tab2 is for the NPV inputs and to calculate and display NPV data

#    runNPV = st.button("Run NPV and Rate of Return Calc")




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


def RunCase(location, dcSysSize, moduleType, arrayType, systemLosses, tilt, azimuth, dcToACRatio, inverterEff, groundCovRatio, year, energyInf, panelDeg):
    #fetch NREL solar data
    dfJson = GetNRELData(location, dcSysSize, moduleType, arrayType, systemLosses, tilt, azimuth, dcToACRatio, inverterEff, groundCovRatio)
    
    #fill index of the active case dataframe
    dfActivecase['Date']=pd.date_range("2022-01-01",periods=(365*24),freq="H")
    dfActivecase['MonthNum']=pd.DatetimeIndex(dfActivecase['Date']).month
    dfActivecase['DayNum']=pd.DatetimeIndex(dfActivecase['Date']).day
    dfActivecase['HourNum']=pd.DatetimeIndex(dfActivecase['Date']).hour
    
    #populate the monthly estimated electrical usage from historical data
    dfResMonDelta = pd.DataFrame()
    dfResMonDelta = pd.DataFrame(pd.read_csv('ResidentalMonthlyDelta2Mean.csv'))
    dfResMonDelta['Delta2YrlyMean'] = dfResMonDelta['Delta2YrlyMean']*avgMonthElecConsump
    dfResMonDelta['Delta2YrlyMean'] = dfResMonDelta['Delta2YrlyMean']+avgMonthElecConsump
    
    #Calculate estimated monthly power usage from annual average and populate active case dataframe
    dfResMonDelta = dfResMonDelta.set_index('MonthNum')
    dfActivecase['Monthly Pwr Consumption (kwh)'] = dfActivecase['MonthNum'].map(dfResMonDelta['Delta2YrlyMean'])
    
    #Calculate hourly power consumption from the location specific historical demand data
    dfERCOTHourly = pd.DataFrame()
    dfERCOTHourly['Hourly Use Change'] = pd.DataFrame(pd.read_csv('ERCOT_Demand.csv'), columns=[location])
    dfERCOTHourly['MonthNum'] = pd.DatetimeIndex(dfActivecase['Date']).month
    dfERCOTHourly['MonthDays'] = pd.to_datetime(dfERCOTHourly['MonthNum']).dt.daysinmonth
    dfERCOTHourly['Monthly Pwr Consumption (kwh)'] = dfActivecase['Monthly Pwr Consumption (kwh)']
    dfERCOTHourly['Hourly Use Change'] = 1 + dfERCOTHourly['Hourly Use Change']
    dfERCOTHourly['Hourly Pwr Consumption (kwh)'] = dfERCOTHourly['Hourly Use Change'] * dfERCOTHourly['Monthly Pwr Consumption (kwh)'] / dfERCOTHourly['MonthDays'] / 24
    dfActivecase['Hourly Pwr Consumption (kwh)'] = dfERCOTHourly['Hourly Pwr Consumption (kwh)']

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

    #Import the real time market (RTM) pricing data developed from 2020 - 2022 ERCOT load zone RTM data
    dfActivecase['RTM Price'] = pd.DataFrame(pd.read_csv('RTMprices-Texas.csv'), columns=[location])
    dfActivecase['Pwr Sold Value - Solar'] = dfActivecase['RTM Price'].multiply(dfActivecase['Power Sold - Solar'])
    if batteryInstalled:
        dfActivecase['Pwr Sold Value - Battery'] = dfActivecase['RTM Price'].multiply(dfActivecase['Power Sold - Battery'])

    dfActivecase.drop('RTM Price', axis=1, inplace = True)

    return dfActivecase

def CalcNPV ():
    year = 0
    return




if runcasebutton:
    dfActivecase = RunCase(location, dcSysSize, moduleType, arrayType, systemLosses, tilt, azimuth, dcToACRatio, inverterEff, groundCovRatio, 1, 1, 1)

    dfResultDisp = pd.DataFrame()
    dfResultDisp = dfActivecase.groupby(['MonthNum'], as_index=False)['Solar Gen (kw)'].sum()
    d = dict(enumerate(calendar.month_abbr))
    dfResultDisp['Month'] = dfResultDisp['MonthNum'].map(d)
    st.text(dfResultDisp['Solar Gen (kw)'].sum())
    #dfResultDisp.sort_values('MonthNum')
    c = alt.Chart(dfResultDisp).mark_bar().encode(x=alt.X('Month',sort=dfResultDisp['MonthNum'].values),y='Solar Gen (kw)')
    st.altair_chart(c, use_container_width=True)
