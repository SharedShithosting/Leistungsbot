#!/bin/bash

install_service () {
  SERVICE_NAME=leistungsbot.service
  # check if service is active
  IS_ACTIVE=$(sudo systemctl is-active $SERVICE_NAME)
  if [ "$IS_ACTIVE" == "active" ]; then
    # restart the service
    echo "Service is running"
    echo "Restarting service"
    sudo systemctl restart $SERVICE_NAME
    echo "Service restarted"
  else
    # create service file
    echo "Creating service file"
    sudo cat > /etc/systemd/system/$SERVICE_NAME << EOF
[Unit]
Description=Running LeistungsBot
After=network.target
[Service]
[Service]
Type=simple
Restart=always
#RestartSec=30
#WatchdogSec=5
WorkingDirectory=/root/Leistungsbot
EnvironmentFile=/root/Leistungsbot/.env
ExecStart=/usr/bin/python3.9 /root/Leistungsbot/Bot.py
[Install]
WantedBy=multi-user.target
EOF
    # restart daemon, enable and start service
    echo "Reloading daemon and enabling service"
    sudo systemctl daemon-reload 
    sudo systemctl enable ${SERVICE_NAME//'.service'/} # remove the extension
    sudo systemctl start ${SERVICE_NAME//'.service'/}
    echo "Service Started"
  fi
}


install_python () {
  if ! command -v pip3 &> /dev/null
  then
    echo "pip3 could not be found"
    echo "installing..."
    sudo apt update
    sudo apt install -y python3 python3-pip
  else
    echo "pip3 found"
  fi
  sudo pip3 install -r requirements.txt
}


if ! command -v git &> /dev/null
then
  echo "git could not be found"
  echo "installing..."
  sudo apt update
  sudo apt install -y git
else
  echo "git found"
fi
git pull
install_python
install_service
