from pymavlink import mavutil
import time

# ==========================================
# 1. 基本設定與連線
# ==========================================
print("正在尋找虛擬無人機連線...")
master = mavutil.mavlink_connection('tcp:127.0.0.1:5762')
master.wait_heartbeat()
print("連線成功！無人機大腦已上線。")

print("向無人機請求數據流 (啟動雷達)...")
master.mav.request_data_stream_send(
    master.target_system, master.target_component,
    mavutil.mavlink.MAV_DATA_STREAM_ALL, 2, 1  # 頻率設2，每秒印 2 次姿態剛剛好
)
time.sleep(1)

# ==========================================
# 2. 定義導航與雷達工具
# ==========================================
def goto_position(north, east, down):
    """發送 NED 絕對座標導航指令"""
    master.mav.send(mavutil.mavlink.MAVLink_set_position_target_local_ned_message(
        10, master.target_system, master.target_component,
        mavutil.mavlink.MAV_FRAME_LOCAL_NED, int(0b110111111000), 
        north, east, down, 
        0, 0, 0, 0, 0, 0, 0, 0))

def fly_and_monitor(wait_seconds):
    """【新工具】一邊等待無人機飛到定位，一邊印出即時姿態雷達"""
    end_time = time.time() + wait_seconds
    while time.time() < end_time:
        # 攔截姿態包裹，timeout=0.5 避免完全卡死
        msg = master.recv_match(type='ATTITUDE', blocking=True, timeout=0.5)
        if msg:
            print(f"  [動態雷達] Pitch: {msg.pitch:.2f} | Roll: {msg.roll:.2f} | Yaw: {msg.yaw:.2f}")

# ==========================================
# 3. 自動起飛流程
# ==========================================
print("切換到 GUIDED 模式並解鎖...")
master.set_mode('GUIDED')
master.arducopter_arm()
master.wait_heartbeat()

print("起飛到 15 公尺...")
master.mav.command_long_send(
    master.target_system, master.target_component,
    mavutil.mavlink.MAV_CMD_NAV_TAKEOFF, 0, 0, 0, 0, 0, 0, 0, 15)

while True:
    msg = master.recv_match(type='GLOBAL_POSITION_INT', blocking=True)
    if msg:
        alt = msg.relative_alt / 1000.0
        if alt >= 14.5:
            print("起飛完成！")
            break

# ==========================================
# 4. 正方形巡邏 + 同步雷達監聽
# ==========================================
print("\n=== 開始執行正方形巡邏任務 ===")
alt = -15 

print("\n飛向第一站：往前 10 公尺")
goto_position(10, 0, alt)
fly_and_monitor(6) # 讓它飛 6 秒，這期間會瘋狂印出姿態數據！

print("\n飛向第二站：接著往右 10 公尺")
goto_position(10, 10, alt)
fly_and_monitor(6)

print("\n飛向第三站：接著往後 10 公尺")
goto_position(0, 10, alt)
fly_and_monitor(6)

print("\n飛向第四站：回到起點")
goto_position(0, 0, alt)
fly_and_monitor(6)

print("\n巡邏結束，準備降落...")
master.set_mode('LAND')