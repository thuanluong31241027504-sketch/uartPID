import streamlit as st
import serial
import time
import pandas as pd
import threading
from serial import SerialException

# --- CẤU HÌNH ---
st.set_page_config(layout="wide", page_title="Water Level Control")

st.title("💧 Hệ thống điều khiển mực nước")
st.caption("Điều khiển và giám sát bồn nước qua UART")

# --- QUẢN LÝ KẾT NỐI SERIAL ---
# Sử dụng session_state và cache để tránh mở port liên tục [citation:5]
@st.cache_resource
def init_serial(port, baudrate=9600):
    try:
        ser = serial.Serial(port, baudrate, timeout=1)
        time.sleep(2)
        return ser
    except SerialException as e:
        st.error(f"❌ Lỗi kết nối Serial: {e}")
        return None

# --- KHỞI TẠO SESSION STATE ---
if 'ser' not in st.session_state:
    st.session_state.ser = None
if 'data' not in st.session_state:
    st.session_state.data = {"water_level": 0, "flow_in": 0, "flow_out": 0}
if 'pid_params' not in st.session_state:
    st.session_state.pid_params = {"Kp": 60.0, "Ki": 0.2, "FF": 0.7}

# --- GIAO DIỆN NGƯỜI DÙNG ---
col1, col2 = st.columns([1, 3])

with col1:
    st.subheader("🔌 Cổng kết nối")
    port = st.text_input("Cổng Serial", value="/dev/cu.usbmodem1101", 
                         help="Ví dụ: COM3, /dev/ttyUSB0, /dev/cu.usbmodem1101")
    if st.button("Kết nối"):
        st.session_state.ser = init_serial(port)
        if st.session_state.ser:
            st.success("✅ Kết nối thành công!")

    st.divider()
    st.subheader("⚙️ Chỉnh PID")
    
    new_Kp = st.number_input("Kp (Tỉ lệ)", value=st.session_state.pid_params["Kp"], step=1.0)
    new_Ki = st.number_input("Ki (Tích phân)", value=st.session_state.pid_params["Ki"], step=0.1)
    new_FF = st.number_input("FF_Gain (Truyền thẳng)", value=st.session_state.pid_params["FF"], step=0.05)
    
    if st.button("📤 Gửi thông số PID mới"):
        st.session_state.pid_params["Kp"] = new_Kp
        st.session_state.pid_params["Ki"] = new_Ki
        st.session_state.pid_params["FF"] = new_FF
        if st.session_state.ser:
            cmd = f"P{new_Kp},I{new_Ki},F{new_FF}\n"
            st.session_state.ser.write(cmd.encode())
            st.toast("Đã gửi thông số mới!")
        else:
            st.warning("⚠️ Vui lòng kết nối Arduino trước!")

with col2:
    st.subheader("📊 Dữ liệu thời gian thực")
    placeholder = st.empty()
    chart_placeholder = st.empty()
    
    if st.session_state.ser:
        while True:
            try:
                if st.session_state.ser.in_waiting:
                    line = st.session_state.ser.readline().decode().strip()
                    values = line.split(',')
                    if len(values) == 4:
                        st.session_state.data["water_level"] = float(values[0])
                        st.session_state.data["flow_in"] = float(values[1])
                        st.session_state.data["flow_out"] = float(values[2])
                        st.session_state.data["pump"] = "ON" if int(values[3]) == 1 else "OFF"
                        
                        # Cập nhật UI
                        with placeholder.container():
                            c1, c2, c3, c4 = st.columns(4)
                            c1.metric("Mực nước", f"{st.session_state.data['water_level']:.2f} cm", 
                                      delta=f"{st.session_state.data['water_level']-7.0:.2f} cm")
                            c2.metric("Lưu lượng vào", f"{st.session_state.data['flow_in']:.1f} L/m")
                            c3.metric("Lưu lượng ra", f"{st.session_state.data['flow_out']:.1f} L/m")
                            c4.metric("Trạng thái bơm", st.session_state.data["pump"])
                        
                        # Vẽ biểu đồ (nếu có dữ liệu tích lũy)
                        # ... 
            except Exception as e:
                st.error(f"Lỗi đọc dữ liệu: {e}")
                break
            time.sleep(0.1)
    else:
        st.info("💡 Vui lòng kết nối Arduino để xem dữ liệu.")
