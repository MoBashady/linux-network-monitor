import sys
import json

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QTableWidget, QTableWidgetItem, QLineEdit,
    QTabWidget, QTextEdit, QComboBox
)
from PyQt5.QtCore import QTimer
import pyqtgraph as pg


class NetworkMonitorGUI(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Linux Network Monitor GUI")
        self.setGeometry(150, 80, 1100, 700)
        self.data_file = "network_log.jsonl"
        self.last_position = 0

        self.counter = 0
        self.time_data = []
        self.upload_data = []
        self.download_data = []
        self.total_upload = 0
        self.total_download = 0
        self.total_packets = 0
        self.total_bytes = 0
        self.tcp_packets = 0
        self.udp_packets = 0
        self.other_packets = 0

        self.init_ui()

        self.timer = QTimer()
        self.timer.timeout.connect(self.packet_input)

    def init_ui(self):
        main_widget = QWidget()
        main_layout = QVBoxLayout()

        title = QLabel("Linux Network Monitoring & Control System")
        title.setStyleSheet("font-size: 24px; font-weight: bold;")
        main_layout.addWidget(title)

        nav_label = QLabel("Navigation: Dashboard | Processes | Raw JSON")
        nav_label.setStyleSheet("font-size: 14px; color: gray;")
        main_layout.addWidget(nav_label)

        controls_layout = QHBoxLayout()

        self.start_button = QPushButton("Start Monitoring")
        self.pause_button = QPushButton("Pause Monitoring")
        self.stop_button = QPushButton("Stop Monitoring")
        self.clear_button = QPushButton("Clear Data")

        self.start_button.clicked.connect(self.start_monitoring)
        self.pause_button.clicked.connect(self.pause_monitoring)
        self.stop_button.clicked.connect(self.stop_monitoring)
        self.clear_button.clicked.connect(self.clear_data)

        controls_layout.addWidget(self.start_button)
        controls_layout.addWidget(self.pause_button)
        controls_layout.addWidget(self.stop_button)
        controls_layout.addWidget(self.clear_button)

        main_layout.addLayout(controls_layout)

        self.tabs = QTabWidget()

        self.dashboard_tab = QWidget()
        self.processes_tab = QWidget()
        self.raw_json_tab = QWidget()

        self.tabs.addTab(self.dashboard_tab, "Dashboard")
        self.tabs.addTab(self.processes_tab, "Processes")
        self.tabs.addTab(self.raw_json_tab, "Raw JSON")

        self.create_dashboard_tab()
        self.create_processes_tab()
        self.create_raw_json_tab()

        main_layout.addWidget(self.tabs)

        main_widget.setLayout(main_layout)
        self.setCentralWidget(main_widget)

    def create_dashboard_tab(self):
        layout = QVBoxLayout()

        stats_layout = QHBoxLayout()

        self.status_label = QLabel("Status: Stopped")
        self.upload_label = QLabel("Total Upload: 0 KB")
        self.download_label = QLabel("Total Download: 0 KB")

        for label in [self.status_label, self.upload_label, self.download_label]:
            label.setStyleSheet("font-size: 16px; font-weight: bold;")

        stats_layout.addWidget(self.status_label)
        stats_layout.addWidget(self.upload_label)
        stats_layout.addWidget(self.download_label)

        layout.addLayout(stats_layout)

        self.total_packets_label = QLabel("Total Packets: 0")
        self.total_bytes_label = QLabel("Total Bytes: 0")
        self.avg_packet_label = QLabel("Average Packet Size: 0 B")
        self.tcp_label = QLabel("TCP: 0 (0%)")
        self.udp_label = QLabel("UDP: 0 (0%)")
        self.other_label = QLabel("Other: 0 (0%)")

        for label in [
            self.total_packets_label, self.total_bytes_label,
            self.avg_packet_label, self.tcp_label,
            self.udp_label, self.other_label
        ]:
            label.setStyleSheet("font-size: 14px;")
            layout.addWidget(label)

        self.graph = pg.PlotWidget()
        self.graph.setTitle("Real-Time Network Traffic")
        self.graph.setLabel("left", "Traffic KB/s")
        self.graph.setLabel("bottom", "Time")
        self.graph.addLegend()

        self.upload_curve = self.graph.plot([], [], name="Upload")
        self.download_curve = self.graph.plot([], [], name="Download")

        layout.addWidget(self.graph)
        self.dashboard_tab.setLayout(layout)

    def create_processes_tab(self):
        layout = QVBoxLayout()

        filter_layout = QHBoxLayout()

        self.filter_type = QComboBox()
        self.filter_type.addItems(["All", "Process", "User", "Protocol"])

        self.filter_input = QLineEdit()
        self.filter_input.setPlaceholderText("Search/filter table")

        filter_layout.addWidget(QLabel("Filter by:"))
        filter_layout.addWidget(self.filter_type)
        filter_layout.addWidget(self.filter_input)

        layout.addLayout(filter_layout)

        self.table = QTableWidget()
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels([
            "Time", "Process", "PID", "User",
            "Sent KB", "Received KB", "Protocol", "Remote IP"
        ])
        self.table.setSortingEnabled(True)

        layout.addWidget(self.table)
        self.processes_tab.setLayout(layout)

    def create_raw_json_tab(self):
        layout = QVBoxLayout()

        self.raw_json_box = QTextEdit()
        self.raw_json_box.setReadOnly(True)
        self.raw_json_box.setPlaceholderText("Live JSON input will appear here...")

        layout.addWidget(self.raw_json_box)
        self.raw_json_tab.setLayout(layout)

    def start_monitoring(self):
        self.timer.start(200)
        self.status_label.setText("Status: Running")

    def pause_monitoring(self):
        self.timer.stop()
        self.status_label.setText("Status: Paused")

    def stop_monitoring(self):
        self.timer.stop()
        self.status_label.setText("Status: Stopped")

    def clear_data(self):
        self.counter = 0
        self.time_data.clear()
        self.upload_data.clear()
        self.download_data.clear()
        self.total_upload = 0
        self.total_download = 0
        self.total_packets = 0
        self.total_bytes = 0
        self.tcp_packets = 0
        self.udp_packets = 0
        self.other_packets = 0
        self.last_position = 0

        self.upload_curve.setData([], [])
        self.download_curve.setData([], [])

        self.table.setRowCount(0)
        self.raw_json_box.clear()

        self.upload_label.setText("Total Upload: 0 KB")
        self.download_label.setText("Total Download: 0 KB")
        self.status_label.setText("Status: Stopped")
        self.total_packets_label.setText("Total Packets: 0")
        self.total_bytes_label.setText("Total Bytes: 0")
        self.avg_packet_label.setText("Average Packet Size: 0 B")
        self.tcp_label.setText("TCP: 0 (0%)")
        self.udp_label.setText("UDP: 0 (0%)")
        self.other_label.setText("Other: 0 (0%)")

        self.timer.stop()
        open(self.data_file, "w").close()

    def packet_input(self):
        try:
            with open(self.data_file, "r") as f:
                f.seek(self.last_position)
                lines = f.readlines()

                if not lines:
                    self.last_position = f.tell()
                    return

                max_lines = 20
                to_process = lines[:max_lines]
                remaining = lines[max_lines:]

                for line in to_process:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        data = json.loads(line)
                        self.update_gui(data)
                    except json.JSONDecodeError:
                        continue

                if remaining:
                    unread = "".join(remaining)
                    self.last_position = f.tell() - len(unread.encode())
                else:
                    self.last_position = f.tell()

        except FileNotFoundError:
            pass

    def passes_filter(self, data):
        filter_text = self.filter_input.text().lower().strip()
        filter_type = self.filter_type.currentText()

        if not filter_text:
            return True

        if filter_type == "All":
            return (
                filter_text in data["process"].lower()
                or filter_text in data["user"].lower()
                or filter_text in data["protocol"].lower()
            )

        if filter_type == "Process":
            return filter_text in data["process"].lower()

        if filter_type == "User":
            return filter_text in data["user"].lower()

        if filter_type == "Protocol":
            return filter_text in data["protocol"].lower()

        return True

    def update_gui(self, data):
        sent_kb = data["bytes_sent"] / 1024
        received_kb = data["bytes_received"] / 1024

        packet_bytes = data["bytes_sent"] + data["bytes_received"]

        self.total_packets += 1
        self.total_bytes += packet_bytes

        if data["protocol"] == "TCP":
            self.tcp_packets += 1
        elif data["protocol"] == "UDP":
            self.udp_packets += 1
        else:
            self.other_packets += 1

        avg_packet = self.total_bytes / self.total_packets if self.total_packets else 0
        tcp_percent = (self.tcp_packets * 100 / self.total_packets) if self.total_packets else 0
        udp_percent = (self.udp_packets * 100 / self.total_packets) if self.total_packets else 0
        other_percent = (self.other_packets * 100 / self.total_packets) if self.total_packets else 0

        self.total_packets_label.setText(f"Total Packets: {self.total_packets}")
        self.total_bytes_label.setText(f"Total Bytes: {self.total_bytes}")
        self.avg_packet_label.setText(f"Average Packet Size: {avg_packet:.2f} B")
        self.tcp_label.setText(f"TCP: {self.tcp_packets} ({tcp_percent:.1f}%)")
        self.udp_label.setText(f"UDP: {self.udp_packets} ({udp_percent:.1f}%)")
        self.other_label.setText(f"Other: {self.other_packets} ({other_percent:.1f}%)")

        if self.upload_data:
            sent_kb = (self.upload_data[-1] + sent_kb) / 2
        if self.download_data:
            received_kb = (self.download_data[-1] + received_kb) / 2

        self.counter += 1
        self.time_data.append(self.counter)
        self.upload_data.append(sent_kb)
        self.download_data.append(received_kb)

        if len(self.time_data) > 30:
            self.time_data.pop(0)
            self.upload_data.pop(0)
            self.download_data.pop(0)

        self.upload_curve.setData(self.time_data, self.upload_data)
        self.download_curve.setData(self.time_data, self.download_data)

        self.total_upload += sent_kb
        self.total_download += received_kb

        self.upload_label.setText(f"Total Upload: {self.total_upload:.2f} KB")
        self.download_label.setText(f"Total Download: {self.total_download:.2f} KB")

        self.raw_json_box.append(json.dumps(data))

        if not self.passes_filter(data):
            return

        self.table.setSortingEnabled(False)

        if self.table.rowCount() >= 100:
            self.table.removeRow(0)

        row = self.table.rowCount()
        self.table.insertRow(row)

        values = [
            data["timestamp"],
            data["process"],
            str(data["pid"]),
            data["user"],
            f"{sent_kb:.2f}",
            f"{received_kb:.2f}",
            data["protocol"],
            data["remote_ip"]
        ]

        for col, value in enumerate(values):
            self.table.setItem(row, col, QTableWidgetItem(value))

        self.table.setSortingEnabled(True)
        self.table.scrollToBottom()
      

    from PyQt5.QtWidgets import (
        QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
        QPushButton, QLabel, QTableWidget, QTableWidgetItem, QLineEdit,
        QTabWidget, QTextEdit, QComboBox
    )


class NetworkMonitorGUI(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Linux Network Monitor GUI")
        self.setGeometry(150, 80, 1100, 700)
        self.data_file = "network_log.jsonl"
        self.last_position = 0

        self.counter = 0
        self.time_data = []
        self.upload_data = []
        self.download_data = []
        self.total_upload = 0
        self.total_download = 0
        self.total_packets = 0
        self.total_bytes = 0
        self.tcp_packets = 0
        self.udp_packets = 0
        self.other_packets = 0

        self.init_ui()

        self.timer = QTimer()
        self.timer.timeout.connect(self.packet_input)

    def init_ui(self):
        main_widget = QWidget()
        main_layout = QVBoxLayout()

        title = QLabel("Linux Network Monitoring & Control System")
        title.setStyleSheet("font-size: 24px; font-weight: bold;")
        main_layout.addWidget(title)

        nav_label = QLabel("Navigation: Dashboard | Processes | Raw JSON")
        nav_label.setStyleSheet("font-size: 14px; color: gray;")
        main_layout.addWidget(nav_label)

        controls_layout = QHBoxLayout()

        self.start_button = QPushButton("Start Monitoring")
        self.pause_button = QPushButton("Pause Monitoring")
        self.stop_button = QPushButton("Stop Monitoring")
        self.clear_button = QPushButton("Clear Data")

        self.start_button.clicked.connect(self.start_monitoring)
        self.pause_button.clicked.connect(self.pause_monitoring)
        self.stop_button.clicked.connect(self.stop_monitoring)
        self.clear_button.clicked.connect(self.clear_data)

        controls_layout.addWidget(self.start_button)
        controls_layout.addWidget(self.pause_button)
        controls_layout.addWidget(self.stop_button)
        controls_layout.addWidget(self.clear_button)

        main_layout.addLayout(controls_layout)

        self.tabs = QTabWidget()

        self.dashboard_tab = QWidget()
        self.processes_tab = QWidget()
        self.raw_json_tab = QWidget()

        self.tabs.addTab(self.dashboard_tab, "Dashboard")
        self.tabs.addTab(self.processes_tab, "Processes")
        self.tabs.addTab(self.raw_json_tab, "Raw JSON")

        self.create_dashboard_tab()
        self.create_processes_tab()
        self.create_raw_json_tab()

        main_layout.addWidget(self.tabs)

        main_widget.setLayout(main_layout)
        self.setCentralWidget(main_widget)

    def create_dashboard_tab(self):
        layout = QVBoxLayout()

        stats_layout = QHBoxLayout()

        self.status_label = QLabel("Status: Stopped")
        self.upload_label = QLabel("Total Upload: 0 KB")
        self.download_label = QLabel("Total Download: 0 KB")

        for label in [self.status_label, self.upload_label, self.download_label]:
            label.setStyleSheet("font-size: 16px; font-weight: bold;")

        stats_layout.addWidget(self.status_label)
        stats_layout.addWidget(self.upload_label)
        stats_layout.addWidget(self.download_label)

        layout.addLayout(stats_layout)

        self.total_packets_label = QLabel("Total Packets: 0")
        self.total_bytes_label = QLabel("Total Bytes: 0")
        self.avg_packet_label = QLabel("Average Packet Size: 0 B")
        self.tcp_label = QLabel("TCP: 0 (0%)")
        self.udp_label = QLabel("UDP: 0 (0%)")
        self.other_label = QLabel("Other: 0 (0%)")

        for label in [
            self.total_packets_label, self.total_bytes_label,
            self.avg_packet_label, self.tcp_label,
            self.udp_label, self.other_label
        ]:
            label.setStyleSheet("font-size: 14px;")
            layout.addWidget(label)

        self.graph = pg.PlotWidget()
        self.graph.setTitle("Real-Time Network Traffic")
        self.graph.setLabel("left", "Traffic KB/s")
        self.graph.setLabel("bottom", "Time")
        self.graph.addLegend()

        self.upload_curve = self.graph.plot([], [], name="Upload")
        self.download_curve = self.graph.plot([], [], name="Download")

        layout.addWidget(self.graph)
        self.dashboard_tab.setLayout(layout)

    def create_processes_tab(self):
        layout = QVBoxLayout()

        filter_layout = QHBoxLayout()

        self.filter_type = QComboBox()
        self.filter_type.addItems(["All", "Process", "User", "Protocol"])

        self.filter_input = QLineEdit()
        self.filter_input.setPlaceholderText("Search/filter table")

        filter_layout.addWidget(QLabel("Filter by:"))
        filter_layout.addWidget(self.filter_type)
        filter_layout.addWidget(self.filter_input)

        layout.addLayout(filter_layout)

        self.table = QTableWidget()
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels([
            "Time", "Process", "PID", "User",
            "Sent KB", "Received KB", "Protocol", "Remote IP"
        ])
        self.table.setSortingEnabled(True)

        layout.addWidget(self.table)
        self.processes_tab.setLayout(layout)

    def create_raw_json_tab(self):
        layout = QVBoxLayout()

        self.raw_json_box = QTextEdit()
        self.raw_json_box.setReadOnly(True)
        self.raw_json_box.setPlaceholderText("Live JSON input will appear here...")

        layout.addWidget(self.raw_json_box)
        self.raw_json_tab.setLayout(layout)

    def start_monitoring(self):
        self.timer.start(50)
        self.status_label.setText("Status: Running")

    def pause_monitoring(self):
        self.timer.stop()
        self.status_label.setText("Status: Paused")

    def stop_monitoring(self):
        self.timer.stop()
        self.status_label.setText("Status: Stopped")

    def clear_data(self):
        self.counter = 0
        self.time_data.clear()
        self.upload_data.clear()
        self.download_data.clear()
        self.total_upload = 0
        self.total_download = 0
        self.total_packets = 0
        self.total_bytes = 0
        self.tcp_packets = 0
        self.udp_packets = 0
        self.other_packets = 0
        self.last_position = 0

        self.upload_curve.setData([], [])
        self.download_curve.setData([], [])

        self.table.setRowCount(0)
        self.raw_json_box.clear()

        self.upload_label.setText("Total Upload: 0 KB")
        self.download_label.setText("Total Download: 0 KB")
        self.status_label.setText("Status: Stopped")
        self.total_packets_label.setText("Total Packets: 0")
        self.total_bytes_label.setText("Total Bytes: 0")
        self.avg_packet_label.setText("Average Packet Size: 0 B")
        self.tcp_label.setText("TCP: 0 (0%)")
        self.udp_label.setText("UDP: 0 (0%)")
        self.other_label.setText("Other: 0 (0%)")

        self.timer.stop()
        open(self.data_file, "w").close()

    def packet_input(self):
        try:
            with open(self.data_file, "r") as f:
                f.seek(self.last_position)
                lines = f.readlines()
                self.last_position = f.tell()

            if not lines:
                return

            max_lines = 20
            for line in lines[:max_lines]:
                line = line.strip()
                if not line:
                    continue
                try:
                    data = json.loads(line)
                    self.update_gui(data)
                except json.JSONDecodeError:
                    continue

        except FileNotFoundError:
            pass

    def passes_filter(self, data):
        filter_text = self.filter_input.text().lower().strip()
        filter_type = self.filter_type.currentText()

        if not filter_text:
            return True

        if filter_type == "All":
            return (
                filter_text in data["process"].lower()
                or filter_text in data["user"].lower()
                or filter_text in data["protocol"].lower()
            )

        if filter_type == "Process":
            return filter_text in data["process"].lower()

        if filter_type == "User":
            return filter_text in data["user"].lower()

        if filter_type == "Protocol":
            return filter_text in data["protocol"].lower()

        return True

    def update_gui(self, data):
        sent_kb = data["bytes_sent"] / 1024
        received_kb = data["bytes_received"] / 1024

        packet_bytes = data["bytes_sent"] + data["bytes_received"]

        self.total_packets += 1
        self.total_bytes += packet_bytes

        if data["protocol"] == "TCP":
            self.tcp_packets += 1
        elif data["protocol"] == "UDP":
            self.udp_packets += 1
        else:
            self.other_packets += 1

        avg_packet = self.total_bytes / self.total_packets if self.total_packets else 0
        tcp_percent = (self.tcp_packets * 100 / self.total_packets) if self.total_packets else 0
        udp_percent = (self.udp_packets * 100 / self.total_packets) if self.total_packets else 0
        other_percent = (self.other_packets * 100 / self.total_packets) if self.total_packets else 0

        self.total_packets_label.setText(f"Total Packets: {self.total_packets}")
        self.total_bytes_label.setText(f"Total Bytes: {self.total_bytes}")
        self.avg_packet_label.setText(f"Average Packet Size: {avg_packet:.2f} B")
        self.tcp_label.setText(f"TCP: {self.tcp_packets} ({tcp_percent:.1f}%)")
        self.udp_label.setText(f"UDP: {self.udp_packets} ({udp_percent:.1f}%)")
        self.other_label.setText(f"Other: {self.other_packets} ({other_percent:.1f}%)")

        if self.upload_data:
            sent_kb = (self.upload_data[-1] + sent_kb) / 2
        if self.download_data:
            received_kb = (self.download_data[-1] + received_kb) / 2

        self.counter += 1
        self.time_data.append(self.counter)
        self.upload_data.append(sent_kb)
        self.download_data.append(received_kb)

        if len(self.time_data) > 30:
            self.time_data.pop(0)
            self.upload_data.pop(0)
            self.download_data.pop(0)

        self.upload_curve.setData(self.time_data, self.upload_data)
        self.download_curve.setData(self.time_data, self.download_data)

        self.total_upload += sent_kb
        self.total_download += received_kb

        self.upload_label.setText(f"Total Upload: {self.total_upload:.2f} KB")
        self.download_label.setText(f"Total Download: {self.total_download:.2f} KB")

        self.raw_json_box.append(json.dumps(data))

        if not self.passes_filter(data):
            return

        self.table.setSortingEnabled(False)

        row = self.table.rowCount()
        if self.table.rowCount() >= 100:
            self.table.removeRow(0)

        row = self.table.rowCount()
        self.table.insertRow(row)

        values = [
            data["timestamp"],
            data["process"],
            str(data["pid"]),
            data["user"],
            f"{sent_kb:.2f}",
            f"{received_kb:.2f}",
            data["protocol"],
            data["remote_ip"]
        ]

        for col, value in enumerate(values):
            self.table.setItem(row, col, QTableWidgetItem(value))

        self.table.setSortingEnabled(True)
        self.table.scrollToBottom()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = NetworkMonitorGUI()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = NetworkMonitorGUI()
    window.show()
    sys.exit(app.exec_())