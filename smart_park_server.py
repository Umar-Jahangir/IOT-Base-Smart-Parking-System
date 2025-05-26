import serial
import time
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from datetime import datetime, timedelta
import json
import os
from collections import defaultdict, deque
import threading
import tkinter as tk
from tkinter import ttk, messagebox

class SmartParkingMonitor:
    def __init__(self, port='COM6', baudrate=9600):
        self.port = port
        self.baudrate = baudrate
        self.serial_connection = None
        self.is_connected = False
        
        # Parking data
        self.current_cars = 0
        self.total_entered_today = 0
        self.total_exited_today = 0
        self.max_capacity = 4
        
        # Historical data storage
        self.daily_data = defaultdict(lambda: {'entered': 0, 'exited': 0, 'peak_occupancy': 0})
        self.hourly_data = defaultdict(lambda: {'entered': 0, 'exited': 0, 'occupancy': 0})
        self.recent_activity = deque(maxlen=50)  # Last 50 activities
        
        # Data file for persistence
        self.data_file = 'parking_data.json'
        self.load_historical_data()
        
        # GUI setup
        self.setup_gui()
        
        # Start monitoring in separate thread
        self.monitoring_thread = threading.Thread(target=self.monitor_arduino, daemon=True)
        self.monitoring_active = True
        
    def setup_gui(self):
        """Create the GUI dashboard"""
        self.root = tk.Tk()
        self.root.title("Smart Parking System Dashboard")
        self.root.geometry("800x600")
        self.root.configure(bg='#2c3e50')
        
        # Main title
        title_label = tk.Label(self.root, text="🅿️ SMART PARKING DASHBOARD", 
                              font=('Arial', 20, 'bold'), 
                              fg='white', bg='#2c3e50')
        title_label.pack(pady=10)
        
        # Connection status frame
        conn_frame = tk.Frame(self.root, bg='#2c3e50')
        conn_frame.pack(pady=5)
        
        self.conn_status_label = tk.Label(conn_frame, text="⚫ Disconnected", 
                                         font=('Arial', 12), 
                                         fg='red', bg='#2c3e50')
        self.conn_status_label.pack(side=tk.LEFT)
        
        # Connect button
        self.connect_btn = tk.Button(conn_frame, text="Connect", 
                                    command=self.toggle_connection,
                                    bg='#3498db', fg='white', 
                                    font=('Arial', 10))
        self.connect_btn.pack(side=tk.LEFT, padx=10)
        
        # Current status frame
        status_frame = tk.LabelFrame(self.root, text="Current Status", 
                                   font=('Arial', 14, 'bold'),
                                   fg='white', bg='#34495e')
        status_frame.pack(pady=10, padx=20, fill='x')
        
        # Current cars display
        self.current_cars_label = tk.Label(status_frame, 
                                          text=f"Cars Currently Parked: {self.current_cars}/{self.max_capacity}",
                                          font=('Arial', 16, 'bold'),
                                          fg='#e74c3c', bg='#34495e')
        self.current_cars_label.pack(pady=10)
        
        # Progress bar for occupancy
        self.occupancy_progress = ttk.Progressbar(status_frame, 
                                                 maximum=self.max_capacity,
                                                 value=self.current_cars,
                                                 length=300)
        self.occupancy_progress.pack(pady=5)
        
        # Today's statistics frame
        today_frame = tk.LabelFrame(self.root, text="Today's Statistics", 
                                  font=('Arial', 14, 'bold'),
                                  fg='white', bg='#34495e')
        today_frame.pack(pady=10, padx=20, fill='x')
        
        stats_inner_frame = tk.Frame(today_frame, bg='#34495e')
        stats_inner_frame.pack(pady=10)
        
        self.entered_label = tk.Label(stats_inner_frame, 
                                     text=f"Cars Entered: {self.total_entered_today}",
                                     font=('Arial', 12),
                                     fg='#27ae60', bg='#34495e')
        self.entered_label.grid(row=0, column=0, padx=20)
        
        self.exited_label = tk.Label(stats_inner_frame, 
                                    text=f"Cars Exited: {self.total_exited_today}",
                                    font=('Arial', 12),
                                    fg='#f39c12', bg='#34495e')
        self.exited_label.grid(row=0, column=1, padx=20)
        
        # Recent activity frame
        activity_frame = tk.LabelFrame(self.root, text="Recent Activity", 
                                     font=('Arial', 14, 'bold'),
                                     fg='white', bg='#34495e')
        activity_frame.pack(pady=10, padx=20, fill='both', expand=True)
        
        # Activity listbox with scrollbar
        listbox_frame = tk.Frame(activity_frame, bg='#34495e')
        listbox_frame.pack(fill='both', expand=True, pady=10)
        
        self.activity_listbox = tk.Listbox(listbox_frame, 
                                          font=('Arial', 10),
                                          bg='#2c3e50', fg='white',
                                          selectbackground='#3498db')
        
        scrollbar = tk.Scrollbar(listbox_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.activity_listbox.pack(side=tk.LEFT, fill='both', expand=True)
        
        self.activity_listbox.config(yscrollcommand=scrollbar.set)
        scrollbar.config(command=self.activity_listbox.yview)
        
        # Control buttons frame
        button_frame = tk.Frame(self.root, bg='#2c3e50')
        button_frame.pack(pady=10)
        
        tk.Button(button_frame, text="📊 Show Daily Graph", 
                 command=self.show_daily_graph,
                 bg='#9b59b6', fg='white', 
                 font=('Arial', 10)).pack(side=tk.LEFT, padx=5)
        
        tk.Button(button_frame, text="📈 Show Hourly Graph", 
                 command=self.show_hourly_graph,
                 bg='#e67e22', fg='white', 
                 font=('Arial', 10)).pack(side=tk.LEFT, padx=5)
        
        tk.Button(button_frame, text="💾 Save Data", 
                 command=self.save_data_manually,
                 bg='#16a085', fg='white', 
                 font=('Arial', 10)).pack(side=tk.LEFT, padx=5)
        
        tk.Button(button_frame, text="🗑️ Clear Today", 
                 command=self.clear_today_data,
                 bg='#e74c3c', fg='white', 
                 font=('Arial', 10)).pack(side=tk.LEFT, padx=5)
    
    def toggle_connection(self):
        """Toggle Arduino connection"""
        if not self.is_connected:
            self.connect_to_arduino()
        else:
            self.disconnect_arduino()
    
    def connect_to_arduino(self):
        """Establish connection with Arduino"""
        try:
            self.serial_connection = serial.Serial(self.port, self.baudrate, timeout=1)
            time.sleep(2)  # Wait for Arduino to reset
            self.is_connected = True
            self.conn_status_label.config(text="🟢 Connected", fg='green')
            self.connect_btn.config(text="Disconnect")
            
            # Start monitoring
            if not self.monitoring_thread.is_alive():
                self.monitoring_thread = threading.Thread(target=self.monitor_arduino, daemon=True)
                self.monitoring_thread.start()
            
            self.add_activity("✅ Connected to Arduino")
            print("Connected to Arduino successfully!")
            
        except Exception as e:
            messagebox.showerror("Connection Error", f"Failed to connect: {str(e)}")
            print(f"Connection failed: {e}")
    
    def disconnect_arduino(self):
        """Disconnect from Arduino"""
        self.monitoring_active = False
        if self.serial_connection:
            self.serial_connection.close()
        self.is_connected = False
        self.conn_status_label.config(text="⚫ Disconnected", fg='red')
        self.connect_btn.config(text="Connect")
        self.add_activity("❌ Disconnected from Arduino")
    
    def monitor_arduino(self):
        """Monitor Arduino data in separate thread"""
        while self.monitoring_active and self.is_connected:
            try:
                if self.serial_connection and self.serial_connection.in_waiting > 0:
                    line = self.serial_connection.readline().decode('utf-8').strip()
                    self.process_arduino_data(line)
                time.sleep(0.1)
            except Exception as e:
                print(f"Monitoring error: {e}")
                self.root.after(0, self.disconnect_arduino)
                break
    
    def process_arduino_data(self, data):
        """Process incoming Arduino data"""
        if data.startswith("PARKING_DATA:"):
            # Parse structured data: PARKING_DATA:ENTERED=5,CURRENT=2,EXITED=3,CAPACITY=4
            try:
                data_part = data.replace("PARKING_DATA:", "")
                params = {}
                for param in data_part.split(","):
                    key, value = param.split("=")
                    params[key] = int(value)
                
                # Update counters
                old_current = self.current_cars
                self.current_cars = params.get("CURRENT", 0)
                self.total_entered_today = params.get("ENTERED", 0)
                self.total_exited_today = params.get("EXITED", 0)
                self.max_capacity = params.get("CAPACITY", 4)
                
                # Log significant changes
                if old_current != self.current_cars:
                    if self.current_cars > old_current:
                        self.add_activity(f"🚗 Car entered - Now: {self.current_cars}/{self.max_capacity}")
                    else:
                        self.add_activity(f"🚙 Car exited - Now: {self.current_cars}/{self.max_capacity}")
                
                # Update historical data
                self.update_historical_data()
                
                # Update GUI
                self.root.after(0, self.update_gui)
                
            except Exception as e:
                print(f"Data parsing error: {e}")
        
        elif data.startswith("STATUS:"):
            # Handle status messages
            self.add_activity(f"📊 {data}")
        
        elif "ENTRY GATE ACTIVATING" in data or "EXIT GATE ACTIVATING" in data:
            self.add_activity(f"🚨 {data}")
    
    def update_historical_data(self):
        """Update historical data records"""
        today = datetime.now().strftime("%Y-%m-%d")
        current_hour = datetime.now().strftime("%Y-%m-%d %H:00")
        
        # Update daily data
        self.daily_data[today]['entered'] = self.total_entered_today
        self.daily_data[today]['exited'] = self.total_exited_today
        self.daily_data[today]['peak_occupancy'] = max(
            self.daily_data[today]['peak_occupancy'], 
            self.current_cars
        )
        
        # Update hourly data
        self.hourly_data[current_hour]['occupancy'] = self.current_cars
        
        # Auto-save data every 10 updates
        if self.total_entered_today % 10 == 0:
            self.save_historical_data()
    
    def update_gui(self):
        """Update GUI elements with current data"""
        # Update current status
        self.current_cars_label.config(
            text=f"Cars Currently Parked: {self.current_cars}/{self.max_capacity}"
        )
        
        # Update progress bar
        self.occupancy_progress.config(value=self.current_cars, maximum=self.max_capacity)
        
        # Update today's statistics
        self.entered_label.config(text=f"Cars Entered: {self.total_entered_today}")
        self.exited_label.config(text=f"Cars Exited: {self.total_exited_today}")
        
        # Color coding based on occupancy
        occupancy_ratio = self.current_cars / self.max_capacity
        if occupancy_ratio >= 1.0:
            color = '#e74c3c'  # Red - Full
        elif occupancy_ratio >= 0.75:
            color = '#f39c12'  # Orange - Nearly full
        else:
            color = '#27ae60'  # Green - Available
        
        self.current_cars_label.config(fg=color)
    
    def add_activity(self, message):
        """Add activity to the recent activity list"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        activity = f"[{timestamp}] {message}"
        self.recent_activity.append(activity)
        
        # Update GUI listbox
        self.root.after(0, self.update_activity_listbox)
    
    def update_activity_listbox(self):
        """Update the activity listbox"""
        self.activity_listbox.delete(0, tk.END)
        for activity in reversed(list(self.recent_activity)):
            self.activity_listbox.insert(0, activity)
    
    def show_daily_graph(self):
        """Show daily entry/exit graph"""
        if not self.daily_data:
            messagebox.showinfo("No Data", "No daily data available to display")
            return
        
        dates = sorted(self.daily_data.keys())
        entries = [self.daily_data[date]['entered'] for date in dates]
        exits = [self.daily_data[date]['exited'] for date in dates]
        peak_occupancy = [self.daily_data[date]['peak_occupancy'] for date in dates]
        
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8))
        
        # Entry/Exit graph
        ax1.bar([d + " (In)" for d in dates], entries, label='Cars Entered', 
               color='#27ae60', alpha=0.7, width=0.4)
        ax1.bar([d + " (Out)" for d in dates], exits, label='Cars Exited', 
               color='#e74c3c', alpha=0.7, width=0.4)
        ax1.set_title('Daily Car Entry/Exit Statistics', fontsize=14, fontweight='bold')
        ax1.set_ylabel('Number of Cars')
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        
        # Peak occupancy graph
        ax2.plot(dates, peak_occupancy, marker='o', linewidth=2, 
                color='#3498db', label='Peak Occupancy')
        ax2.axhline(y=self.max_capacity, color='red', linestyle='--', 
                   label=f'Max Capacity ({self.max_capacity})')
        ax2.set_title('Daily Peak Occupancy', fontsize=14, fontweight='bold')
        ax2.set_ylabel('Number of Cars')
        ax2.set_xlabel('Date')
        ax2.legend()
        ax2.grid(True, alpha=0.3)
        
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.show()
    
    def show_hourly_graph(self):
        """Show hourly occupancy graph for today"""
        today = datetime.now().strftime("%Y-%m-%d")
        hourly_today = {k: v for k, v in self.hourly_data.items() if k.startswith(today)}
        
        if not hourly_today:
            messagebox.showinfo("No Data", "No hourly data available for today")
            return
        
        hours = sorted(hourly_today.keys())
        occupancy = [hourly_today[hour]['occupancy'] for hour in hours]
        hour_labels = [datetime.strptime(h, "%Y-%m-%d %H:%M").strftime("%H:%M") for h in hours]
        
        plt.figure(figsize=(12, 6))
        plt.plot(hour_labels, occupancy, marker='o', linewidth=2, markersize=8, 
                color='#9b59b6', label='Current Occupancy')
        plt.axhline(y=self.max_capacity, color='red', linestyle='--', 
                   label=f'Max Capacity ({self.max_capacity})')
        plt.title(f'Hourly Parking Occupancy - {today}', fontsize=14, fontweight='bold')
        plt.xlabel('Time (Hour)')
        plt.ylabel('Number of Cars')
        plt.legend()
        plt.grid(True, alpha=0.3)
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.show()
    
    def save_historical_data(self):
        """Save historical data to file"""
        data = {
            'daily_data': dict(self.daily_data),
            'hourly_data': dict(self.hourly_data),
            'last_updated': datetime.now().isoformat()
        }
        
        try:
            with open(self.data_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"Error saving data: {e}")
    
    def load_historical_data(self):
        """Load historical data from file"""
        try:
            if os.path.exists(self.data_file):
                with open(self.data_file, 'r') as f:
                    data = json.load(f)
                    self.daily_data = defaultdict(lambda: {'entered': 0, 'exited': 0, 'peak_occupancy': 0})
                    self.daily_data.update(data.get('daily_data', {}))
                    self.hourly_data = defaultdict(lambda: {'entered': 0, 'exited': 0, 'occupancy': 0})
                    self.hourly_data.update(data.get('hourly_data', {}))
        except Exception as e:
            print(f"Error loading data: {e}")
    
    def save_data_manually(self):
        """Manually save data"""
        self.save_historical_data()
        messagebox.showinfo("Data Saved", "Parking data saved successfully!")
    
    def clear_today_data(self):
        """Clear today's data after confirmation"""
        if messagebox.askyesno("Clear Data", "Are you sure you want to clear today's data?"):
            self.current_cars = 0
            self.total_entered_today = 0
            self.total_exited_today = 0
            self.update_gui()
            self.add_activity("🗑️ Today's data cleared")
    
    def run(self):
        """Start the monitoring system"""
        print("🅿️  Smart Parking Monitor Started")
        print(f"📡 Configured for port: {self.port}")
        print("🖥️  GUI Dashboard launching...")
        
        # Handle window closing
        def on_closing():
            if self.is_connected:
                self.disconnect_arduino()
            self.monitoring_active = False
            self.save_historical_data()
            self.root.destroy()
        
        self.root.protocol("WM_DELETE_WINDOW", on_closing)
        
        # Start GUI main loop
        try:
            self.root.mainloop()
        except KeyboardInterrupt:
            print("\n🛑 Shutting down...")
            on_closing()

# Main execution
if __name__ == "__main__":
    # Configuration - Update COM port as needed
    ARDUINO_PORT = 'COM6'  # Change this to your Arduino port (COM3, COM4, etc. on Windows)
    BAUD_RATE = 9600
    
    print("🚀 Starting Smart Parking System...")
    print("=" * 50)
    
    try:
        # Create and run the monitoring system
        monitor = SmartParkingMonitor(port=ARDUINO_PORT, baudrate=BAUD_RATE)
        monitor.run()
        
    except Exception as e:
        print(f"❌ Error starting system: {e}")
        input("Press Enter to exit...")
    
    print("👋 Smart Parking System stopped.")