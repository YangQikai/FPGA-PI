import sys
import numpy as np
import json
import csv
from scipy.fftpack import fft
import matplotlib.pyplot as plt
import time
from PyQt5.QtWidgets import (QApplication, QMainWindow, QPushButton, QVBoxLayout
                             , QHBoxLayout, QWidget, QLineEdit, QFormLayout, QTextEdit
                             , QComboBox, QLabel, QInputDialog, QFileDialog, QMessageBox)
from PyQt5.QtCore import QTimer,Qt
from PyQt5.QtGui import QColor, QPainter, QBrush, QRadialGradient
from PyQt5.QtWidgets import QGridLayout, QWidget, QVBoxLayout
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
import os
os.environ['DISPLAY'] = "localhost:10.0"

# 采样点数全局变量
NUM_SAMPLES=50000

class LedIndicator(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(20, 20)
        self.state = 2

    def set_state(self, state):
        self.state = state
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)

        # 画一个圆形
        gradient = QRadialGradient(self.width() / 2, self.height() / 2, self.width() / 2)
        if self.state==2:
            gradient.setColorAt(0.6, QColor(99, 199, 86, 255))  # 绿色表示开
            gradient.setColorAt(1, QColor(0, 0, 0, 0)) 
        elif self.state==0:
            gradient.setColorAt(0.6, QColor(237, 106, 95, 255))  # 红色表示关
            gradient.setColorAt(1, QColor(0, 0, 0, 0))  
        else:
            gradient.setColorAt(0.6, QColor(244, 191, 79, 255))
            gradient.setColorAt(1, QColor(0, 0, 0, 0))  # 黄色表示接收中

        painter.setBrush(QBrush(gradient))
        painter.setPen(Qt.NoPen) # 无边框
        painter.drawEllipse(0, 0, self.width(), self.height())

class OverlayWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_TransparentForMouseEvents)

    def paintEvent(self, event):
        pass

class SignalAnalyzer(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initializeUI()

    plt.rcParams['axes.unicode_minus'] = False  # 解决保存图像是负号'-'显示为方块的问题
    plt.rc('font',family='SimHei')
    #plt.style.use('ggplot')   

    def initializeUI(self):
        self.setWindowTitle('Signal Analyzer')
        self.setGeometry(100, 100, 1200, 800)

        # 创建一个水平布局
        main_layout = QHBoxLayout()

        # 创建一个垂直布局用于图形显示
        graph_layout = QVBoxLayout()

        # 创建两个Figure和FigureCanvas来显示图形
        self.figure1, self.ax1 = plt.subplots(2, 1, figsize=(10, 7), tight_layout=True)
        self.canvas1 = FigureCanvas(self.figure1)
        self.figure2, self.ax2 = plt.subplots(1, 1, figsize=(10, 4.5), tight_layout=True)
        self.canvas2 = FigureCanvas(self.figure2)

        # 创建一个水平布局用于控制信号增益
        gain_layout = QHBoxLayout()
        self.gain = 1
        # 无增益按钮
        self.no_gain_button = QPushButton('无增益', self)
        self.no_gain_button.clicked.connect(self.noGain)
        # 5.1/5.1倍增益按钮
        self.gain_1_button = QPushButton('2倍增益', self)
        self.gain_1_button.clicked.connect(self.gain5)
        # 10/5.1倍增益按钮
        self.gain_10_button = QPushButton('2.961倍增益', self)
        self.gain_10_button.clicked.connect(self.gain10)
        # 15/5.1倍增益按钮
        self.gain_15_button = QPushButton('3.941倍增益', self)
        self.gain_15_button.clicked.connect(self.gain15)
        # 47/5.1倍增益按钮
        self.gain_47_button = QPushButton('10.216倍增益', self)
        self.gain_47_button.clicked.connect(self.gain47)
        # 100/5.1倍增益按钮
        self.gain_100_button = QPushButton('20.608倍增益', self)
        self.gain_100_button.clicked.connect(self.gain100)
        # 200/5.1倍增益按钮
        self.gain_200_button = QPushButton('40.216倍增益', self)
        self.gain_200_button.clicked.connect(self.gain200)

        gain_layout.addWidget(self.no_gain_button)
        gain_layout.addWidget(self.gain_1_button)
        gain_layout.addWidget(self.gain_10_button)
        gain_layout.addWidget(self.gain_15_button)
        gain_layout.addWidget(self.gain_47_button)
        gain_layout.addWidget(self.gain_100_button)
        gain_layout.addWidget(self.gain_200_button)
        
        # 创建一个水平布局用于显示时间基波形
        time_base=QHBoxLayout()
        self.time_base=4    #时基初始化
        self.time_dalay=0   #延迟初始化
        # 添加获取稳态波形按钮
        self.get_data_button = QPushButton('获取稳态波形', self)
        self.get_data_button.clicked.connect(self.plotSignal)
        # 时基减少按钮
        self.time_base_reduce_button = QPushButton('时基减少', self)
        self.time_base_reduce_button.clicked.connect(self.timeBaseReduce)
        # 时基增加按钮
        self.time_base_increase_button = QPushButton('时基增加', self)
        self.time_base_increase_button.clicked.connect(self.timeBaseIncrease)
        # 延迟增加按钮
        self.time_dalay_increase_button = QPushButton('延迟增加', self)
        self.time_dalay_increase_button.setFixedWidth(80)
        self.time_dalay_increase_button.clicked.connect(self.timeDelayIncrease)
        # 延迟减少按钮
        self.time_dalay_reduce_button = QPushButton('延迟减少', self)
        self.time_dalay_reduce_button.setFixedWidth(80)
        self.time_dalay_reduce_button.clicked.connect(self.timeDelayReduce)

        time_base.addWidget(self.get_data_button)
        time_base.addWidget(self.time_base_reduce_button)
        time_base.addWidget(self.time_base_increase_button)
        time_base.addWidget(self.time_dalay_reduce_button)
        time_base.addWidget(self.time_dalay_increase_button)

        # 创建一个容器用于显示波形和LED指示灯
        container = QWidget()
        container_layout = QGridLayout(container)
        container_layout.addWidget(self.canvas1, 0, 0)
        # 创建一个LED指示灯
        self.led = LedIndicator()
        overlay = OverlayWidget(container)
        overlay_layout = QVBoxLayout(overlay)
        overlay_layout.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        overlay_layout.setContentsMargins(10, 10, 0, 0)
        overlay_layout.addWidget(self.led)
        container_layout.addWidget(overlay, 0, 0)

        # 创建一个水平布局用于控制瞬态波形
        transient_signal_layout = QHBoxLayout()
        
        self.if_stop=True
        self.start_button = QPushButton('开始采集瞬态波形', self)
        self.start_button.clicked.connect(self.start_transient_signal)
        self.stop_button = QPushButton('停止采集瞬态波形', self)
        self.stop_button.clicked.connect(self.stop_transient_signal)
        self.save_button = QPushButton('保存瞬态波形', self)
        self.save_button.clicked.connect(self.save_transient_signal)

        transient_signal_layout.addWidget(self.start_button)
        transient_signal_layout.addWidget(self.stop_button)
        transient_signal_layout.addWidget(self.save_button)

        # 将图形画布添加到布局中
        graph_layout.addWidget(container)
        graph_layout.addLayout(gain_layout)
        graph_layout.addLayout(time_base)
        graph_layout.addWidget(self.canvas2)
        graph_layout.addLayout(transient_signal_layout)
        # 设置布局间距
        graph_layout.setSpacing(0)
        gain_layout.setSpacing(10)
        time_base.setSpacing(10)
        transient_signal_layout.setSpacing(10)

        # 创建一个垂直布局用于显示测量值
        control_layout = QVBoxLayout()

        # 创建一个下拉框用于选择设备
        self.device_select = QComboBox(self)
        self.device_select.addItem("选择设备")
        self.device_select.currentIndexChanged.connect(self.loadDeviceData)
        control_layout.addWidget(self.device_select)

        self.add_device_button = QPushButton('添加设备', self)
        self.add_device_button.clicked.connect(self.addDevice)
        control_layout.addWidget(self.add_device_button)

        # 创建空载按钮
        self.unloaded_button = QPushButton('空载计算', self)
        self.unloaded_button.clicked.connect(lambda: self.showSignalInfo('unloaded'))
        control_layout.addWidget(self.unloaded_button)
        

        # 创建一个表单布局用于显示空载测量结果
        unloaded_form_layout = QFormLayout()

        self.unloaded_peak_voltage_edit = QLineEdit()
        self.unloaded_peak_voltage_edit.setReadOnly(True)
        unloaded_form_layout.addRow('空载波峰值:', self.unloaded_peak_voltage_edit)

        self.unloaded_trough_voltage_edit = QLineEdit()
        self.unloaded_trough_voltage_edit.setReadOnly(True)
        unloaded_form_layout.addRow('空载波谷值:', self.unloaded_trough_voltage_edit)

        self.unloaded_rms_voltage_edit = QLineEdit()
        self.unloaded_rms_voltage_edit.setReadOnly(True)
        unloaded_form_layout.addRow('空载纹波有效值:', self.unloaded_rms_voltage_edit)

        self.unloaded_mean_voltage_edit = QLineEdit()
        self.unloaded_mean_voltage_edit.setReadOnly(True)
        unloaded_form_layout.addRow('空载平均值:', self.unloaded_mean_voltage_edit)

        self.unloaded_snr_edit = QLineEdit()
        self.unloaded_snr_edit.setReadOnly(True)
        unloaded_form_layout.addRow('空载信噪比:', self.unloaded_snr_edit)

        self.unloaded_ripple_freq_edit = QTextEdit()
        self.unloaded_ripple_freq_edit.setReadOnly(True)
        self.unloaded_ripple_freq_edit.setFixedHeight(60)
        self.unloaded_ripple_freq_edit.setFixedWidth(210)
        unloaded_form_layout.addRow('空载纹波分量', self.unloaded_ripple_freq_edit)

        control_layout.addLayout(unloaded_form_layout)

        # 创建满载按钮
        self.loaded_button = QPushButton('满载计算', self)
        self.loaded_button.clicked.connect(lambda: self.showSignalInfo('loaded'))
        control_layout.addWidget(self.loaded_button)

        # 创建一个表单布局用于显示满载测量结果
        loaded_form_layout = QFormLayout()

        self.loaded_peak_voltage_edit = QLineEdit()
        self.loaded_peak_voltage_edit.setReadOnly(True)
        loaded_form_layout.addRow('满载波峰值:', self.loaded_peak_voltage_edit)

        self.loaded_trough_voltage_edit = QLineEdit()
        self.loaded_trough_voltage_edit.setReadOnly(True)
        loaded_form_layout.addRow('满载波谷值:', self.loaded_trough_voltage_edit)

        self.loaded_rms_voltage_edit = QLineEdit()
        self.loaded_rms_voltage_edit.setReadOnly(True)
        loaded_form_layout.addRow('满载纹波有效值:', self.loaded_rms_voltage_edit)

        self.loaded_mean_voltage_edit = QLineEdit()
        self.loaded_mean_voltage_edit.setReadOnly(True)
        loaded_form_layout.addRow('满载平均值:', self.loaded_mean_voltage_edit)

        self.loaded_snr_edit = QLineEdit()
        self.loaded_snr_edit.setReadOnly(True)
        loaded_form_layout.addRow('满载信噪比:', self.loaded_snr_edit)

        self.loaded_ripple_freq_edit = QTextEdit()
        self.loaded_ripple_freq_edit.setReadOnly(True)
        self.loaded_ripple_freq_edit.setFixedHeight(60)
        self.loaded_ripple_freq_edit.setFixedWidth(210)
        loaded_form_layout.addRow('满载纹波分量', self.loaded_ripple_freq_edit)

        control_layout.addLayout(loaded_form_layout)

        # 创建一个按钮，点击后显示导出数据
        self.current_device = None
        self.export_button = QPushButton('导出数据', self)
        self.export_button.clicked.connect(self.exportData)
        control_layout.addWidget(self.export_button)

        # 创建一个垂直布局用于显示计算信息
        inf_layout = QVBoxLayout()

        # 创建电压调节范围计算按钮和清零按钮放在一个平行布局中
        votage_adjustment_range_layout = QHBoxLayout()
        self.voltage_adjustment_range_button = QPushButton('电压调节范围计算', self)
        self.voltage_adjustment_range_button.clicked.connect(lambda: self.showSignalInfo('min_max_voltage'))
        self.voltage_adjustment_range_button_clear = QPushButton('清零', self)
        self.voltage_adjustment_range_button_clear.clicked.connect(lambda: self.showSignalInfo('clear'))
        votage_adjustment_range_layout.addWidget(self.voltage_adjustment_range_button)
        votage_adjustment_range_layout.addWidget(self.voltage_adjustment_range_button_clear)

        inf_layout.addLayout(votage_adjustment_range_layout)

        # 创建一个表单布局用于显示电压调整率
        volage_adjustment_layout = QFormLayout()
        # 创建一个文本框，显示max和min值和电压调节范围=max-min
        self.max_voltage_edit = QLineEdit()
        self.max_voltage_edit.setReadOnly(True)
        volage_adjustment_layout.addRow('最大值:', self.max_voltage_edit)
        self.min_voltage_edit = QLineEdit()
        self.min_voltage_edit.setReadOnly(True)
        volage_adjustment_layout.addRow('最小值:', self.min_voltage_edit)
        self.voltage_range_edit = QLineEdit()
        self.voltage_range_edit.setReadOnly(True)
        volage_adjustment_layout.addRow('电压调节范围:', self.voltage_range_edit)

        # 创建一个文本框，显示电压相对负载调整率
        self.voltage_adjustment_rate_edit = QLineEdit()
        self.voltage_adjustment_rate_edit.setReadOnly(True)
        volage_adjustment_layout.addRow('电压相对负载调整率:', self.voltage_adjustment_rate_edit)

        inf_layout.addLayout(volage_adjustment_layout)

        
        # 将布局添加到主布局中
        main_layout.addLayout(graph_layout, 3)
        main_layout.addLayout(control_layout, 1)
        main_layout.addLayout(inf_layout, 1)

        # 创建一个Widget作为布局的容器
        central_widget = QWidget()
        central_widget.setLayout(main_layout)
        self.setCentralWidget(central_widget)

        # 绘制波形图和FFT图
        self.setupTransientSignalTimer()
        self.loadDevices()
        #延迟10ms
        QTimer.singleShot(10, self.plotSignal)
        self.plotSignal()
    
    #给信号添加白噪声
    def addNoise(self, data, noise_level):
        noise = np.random.randn(len(data)) * np.sqrt(noise_level)
        return data + noise
    
    #设置暂态信号定时器
    def setupTransientSignalTimer(self):
        self.transient_data = np.array([])
        self.t=0
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.createTransientSignal)
        self.timer.start(10)   

    #调整增益
    def noGain(self):
        self.gain = 1
        self.plotSignal()
    def gain5(self):
        self.gain = (5.1+5.1)/5.1
        self.plotSignal()
    def gain10(self):
        self.gain = (10+5.1)/5.1
        self.plotSignal()
    def gain15(self):
        self.gain = (5.1+15)/5.1
        self.plotSignal()
    def gain47(self):
        self.gain = (5.1+47)/5.1
        self.plotSignal()
    def gain100(self):
        self.gain = (5.1+100)/5.1
        self.plotSignal()
    def gain200(self):
        self.gain = (5.1+200)/5.1
        self.plotSignal()
    
    #时基减少
    def timeBaseReduce(self):
        if self.time_base>1:
            self.time_base=self.time_base//2
            self.plotSignal()
    #时基增加
    def timeBaseIncrease(self):
        if self.time_base<128:
            self.time_base=self.time_base*2
            self.plotSignal()
    #延迟增加
    def timeDelayIncrease(self):
        if self.time_dalay<19:
            self.time_dalay+=1
            self.plotSignal()
    #延迟减少
    def timeDelayReduce(self):
        if self.time_dalay>0:
            self.time_dalay-=1
            self.plotSignal()

    #创建暂态信号
    def createTransientSignal(self):
        global NUM_SAMPLES

        NUM_SAMPLES=50000
        self.Fs= 65000
        f1 = 100
        f2 = 1200
        f3 = 3000
        f4 = 5000
        self.t+=0.0001
        t = np.linspace(0+self.t, 1+self.t, self.Fs)
        data_to_send=1.5+0.3*np.sin(2*np.pi*f1*t)+0.1*np.sin(2*np.pi*f2*t)\
                    +0.1*np.sin(2*np.pi*f3*t)+0.05*np.sin(2*np.pi*f4*t)\
                     +0.1*np.sin(2*np.pi*10000*t)+0.05*np.sin(2*np.pi*20000*t)+0.02*np.sin(2*np.pi*30000*t)
        #添加方波
        data_to_send[10000:20000]=data_to_send[10000:20000]+0.5
        #data_to_send = self.addNoise(data_to_send, 0.000001)   #添加白噪声
        self.transient_data = data_to_send
        if (self.if_stop==False):self.start_transient_signal()

    def plotSignal(self):
        if self.transient_data.size == 0: return      #暂态信号未生成
        self.data = self.transient_data*self.gain               #获取稳态信号
        self.data = self.addNoise(self.data, 0.001)   #添加白噪声

        # 计算FFT
        N = len(self.data)
        fft_data = fft(self.data)
        abs_data = np.abs(fft_data)
        normalization_data = abs_data / N
        normalization_data[1:N // 2] *= 2
        normalization_half_data = normalization_data[range(int(N / 2))]
        half_fx = np.fft.fftfreq(len(self.data), 1 / self.Fs)[:len(self.data) // 2]

        # 找到最大的数值及其索引
        n=0 
        #while True:

        top_four_indices = np.argsort(normalization_half_data)[-7:][::-1]  # 从大到小排序
        top_four_values = normalization_half_data[top_four_indices]
        top_four_frequencies = half_fx[top_four_indices]  # 获取对应的频率值

        # 绘制波形图
        self.ax1[0].clear()
        self.ax1[0].set_xlabel('Time/s', fontsize=8)
        self.ax1[0].set_ylabel('电压/V', fontsize=8)
        self.ax1[0].set_title('稳态时域波形', fontsize=10)
        data_base=NUM_SAMPLES//128*self.time_base
        self.ax1[0].set_xlism(self.time_dalay*data_base//20,self.time_dalay*data_base//20+data_base)
        self.ax1[0].plot(range(NUM_SAMPLES),self.data[:NUM_SAMPLES])
        self.ax1[0].set_ylim()
        self.ax1[0].grid(True)

        # 绘制FFT图
        self.ax1[1].clear()
        self.ax1[1].set_xlabel('频率f/Hz', fontsize=8)
        self.ax1[1].set_ylabel('电压/V', fontsize=8)
        self.ax1[1].set_title('稳态FFT', fontsize=10)
        self.ax1[1].plot(half_fx[1:], normalization_half_data[1:], '-c')
        #self.ax1[1].set_ylim(0,0.03)
        self.ax1[1].grid(True)

        # 在图形上标记点
        for index, value, freq in zip(top_four_indices, top_four_values, top_four_frequencies):
            self.ax1[1].annotate(f'({freq:.0f},{value:.2f})',(freq, value)
                                 , textcoords="offset points", xytext=(0,10), ha='center',fontsize=7)

        # 重绘画布
        self.canvas1.draw()

    def start_transient_signal(self):
        self.if_stop=False
        self.led.set_state(1)
        # 读取瞬态波形数据
        self.ax2.clear()
        self.ax2.set_xlabel('Time/s', fontsize=8)
        self.ax2.set_ylabel('电压/V', fontsize=8)
        self.ax2.set_title('瞬态波形', fontsize=10)
        self.ax2.plot(range(2200), self.transient_data[:2200])
        self.ax2.grid(True)

        # 重绘画布
        self.canvas2.draw()
        
    def stop_transient_signal(self):
        self.if_stop=True
        self.led.set_state(2)
    
    def save_transient_signal(self):
        file_name, _ = QFileDialog.getSaveFileName(self, '导出数据', '', 'CSV Files (*.csv)')
        if self.current_device is None:
            QMessageBox.warning(self, '警告', '请先选择一个设备')
            return
        if file_name:
            with open(file_name, 'w', newline='') as file:
                writer = csv.writer(file)
                # 写入设备名称
                writer.writerow(['Transient Signal Data'])
                writer.writerow(['Device'])
                writer.writerow([self.current_device])
            
                # 写入波形数据
                writer.writerow(['\n dataset:'])
                writer.writerow(['index','value/V'])
                for idx, val in enumerate(self.transient_data):
                    writer.writerow([idx,val])

    def showSignalInfo(self, mode):
        if self.current_device is None:
            QMessageBox.warning(self, '警告', '请先选择一个设备')
            return 

        # 波峰值、波谷值、有效值、平均值计算
        peak_voltage = np.max(self.data)
        trough_voltage = np.min(self.data)
        mean_voltage = np.mean(self.data)
        rms_voltage = np.sqrt(np.mean(np.array(self.data)**2)) - mean_voltage

        #重新FFT
        fft_data = fft(self.data)
        abs_data = np.abs(fft_data)
        normalization_data = abs_data / len(self.data)
        normalization_data[1:len(self.data) // 2] *= 2
        normalization_half_data = normalization_data[range(int(len(self.data) / 2))]
        half_fx = np.fft.fftfreq(len(self.data), 1 / self.Fs)[:len(self.data) // 2]
        #信噪比计算
        noise_power = np.mean(np.array((self.data - np.mean(self.data)))**2)
        signal_power = np.mean(np.array(self.data)**2)
        snr = 10 * np.log10(signal_power / noise_power)
        #筛选出FFT结果最大的信号频率
        top_indices = np.argsort(normalization_half_data)[-4:][::-1]
        top_freqs = half_fx[top_indices]
        top_amplitudes = normalization_half_data[top_indices]
        # 更新UI
        if mode == 'unloaded':  # 空载
            self.unloaded_peak_voltage_edit.setText(f'{peak_voltage:.2f} V')
            self.unloaded_trough_voltage_edit.setText(f'{trough_voltage:.2f} V')
            self.unloaded_rms_voltage_edit.setText(f'{rms_voltage:.2f} V')
            self.unloaded_mean_voltage_edit.setText(f'{mean_voltage:.2f} V')
            self.unloaded_snr_edit.setText(f'{snr:.2f} dB')
            self.unloaded_ripple_freq_edit.setText(
                f"freq= {top_freqs[1]:.2f} Hz, 幅值= {top_amplitudes[1]:.2f} V\n"
                f"freq= {top_freqs[2]:.2f} Hz, 幅值= {top_amplitudes[2]:.2f} V\n"
                f"freq= {top_freqs[3]:.2f} Hz, 幅值= {top_amplitudes[3]:.2f} V"
            )

            # 保存数据
            self.devices[self.current_device]['unloaded'] = {
                'peak_voltage': peak_voltage,
                'trough_voltage': trough_voltage,
                'rms_voltage': rms_voltage,
                'mean_voltage': mean_voltage,
                'snr': snr,
                'ripple_frequencies': top_freqs[1:].tolist(),
                'ripple_amplitudes': top_amplitudes[1:].tolist()
            }
        elif mode == 'loaded':  #满载
            self.loaded_peak_voltage_edit.setText(f'{peak_voltage:.2f} V')
            self.loaded_trough_voltage_edit.setText(f'{trough_voltage:.2f} V')
            self.loaded_rms_voltage_edit.setText(f'{rms_voltage:.2f} V')
            self.loaded_mean_voltage_edit.setText(f'{mean_voltage:.2f} V')
            self.loaded_snr_edit.setText(f'{snr:.2f} dB')
            self.loaded_ripple_freq_edit.setText(
                f"freq= {top_freqs[1]:.2f} Hz, 幅值= {top_amplitudes[1]:.2f} V\n"
                f"freq= {top_freqs[2]:.2f} Hz, 幅值= {top_amplitudes[2]:.2f} V\n"
                f"freq= {top_freqs[3]:.2f} Hz, 幅值= {top_amplitudes[3]:.2f} V"
            )

            self.devices[self.current_device]['loaded'] = {
                'peak_voltage': peak_voltage,
                'trough_voltage': trough_voltage,
                'rms_voltage': rms_voltage,
                'mean_voltage': mean_voltage,
                'snr': snr,
                'ripple_frequencies': top_freqs[1:].tolist(),
                'ripple_amplitudes': top_amplitudes[1:].tolist()
            }
        elif mode == 'min_max_voltage': # 电压调节范围计算
            max_voltage = self.max_voltage_edit.text()
            min_voltage = self.min_voltage_edit.text()
            if max_voltage : max_voltage = float(max_voltage.split(' ')[0])
            else : max_voltage = -10
            if min_voltage : min_voltage = float(min_voltage.split(' ')[0])
            else : min_voltage = 10
            max_voltage = max(max_voltage, peak_voltage)
            min_voltage = min(min_voltage, trough_voltage)
            voltage_range = max_voltage - min_voltage
            self.max_voltage_edit.setText(f'{max_voltage:.2f} V')
            self.min_voltage_edit.setText(f'{min_voltage:.2f} V')
            self.voltage_range_edit.setText(f'{voltage_range:.2f} V')
            self.devices[self.current_device]['min_max_range'] = {
                'max_voltage': max_voltage,
                'min_voltage': min_voltage,
                'voltage_range': voltage_range
            }
        elif mode == 'clear':  # 清零
            self.max_voltage_edit.setText(f"")
            self.min_voltage_edit.setText(f"")
            self.voltage_range_edit.setText(f"")
            self.devices[self.current_device]['min_max_range'] = {}
            
        # 计算电压相对负载调整率为（满载-空载）/空载*100%
        loaded_mean=self.loaded_mean_voltage_edit.text()
        unloaded_mean=self.unloaded_mean_voltage_edit.text()
        if loaded_mean and unloaded_mean:
            loaded_mean = float(loaded_mean.split(' ')[0])
            unloaded_mean = float(unloaded_mean.split(' ')[0])
            voltage_adjustment_rate = abs(loaded_mean - unloaded_mean) / unloaded_mean * 100
            self.voltage_adjustment_rate_edit.setText(f'{voltage_adjustment_rate:.2f}%')
            self.devices[self.current_device]['carculation_results'] = {
                'voltage_adjustment_rate': voltage_adjustment_rate
        }

        self.saveDevices()  # 保存数据

    #添加设备
    def addDevice(self):
        device_name, ok = QInputDialog.getText(self, '添加设备', '请输入设备名称:')
        if ok and device_name:
            if device_name in self.devices:
                QMessageBox.warning(self, '警告', '设备已存在')
            else:
                self.devices[device_name] = {'unloaded': {}, 'loaded': {}}
                self.device_select.addItem(device_name)
                self.device_select.setCurrentText(device_name)
                self.saveDevices()

    #加载设备数据
    def loadDeviceData(self):
        device_name = self.device_select.currentText()
        if device_name == "选择设备":
            # 清空数据
            self.current_device = None
            self.unloaded_peak_voltage_edit.setText(f"")
            self.unloaded_trough_voltage_edit.setText(f"")
            self.unloaded_rms_voltage_edit.setText(f"")
            self.unloaded_mean_voltage_edit.setText(f"")
            self.unloaded_snr_edit.setText(f"")
            self.unloaded_ripple_freq_edit.setText("")
            self.loaded_peak_voltage_edit.setText(f"")
            self.loaded_trough_voltage_edit.setText(f"")
            self.loaded_rms_voltage_edit.setText(f"")
            self.loaded_mean_voltage_edit.setText(f"")
            self.loaded_snr_edit.setText(f"")
            self.loaded_ripple_freq_edit.setText("")

            self.voltage_adjustment_rate_edit.setText(f"")
            self.min_voltage_edit.setText(f"")
            self.max_voltage_edit.setText(f"")
            self.voltage_range_edit.setText(f"")

        elif device_name in self.devices:
            self.current_device = device_name
            unloaded = self.devices[device_name].get('unloaded', {})
            loaded = self.devices[device_name].get('loaded', {})
            # 读取文件中保存的设备数据
            self.unloaded_peak_voltage_edit.setText(f"{unloaded.get('peak_voltage', ''):.2f} V" if unloaded else "")
            self.unloaded_trough_voltage_edit.setText(f"{unloaded.get('trough_voltage', ''):.2f} V" if unloaded else "")
            self.unloaded_rms_voltage_edit.setText(f"{unloaded.get('rms_voltage', ''):.2f} V" if unloaded else "")
            self.unloaded_mean_voltage_edit.setText(f"{unloaded.get('mean_voltage', ''):.2f} V" if unloaded else "")
            self.unloaded_snr_edit.setText(f"{unloaded.get('snr', ''):.2f} dB" if unloaded else "")
            ripple_frequencies = unloaded.get('ripple_frequencies', [])
            ripple_amplitudes = unloaded.get('ripple_amplitudes', [])
            self.unloaded_ripple_freq_edit.setText(
                '\n'.join([f"freq= {freq:.2f} Hz, 幅值= {amp:.2f} V" for freq, amp in zip(ripple_frequencies, ripple_amplitudes)]))

            self.loaded_peak_voltage_edit.setText(f"{loaded.get('peak_voltage', ''):.2f} V" if loaded else "")
            self.loaded_trough_voltage_edit.setText(f"{loaded.get('trough_voltage', ''):.2f} V" if loaded else "")
            self.loaded_rms_voltage_edit.setText(f"{loaded.get('rms_voltage', ''):.2f} V" if loaded else "")
            self.loaded_mean_voltage_edit.setText(f"{loaded.get('mean_voltage', ''):.2f} V" if loaded else "")
            self.loaded_snr_edit.setText(f"{loaded.get('snr', ''):.2f} dB" if loaded else "")
            ripple_frequencies = loaded.get('ripple_frequencies', [])
            ripple_amplitudes = loaded.get('ripple_amplitudes', [])
            self.loaded_ripple_freq_edit.setText(
                '\n'.join([f"freq= {freq:.2f} Hz, 幅值= {amp:.2f} V" for freq, amp in zip(ripple_frequencies, ripple_amplitudes)]))
            
            min_max_range = self.devices[device_name].get('min_max_range', {})
            self.min_voltage_edit.setText(f"{min_max_range.get('min_voltage', ''):.2f} V" if min_max_range else "")
            self.max_voltage_edit.setText(f"{min_max_range.get('max_voltage', ''):.2f} V" if min_max_range else "")
            self.voltage_range_edit.setText(f"{min_max_range.get('voltage_range', ''):.2f} V" if min_max_range else "")
            
            info = self.devices[device_name].get('carculation_results', {})
            self.voltage_adjustment_rate_edit.setText(f"{info.get('voltage_adjustment_rate', ''):.2f}%" if info else "")

    # 保存文件
    def saveDevices(self):
        with open('devices.json', 'w') as file:
            json.dump(self.devices, file)

    # 加载文件
    def loadDevices(self):
        if os.path.exists('devices.json'):
            with open('devices.json', 'r') as file:
                self.devices = json.load(file)
                self.device_select.addItems(self.devices.keys())

    # 输出数据为csv文件 
    def exportData(self):
        if self.current_device is None:
            QMessageBox.warning(self, '警告', '请先选择一个设备')
            return

        file_name, _ = QFileDialog.getSaveFileName(self, '导出数据', '', 'CSV Files (*.csv)')
        if file_name:
            device_data = self.devices[self.current_device]
            with open(file_name, 'w', newline='') as file:
                writer = csv.writer(file)
                # 写入设备名称
                writer.writerow(['Stable Signal Data'])
                writer.writerow(['Device'])
                writer.writerow([self.current_device])
                # 写入表头
                writer.writerow(['Mode', 'Peak Voltage (V)', 'Trough Voltage (V)', 'RMS Voltage (V)'
                                 , 'Mean Voltage (V)', 'SNR (dB)', 'Ripple Frequencies (Hz)'
                                 , 'Ripple Amplitudes (V)'])
                # 写入空载和满载数据
                unloaded = device_data.get('unloaded', {})
                loaded = device_data.get('loaded', {})
                if unloaded:
                    writer.writerow([
                        'Unloaded',
                        unloaded.get('peak_voltage', ''),
                        unloaded.get('trough_voltage', ''),
                        unloaded.get('rms_voltage', ''),
                        unloaded.get('mean_voltage', ''),
                        unloaded.get('snr', ''),
                        ', '.join([f"{freq:.0f}" for freq in unloaded.get('ripple_frequencies', [])]),
                        ', '.join([f"{amp:.2f}" for amp in unloaded.get('ripple_amplitudes', [])])
                    ])
                if loaded:
                    writer.writerow([
                        'Loaded',
                        loaded.get('peak_voltage', ''),
                        loaded.get('trough_voltage', ''),
                        loaded.get('rms_voltage', ''),
                        loaded.get('mean_voltage', ''),
                        loaded.get('snr', ''),
                        ', '.join([f"{freq:.0f}" for freq in loaded.get('ripple_frequencies', [])]),
                        ', '.join([f"{amp:.2f}" for amp in loaded.get('ripple_amplitudes', [])])
                    ])
                writer.writerow(['Min(v)','Max(v)','Min-Max Voltage Range(v)'])
                min_max_range = device_data.get('min_max_range', {})
                if min_max_range:
                    writer.writerow([
                        min_max_range.get('min_voltage', ''),
                        min_max_range.get('max_voltage', ''),
                        min_max_range.get('voltage_range', '')
                    ])
                writer.writerow(['Voltage Adjustment Rate(%)'])
                info = device_data.get('carculation_results', {})
                if info:
                    writer.writerow([
                        info.get('voltage_adjustment_rate', '')
                    ])

                # 写入波形数据
                writer.writerow(['\n dataset:'])
                writer.writerow(['index','value/V'])
                for idx, val in enumerate(self.data):
                    writer.writerow([idx,val])


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = SignalAnalyzer()
    ex.show()
    sys.exit(app.exec_())