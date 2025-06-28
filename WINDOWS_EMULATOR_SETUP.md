# Windows Android Emulator Setup for WSL2 Flutter Development

## 🎯 **Optimal Configuration for FlipSync Testing**

This guide sets up seamless integration between Windows Android emulator and WSL2 Flutter development.

## 📱 **Step 1: Install Android Studio on Windows**

### **Download and Install**
1. Download Android Studio from: https://developer.android.com/studio
2. Install with default settings
3. Complete the setup wizard
4. Install Android SDK and emulator components

### **Create Android Virtual Device (AVD)**
1. Open Android Studio
2. Go to "Tools" → "AVD Manager"
3. Click "Create Virtual Device"
4. **Recommended Configuration:**
   ```
   Device: Pixel 7 Pro
   System Image: Android 14 (API 34) - Google APIs
   RAM: 4GB
   Internal Storage: 8GB
   Graphics: Hardware - GLES 2.0
   ```

## 🔗 **Step 2: Configure ADB Bridge (Windows)**

### **Set up ADB Server on Windows**
```cmd
# Open Command Prompt as Administrator
cd "C:\Users\%USERNAME%\AppData\Local\Android\Sdk\platform-tools"

# Start ADB server
adb start-server

# Verify ADB is running
adb devices
```

### **Configure ADB for Network Access**
```cmd
# Allow ADB to accept connections from WSL2
adb -a -P 5037 server nodaemon
```

**Or create a batch file for easy startup:**
```batch
@echo off
cd "C:\Users\%USERNAME%\AppData\Local\Android\Sdk\platform-tools"
echo Starting ADB server for WSL2 access...
adb -a -P 5037 server nodaemon
pause
```

## 🐧 **Step 3: Configure WSL2 Flutter Environment**

### **Install ADB in WSL2**
```bash
# Install Android tools
sudo apt update
sudo apt install -y android-tools-adb

# Verify installation
adb version
```

### **Configure ADB to Connect to Windows**
```bash
# Add to ~/.bashrc
echo 'export ADB_SERVER_SOCKET=tcp:$(hostname).local:5037' >> ~/.bashrc
echo 'export ANDROID_ADB_SERVER_ADDRESS=$(hostname).local' >> ~/.bashrc
echo 'export ANDROID_ADB_SERVER_PORT=5037' >> ~/.bashrc

# Reload bashrc
source ~/.bashrc
```

### **Alternative: Direct IP Connection**
```bash
# Get Windows host IP from WSL2
export WINDOWS_HOST_IP=$(cat /etc/resolv.conf | grep nameserver | awk '{print $2}')

# Connect to Windows ADB server
adb connect $WINDOWS_HOST_IP:5037

# Verify connection
adb devices
```

## 🚀 **Step 4: Flutter Development Workflow**

### **Start Emulator from Windows**
1. Open Android Studio
2. Go to AVD Manager
3. Click "Play" button next to your AVD
4. Wait for emulator to fully boot

### **Connect from WSL2**
```bash
# Navigate to Flutter project
cd /home/brend/Flipsync_Final/mobile

# Check connected devices
flutter devices

# Should show something like:
# Android SDK built for x86_64 (mobile) • emulator-5554 • android-x64 • Android 14 (API 34)

# Run Flutter app on emulator
flutter run
```

### **Automated Setup Script**
```bash
# Create setup script
cat > ~/setup_android_emulator.sh << 'EOF'
#!/bin/bash

echo "🔍 Setting up Android emulator connection..."

# Get Windows host IP
WINDOWS_HOST_IP=$(cat /etc/resolv.conf | grep nameserver | awk '{print $2}')
echo "Windows Host IP: $WINDOWS_HOST_IP"

# Kill any existing ADB server
adb kill-server

# Connect to Windows ADB server
adb connect $WINDOWS_HOST_IP:5037

# Wait a moment for connection
sleep 2

# Check devices
echo "📱 Available devices:"
flutter devices

echo "✅ Setup complete! You can now run: flutter run"
EOF

chmod +x ~/setup_android_emulator.sh
```

## 🧪 **Step 5: Testing and Verification**

### **Test Connection**
```bash
# Run setup script
~/setup_android_emulator.sh

# Verify Flutter can see the emulator
flutter devices

# Test app deployment
cd /home/brend/Flipsync_Final/mobile
flutter run --debug
```

### **Troubleshooting Commands**
```bash
# Check ADB connection
adb devices -l

# Restart ADB if needed
adb kill-server
adb start-server

# Check Flutter doctor
flutter doctor -v

# Check emulator logs
adb logcat | grep flutter
```

## 🔧 **Step 6: Optimize for FlipSync Development**

### **Create FlipSync Testing Script**
```bash
cat > ~/test_flipsync_mobile.sh << 'EOF'
#!/bin/bash

echo "🚀 FlipSync Mobile Testing Setup"
echo "================================"

# Setup Android connection
~/setup_android_emulator.sh

# Navigate to mobile app
cd /home/brend/Flipsync_Final/mobile

# Clean and get dependencies
echo "📦 Getting dependencies..."
flutter clean
flutter pub get

# Build and run
echo "🏗️ Building and deploying FlipSync..."
flutter run --debug --hot

echo "✅ FlipSync mobile app deployed to emulator!"
EOF

chmod +x ~/test_flipsync_mobile.sh
```

### **Hot Reload Development**
```bash
# Start development session
~/test_flipsync_mobile.sh

# In the Flutter console:
# r - Hot reload
# R - Hot restart
# q - Quit
# h - Help
```

## 📊 **Performance Optimization**

### **Emulator Settings for Better Performance**
1. **In Android Studio AVD Manager:**
   - Edit your AVD
   - Advanced Settings:
     - RAM: 4GB (or more if available)
     - VM Heap: 512MB
     - Graphics: Hardware - GLES 2.0
     - Multi-Core CPU: 4 cores

2. **Windows Performance:**
   - Enable Hyper-V (if available)
   - Disable Windows Defender real-time scanning for Android SDK folder
   - Close unnecessary applications

### **WSL2 Performance Tips**
```bash
# Add to ~/.bashrc for better performance
echo 'export FLUTTER_STORAGE_BASE_URL=https://storage.flutter-io.cn' >> ~/.bashrc
echo 'export PUB_HOSTED_URL=https://pub.flutter-io.cn' >> ~/.bashrc
```

## 🎯 **Quick Start Commands**

```bash
# 1. Start Windows emulator (in Android Studio)
# 2. Connect from WSL2
~/setup_android_emulator.sh

# 3. Test FlipSync app
~/test_flipsync_mobile.sh

# 4. For subsequent runs
cd /home/brend/Flipsync_Final/mobile && flutter run --hot
```

---

**This setup provides seamless integration between Windows Android emulator and WSL2 Flutter development, avoiding all Docker-related connectivity issues.**
