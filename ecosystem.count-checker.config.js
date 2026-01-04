module.exports = {
  apps: [{
    name: 'count-checker',
    script: './count_check_daemon.py',
    interpreter: 'python3',
    cwd: '/home/user/webapp',
    instances: 1,
    autorestart: true,
    watch: false,
    max_memory_restart: '200M',
    error_file: '/home/user/.pm2/logs/count-checker-error.log',
    out_file: '/home/user/.pm2/logs/count-checker-out.log',
    log_date_format: 'YYYY-MM-DD HH:mm:ss',
    env: {
      TZ: 'Asia/Shanghai'
    }
  }]
};
