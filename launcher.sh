#!/bin/bash

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

clear
echo -e "${GREEN}================================================${NC}"
echo -e "${GREEN}     BASIC RAT - QUICK LAUNCHER${NC}"
echo -e "${GREEN}     Complete Merged Edition${NC}"
echo -e "${GREEN}================================================${NC}"
echo ""
echo -e "${YELLOW}1.${NC} Start C2 Server"
echo -e "${YELLOW}2.${NC} Start Client (Local Test)"
echo -e "${YELLOW}3.${NC} Start Controller"
echo -e "${YELLOW}4.${NC} Install Dependencies"
echo -e "${YELLOW}5.${NC} Compile All"
echo -e "${YELLOW}6.${NC} Exit"
echo ""
read -p "Select option (1-6): " choice

case $choice in
    1)
        clear
        echo -e "${GREEN}[+] Starting C2 Server...${NC}"
        python3 server.py
        ;;
    2)
        clear
        echo -e "${GREEN}[+] Starting Client...${NC}"
        python3 client.py
        ;;
    3)
        clear
        echo -e "${GREEN}[+] Starting Controller...${NC}"
        python3 controller.py
        ;;
    4)
        clear
        echo -e "${GREEN}[+] Installing dependencies...${NC}"
        pip3 install -r requirements.txt
        echo ""
        echo -e "${GREEN}[+] Installation complete!${NC}"
        read -p "Press Enter to continue..."
        ;;
    5)
        clear
        echo -e "${GREEN}[+] Compiling all components...${NC}"
        python3 compile.py
        echo ""
        echo -e "${GREEN}[+] Compilation complete! Check dist/ folder${NC}"
        read -p "Press Enter to continue..."
        ;;
    6)
        echo -e "${GREEN}[+] Goodbye!${NC}"
        exit 0
        ;;
    *)
        echo -e "${RED}Invalid option!${NC}"
        read -p "Press Enter to continue..."
        ;;
esac
