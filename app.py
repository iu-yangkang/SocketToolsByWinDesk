#!/usr/bin/env python3
"""
SSL Socket Tools - 支持双向认证和单向认证的SSL Socket工具
"""

import os
import ssl
import socket
import threading
import json
from datetime import datetime
from flask import Flask, render_template, request, jsonify, send_from_directory
from flask_cors import CORS
from werkzeug.utils import secure_filename
import logging
from cryptography import x509
from cryptography.hazmat.backends import default_backend
import OpenSSL.crypto

app = Flask(__name__)
CORS(app)

# 配置
UPLOAD_FOLDER = 'certificates'
ALLOWED_EXTENSIONS = {'pem', 'crt', 'key', 'p12', 'pfx'}
MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_CONTENT_LENGTH

# 确保证书目录存在
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs('logs', exist_ok=True)

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/ssl_tools.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

class SSLSocketServer:
    """SSL Socket 服务器类"""
    
    def __init__(self, host='localhost', port=8443):
        self.host = host
        self.port = port
        self.server_socket = None
        self.running = False
        self.clients = []
        
    def load_certificates(self, cert_file, key_file, ca_file=None, require_client_cert=False):
        """加载SSL证书"""
        try:
            context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
            context.load_cert_chain(cert_file, key_file)
            
            if require_client_cert and ca_file:
                context.load_verify_locations(ca_file)
                context.verify_mode = ssl.CERT_REQUIRED
            else:
                context.verify_mode = ssl.CERT_NONE
                
            return context
        except Exception as e:
            logger.error(f"证书加载失败: {e}")
            return None
    
    def start_server(self, cert_file, key_file, ca_file=None, require_client_cert=False):
        """启动SSL服务器"""
        try:
            context = self.load_certificates(cert_file, key_file, ca_file, require_client_cert)
            if not context:
                return False
                
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.bind((self.host, self.port))
            self.server_socket.listen(5)
            
            # 包装为SSL socket
            self.server_socket = context.wrap_socket(self.server_socket, server_side=True)
            self.running = True
            
            logger.info(f"SSL服务器启动在 {self.host}:{self.port}")
            logger.info(f"双向认证: {'启用' if require_client_cert else '禁用'}")
            
            return True
        except Exception as e:
            logger.error(f"服务器启动失败: {e}")
            return False
    
    def handle_client(self, client_socket, client_address):
        """处理客户端连接"""
        try:
            logger.info(f"客户端连接: {client_address}")
            
            # 获取客户端证书信息（如果有）
            try:
                peer_cert = client_socket.getpeercert()
                if peer_cert:
                    logger.info(f"客户端证书: {peer_cert.get('subject', 'Unknown')}")
            except:
                logger.info("无客户端证书")
            
            while self.running:
                try:
                    data = client_socket.recv(1024)
                    if not data:
                        break
                    
                    message = data.decode('utf-8')
                    logger.info(f"收到消息: {message}")
                    
                    # 回显消息
                    response = f"服务器回应: {message} (时间: {datetime.now()})"
                    client_socket.send(response.encode('utf-8'))
                    
                except socket.timeout:
                    continue
                except Exception as e:
                    logger.error(f"处理客户端数据错误: {e}")
                    break
                    
        except Exception as e:
            logger.error(f"客户端处理错误: {e}")
        finally:
            client_socket.close()
            logger.info(f"客户端断开: {client_address}")
    
    def accept_connections(self):
        """接受客户端连接"""
        while self.running:
            try:
                client_socket, client_address = self.server_socket.accept()
                client_thread = threading.Thread(
                    target=self.handle_client, 
                    args=(client_socket, client_address)
                )
                client_thread.daemon = True
                client_thread.start()
                self.clients.append(client_thread)
            except Exception as e:
                if self.running:
                    logger.error(f"接受连接错误: {e}")
                break
    
    def stop_server(self):
        """停止服务器"""
        self.running = False
        if self.server_socket:
            self.server_socket.close()
        logger.info("SSL服务器已停止")

class SSLSocketClient:
    """SSL Socket 客户端类"""
    
    def __init__(self):
        self.socket = None
        self.connected = False
        
    def connect(self, host, port, cert_file=None, key_file=None, ca_file=None, verify_server=True):
        """连接到SSL服务器"""
        try:
            context = ssl.create_default_context()
            
            if not verify_server:
                context.check_hostname = False
                context.verify_mode = ssl.CERT_NONE
            elif ca_file:
                context.load_verify_locations(ca_file)
            
            if cert_file and key_file:
                context.load_cert_chain(cert_file, key_file)
                logger.info("客户端证书已加载")
            
            # 创建socket并连接
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket = context.wrap_socket(sock, server_hostname=host if verify_server else None)
            self.socket.connect((host, port))
            self.connected = True
            
            logger.info(f"已连接到SSL服务器 {host}:{port}")
            
            # 获取服务器证书信息
            server_cert = self.socket.getpeercert()
            if server_cert:
                logger.info(f"服务器证书: {server_cert.get('subject', 'Unknown')}")
            
            return True
        except Exception as e:
            logger.error(f"连接失败: {e}")
            return False
    
    def send_message(self, message):
        """发送消息"""
        if not self.connected or not self.socket:
            return False
        try:
            self.socket.send(message.encode('utf-8'))
            response = self.socket.recv(1024)
            return response.decode('utf-8')
        except Exception as e:
            logger.error(f"发送消息失败: {e}")
            return None
    
    def disconnect(self):
        """断开连接"""
        if self.socket:
            self.socket.close()
            self.connected = False
            logger.info("已断开SSL连接")

# 全局变量
ssl_server = None
ssl_client = SSLSocketClient()

def allowed_file(filename):
    """检查文件扩展名"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def validate_certificate(cert_path):
    """验证证书文件"""
    try:
        with open(cert_path, 'rb') as f:
            cert_data = f.read()
        
        # 尝试解析为X.509证书
        try:
            cert = x509.load_pem_x509_certificate(cert_data, default_backend())
            return {
                'valid': True,
                'type': 'X.509',
                'subject': str(cert.subject),
                'issuer': str(cert.issuer),
                'not_before': cert.not_valid_before.isoformat(),
                'not_after': cert.not_valid_after.isoformat()
            }
        except:
            # 尝试解析为私钥
            try:
                from cryptography.hazmat.primitives import serialization
                key = serialization.load_pem_private_key(cert_data, password=None, backend=default_backend())
                return {
                    'valid': True,
                    'type': 'Private Key',
                    'algorithm': key.__class__.__name__
                }
            except:
                return {'valid': False, 'error': '无法解析证书文件'}
    except Exception as e:
        return {'valid': False, 'error': str(e)}

@app.route('/')
def index():
    """主页"""
    return render_template('index.html')

@app.route('/api/upload-certificate', methods=['POST'])
def upload_certificate():
    """上传证书文件"""
    if 'file' not in request.files:
        return jsonify({'success': False, 'error': '没有选择文件'})
    
    file = request.files['file']
    cert_type = request.form.get('type', 'cert')
    
    if file.filename == '':
        return jsonify({'success': False, 'error': '没有选择文件'})
    
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        # 添加类型前缀避免冲突
        filename = f"{cert_type}_{filename}"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        # 验证证书
        validation = validate_certificate(filepath)
        
        return jsonify({
            'success': True,
            'filename': filename,
            'path': filepath,
            'validation': validation
        })
    
    return jsonify({'success': False, 'error': '不支持的文件类型'})

@app.route('/api/list-certificates')
def list_certificates():
    """列出已上传的证书"""
    try:
        files = []
        for filename in os.listdir(app.config['UPLOAD_FOLDER']):
            if allowed_file(filename):
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                stat = os.stat(filepath)
                validation = validate_certificate(filepath)
                files.append({
                    'filename': filename,
                    'size': stat.st_size,
                    'modified': datetime.fromtimestamp(stat.st_mtime).isoformat(),
                    'validation': validation
                })
        return jsonify({'success': True, 'files': files})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/start-server', methods=['POST'])
def start_server():
    """启动SSL服务器"""
    global ssl_server
    
    try:
        data = request.json
        host = data.get('host', 'localhost')
        port = int(data.get('port', 8443))
        cert_file = data.get('cert_file')
        key_file = data.get('key_file')
        ca_file = data.get('ca_file')
        require_client_cert = data.get('require_client_cert', False)
        
        if not cert_file or not key_file:
            return jsonify({'success': False, 'error': '需要提供服务器证书和私钥'})
        
        # 构建完整路径
        cert_path = os.path.join(app.config['UPLOAD_FOLDER'], cert_file)
        key_path = os.path.join(app.config['UPLOAD_FOLDER'], key_file)
        ca_path = os.path.join(app.config['UPLOAD_FOLDER'], ca_file) if ca_file else None
        
        # 检查文件存在
        if not os.path.exists(cert_path) or not os.path.exists(key_path):
            return jsonify({'success': False, 'error': '证书文件不存在'})
        
        if ca_file and not os.path.exists(ca_path):
            return jsonify({'success': False, 'error': 'CA证书文件不存在'})
        
        # 停止现有服务器
        if ssl_server:
            ssl_server.stop_server()
        
        # 启动新服务器
        ssl_server = SSLSocketServer(host, port)
        if ssl_server.start_server(cert_path, key_path, ca_path, require_client_cert):
            # 在后台线程中接受连接
            server_thread = threading.Thread(target=ssl_server.accept_connections)
            server_thread.daemon = True
            server_thread.start()
            
            return jsonify({
                'success': True,
                'message': f'SSL服务器已启动在 {host}:{port}',
                'config': {
                    'host': host,
                    'port': port,
                    'mutual_auth': require_client_cert
                }
            })
        else:
            return jsonify({'success': False, 'error': '服务器启动失败'})
            
    except Exception as e:
        logger.error(f"启动服务器错误: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/stop-server', methods=['POST'])
def stop_server():
    """停止SSL服务器"""
    global ssl_server
    
    try:
        if ssl_server:
            ssl_server.stop_server()
            ssl_server = None
            return jsonify({'success': True, 'message': 'SSL服务器已停止'})
        else:
            return jsonify({'success': False, 'error': '服务器未运行'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/connect-client', methods=['POST'])
def connect_client():
    """客户端连接到SSL服务器"""
    try:
        data = request.json
        host = data.get('host', 'localhost')
        port = int(data.get('port', 8443))
        cert_file = data.get('cert_file')
        key_file = data.get('key_file')
        ca_file = data.get('ca_file')
        verify_server = data.get('verify_server', True)
        
        # 构建文件路径
        cert_path = os.path.join(app.config['UPLOAD_FOLDER'], cert_file) if cert_file else None
        key_path = os.path.join(app.config['UPLOAD_FOLDER'], key_file) if key_file else None
        ca_path = os.path.join(app.config['UPLOAD_FOLDER'], ca_file) if ca_file else None
        
        # 断开现有连接
        ssl_client.disconnect()
        
        # 建立新连接
        if ssl_client.connect(host, port, cert_path, key_path, ca_path, verify_server):
            return jsonify({
                'success': True,
                'message': f'已连接到 {host}:{port}',
                'config': {
                    'host': host,
                    'port': port,
                    'client_cert': bool(cert_file),
                    'verify_server': verify_server
                }
            })
        else:
            return jsonify({'success': False, 'error': '连接失败'})
            
    except Exception as e:
        logger.error(f"客户端连接错误: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/send-message', methods=['POST'])
def send_message():
    """发送消息到SSL服务器"""
    try:
        data = request.json
        message = data.get('message', '')
        
        if not ssl_client.connected:
            return jsonify({'success': False, 'error': '客户端未连接'})
        
        response = ssl_client.send_message(message)
        if response:
            return jsonify({
                'success': True,
                'sent': message,
                'received': response
            })
        else:
            return jsonify({'success': False, 'error': '发送失败'})
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/disconnect-client', methods=['POST'])
def disconnect_client():
    """断开客户端连接"""
    try:
        ssl_client.disconnect()
        return jsonify({'success': True, 'message': '客户端已断开连接'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/status')
def get_status():
    """获取系统状态"""
    return jsonify({
        'server_running': ssl_server is not None and ssl_server.running,
        'client_connected': ssl_client.connected,
        'certificates_count': len([f for f in os.listdir(app.config['UPLOAD_FOLDER']) if allowed_file(f)]) if os.path.exists(app.config['UPLOAD_FOLDER']) else 0
    })

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)