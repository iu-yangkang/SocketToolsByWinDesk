// SSL Socket 工具 JavaScript

class SSLSocketApp {
    constructor() {
        this.init();
        this.bindEvents();
        this.loadCertificates();
        this.updateStatus();
    }

    init() {
        // 初始化状态
        this.serverRunning = false;
        this.clientConnected = false;
        
        // 定期更新状态
        setInterval(() => this.updateStatus(), 5000);
    }

    bindEvents() {
        // 证书上传
        document.getElementById('upload-form').addEventListener('submit', (e) => {
            e.preventDefault();
            this.uploadCertificate();
        });

        // 服务器控制
        document.getElementById('server-form').addEventListener('submit', (e) => {
            e.preventDefault();
            this.startServer();
        });

        document.getElementById('stop-server-btn').addEventListener('click', () => {
            this.stopServer();
        });

        // 客户端控制
        document.getElementById('client-form').addEventListener('submit', (e) => {
            e.preventDefault();
            this.connectClient();
        });

        document.getElementById('disconnect-client-btn').addEventListener('click', () => {
            this.disconnectClient();
        });

        // 双向认证选项切换
        document.getElementById('require-client-cert').addEventListener('change', (e) => {
            document.getElementById('ca-cert-section').style.display = e.target.checked ? 'block' : 'none';
        });

        // 服务器验证选项切换
        document.getElementById('verify-server').addEventListener('change', (e) => {
            document.getElementById('client-ca-section').style.display = e.target.checked ? 'block' : 'none';
        });

        // 客户端证书选项切换
        document.getElementById('use-client-cert').addEventListener('change', (e) => {
            document.getElementById('client-cert-section').style.display = e.target.checked ? 'block' : 'none';
        });

        // 消息输入回车发送
        document.getElementById('message-input').addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                this.sendMessage();
            }
        });
    }

    async uploadCertificate() {
        const fileInput = document.getElementById('cert-file');
        const typeSelect = document.getElementById('cert-type');
        
        if (!fileInput.files[0]) {
            this.showMessage('请选择证书文件', 'error');
            return;
        }

        const formData = new FormData();
        formData.append('file', fileInput.files[0]);
        formData.append('type', typeSelect.value);

        try {
            this.showLoading('上传中...');
            const response = await fetch('/api/upload-certificate', {
                method: 'POST',
                body: formData
            });

            const result = await response.json();
            
            if (result.success) {
                this.showMessage(`证书上传成功: ${result.filename}`, 'success');
                this.loadCertificates();
                fileInput.value = '';
            } else {
                this.showMessage(`上传失败: ${result.error}`, 'error');
            }
        } catch (error) {
            this.showMessage(`上传错误: ${error.message}`, 'error');
        } finally {
            this.hideLoading();
        }
    }

    async loadCertificates() {
        try {
            const response = await fetch('/api/list-certificates');
            const result = await response.json();

            if (result.success) {
                this.updateCertificateList(result.files);
                this.updateCertificateSelects(result.files);
            } else {
                console.error('加载证书列表失败:', result.error);
            }
        } catch (error) {
            console.error('加载证书列表错误:', error);
        }
    }

    updateCertificateList(files) {
        const listContainer = document.getElementById('certificate-list');
        
        if (files.length === 0) {
            listContainer.innerHTML = '<div class="text-muted text-center p-3">暂无证书文件</div>';
            return;
        }

        listContainer.innerHTML = files.map(file => `
            <div class="certificate-item">
                <div class="cert-name">${file.filename}</div>
                <div class="cert-info">
                    大小: ${this.formatFileSize(file.size)} | 
                    修改时间: ${new Date(file.modified).toLocaleString()}
                </div>
                ${file.validation.valid ? `
                    <div class="cert-status valid">
                        ✓ ${file.validation.type}
                        ${file.validation.subject ? `<br>主题: ${file.validation.subject}` : ''}
                    </div>
                ` : `
                    <div class="cert-status invalid">
                        ✗ ${file.validation.error}
                    </div>
                `}
            </div>
        `).join('');
    }

    updateCertificateSelects(files) {
        const selects = [
            'server-cert', 'server-key', 'server-ca',
            'client-cert', 'client-key', 'client-ca'
        ];

        selects.forEach(selectId => {
            const select = document.getElementById(selectId);
            const currentValue = select.value;
            
            // 保留默认选项
            const defaultOption = select.querySelector('option[value=""]');
            select.innerHTML = '';
            if (defaultOption) {
                select.appendChild(defaultOption);
            }

            // 根据选择器类型过滤文件
            const filteredFiles = this.filterFilesByType(files, selectId);
            
            filteredFiles.forEach(file => {
                const option = document.createElement('option');
                option.value = file.filename;
                option.textContent = `${file.filename} (${file.validation.type || 'Unknown'})`;
                select.appendChild(option);
            });

            // 恢复之前的选择
            if (currentValue && [...select.options].some(opt => opt.value === currentValue)) {
                select.value = currentValue;
            }
        });
    }

    filterFilesByType(files, selectId) {
        return files.filter(file => {
            const validation = file.validation;
            const filename = file.filename.toLowerCase();
            
            switch (selectId) {
                case 'server-cert':
                case 'client-cert':
                    return validation.type === 'X.509' || filename.includes('cert');
                case 'server-key':
                case 'client-key':
                    return validation.type === 'Private Key' || filename.includes('key');
                case 'server-ca':
                case 'client-ca':
                    return validation.type === 'X.509' || filename.includes('ca');
                default:
                    return true;
            }
        });
    }

    async startServer() {
        const formData = {
            host: document.getElementById('server-host').value,
            port: parseInt(document.getElementById('server-port').value),
            cert_file: document.getElementById('server-cert').value,
            key_file: document.getElementById('server-key').value,
            ca_file: document.getElementById('server-ca').value,
            require_client_cert: document.getElementById('require-client-cert').checked
        };

        if (!formData.cert_file || !formData.key_file) {
            this.showMessage('请选择服务器证书和私钥', 'error');
            return;
        }

        try {
            this.showLoading('启动服务器...');
            const response = await fetch('/api/start-server', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(formData)
            });

            const result = await response.json();
            
            if (result.success) {
                this.showMessage(result.message, 'success');
                this.serverRunning = true;
                this.updateServerUI(true, result.config);
            } else {
                this.showMessage(`启动失败: ${result.error}`, 'error');
            }
        } catch (error) {
            this.showMessage(`启动错误: ${error.message}`, 'error');
        } finally {
            this.hideLoading();
        }
    }

    async stopServer() {
        try {
            this.showLoading('停止服务器...');
            const response = await fetch('/api/stop-server', {
                method: 'POST'
            });

            const result = await response.json();
            
            if (result.success) {
                this.showMessage(result.message, 'success');
                this.serverRunning = false;
                this.updateServerUI(false);
            } else {
                this.showMessage(`停止失败: ${result.error}`, 'error');
            }
        } catch (error) {
            this.showMessage(`停止错误: ${error.message}`, 'error');
        } finally {
            this.hideLoading();
        }
    }

    async connectClient() {
        const formData = {
            host: document.getElementById('client-host').value,
            port: parseInt(document.getElementById('client-port').value),
            cert_file: document.getElementById('use-client-cert').checked ? 
                      document.getElementById('client-cert').value : null,
            key_file: document.getElementById('use-client-cert').checked ? 
                     document.getElementById('client-key').value : null,
            ca_file: document.getElementById('verify-server').checked ? 
                    document.getElementById('client-ca').value : null,
            verify_server: document.getElementById('verify-server').checked
        };

        try {
            this.showLoading('连接中...');
            const response = await fetch('/api/connect-client', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(formData)
            });

            const result = await response.json();
            
            if (result.success) {
                this.showMessage(result.message, 'success');
                this.clientConnected = true;
                this.updateClientUI(true, result.config);
                this.showMessagePanel(true);
            } else {
                this.showMessage(`连接失败: ${result.error}`, 'error');
            }
        } catch (error) {
            this.showMessage(`连接错误: ${error.message}`, 'error');
        } finally {
            this.hideLoading();
        }
    }

    async disconnectClient() {
        try {
            const response = await fetch('/api/disconnect-client', {
                method: 'POST'
            });

            const result = await response.json();
            
            if (result.success) {
                this.showMessage(result.message, 'success');
                this.clientConnected = false;
                this.updateClientUI(false);
                this.showMessagePanel(false);
            } else {
                this.showMessage(`断开失败: ${result.error}`, 'error');
            }
        } catch (error) {
            this.showMessage(`断开错误: ${error.message}`, 'error');
        }
    }

    async sendMessage() {
        const messageInput = document.getElementById('message-input');
        const message = messageInput.value.trim();
        
        if (!message) return;

        try {
            const response = await fetch('/api/send-message', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ message })
            });

            const result = await response.json();
            
            if (result.success) {
                this.addMessageToLog(`发送: ${result.sent}`, 'sent');
                this.addMessageToLog(`接收: ${result.received}`, 'received');
                messageInput.value = '';
            } else {
                this.addMessageToLog(`发送失败: ${result.error}`, 'error');
            }
        } catch (error) {
            this.addMessageToLog(`发送错误: ${error.message}`, 'error');
        }
    }

    async updateStatus() {
        try {
            const response = await fetch('/api/status');
            const status = await response.json();
            
            this.serverRunning = status.server_running;
            this.clientConnected = status.client_connected;
            
            this.updateStatusIndicator();
            this.updateServerUI(this.serverRunning);
            this.updateClientUI(this.clientConnected);
            
            if (!this.clientConnected) {
                this.showMessagePanel(false);
            }
        } catch (error) {
            console.error('状态更新错误:', error);
        }
    }

    updateStatusIndicator() {
        const indicator = document.getElementById('status-indicator');
        
        if (this.serverRunning && this.clientConnected) {
            indicator.innerHTML = '<i class="fas fa-circle text-success me-1"></i>服务器运行中 | 客户端已连接';
        } else if (this.serverRunning) {
            indicator.innerHTML = '<i class="fas fa-circle text-warning me-1"></i>服务器运行中';
        } else if (this.clientConnected) {
            indicator.innerHTML = '<i class="fas fa-circle text-info me-1"></i>客户端已连接';
        } else {
            indicator.innerHTML = '<i class="fas fa-circle text-secondary me-1"></i>就绪';
        }
    }

    updateServerUI(running, config = null) {
        const startBtn = document.getElementById('start-server-btn');
        const stopBtn = document.getElementById('stop-server-btn');
        const statusDiv = document.getElementById('server-status');

        startBtn.disabled = running;
        stopBtn.disabled = !running;

        if (running && config) {
            statusDiv.innerHTML = `
                <div class="status-message status-success">
                    <strong>服务器运行中</strong><br>
                    地址: ${config.host}:${config.port}<br>
                    双向认证: ${config.mutual_auth ? '启用' : '禁用'}
                </div>
            `;
        } else if (!running) {
            statusDiv.innerHTML = '';
        }
    }

    updateClientUI(connected, config = null) {
        const connectBtn = document.getElementById('connect-client-btn');
        const disconnectBtn = document.getElementById('disconnect-client-btn');
        const statusDiv = document.getElementById('client-status');

        connectBtn.disabled = connected;
        disconnectBtn.disabled = !connected;

        if (connected && config) {
            statusDiv.innerHTML = `
                <div class="status-message status-success">
                    <strong>已连接到服务器</strong><br>
                    地址: ${config.host}:${config.port}<br>
                    客户端证书: ${config.client_cert ? '使用' : '未使用'}<br>
                    服务器验证: ${config.verify_server ? '启用' : '禁用'}
                </div>
            `;
        } else if (!connected) {
            statusDiv.innerHTML = '';
        }
    }

    showMessagePanel(show) {
        const panel = document.getElementById('message-panel');
        panel.style.display = show ? 'block' : 'none';
        
        if (show) {
            panel.classList.add('fade-in');
        }
    }

    addMessageToLog(message, type) {
        const logContainer = document.getElementById('message-log');
        const timestamp = new Date().toLocaleTimeString();
        
        const logEntry = document.createElement('div');
        logEntry.className = `log-entry log-${type}`;
        logEntry.innerHTML = `
            <div class="log-timestamp">${timestamp}</div>
            <div>${message}</div>
        `;
        
        logContainer.appendChild(logEntry);
        logContainer.scrollTop = logContainer.scrollHeight;
    }

    showMessage(message, type) {
        // 可以用模态框或toast显示消息
        console.log(`${type.toUpperCase()}: ${message}`);
        
        // 简单的alert替代方案
        const alertClass = type === 'success' ? 'alert-success' : 
                          type === 'error' ? 'alert-danger' : 'alert-info';
        
        const alertDiv = document.createElement('div');
        alertDiv.className = `alert ${alertClass} alert-dismissible fade show position-fixed`;
        alertDiv.style.cssText = 'top: 20px; right: 20px; z-index: 1050; max-width: 300px;';
        alertDiv.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        
        document.body.appendChild(alertDiv);
        
        // 5秒后自动移除
        setTimeout(() => {
            if (alertDiv.parentNode) {
                alertDiv.parentNode.removeChild(alertDiv);
            }
        }, 5000);
    }

    showLoading(message) {
        // 简单的加载提示
        console.log(`Loading: ${message}`);
    }

    hideLoading() {
        // 隐藏加载提示
    }

    formatFileSize(bytes) {
        if (bytes === 0) return '0 B';
        const k = 1024;
        const sizes = ['B', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }
}

// 全局函数
function loadCertificates() {
    app.loadCertificates();
}

function sendMessage() {
    app.sendMessage();
}

// 初始化应用
let app;
document.addEventListener('DOMContentLoaded', () => {
    app = new SSLSocketApp();
});