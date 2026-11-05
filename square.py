from pymavlink import mavutil
import time
def goto_position(north, east, down):
    master.mav.send(mavutil.mavlink.MAVLink_set_position_target_local_ned_message(
        10, master.target_system, master.target_component,
        mavutil.mavlink.MAV_FRAME_LOCAL_NED, int(0b110111111000), 
        north, east, down, 
        0, 0, 0, 0, 0, 0, 0, 0))
    
print("正在尋找虛擬無人機連線...")
# 1.建立通訊連線(透過tcp連線到本機模擬器)
# 飛控不會主動透過這個連線發送高度包裹
master = mavutil.mavlink_connection('tcp:127.0.0.1:5762')

# 等待無人機回傳「心跳包」，確認真的連接到
master.wait_heartbeat()
print("連線成功!無人機大腦已上線。")

# 所以要像飛控請求發送數據流
print("向無人機請求高度與位置數據流...")
master.mav.request_data_stream_send(
    master.target_system,
    master.target_component,
    mavutil.mavlink.MAV_DATA_STREAM_ALL,
    1, # 每秒傳送5次
    1 # 1代表開啟
)
time.sleep(2)

# 2.切換到GUIDED(引導)模式
print("切換到 GUIDED 模式...")
master.set_mode('GUIDED')
time.sleep(2) # 等待切換時間

# 3.解鎖馬達
print("解鎖馬達...")
master.arducopter_arm()
time.sleep(2) # 解鎖時間(待螺旋槳運轉)

# 4. 下達起飛命令(起飛至15公尺高)
print("發送起飛指令 (高度：15m)")
master.mav.command_long_send(
    master.target_system,
    master.target_component,
    mavutil.mavlink.MAV_CMD_NAV_TAKEOFF, # 起飛指令
    0, 0, 0, 0, 0, 0, 0, 15
)
print("指令發送完畢! 請看您的虛擬地圖和儀表板")

# 11/3 2026
print("無人機正在爬升中...")
while True:
    #在收到GLOBAL_POSITION_INT包裹之前，請停在這一行，不要往下執行
    msg = master.recv_match(type='GLOBAL_POSITION_INT', blocking=True) 
    if msg:
        # 提取相對高度(無人機傳回的單位是毫米(mm)，除以1000變公尺)
        current_alt = msg.relative_alt / 1000.0
        print(f"目前高度:{current_alt:.2f}公尺")
        #
        if current_alt >= 14.5:
            print("到達指定高度! 起飛任務完成。")
            break # 跳出迴圈
    #time.sleep(0.5)
#--- 到達指定高度後的動作 ---

print("=== 開始執行正方形巡邏任務 ===")
# 高度維持 15 公尺 (Z = -15)
alt = -15 

print("飛向第一站：往前 10 公尺")
goto_position(10, 0, alt)
time.sleep(5) # 等待 5 秒讓它飛過去

print("飛向第二站：接著往右 10 公尺")
goto_position(10, 10, alt)
time.sleep(5)

print("飛向第三站：接著往後 10 公尺")
goto_position(0, 10, alt)
time.sleep(5)

print("飛向第四站：回到起點")
goto_position(0, 0, alt)
time.sleep(5)

print("巡邏結束，準備降落...")
master.set_mode('LAND')

