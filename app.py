# app.py
# Streamlit WOL dashboard with tabs, OS-based SSH shutdown, and IP-only status check
# Updated ping_device for proper OS detection

import streamlit as st
import yaml
import os
import platform
import subprocess
import time
from wakeonlan import send_magic_packet
import paramiko

DATA_FILE = "devices.yaml"

# YAML load/save

def load_devices():
    if not os.path.exists(DATA_FILE):
        return []
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        try:
            data = yaml.safe_load(f)
            return data if data else []
        except yaml.YAMLError:
            return []

def save_devices(devices):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        yaml.dump(devices, f, allow_unicode=True)

# Updated ping helper

# Updated ping helper

def ping_device(ip: str, timeout_sec: float = 1.0) -> bool:
    import platform, subprocess
    if not ip:
        return False
    system = platform.system().lower()
    try:
        if system == "windows":
            cmd = ["ping", "-n", "1", "-w", str(int(timeout_sec * 1000)), ip]
        else:
            cmd = ["ping", "-c", "1", ip]
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return result.returncode == 0
    except Exception as e:
        print(f"[PING DEBUG] Failed for {ip}: {e}")
        return False
    system = platform.system().lower()
    try:
        if system == "windows":
            cmd = ["ping", "-n", "1", "-w", str(int(timeout_sec * 1000)), ip]
        else:
            cmd = ["ping", "-c", "1", ip]
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return result.returncode == 0
    except Exception as e:
        print(f"[PING DEBUG] Failed for {ip}: {e}")
        return False

# WOL

def wol_device(mac: str):
    try:
        send_magic_packet(mac)
        return True, None
    except Exception as e:
        return False, str(e)

# SSH Shutdown

def ssh_shutdown(ip: str, os_type: str, username: str, password: str, timeout: float = 8.0):
    if not (ip and os_type and username and password):
        return False, "IP/OS/SSH 계정 정보가 부족합니다."
    os_type = os_type.strip().lower()
    if os_type not in {"windows", "linux", "mac"}:
        return False, "OS 타입은 windows/linux/mac 중 하나여야 합니다."
    if os_type == "windows":
        remote_cmd = "shutdown /s /t 0"
    else:
        remote_cmd = "echo '" + password.replace("'", "'\\''") + "' | sudo -S shutdown -h now"
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        client.connect(ip, port=22, username=username, password=password, timeout=timeout, banner_timeout=timeout, auth_timeout=timeout)
        stdin, stdout, stderr = client.exec_command(remote_cmd, timeout=timeout)
        exit_status = stdout.channel.recv_exit_status()
        if exit_status == 0:
            return True, "Shutdown 명령 전송 완료"
        else:
            err_txt = stderr.read().decode(errors="ignore") if stderr else ""
            return False, f"원격 명령 실패(exit {exit_status}): {err_txt.strip()}"
    except Exception as e:
        return False, f"SSH 오류: {e}"
    finally:
        try:
            client.close()
        except Exception:
            pass

# Streamlit App

def main():
    st.set_page_config(page_title="Wake-on-LAN Dashboard (Tabs + Shutdown)", page_icon="💡", layout="wide")
    if "last_refresh" not in st.session_state:
        st.session_state.last_refresh = time.time()
    now = time.time()
    if now - st.session_state.last_refresh >= 5 and not st.session_state.get("in_action", False):
        st.session_state.last_refresh = now
        st.rerun()
    st.title("💻 Wake-on-LAN Dashboard")
    devices = load_devices()
    # Ensure devices is a list
    if isinstance(devices, dict):
        devices = [{"name": k, **v} for k, v in devices.items()]
    tab_list, tab_register = st.tabs(["📋 장비 목록", "➕ 장비 등록"])
    with tab_list:
        st.subheader("📋 등록된 장비")
        if not devices:
            st.info("등록된 장비가 없습니다. 우측 탭에서 장비를 추가해 주세요.")
        else:
            for idx, device in enumerate(devices):
                name = device.get("name") or f"Device {idx+1}"
                mac = device.get("mac")
                ip = device.get("ip")
                os_type = (device.get("os") or "").lower()
                ssh_user = device.get("ssh_user")
                ssh_pass = device.get("ssh_pass")
                col1, col2, col3, col4, col5 = st.columns([3, 1, 1, 1, 1])
                with col1:
                    os_label = os_type if os_type else "미등록"
                    info_line = f"**{name}** | MAC: `{mac}` | IP: `{ip or '미등록'}` | OS: `{os_label}`"
                    if ssh_user:
                        masked = ("*" * len(ssh_pass)) if ssh_pass else ""
                        info_line += f" | SSH: `{ssh_user}`"
                    st.markdown(info_line)
                with col2:
                    if ip:
                        is_on = ping_device(ip, timeout_sec=0.8)
                        st.write("🟢 On" if is_on else "🔴 Off")
                    else:
                        st.write("❓ Unknown")
                        st.caption("IP 필요")
                with col3:
                    if st.button("Wake", key=f"wake_{idx}"):
                        st.session_state["in_action"] = True
                        try:
                            with st.spinner("WOL 패킷 전송 중..."):
                                ok, err = wol_device(mac)
                                if ok:
                                    st.success("WOL 전송 완료")
                                else:
                                    st.error(f"WOL 전송 실패: {err}")
                                prog = st.progress(100)
                                time.sleep(0.4)
                                prog.empty()
                        finally:
                            st.session_state["in_action"] = False
                            st.rerun()
                with col4:
                    disabled = not (ip and os_type in {"windows", "linux", "mac"} and ssh_user and ssh_pass)
                    if st.button("Shutdown", key=f"shutdown_{idx}", disabled=disabled):
                        st.session_state["in_action"] = True
                        try:
                            with st.spinner("원격 종료 명령 전송 중..."):
                                ok, msg = ssh_shutdown(ip, os_type, ssh_user, ssh_pass)
                                if ok:
                                    st.success(msg)
                                else:
                                    st.error(msg)
                                prog = st.progress(100)
                                time.sleep(0.4)
                                prog.empty()
                        finally:
                            st.session_state["in_action"] = False
                            st.rerun()
                with col5:
                    if st.button("삭제", key=f"del_{idx}"):
                        devices.pop(idx)
                        save_devices(devices)
                        st.warning(f"{name} 삭제 완료")
                        st.rerun()
    with tab_register:
        st.subheader("➕ 새 장비 등록")
        with st.form("register_device_form"):
            name = st.text_input("장비 이름")
            mac = st.text_input("MAC 주소 (예: AA:BB:CC:DD:EE:FF)")
            ip = st.text_input("IP 주소 (선택)")
            os_type = st.selectbox("장비 OS", ["", "windows", "linux", "mac"], index=0)
            ssh_user = st.text_input("SSH 사용자명 (선택)")
            ssh_pass = st.text_input("SSH 비밀번호 (선택)", type="password")
            submitted = st.form_submit_button("등록하기")
            if submitted:
                if not mac:
                    st.error("MAC 주소는 필수입니다.")
                else:
                    devices.append({
                        "name": name,
                        "mac": mac,
                        "ip": ip if ip else None,
                        "os": os_type if os_type else None,
                        "ssh_user": ssh_user if ssh_user else None,
                        "ssh_pass": ssh_pass if ssh_pass else None,
                    })
                    save_devices(devices)
                    st.success(f"등록 완료: {name or mac}")
                    st.rerun()

if __name__ == "__main__":
    main()
