# 通过FPGA-树莓派实现简单波形探测功能
文件包括：
1.gui测试，是本地的python调试文件，可以在本地执行进行ui和信号传输的仿真
2.PI_FPGA，是实际与FPGA进行通信的最终文件，通过串口与FPGA连接后可以接受波形并在UI显示
3.devices文件是保存的设备信息文件，包含了设备名称、测量数据等信息
4.信号源数据是测试的信号源数据，包含了设备名称、测量结果和波形信息数据
