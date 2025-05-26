# 🚗 IoT-Based Smart Parking System

An automated parking management system using Arduino and Python to track vehicle entries/exits, control gates with servo motors, and visualize real-time data via a dashboard.

![System Demo](media/image1.jpeg)  
*(Replace with your project image/video)*

## 🌟 Features
- **Vehicle Detection**: HC-SR04 ultrasonic sensors detect cars at entry/exit.
- **Automated Gates**: SG90 servo motors open/close barriers.
- **Visual Indicators**: Red/green LEDs show gate status.
- **Real-Time Monitoring**: Python dashboard displays:
  - Current parked vehicles (max capacity: 4)
  - Daily entries/exits
  - Historical trends (graphs)
- **Data Logging**: JSON storage for long-term analysis.

## 🛠️ Hardware Components
| Component           | Quantity | Purpose                          |
|---------------------|----------|----------------------------------|
| Arduino Uno         | 1        | Main controller                  |
| HC-SR04 Sensors     | 2        | Vehicle detection               |
| SG90 Servo Motors   | 2        | Gate control                    |
| LEDs (Red/Green)    | 4        | Visual status                   |
| Buzzers             | 2        | Audible alerts                  |

## 📋 Software Requirements
- **Arduino IDE** (Upload `SmartParking.ino`)
- **Python 3.x** (Run `dashboard.py`)
  - Libraries: `pyserial`, `matplotlib`, `tkinter`

## 🔌 Circuit Connections
![Circuit Diagram](media/circuit_diagram.png)  
*(Add your Fritzing/Tinkercad diagram)*

| Arduino Pin | Component        |
|-------------|------------------|
| D2, D3      | Entry Sensor     |
| D5          | Entry Servo      |
| D6, D7      | Entry LEDs       |
| D8          | Entry Buzzer     |
| D9, D10     | Exit Sensor      |
| D11         | Exit Servo       |
| A0, A1      | Exit LEDs        |
| A2          | Exit Buzzer      |

## 🚀 Getting Started
1. **Hardware Setup**:  
   - Wire components as per the circuit diagram.
   - Power Arduino via USB/5V adapter.

2. **Upload Arduino Code**:  
   ```bash
   git clone https://github.com/Umar-Jahangir/IOT-Base-Smart-Parking-System.git
   cd IOT-Base-Smart-Parking-System/Arduino
   # Open SmartParking.ino in Arduino IDE and upload


cd ../Python
pip install -r requirements.txt
python dashboard.py


File Structure:-
├── Arduino/
│   └── SmartParking.ino       # Main controller code
├── Python/
│   ├── dashboard.py           # Monitoring GUI
│   └── parking_data.json      # Historical logs
├── media/                     # Images/diagrams
└── README.md



![image](https://github.com/user-attachments/assets/cdae8a02-2363-46de-8459-97a1e1c8afc3)



![image](https://github.com/user-attachments/assets/fe9202ec-169d-4a59-ba00-7db06b51813a)




![WhatsApp Image 2025-05-26 at 10 58 10_192125b5](https://github.com/user-attachments/assets/6a1fa298-b53a-493a-aded-b3eb207e3a6b)



![WhatsApp Image 2025-05-26 at 10 52 09_494e1321](https://github.com/user-attachments/assets/91f9d575-288b-4d88-9a16-16eb8f12c5d4)

