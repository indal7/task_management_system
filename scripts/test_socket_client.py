#!/usr/bin/env python3
"""
Socket.IO Test Client for Terminal Testing

Run this to test socket connections from terminal:
    TEST_EMAIL=user@example.com TEST_PASSWORD=secret python scripts/test_socket_client.py
"""

import os
import socketio
import time
import requests
import json
import threading

class SocketTestClient:
    def __init__(self, server_url='http://localhost:5000'):
        self.server_url = server_url
        self.sio = socketio.Client(logger=True, engineio_logger=True)
        self.token = None
        self.user_id = None
        self.setup_event_handlers()

    def setup_event_handlers(self):
        """Setup event handlers for socket responses"""
        
        @self.sio.on('connect')
        def on_connect():
            print("🔌 Connected to server!")

        @self.sio.on('disconnect')
        def on_disconnect():
            print("🔌 Disconnected from server!")

        @self.sio.on('connected')
        def on_authenticated(data):
            print(f"✅ Authenticated: {data}")

        @self.sio.on('error')
        def on_error(data):
            print(f"❌ Error: {data}")

        @self.sio.on('new_notification')
        def on_new_notification(data):
            print(f"🔔 New Notification: {data}")

        @self.sio.on('notification_updated')
        def on_notification_updated(data):
            print(f"📝 Notification Updated: {data}")

        @self.sio.on('notifications_data')
        def on_notifications_data(data):
            print(f"📋 Notifications Data: {json.dumps(data, indent=2)}")

        @self.sio.on('task_updated')
        def on_task_updated(data):
            print(f"📋 Task Updated: {data}")

        @self.sio.on('room_joined')
        def on_room_joined(data):
            print(f"🏠 Room Joined: {data}")

        @self.sio.on('room_left')
        def on_room_left(data):
            print(f"🚪 Room Left: {data}")

        @self.sio.on('pong')
        def on_pong(data):
            print(f"🏓 Pong received: {data}")

    def login(self, username=None, password=None):
        """Login to get JWT token"""
        username = username or os.environ.get('TEST_EMAIL', 'test@example.com')
        password = password or os.environ.get('TEST_PASSWORD', '')
        try:
            response = requests.post(f'{self.server_url}/api/auth/login', json={
                'email': username,
                'username': username,
                'password': password
            })
            
            if response.status_code == 200:
                data = response.json()
                self.token = data.get('data', {}).get('access_token')
                print(f"✅ Login successful! Token: {self.token[:20]}...")
                return True
            else:
                print(f"❌ Login failed: {response.text}")
                return False
        except Exception as e:
            print(f"❌ Login error: {e}")
            return False

    def connect_socket(self):
        """Connect to socket with authentication"""
        try:
            if not self.token:
                print("❌ No token available. Please login first.")
                return False
                
            # Connect with token as query parameter
            self.sio.connect(
                self.server_url, 
                auth={'token': self.token},
                transports=['websocket', 'polling']
            )
            return True
        except Exception as e:
            print(f"❌ Socket connection failed: {e}")
            return False

    def test_basic_functionality(self):
        """Test basic socket functionality"""
        if not self.sio.connected:
            print("❌ Not connected to server")
            return

        print("\n🧪 Testing basic socket functionality...")
        
        # Test ping
        print("📡 Sending ping...")
        self.sio.emit('ping', {'message': 'test ping'})
        time.sleep(1)
        
        # Test joining user room
        print("🏠 Joining user room...")
        self.sio.emit('join_user_room', {})
        time.sleep(1)
        
        # Test getting notifications
        print("📋 Getting notifications...")
        self.sio.emit('get_notifications', {'unread_only': False})
        time.sleep(2)

    def test_notification_operations(self):
        """Test notification-related operations"""
        if not self.sio.connected:
            print("❌ Not connected to server")
            return

        print("\n🔔 Testing notification operations...")
        
        # Get unread notifications
        print("📬 Getting unread notifications...")
        self.sio.emit('get_notifications', {'unread_only': True})
        time.sleep(2)
        
        # You can add more notification tests here
        # For example, if you have notification IDs to test:
        # self.sio.emit('mark_notification_read', {'notification_id': 1})

    def interactive_mode(self):
        """Start interactive mode for manual testing"""
        print("\n🎮 Interactive Mode Started!")
        print("Available commands:")
        print("  ping - Send ping to server")
        print("  join_user - Join user room")
        print("  join_project <id> - Join project room")
        print("  notifications - Get all notifications")
        print("  unread - Get unread notifications")
        print("  read <id> - Mark notification as read")
        print("  quit - Exit interactive mode")
        
        while self.sio.connected:
            try:
                command = input("\n💬 Enter command: ").strip().lower()
                
                if command == 'quit':
                    break
                elif command == 'ping':
                    self.sio.emit('ping', {'message': 'manual ping'})
                elif command == 'join_user':
                    self.sio.emit('join_user_room', {})
                elif command.startswith('join_project'):
                    parts = command.split()
                    if len(parts) > 1:
                        project_id = parts[1]
                        self.sio.emit('join_project_room', {'project_id': int(project_id)})
                    else:
                        print("❌ Please provide project ID")
                elif command == 'notifications':
                    self.sio.emit('get_notifications', {'unread_only': False})
                elif command == 'unread':
                    self.sio.emit('get_notifications', {'unread_only': True})
                elif command.startswith('read'):
                    parts = command.split()
                    if len(parts) > 1:
                        notification_id = parts[1]
                        self.sio.emit('mark_notification_read', {'notification_id': int(notification_id)})
                    else:
                        print("❌ Please provide notification ID")
                else:
                    print("❌ Unknown command")
                    
                time.sleep(0.5)  # Brief pause between commands
                
            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"❌ Command error: {e}")

    def disconnect_socket(self):
        """Disconnect from socket"""
        if self.sio.connected:
            self.sio.disconnect()
            print("🔌 Disconnected from server")

def main():
    """Main test function"""
    print("🧪 Socket.IO Test Client Starting...")
    
    client = SocketTestClient()
    
    # Step 1: Login (optional - you can skip if testing without auth)
    print("\n1️⃣ Attempting login...")
    login_success = client.login()
    
    # Step 2: Connect to socket
    print("\n2️⃣ Connecting to socket...")
    if client.connect_socket():
        print("✅ Socket connected successfully!")
        
        # Step 3: Wait a moment for connection to stabilize
        time.sleep(2)
        
        # Step 4: Test basic functionality
        client.test_basic_functionality()
        
        # Step 5: Test notifications
        client.test_notification_operations()
        
        # Step 6: Interactive mode
        try:
            client.interactive_mode()
        except KeyboardInterrupt:
            print("\n⏹️  Interactive mode interrupted")
        
        # Step 7: Disconnect
        client.disconnect_socket()
    else:
        print("❌ Failed to connect to socket")

    print("\n🏁 Test completed!")

if __name__ == '__main__':
    main()