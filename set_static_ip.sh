#!/bin/bash

# For Ubuntu/Debian with Netplan
cat > /etc/netplan/01-netcfg.yaml << EOF
network:
  version: 2
  renderer: networkd
  ethernets:
    enp5s0:  # Your network interface name from 'ip a'
      dhcp4: no
      addresses:
        - 192.168.18.10/24  # Your current IP and subnet
      routes:
        - to: default
          via: 192.168.18.1  # Your router IP
      nameservers:
          addresses: [8.8.8.8, 8.8.4.4]
EOF

# Fix permissions on the netplan config file
chmod 600 /etc/netplan/01-netcfg.yaml

# Make sure systemd-networkd is installed and running
if ! systemctl is-active --quiet systemd-networkd; then
    echo "Installing and enabling systemd-networkd..."
    apt-get update
    apt-get install -y systemd-networkd
    systemctl enable systemd-networkd
    systemctl start systemd-networkd
fi

# Apply the configuration
echo "Applying netplan configuration..."
netplan generate
netplan apply

# For older Ubuntu/Debian systems with /etc/network/interfaces
# cat > /etc/network/interfaces << EOF
# auto enp5s0
# iface enp5s0 inet static
#     address 192.168.18.10
#     netmask 255.255.255.0
#     gateway 192.168.18.1
#     dns-nameservers 8.8.8.8 8.8.4.4
# EOF
# 
# # Restart networking
# sudo systemctl restart networking

echo "Static IP configured. Your server IP is: 192.168.18.10"
echo "You may need to restart your system for changes to take full effect."