#!/bin/bash

# Create log directories
mkdir -p logs/nginx
mkdir -p logs/supervisor

# Set proper permissions
chmod -R 755 logs
touch logs/supervisor/send_note_out.log logs/supervisor/send_note_err.log
touch logs/supervisor/nginx.log logs/supervisor/nginx-error.log
touch logs/supervisor/supervisord.log
chmod 666 logs/supervisor/* 