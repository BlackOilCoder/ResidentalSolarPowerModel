# -*- coding: utf-8 -*-
"""
Created on Fri Sep 16 21:29:51 2022

@author: aodl
"""

import pandas as pd
import requests
import streamlit as st

dfJson = pd.DataFrame()
dfFixeddata = pd.DataFrame()
global dfActivecase
dfActivecase = pd.DataFrame()

#Setup the Streamlit Input

st.title('Texas Residential Solar Power System Modelling Tool')

st.sidebar.title('User Input')
runcasebutton = st.sidebar.button('Run Case')
st.sidebar.text_input('Case Name',value='Case 1',help='Enter a name for the modelled scenario')
#location = st.sidebar.text_input('ZIP code',value=77001)
location = st.sidebar.selectbox('City',['Austin','Dallas','Houston','Midland','San Antonio'])

@st.cache
def FixedDataSetup():
    
    dfFixeddata['Date']=pd.date_range("2022-01-01",periods=(365*24),freq="H")

    dfFixeddata['MonthNum']=pd.DatetimeIndex(dfFixeddata['Date']).month

    dfFixeddata['DayNum']=pd.DatetimeIndex(dfFixeddata['Date']).day

    dfFixeddata['HourNum']=pd.DatetimeIndex(dfFixeddata['Date']).hour
    return dfFixeddata

dfFixeddata = FixedDataSetup()

st.write(dfFixeddata)

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
        soiling = st.number_input('Soiling (%)',min_value=(0.0),max_value=(100.0),value=2.0)
        shading = st.number_input('Shading (%)',min_value=(0.0),max_value=(100.0),value=3.0)
        snow = st.number_input('Snow (%)',min_value=(0.0),max_value=(100.0),value=0.0)
        mismatch = st.number_input('Mismatch (%)',min_value=(0.0),max_value=(100.0),value=2.0)
        wiring = st.number_input('Wiring (%)',min_value=(0.0),max_value=(100.0),value=2.0)
        connections = st.number_input('Connections (%)',min_value=(0.0),max_value=(100.0),value=0.5)
        initialDegradation = st.number_input('Inital Degradation',min_value=(0.0),max_value=(100.0),value=1.5)
        nameplateRating = st.number_input('Nameplate Rating (%)',min_value=(0.0),max_value=(100.0),value=1.0)
        age = st.number_input('Age (%)',min_value=(0.0),max_value=(100.0),value=0.0)
        availability = st.number_input('Availability (%)',min_value=(0.0),max_value=(100.0),value=0.0)
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
    
#Electric Conctract Setup


#NREL request building
@st.cache
def GetNRELData(location, dcSysSize, moduleType, arrayType, systemLosses, tilt, azimuth, dcToACRatio, inverterEff, groundCovRatio):
    myAPIkey = "9zzEI7dNgn4vk8706ibfhr9XPbzn7eKXIGc3TgMp"
    df = pd.DataFrame()
    jsonRequestStr = "&address="+str(location)+"&system_capacity="+str(dcSysSize)+"&module_type="+str(moduleType)+"&array_type="+str(arrayType)+"&losses="+str(systemLosses)+"&tilt="+str(tilt)+"&azimuth="+str(azimuth)+"&dc_ac_ratio="+str(dcToACRatio)+"&gcr="+str(groundCovRatio)+"&inv_eff="+str(inverterEff)
    #jsonRequestStr = "&address="+str(location)+"&system_capacity="+str(dcSysSize)+"&module_type="+str(moduleType)+"&array_type="+str(arrayType)+"&losses="+str(systemLosses)+"&tilt="+str(tilt)+"&azimuth="+str(azimuth)+"&dc_ac_ratio="+str(dcToACRatio)+"&inv_eff="+str(inverterEff)  
    request = "https://developer.nrel.gov/api/pvwatts/v6.json?api_key="+myAPIkey+jsonRequestStr+"&timeframe=hourly"
    response = requests.get(request)
    df=pd.json_normalize(response.json(),max_level=1)
    return df


def RunCase(location, dcSysSize, moduleType, arrayType, systemLosses, tilt, azimuth, dcToACRatio, inverterEff, groundCovRatio):
    global dfActivecase
    dfJson = GetNRELData(location, dcSysSize, moduleType, arrayType, systemLosses, tilt, azimuth, dcToACRatio, inverterEff, groundCovRatio)
    dfActivecase['SolarGen(w)']=dfJson.iloc[0,dfJson.columns.get_loc("outputs.ac")]
    st.write(dfActivecase['SolarGen(w)'])
    return None

#st.sidebar.button('Calculate Case',on_click=RunCase,args=(location, dcSysSize, moduleType, arrayType, systemLosses, tilt, azimuth))
if runcasebutton:
    RunCase(location, dcSysSize, moduleType, arrayType, systemLosses, tilt, azimuth, dcToACRatio, inverterEff, groundCovRatio)
    
    

