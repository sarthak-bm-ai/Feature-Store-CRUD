#!/usr/bin/env python3
"""
Simple StatsD server for development and testing.
Receives metrics and prints them to console with timestamps.
"""

import socket
import threading
import time
from datetime import datetime
import re

class SimpleStatsDServer:
    def __init__(self, host='localhost', port=8125):
        self.host = host
        self.port = port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind((host, port))
        self.running = True
        
        # Metrics storage
        self.metrics = {
            'counters': {},
            'gauges': {},
            'timers': {}
        }
        
    def parse_metric(self, data):
        """Parse StatsD metric format: metric.name:value|type|@sample_rate|#tag1:value1,tag2:value2"""
        try:
            # Split by | to get metric, type, sample_rate, tags
            parts = data.split('|')
            if len(parts) < 2:
                return None
                
            metric_part = parts[0]
            metric_type = parts[1]
            
            # Extract sample rate and tags
            sample_rate = 1.0
            tags = {}
            
            for part in parts[2:]:
                if part.startswith('@'):
                    sample_rate = float(part[1:])
                elif part.startswith('#'):
                    tag_str = part[1:]
                    for tag in tag_str.split(','):
                        if ':' in tag:
                            key, value = tag.split(':', 1)
                            tags[key] = value
            
            # Parse metric name and value
            if ':' not in metric_part:
                return None
                
            metric_name, value = metric_part.split(':', 1)
            value = float(value)
            
            return {
                'name': metric_name,
                'value': value,
                'type': metric_type,
                'sample_rate': sample_rate,
                'tags': tags,
                'timestamp': datetime.now()
            }
        except Exception as e:
            print(f"Error parsing metric: {data} - {e}")
            return None
    
    def process_metric(self, metric):
        """Process and store the metric"""
        if not metric:
            return
            
        name = metric['name']
        value = metric['value']
        metric_type = metric['type']
        tags = metric['tags']
        
        # Apply sample rate
        if metric['sample_rate'] < 1.0:
            value = value / metric['sample_rate']
        
        # Create tag string for display
        tag_str = ""
        if tags:
            tag_str = " | " + ", ".join([f"{k}={v}" for k, v in tags.items()])
        
        # Store and display based on type
        if metric_type == 'c':  # Counter
            if name not in self.metrics['counters']:
                self.metrics['counters'][name] = 0
            self.metrics['counters'][name] += value
            print(f"📊 COUNTER: {name} += {value} (total: {self.metrics['counters'][name]}){tag_str}")
            
        elif metric_type == 'g':  # Gauge
            self.metrics['gauges'][name] = value
            print(f"📈 GAUGE: {name} = {value}{tag_str}")
            
        elif metric_type == 'ms':  # Timer
            if name not in self.metrics['timers']:
                self.metrics['timers'][name] = []
            self.metrics['timers'][name].append(value)
            print(f"⏱️  TIMER: {name} = {value}ms{tag_str}")
            
        elif metric_type == 'h':  # Histogram
            if name not in self.metrics['timers']:
                self.metrics['timers'][name] = []
            self.metrics['timers'][name].append(value)
            print(f"📊 HISTOGRAM: {name} = {value}{tag_str}")
    
    def start(self):
        """Start the StatsD server"""
        print(f"🚀 Starting StatsD server on {self.host}:{self.port}")
        print("📡 Listening for metrics... (Press Ctrl+C to stop)")
        print("=" * 80)
        
        while self.running:
            try:
                data, addr = self.sock.recvfrom(1024)
                message = data.decode('utf-8').strip()
                
                # Handle multiple metrics in one packet
                for line in message.split('\n'):
                    if line.strip():
                        metric = self.parse_metric(line.strip())
                        self.process_metric(metric)
                        
            except KeyboardInterrupt:
                print("\n🛑 Shutting down StatsD server...")
                self.running = False
                break
            except Exception as e:
                print(f"❌ Error receiving data: {e}")
                
        self.sock.close()
    
    def print_summary(self):
        """Print a summary of collected metrics"""
        print("\n" + "=" * 80)
        print("📊 METRICS SUMMARY")
        print("=" * 80)
        
        if self.metrics['counters']:
            print("\n🔢 COUNTERS:")
            for name, value in self.metrics['counters'].items():
                print(f"  {name}: {value}")
        
        if self.metrics['gauges']:
            print("\n📈 GAUGES:")
            for name, value in self.metrics['gauges'].items():
                print(f"  {name}: {value}")
        
        if self.metrics['timers']:
            print("\n⏱️  TIMERS (avg/min/max):")
            for name, values in self.metrics['timers'].items():
                if values:
                    avg = sum(values) / len(values)
                    min_val = min(values)
                    max_val = max(values)
                    print(f"  {name}: avg={avg:.2f}ms, min={min_val:.2f}ms, max={max_val:.2f}ms (count: {len(values)})")

if __name__ == "__main__":
    server = SimpleStatsDServer()
    try:
        server.start()
    finally:
        server.print_summary()
