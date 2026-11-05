from pymavlink import mavutil
import time
print("正在尋找虛擬無人機連線...")

master = mavutil.mavlink_connection('tcp:127.0.0.1:5762')

master.wait_heartbeat()
print("連線成功!無人機大腦已上線")

print("向無人機請求高度與位置數據流...")
master.mav.request_data_stream_send(
    master.target_system,
    master.target_component,
    mavutil.mavlink.MAV_DATA_STREAM_ALL,
    1, # 每秒傳送5次
    1 # 1代表開啟
)
time.sleep(2)

print("開始監聽飛行姿態數據(按ctrl+c結束)")
while True:
    # 
    msg = master.recv_match(type='ATTITUDE', blocking=True)
    if msg:
        print(f"俯仰角(Pitch):{msg.pitch:.2f} | 翻滾角(Roll):{msg.roll:.2f} | 偏航角(Yaw):{msg.yaw:.2f}")