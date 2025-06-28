# Docker WSL2 Integration Fix Guide

## 🚨 **Issue Identified**
Docker Desktop WSL2 integration is not properly configured. Docker commands are not available in your WSL2 Ubuntu distro.

## 🔧 **Step-by-Step Fix**

### **1. Configure Docker Desktop (Windows Host)**

**Open Docker Desktop Settings:**
1. Right-click Docker Desktop icon in system tray
2. Select "Settings" or "Preferences"
3. Navigate to "Resources" → "WSL Integration"

**Enable WSL2 Integration:**
```
✅ Enable integration with my default WSL distro
✅ Enable integration with additional distros:
   ✅ Ubuntu-24.04 (or your specific Ubuntu version)
```

**Apply & Restart:**
1. Click "Apply & Restart"
2. Wait for Docker Desktop to restart completely

### **2. Verify WSL2 Distro (Windows PowerShell)**

```powershell
# Check WSL distros
wsl --list --verbose

# Should show something like:
#   NAME                   STATE           VERSION
# * Ubuntu-24.04           Running         2
#   docker-desktop         Running         2
#   docker-desktop-data    Running         2
```

### **3. Test Docker in WSL2**

```bash
# In your WSL2 Ubuntu terminal
docker --version
docker ps

# Should show Docker version and running containers
```

### **4. Alternative: Install Docker Engine in WSL2 (If Desktop Integration Fails)**

```bash
# Update package index
sudo apt update

# Install prerequisites
sudo apt install -y apt-transport-https ca-certificates curl gnupg lsb-release

# Add Docker's official GPG key
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg

# Add Docker repository
echo "deb [arch=amd64 signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# Install Docker Engine
sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io

# Add user to docker group
sudo usermod -aG docker $USER

# Start Docker service
sudo service docker start

# Test installation
docker --version
```

## 🚀 **Recommended Approach: Skip Docker for Development**

Given the connectivity issues, here's a better approach:

### **Use Native PostgreSQL Instead of Docker**

```bash
# Install PostgreSQL directly in WSL2
sudo apt update
sudo apt install -y postgresql postgresql-contrib

# Start PostgreSQL service
sudo service postgresql start

# Create FlipSync user and databases
sudo -u postgres psql << EOF
CREATE USER flipsync WITH PASSWORD 'flipsync_password';
CREATE DATABASE flipsync OWNER flipsync;
CREATE DATABASE flipsync_ai_tools OWNER flipsync;
CREATE DATABASE flipsync_test OWNER flipsync;
GRANT ALL PRIVILEGES ON DATABASE flipsync TO flipsync;
GRANT ALL PRIVILEGES ON DATABASE flipsync_ai_tools TO flipsync;
GRANT ALL PRIVILEGES ON DATABASE flipsync_test TO flipsync;
\q
EOF

# Test connection
psql -h localhost -U flipsync -d flipsync -c "SELECT 'Connection successful' AS status;"
```

### **Use Native Redis Instead of Docker**

```bash
# Install Redis
sudo apt install -y redis-server

# Start Redis service
sudo service redis-server start

# Test Redis
redis-cli ping
```

## 🎯 **Benefits of Native Installation**

1. **No Network Conflicts**: Direct WSL2 networking
2. **Better Performance**: No Docker overhead
3. **Simpler Configuration**: Standard Linux service management
4. **Reliable Connectivity**: No Docker bridge issues
5. **Easier Debugging**: Direct access to logs and configuration

## 🔄 **Service Management Commands**

```bash
# PostgreSQL
sudo service postgresql start
sudo service postgresql stop
sudo service postgresql restart
sudo service postgresql status

# Redis
sudo service redis-server start
sudo service redis-server stop
sudo service redis-server restart
sudo service redis-server status

# Auto-start services on WSL2 boot
echo "sudo service postgresql start" >> ~/.bashrc
echo "sudo service redis-server start" >> ~/.bashrc
```

## 🧪 **Testing Database Connectivity**

```bash
# Test PostgreSQL
psql -h localhost -U flipsync -d flipsync -c "\dt"

# Test Redis
redis-cli set test_key "test_value"
redis-cli get test_key
redis-cli del test_key
```

---

**Recommendation**: Use native PostgreSQL and Redis installation for reliable, high-performance development without Docker complexity.
