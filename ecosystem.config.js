module.exports = {
  apps: [{
    name: 'ratings-api',
    script: '/root/chesstools/ratings-api/venv/bin/uvicorn',
    args: 'src.api:app --host 127.0.0.1 --port 5002',
    cwd: '/root/chesstools/ratings-api',
    interpreter: 'none',
    env: {
      PORT: 5002
    },
    instances: 1,
    autorestart: true,
    watch: false,
    max_memory_restart: '500M',
    error_file: '/var/log/ratings-api-error.log',
    out_file: '/var/log/ratings-api-out.log',
    log_file: '/var/log/ratings-api.log',
    time: true
  }]
};
