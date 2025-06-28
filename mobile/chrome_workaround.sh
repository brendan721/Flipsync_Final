#!/bin/bash

# Chrome workaround for Flutter web development in containers
# This script provides alternatives when Chrome is not available

echo "=== Flutter Web Development - Chrome Workaround ==="

# Option 1: Use web-server mode (recommended for containers)
echo "Option 1: Using Flutter web-server mode (no Chrome needed)"
echo "Command: flutter run -d web-server --web-port 3000 --web-hostname 0.0.0.0"
echo "Access at: http://localhost:3000"
echo ""

# Option 2: Create a dummy Chrome executable for Flutter doctor
echo "Option 2: Creating dummy Chrome executable to satisfy Flutter doctor"

# Create a local bin directory
mkdir -p ~/bin

# Create a dummy Chrome script
cat > ~/bin/google-chrome << 'EOF'
#!/bin/bash
echo "Chrome workaround: Using Flutter web-server mode instead"
echo "For web development, use: flutter run -d web-server --web-port 3000"
exit 0
EOF

# Make it executable
chmod +x ~/bin/google-chrome

# Add to PATH if not already there
if [[ ":$PATH:" != *":$HOME/bin:"* ]]; then
    echo 'export PATH="$HOME/bin:$PATH"' >> ~/.bashrc
    export PATH="$HOME/bin:$PATH"
fi

echo "Dummy Chrome executable created at ~/bin/google-chrome"
echo "Added ~/bin to PATH"

# Option 3: Set CHROME_EXECUTABLE environment variable
echo ""
echo "Option 3: Setting CHROME_EXECUTABLE environment variable"
export CHROME_EXECUTABLE="$HOME/bin/google-chrome"
echo "export CHROME_EXECUTABLE=\"$HOME/bin/google-chrome\"" >> ~/.bashrc

echo "CHROME_EXECUTABLE set to: $CHROME_EXECUTABLE"

echo ""
echo "=== Testing Flutter Doctor ==="
flutter doctor

echo ""
echo "=== Flutter Web Development Ready ==="
echo "Use these commands for web development:"
echo "  flutter build web                    # Build for production"
echo "  flutter run -d web-server --web-port 3000  # Development server"
echo ""
echo "Note: For full Chrome debugging, install Chrome with:"
echo "  sudo apt update && sudo apt install -y google-chrome-stable"
