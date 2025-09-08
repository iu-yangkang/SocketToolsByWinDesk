# SSL Socket 工具

一个功能完整的SSL Socket工具，支持双向认证、单向认证，允许用户上传自定义证书。

## 功能特性

- ✅ **SSL服务器**: 支持启动SSL服务器，可配置单向或双向认证
- ✅ **SSL客户端**: 支持连接到SSL服务器，可选择验证服务器证书
- ✅ **证书管理**: 上传、验证、管理SSL证书文件
- ✅ **双向认证**: 支持客户端和服务器相互验证证书
- ✅ **单向认证**: 仅验证服务器证书的标准SSL连接
- ✅ **实时通信**: 通过SSL连接发送和接收消息
- ✅ **Web界面**: 直观的Web管理界面
- ✅ **日志记录**: 详细的连接和操作日志

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 生成测试证书

```bash
python generate_test_certs.py
```

这将在 `certificates/` 目录下生成以下测试证书：
- `ca_test_ca.pem` - CA根证书
- `cert_test_server.pem` - 服务器证书
- `client_cert_test_client.pem` - 客户端证书
- 对应的私钥文件

### 3. 启动应用

```bash
python app.py
```

访问 http://localhost:5000 打开Web界面。

## 使用指南

### 证书管理

1. **上传证书**: 在左侧面板上传你的SSL证书文件
2. **文件类型**: 支持 `.pem`, `.crt`, `.key`, `.p12`, `.pfx` 格式
3. **自动验证**: 系统会自动验证证书的有效性和类型

### SSL服务器

1. **基础配置**: 设置监听主机和端口
2. **证书选择**: 选择服务器证书和私钥
3. **双向认证**: 勾选"要求客户端证书"并选择CA证书
4. **启动服务**: 点击"启动服务器"开始监听连接

### SSL客户端

1. **连接配置**: 设置目标服务器地址和端口
2. **服务器验证**: 选择是否验证服务器证书
3. **客户端证书**: 可选择使用客户端证书进行双向认证
4. **建立连接**: 点击"连接服务器"建立SSL连接
5. **消息测试**: 连接成功后可发送测试消息

## 认证模式

### 单向认证 (Server Authentication)

- 服务器提供证书，客户端验证服务器身份
- 适用于大多数Web应用场景
- 配置简单，只需服务器证书

**服务器配置**:
- 服务器证书: `cert_test_server.pem`
- 服务器私钥: `key_test_server_key.pem`
- 不勾选"要求客户端证书"

**客户端配置**:
- 勾选"验证服务器证书"
- CA证书: `ca_test_ca.pem` (可选，使用自签名证书时需要)

### 双向认证 (Mutual Authentication)

- 服务器和客户端都提供证书，相互验证身份
- 适用于高安全要求的应用
- 需要完整的PKI证书链

**服务器配置**:
- 服务器证书: `cert_test_server.pem`
- 服务器私钥: `key_test_server_key.pem`
- 勾选"要求客户端证书"
- CA证书: `ca_test_ca.pem`

**客户端配置**:
- 勾选"验证服务器证书"
- 勾选"使用客户端证书"
- 客户端证书: `client_cert_test_client.pem`
- 客户端私钥: `client_key_test_client_key.pem`
- CA证书: `ca_test_ca.pem`

## API 接口

### 证书管理
- `POST /api/upload-certificate` - 上传证书文件
- `GET /api/list-certificates` - 获取证书列表

### 服务器控制
- `POST /api/start-server` - 启动SSL服务器
- `POST /api/stop-server` - 停止SSL服务器

### 客户端控制
- `POST /api/connect-client` - 连接SSL服务器
- `POST /api/disconnect-client` - 断开连接
- `POST /api/send-message` - 发送消息

### 状态查询
- `GET /api/status` - 获取系统状态

## 项目结构

```
├── app.py                 # 主应用文件
├── requirements.txt       # Python依赖
├── generate_test_certs.py # 测试证书生成工具
├── templates/
│   └── index.html        # Web界面模板
├── static/
│   ├── css/
│   │   └── style.css     # 样式文件
│   └── js/
│       └── app.js        # 前端JavaScript
├── certificates/         # 证书存储目录
└── logs/                 # 日志目录
```

## 安全注意事项

1. **生产环境**: 请使用正式的CA签发的证书，不要使用测试证书
2. **私钥保护**: 确保私钥文件的安全，设置适当的文件权限
3. **证书验证**: 在生产环境中务必启用证书验证
4. **网络安全**: 在不安全的网络环境中使用SSL/TLS加密

## 故障排除

### 常见错误

1. **证书格式错误**: 确保证书文件是PEM格式
2. **私钥不匹配**: 检查证书和私钥是否匹配
3. **CA证书缺失**: 双向认证时确保提供正确的CA证书
4. **端口占用**: 检查端口是否被其他程序占用
5. **权限问题**: 确保有读取证书文件的权限

### 调试信息

- 查看浏览器控制台的JavaScript错误
- 检查 `logs/ssl_tools.log` 日志文件
- 使用 `openssl` 命令验证证书文件

## 开发

### 本地开发

```bash
# 安装开发依赖
pip install -r requirements.txt

# 生成测试证书
python generate_test_certs.py

# 启动开发服务器
python app.py
```

### 生产部署

```bash
# 使用Gunicorn部署
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

## 许可证

MIT License