# ================================================================
# WATER LEVEL CONTROL APP
# Minimal Style - Black & Orange
# ================================================================

import streamlit as st
import serial
import time
import pandas as pd
from serial import SerialException

# ================================================================
# PAGE CONFIG
# ================================================================
st.set_page_config(
    page_title="Water Level Control",
    page_icon="",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ================================================================
# CUSTOM CSS - MINIMAL BLACK & ORANGE
# ================================================================
st.markdown("""
<style>
    .stApp { background-color: #0d0d0d; }
    .stMarkdown, .stText, .stTitle, .stCaption, .stSubheader { color: #e6e6e6 !important; }
    
    [data-testid="metric-container"] {
        background-color: #1a1a1a !important;
        border: 1px solid #e65c00 !important;
        border-radius: 8px !important;
        padding: 15px !important;
    }
    [data-testid="metric-container"] label {
        color: #e65c00 !important;
        font-weight: bold !important;
        text-transform: uppercase !important;
        font-size: 12px !important;
        letter-spacing: 1px !important;
    }
    [data-testid="metric-container"] [data-testid="metric-value"] {
        color: #ffffff !important;
        font-size: 28px !important;
    }
    
    .stButton button {
        background-color: #e65c00 !important;
        color: #000000 !important;
        font-weight: bold !important;
        border: none !important;
        border-radius: 4px !important;
        padding: 8px 24px !important;
        width: 100% !important;
        text-transform: uppercase !important;
        letter-spacing: 1px !important;
        font-size: 13px !important;
    }
    .stButton button:hover {
        background-color: #ff751a !important;
        color: #000000 !important;
    }
    
    .stNumberInput input, .stTextInput input {
        background-color: #1a1a1a !important;
        border: 1px solid #333333 !important;
        border-radius: 4px !important;
        color: #ffffff !important;
    }
    .stNumberInput input:focus, .stTextInput input:focus {
        border-color: #e65c00 !important;
        box-shadow: 0 0 0 1px #e65c00 !important;
    }
    
    [data-testid="stSidebar"] {
        background-color: #0d0d0d !important;
        border-right: 1px solid #1a1a1a !important;
    }
    hr { border-color: #e65c00 !important; opacity: 0.3 !important; }
    .stAlert { background-color: #1a1a1a !important; border-left: 3px solid #e65c00 !important; }
    
    .dataframe {
        background-color: #1a1a1a !important;
        color: #e6e6e6 !important;
    }
    .dataframe th {
        background-color: #e65c00 !important;
        color: #000000 !important;
    }
</style>
""", unsafe_allow_html=True)

# ================================================================
# HEADER
# ================================================================
st.markdown(
    """
    <div style="border-bottom: 2px solid #e65c00; padding-bottom: 10px; margin-bottom: 30px;">
        <h1 style="color: #ffffff; font-weight: 300; letter-spacing: 2px; margin: 0; font-size: 32px;">
            WATER LEVEL CONTROL
        </h1>
        <p style="color: #e65c00; font-size: 14px; letter-spacing: 4px; margin: 0; text-transform: uppercase;">
            real-time monitoring & pid tuning
        </p>
    </div>
    """,
    unsafe_allow_html=True
)

# ================================================================
# SESSION STATE
# ================================================================
if 'ser' not in st.session_state:
    st.session_state.ser = None
    st.session_state.connected = False
    
if 'data' not in st.session_state:
    st.session_state.data = {
        'water_level': 0.0,
        'flow_in': 0.0,
        'flow_out': 0.0,
        'pump': 'OFF'
    }
    
if 'pid_params' not in st.session_state:
    st.session_state.pid_params = {
        'kp': 60.0,
        'ki': 0.2,
        'ff': 0.70,
        'setpoint': 7.0
    }
    
if 'history' not in st.session_state:
    st.session_state.history = {
        'time': [],
        'water_level': [],
        'flow_in': [],
        'flow_out': []
    }

# ================================================================
# FUNCTIONS
# ================================================================
def init_serial(port, baudrate=9600):
    try:
        ser = serial.Serial(port, baudrate, timeout=1)
        time.sleep(2)
        ser.reset_input_buffer()
        return ser
    except SerialException:
        return None

def send_command(ser, command):
    if ser and ser.is_open:
        ser.write(f"{command}\n".encode())
        return True
    return False

def read_data(ser):
    try:
        if ser and ser.in_waiting:
            line = ser.readline().decode().strip()
            if line:
                values = line.split(',')
                if len(values) == 4:
                    return {
                        'water_level': float(values[0]),
                        'flow_in': float(values[1]),
                        'flow_out': float(values[2]),
                        'pump': 'ON' if int(values[3]) == 1 else 'OFF'
                    }
    except:
        pass
    return None

# ================================================================
# SIDEBAR
# ================================================================
with st.sidebar:
    st.markdown(
        """
        <h3 style="color: #e65c00; font-weight: 300; letter-spacing: 2px; margin-top: 0; text-transform: uppercase; font-size: 14px;">
            connection
        </h3>
        """,
        unsafe_allow_html=True
    )
    
    port = st.text_input(
        "port",
        value="/dev/cu.usbmodem1101",
        label_visibility="collapsed"
    )
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("connect", use_container_width=True):
            st.session_state.ser = init_serial(port)
            if st.session_state.ser:
                st.session_state.connected = True
                st.success("connected")
            else:
                st.session_state.connected = False
                st.error("connection failed")
    
    with col2:
        if st.button("disconnect", use_container_width=True):
            if st.session_state.ser:
                st.session_state.ser.close()
                st.session_state.ser = None
                st.session_state.connected = False
            st.info("disconnected")
    
    st.divider()
    
    st.markdown(
        """
        <h3 style="color: #e65c00; font-weight: 300; letter-spacing: 2px; margin-top: 0; text-transform: uppercase; font-size: 14px;">
            pid tuning
        </h3>
        """,
        unsafe_allow_html=True
    )
    
    new_kp = st.number_input(
        "Kp",
        value=st.session_state.pid_params['kp'],
        step=1.0,
        format="%.1f",
        label_visibility="collapsed"
    )
    
    new_ki = st.number_input(
        "Ki",
        value=st.session_state.pid_params['ki'],
        step=0.1,
        format="%.1f",
        label_visibility="collapsed"
    )
    
    new_ff = st.number_input(
        "FF_Gain",
        value=st.session_state.pid_params['ff'],
        step=0.05,
        format="%.2f",
        label_visibility="collapsed"
    )
    
    new_setpoint = st.number_input(
        "Setpoint (cm)",
        value=st.session_state.pid_params['setpoint'],
        step=0.5,
        format="%.1f",
        label_visibility="collapsed"
    )
    
    if st.button("apply", use_container_width=True):
        st.session_state.pid_params['kp'] = new_kp
        st.session_state.pid_params['ki'] = new_ki
        st.session_state.pid_params['ff'] = new_ff
        st.session_state.pid_params['setpoint'] = new_setpoint
        
        if st.session_state.ser and st.session_state.connected:
            cmd = f"P{new_kp},I{new_ki},F{new_ff},S{new_setpoint}"
            if send_command(st.session_state.ser, cmd):
                st.success("parameters sent")
            else:
                st.error("send failed")
        else:
            st.warning("not connected")

# ================================================================
# MAIN CONTENT
# ================================================================
if st.session_state.connected and st.session_state.ser:
    # READ DATA
    data = read_data(st.session_state.ser)
    if data:
        st.session_state.data = data
        
        # Update history
        st.session_state.history['time'].append(time.time())
        st.session_state.history['water_level'].append(data['water_level'])
        st.session_state.history['flow_in'].append(data['flow_in'])
        st.session_state.history['flow_out'].append(data['flow_out'])
        
        if len(st.session_state.history['time']) > 50:
            for key in st.session_state.history:
                st.session_state.history[key] = st.session_state.history[key][-50:]
    
    # METRICS
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "water level",
            f"{st.session_state.data['water_level']:.2f} cm",
            delta=f"{(st.session_state.data['water_level'] - st.session_state.pid_params['setpoint']):+.2f} cm"
        )
    
    with col2:
        st.metric(
            "flow in",
            f"{st.session_state.data['flow_in']:.1f} L/m"
        )
    
    with col3:
        st.metric(
            "flow out",
            f"{st.session_state.data['flow_out']:.1f} L/m"
        )
    
    with col4:
        st.metric(
            "pump",
            f"{st.session_state.data['pump']}"
        )
    
    # HISTORY TABLE
    st.divider()
    if len(st.session_state.history['time']) > 0:
        df = pd.DataFrame({
            'time': st.session_state.history['time'],
            'water_level': st.session_state.history['water_level'],
            'flow_in': st.session_state.history['flow_in'],
            'flow_out': st.session_state.history['flow_out']
        })
        st.dataframe(df, use_container_width=True, height=200)
    
    # AUTO REFRESH
    time.sleep(0.2)
    st.rerun()

else:
    st.markdown(
        """
        <div style="
            display: flex;
            justify-content: center;
            align-items: center;
            height: 400px;
            border: 1px solid #333333;
            border-radius: 8px;
            background-color: #0d0d0d;
        ">
            <p style="
                color: #666666;
                font-size: 18px;
                letter-spacing: 4px;
                text-transform: uppercase;
            ">
                connect to arduino
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )
