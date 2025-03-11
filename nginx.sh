#!/bin/bash

# Install necessary dependencies
sudo apt update
sudo apt install -y python3 python3-pip python3-venv nginx supervisor

# Create application directory if it doesn't exist
mkdir -p /opt/video-processing-app

# Copy application files to the directory
# Assuming your code is in the current directory
cp -r . /opt/video-processing-app/

# Set up virtual environment
cd /opt/video-processing-app
python3 -m venv venv
source venv/bin/activate
pip install flask gunicorn werkzeug
# Install any other dependencies required by your application

# Create a Supervisor configuration file
cat > /etc/supervisor/conf.d/video-processing.conf << EOF
[program:video-processing]
directory=/opt/video-processing-app
command=/opt/video-processing-app/venv/bin/gunicorn -b 127.0.0.1:5000 -w 4 app:app
autostart=true
autorestart=true
stderr_logfile=/var/log/video-processing.err.log
stdout_logfile=/var/log/video-processing.out.log
user=www-data
EOF

# Create uploads and processed folders with proper permissions
mkdir -p /opt/video-processing-app/uploads
mkdir -p /opt/video-processing-app/Processed_Videos
chmod 755 /opt/video-processing-app/uploads
chmod 755 /opt/video-processing-app/Processed_Videos
chown -R www-data:www-data /opt/video-processing-app

# Configure Nginx
cat > /etc/nginx/sites-available/video-processing << EOF
server {
    listen 80;
    server_name your_server_ip;

    client_max_body_size 100M;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
    }
}
EOF

# Enable the Nginx site
ln -s /etc/nginx/sites-available/video-processing /etc/nginx/sites-enabled/

# Replace the placeholder IP with your server's IP
sed -i "s/your_server_ip/$(hostname -I | awk '{print $1}')/g" /etc/nginx/sites-available/video-processing

# Restart services
supervisorctl reread
supervisorctl update
systemctl restart nginx

echo "Video processing server deployed successfully!"
echo "Server is running at: $(hostname -I | awk '{print $1}')"