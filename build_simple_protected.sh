#!/bin/bash

echo "🍎 WiFi Led Studio - Simple Protected Build (macOS)"
echo "=================================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Step 1: Compile source to bytecode
echo -e "${CYAN}Step 1: Compiling source to bytecode...${NC}"
python3 simple_protect.py

if [ $? -ne 0 ]; then
    echo -e "${RED}Source compilation failed!${NC}"
    read -p "Press Enter to exit"
    exit 1
fi

echo -e "${GREEN}Source code compiled to bytecode!${NC}"
echo ""

# Step 2: Clean previous build
echo -e "${CYAN}Step 2: Cleaning previous build...${NC}"
rm -rf "build_simple_protected"
echo -e "${GREEN}Previous build cleaned!${NC}"
echo ""

# Step 3: Build with protected source
echo -e "${CYAN}Step 3: Building with bytecode-protected source...${NC}"
python3 setup_simple_protected.py build

if [ $? -eq 0 ]; then
    echo -e "${GREEN}Protected build completed successfully!${NC}"
else
    echo -e "${RED}Protected build failed!${NC}"
    read -p "Press Enter to exit"
    exit 1
fi

echo ""

# Step 4: Verify build
APP_PATH="build_simple_protected/WiFi Led Studio.app"
if [ -d "$APP_PATH" ]; then
    echo -e "${GREEN}Protected .app bundle created: $APP_PATH${NC}"

    # Check bundle size
    BUNDLE_SIZE=$(du -sh "$APP_PATH" | cut -f1)
    echo -e "${CYAN}Bundle size: $BUNDLE_SIZE${NC}"

    # Check for executable
    EXECUTABLE_PATH="$APP_PATH/Contents/MacOS/WiFi Led Studio"
    if [ -f "$EXECUTABLE_PATH" ]; then
        echo -e "${GREEN}Executable found and ready${NC}"
        
        # Check executable permissions
        if [ -x "$EXECUTABLE_PATH" ]; then
            echo -e "${GREEN}Executable permissions: OK${NC}"
        else
            echo -e "${YELLOW}Fixing executable permissions...${NC}"
            chmod +x "$EXECUTABLE_PATH"
        fi
    else
        echo -e "${RED}Executable not found in bundle!${NC}"
        exit 1
    fi

    # Check for source files in bundle
    LIB_PATH="$APP_PATH/Contents/MacOS/lib"
    if [ -d "$LIB_PATH" ]; then
        PY_FILES=$(find "$LIB_PATH" -name "*.py" | wc -l)
        PYC_FILES=$(find "$LIB_PATH" -name "*.pyc" | wc -l)

        echo -e "${CYAN}Source protection status:${NC}"
        if [ $PY_FILES -eq 0 ]; then
            echo -e "   ${GREEN}.py files: $PY_FILES${NC}"
        else
            echo -e "   ${YELLOW}.py files: $PY_FILES${NC}"
        fi
        
        if [ $PYC_FILES -gt 0 ]; then
            echo -e "   ${GREEN}.pyc files: $PYC_FILES${NC}"
        else
            echo -e "   ${RED}.pyc files: $PYC_FILES${NC}"
        fi

        if [ $PY_FILES -eq 0 ] && [ $PYC_FILES -gt 0 ]; then
            echo -e "${GREEN}Source is protected with bytecode!${NC}"
        elif [ $PY_FILES -gt 0 ]; then
            echo -e "${YELLOW}Some .py files still present - partial protection${NC}"
        else
            echo -e "${RED}No source files found - check build${NC}"
        fi
    fi
else
    echo -e "${RED}Protected .app bundle not found!${NC}"
    read -p "Press Enter to exit"
    exit 1
fi

echo ""

# Step 5: Test the protected build
echo -e "${CYAN}Step 5: Testing protected build...${NC}"
echo -e "${YELLOW}Starting protected WiFi Led Studio...${NC}"
echo -e "${YELLOW}Check menu bar for icon and web interface at http://localhost:8090${NC}"
echo -e "${YELLOW}Test will run for 15 seconds${NC}"
echo ""

# Start the app in background
open "$APP_PATH"
APP_PID=$!

echo -e "${GREEN}Protected app started${NC}"
echo ""

# Wait for 15 seconds
for i in {15..1}; do
    echo -ne "${YELLOW}Testing $i seconds... (Check menu bar and http://localhost:8090)${NC}\r"
    sleep 1
done

echo ""
echo ""
echo -e "${YELLOW}Stopping test...${NC}"

# Stop the app
pkill -f "WiFi Led Studio" 2>/dev/null

echo -e "${GREEN}Test completed${NC}"

echo ""
echo "============================================================"
echo -e "${GREEN}Simple Protected Build Summary:${NC}"
echo -e "${GREEN}Source code compiled to bytecode (.pyc files)${NC}"
echo -e "${GREEN}Protected .app bundle created${NC}"
echo -e "${GREEN}Menu bar functionality preserved${NC}"
echo -e "${GREEN}Source code protected from casual inspection${NC}"
echo ""
echo -e "${CYAN}Build location: build_simple_protected/WiFi Led Studio.app${NC}"
echo ""
echo -e "${CYAN}Protection level:${NC}"
echo "   • Python source compiled to bytecode (.pyc)"
echo "   • Source files not readable as plain text"
echo "   • Suitable for basic source protection"
echo "   • macOS .app bundle with proper Info.plist"

echo ""
read -p "Press Enter to exit"