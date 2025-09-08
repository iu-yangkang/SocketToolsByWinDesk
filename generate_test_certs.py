#!/usr/bin/env python3
"""
生成测试用的SSL证书
用于演示SSL Socket工具的功能
"""

import os
import datetime
import ipaddress
from cryptography import x509
from cryptography.x509.oid import NameOID
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization

def generate_private_key():
    """生成RSA私钥"""
    return rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
    )

def generate_ca_certificate():
    """生成CA证书"""
    # 生成CA私钥
    ca_key = generate_private_key()
    
    # 创建CA证书
    subject = issuer = x509.Name([
        x509.NameAttribute(NameOID.COUNTRY_NAME, "CN"),
        x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, "Beijing"),
        x509.NameAttribute(NameOID.LOCALITY_NAME, "Beijing"),
        x509.NameAttribute(NameOID.ORGANIZATION_NAME, "SSL Tools Test CA"),
        x509.NameAttribute(NameOID.COMMON_NAME, "SSL Tools Root CA"),
    ])
    
    cert = x509.CertificateBuilder().subject_name(
        subject
    ).issuer_name(
        issuer
    ).public_key(
        ca_key.public_key()
    ).serial_number(
        x509.random_serial_number()
    ).not_valid_before(
        datetime.datetime.now(datetime.UTC)
    ).not_valid_after(
        datetime.datetime.now(datetime.UTC) + datetime.timedelta(days=365)
    ).add_extension(
        x509.SubjectAlternativeName([
            x509.DNSName("localhost"),
            x509.IPAddress(ipaddress.ip_address("127.0.0.1")),
        ]),
        critical=False,
    ).add_extension(
        x509.BasicConstraints(ca=True, path_length=None),
        critical=True,
    ).add_extension(
        x509.KeyUsage(
            digital_signature=True,
            key_cert_sign=True,
            crl_sign=True,
            key_encipherment=False,
            data_encipherment=False,
            key_agreement=False,
            encipher_only=False,
            decipher_only=False,
            content_commitment=False,
        ),
        critical=True,
    ).sign(ca_key, hashes.SHA256())
    
    return ca_key, cert

def generate_server_certificate(ca_key, ca_cert):
    """生成服务器证书"""
    # 生成服务器私钥
    server_key = generate_private_key()
    
    # 创建服务器证书
    subject = x509.Name([
        x509.NameAttribute(NameOID.COUNTRY_NAME, "CN"),
        x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, "Beijing"),
        x509.NameAttribute(NameOID.LOCALITY_NAME, "Beijing"),
        x509.NameAttribute(NameOID.ORGANIZATION_NAME, "SSL Tools Test"),
        x509.NameAttribute(NameOID.COMMON_NAME, "localhost"),
    ])
    
    cert = x509.CertificateBuilder().subject_name(
        subject
    ).issuer_name(
        ca_cert.issuer
    ).public_key(
        server_key.public_key()
    ).serial_number(
        x509.random_serial_number()
    ).not_valid_before(
        datetime.datetime.now(datetime.UTC)
    ).not_valid_after(
        datetime.datetime.now(datetime.UTC) + datetime.timedelta(days=365)
    ).add_extension(
        x509.SubjectAlternativeName([
            x509.DNSName("localhost"),
            x509.DNSName("*.localhost"),
            x509.IPAddress(ipaddress.ip_address("127.0.0.1")),
            x509.IPAddress(ipaddress.ip_address("::1")),
        ]),
        critical=False,
    ).add_extension(
        x509.BasicConstraints(ca=False, path_length=None),
        critical=True,
    ).add_extension(
        x509.KeyUsage(
            digital_signature=True,
            key_encipherment=True,
            data_encipherment=False,
            key_agreement=False,
            key_cert_sign=False,
            crl_sign=False,
            encipher_only=False,
            decipher_only=False,
            content_commitment=False,
        ),
        critical=True,
    ).add_extension(
        x509.ExtendedKeyUsage([
            x509.oid.ExtendedKeyUsageOID.SERVER_AUTH,
        ]),
        critical=True,
    ).sign(ca_key, hashes.SHA256())
    
    return server_key, cert

def generate_client_certificate(ca_key, ca_cert):
    """生成客户端证书"""
    # 生成客户端私钥
    client_key = generate_private_key()
    
    # 创建客户端证书
    subject = x509.Name([
        x509.NameAttribute(NameOID.COUNTRY_NAME, "CN"),
        x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, "Beijing"),
        x509.NameAttribute(NameOID.LOCALITY_NAME, "Beijing"),
        x509.NameAttribute(NameOID.ORGANIZATION_NAME, "SSL Tools Test"),
        x509.NameAttribute(NameOID.COMMON_NAME, "Test Client"),
    ])
    
    cert = x509.CertificateBuilder().subject_name(
        subject
    ).issuer_name(
        ca_cert.issuer
    ).public_key(
        client_key.public_key()
    ).serial_number(
        x509.random_serial_number()
    ).not_valid_before(
        datetime.datetime.now(datetime.UTC)
    ).not_valid_after(
        datetime.datetime.now(datetime.UTC) + datetime.timedelta(days=365)
    ).add_extension(
        x509.BasicConstraints(ca=False, path_length=None),
        critical=True,
    ).add_extension(
        x509.KeyUsage(
            digital_signature=True,
            key_encipherment=True,
            data_encipherment=False,
            key_agreement=False,
            key_cert_sign=False,
            crl_sign=False,
            encipher_only=False,
            decipher_only=False,
            content_commitment=False,
        ),
        critical=True,
    ).add_extension(
        x509.ExtendedKeyUsage([
            x509.oid.ExtendedKeyUsageOID.CLIENT_AUTH,
        ]),
        critical=True,
    ).sign(ca_key, hashes.SHA256())
    
    return client_key, cert

def save_certificate_and_key(cert, key, cert_filename, key_filename, directory="certificates"):
    """保存证书和私钥到文件"""
    os.makedirs(directory, exist_ok=True)
    
    # 保存证书
    cert_path = os.path.join(directory, cert_filename)
    with open(cert_path, "wb") as f:
        f.write(cert.public_bytes(serialization.Encoding.PEM))
    
    # 保存私钥
    key_path = os.path.join(directory, key_filename)
    with open(key_path, "wb") as f:
        f.write(key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        ))
    
    return cert_path, key_path

def main():
    """生成测试证书"""
    print("生成SSL测试证书...")
    
    # 生成CA证书
    print("1. 生成CA证书...")
    ca_key, ca_cert = generate_ca_certificate()
    ca_cert_path, ca_key_path = save_certificate_and_key(
        ca_cert, ca_key, "ca_test_ca.pem", "key_test_ca_key.pem"
    )
    print(f"   CA证书: {ca_cert_path}")
    print(f"   CA私钥: {ca_key_path}")
    
    # 生成服务器证书
    print("2. 生成服务器证书...")
    server_key, server_cert = generate_server_certificate(ca_key, ca_cert)
    server_cert_path, server_key_path = save_certificate_and_key(
        server_cert, server_key, "cert_test_server.pem", "key_test_server_key.pem"
    )
    print(f"   服务器证书: {server_cert_path}")
    print(f"   服务器私钥: {server_key_path}")
    
    # 生成客户端证书
    print("3. 生成客户端证书...")
    client_key, client_cert = generate_client_certificate(ca_key, ca_cert)
    client_cert_path, client_key_path = save_certificate_and_key(
        client_cert, client_key, "client_cert_test_client.pem", "client_key_test_client_key.pem"
    )
    print(f"   客户端证书: {client_cert_path}")
    print(f"   客户端私钥: {client_key_path}")
    
    print("\n证书生成完成！")
    print("\n使用说明:")
    print("1. 单向认证 (服务器认证):")
    print("   - 服务器使用: test_server.pem + test_server_key.pem")
    print("   - 客户端使用: test_ca.pem (验证服务器)")
    print()
    print("2. 双向认证 (相互认证):")
    print("   - 服务器使用: test_server.pem + test_server_key.pem + test_ca.pem")
    print("   - 客户端使用: test_client.pem + test_client_key.pem + test_ca.pem")

if __name__ == "__main__":
    main()