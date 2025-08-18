# AI陪伴功能模块部署指南

## 概述

本指南将帮助您部署AI陪伴功能模块到生产环境。该模块包含完整的后端API、前端界面和设备端集成。

## 系统要求

### 硬件要求
- **服务器**: 2核CPU，4GB内存，50GB存储
- **数据库**: MySQL 8.0+
- **网络**: 稳定的网络连接

### 软件要求
- **操作系统**: Linux (Ubuntu 20.04+ 推荐)
- **Java**: OpenJDK 11+
- **Node.js**: 16+
- **Python**: 3.8+
- **MySQL**: 8.0+

## 部署步骤

### 1. 数据库部署

#### 1.1 创建数据库
```sql
CREATE DATABASE xiaozhi_ai_companion CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

#### 1.2 执行数据库脚本
```bash
# 进入项目目录
cd /path/to/xiaozhi-esp32-server-chenzhi

# 执行数据库脚本
mysql -u root -p xiaozhi_ai_companion < main/manager-api/src/main/resources/db/changelog/20241201_001_create_ai_scenario_tables.sql
```

#### 1.3 验证数据库表
```sql
USE xiaozhi_ai_companion;
SHOW TABLES;
-- 应该看到以下表：
-- ai_scenario
-- ai_scenario_step
-- ai_step_template
-- ai_child_learning_record
```

### 2. 后端API部署

#### 2.1 编译打包
```bash
# 进入后端项目目录
cd main/manager-api

# 清理并编译
mvn clean package -DskipTests

# 检查生成的jar文件
ls -la target/*.jar
```

#### 2.2 配置环境变量
```bash
# 创建配置文件
cat > application-prod.yml << EOF
spring:
  datasource:
    url: jdbc:mysql://localhost:3306/xiaozhi_ai_companion?useUnicode=true&characterEncoding=utf8&useSSL=false&serverTimezone=Asia/Shanghai
    username: your_db_username
    password: your_db_password
    driver-class-name: com.mysql.cj.jdbc.Driver
  
  redis:
    host: localhost
    port: 6379
    password: your_redis_password
    
server:
  port: 8002
  
logging:
  level:
    xiaozhi: INFO
    root: WARN
EOF
```

#### 2.3 启动后端服务
```bash
# 使用生产配置启动
java -jar target/manager-api.jar --spring.profiles.active=prod

# 或者使用nohup后台运行
nohup java -jar target/manager-api.jar --spring.profiles.active=prod > api.log 2>&1 &
```

#### 2.4 验证API服务
```bash
# 测试API健康检查
curl http://localhost:8002/actuator/health

# 测试场景API
curl http://localhost:8002/xiaozhi/scenario/list
```

### 3. 前端部署

#### 3.1 安装依赖
```bash
# 进入前端项目目录
cd main/manager-web

# 安装依赖
npm install

# 或者使用yarn
yarn install
```

#### 3.2 配置环境变量
```bash
# 创建生产环境配置文件
cat > .env.production << EOF
VUE_APP_API_BASE_URL=http://localhost:8002
VUE_APP_TITLE=AI陪伴系统
EOF
```

#### 3.3 构建生产版本
```bash
# 构建生产版本
npm run build

# 检查构建结果
ls -la dist/
```

#### 3.4 部署到Web服务器

##### 使用Nginx部署
```bash
# 安装Nginx
sudo apt update
sudo apt install nginx

# 配置Nginx
sudo tee /etc/nginx/sites-available/xiaozhi-ai-companion << EOF
server {
    listen 80;
    server_name your-domain.com;
    
    root /var/www/xiaozhi-ai-companion;
    index index.html;
    
    location / {
        try_files \$uri \$uri/ /index.html;
    }
    
    location /api/ {
        proxy_pass http://localhost:8002/;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
    }
}
EOF

# 创建网站目录
sudo mkdir -p /var/www/xiaozhi-ai-companion

# 复制构建文件
sudo cp -r dist/* /var/www/xiaozhi-ai-companion/

# 启用站点
sudo ln -s /etc/nginx/sites-available/xiaozhi-ai-companion /etc/nginx/sites-enabled/

# 测试配置
sudo nginx -t

# 重启Nginx
sudo systemctl restart nginx
```

### 4. 设备端部署

#### 4.1 安装Python依赖
```bash
# 进入设备端项目目录
cd main/xiaozhi-server

# 安装依赖
pip install -r requirements.txt

# 或者手动安装主要依赖
pip install aiohttp httpx asyncio websockets
```

#### 4.2 配置设备端
```bash
# 创建配置文件
cat > config_from_api.yaml << EOF
manager_api_url: http://localhost:8002
device_id: your_device_id
device_name: AI陪伴设备
log_level: INFO
EOF
```

#### 4.3 启动设备端服务
```bash
# 启动服务
python app.py

# 或者使用nohup后台运行
nohup python app.py > device.log 2>&1 &
```

### 5. 监控和日志

#### 5.1 配置日志
```bash
# 创建日志目录
sudo mkdir -p /var/log/xiaozhi-ai-companion

# 配置日志轮转
sudo tee /etc/logrotate.d/xiaozhi-ai-companion << EOF
/var/log/xiaozhi-ai-companion/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 644 root root
}
EOF
```

#### 5.2 配置监控
```bash
# 安装监控工具
sudo apt install htop iotop

# 创建监控脚本
cat > monitor.sh << 'EOF'
#!/bin/bash
echo "=== AI陪伴系统监控 ==="
echo "时间: $(date)"
echo "CPU使用率: $(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | cut -d'%' -f1)%"
echo "内存使用率: $(free | grep Mem | awk '{printf "%.2f", $3/$2 * 100.0}')%"
echo "磁盘使用率: $(df / | tail -1 | awk '{print $5}')"
echo "API服务状态: $(curl -s -o /dev/null -w "%{http_code}" http://localhost:8002/actuator/health)"
echo "前端服务状态: $(curl -s -o /dev/null -w "%{http_code}" http://localhost/)"
EOF

chmod +x monitor.sh
```

## 验证部署

### 1. 功能验证

#### 1.1 测试API接口
```bash
# 测试场景API
curl -X GET "http://localhost:8002/xiaozhi/scenario/list" \
  -H "Content-Type: application/json"

# 测试步骤模板API
curl -X GET "http://localhost:8002/xiaozhi/step-template/list" \
  -H "Content-Type: application/json"

# 测试学习记录API
curl -X GET "http://localhost:8002/xiaozhi/learning-record/list" \
  -H "Content-Type: application/json"
```

#### 1.2 测试前端界面
```bash
# 访问前端界面
curl -I http://localhost/

# 检查JavaScript文件
curl -I http://localhost/js/app.js
```

#### 1.3 测试设备端
```bash
# 检查设备端日志
tail -f device.log

# 测试WebSocket连接
curl -i -N -H "Connection: Upgrade" \
  -H "Upgrade: websocket" \
  -H "Sec-WebSocket-Version: 13" \
  -H "Sec-WebSocket-Key: SGVsbG8sIHdvcmxkIQ==" \
  http://localhost:8001/
```

### 2. 性能测试

#### 2.1 API性能测试
```bash
# 使用ab进行压力测试
ab -n 1000 -c 10 http://localhost:8002/xiaozhi/scenario/list

# 使用wrk进行更详细的测试
wrk -t12 -c400 -d30s http://localhost:8002/xiaozhi/scenario/list
```

#### 2.2 数据库性能测试
```sql
-- 检查数据库性能
EXPLAIN SELECT * FROM ai_scenario WHERE is_active = 1;

-- 检查索引使用情况
SHOW INDEX FROM ai_scenario;
```

## 故障排除

### 常见问题

#### 1. API服务无法启动
```bash
# 检查端口占用
netstat -tlnp | grep 8002

# 检查Java进程
ps aux | grep java

# 查看错误日志
tail -f api.log
```

#### 2. 数据库连接失败
```bash
# 检查MySQL服务状态
sudo systemctl status mysql

# 检查数据库连接
mysql -u root -p -e "SHOW DATABASES;"

# 检查防火墙
sudo ufw status
```

#### 3. 前端无法访问
```bash
# 检查Nginx状态
sudo systemctl status nginx

# 检查Nginx配置
sudo nginx -t

# 检查网站文件
ls -la /var/www/xiaozhi-ai-companion/
```

#### 4. 设备端连接失败
```bash
# 检查Python进程
ps aux | grep python

# 检查设备端日志
tail -f device.log

# 检查网络连接
ping localhost
```

### 日志分析

#### 1. 查看错误日志
```bash
# 查看API错误日志
grep ERROR api.log

# 查看设备端错误日志
grep ERROR device.log

# 查看Nginx错误日志
sudo tail -f /var/log/nginx/error.log
```

#### 2. 性能分析
```bash
# 查看系统资源使用
htop

# 查看磁盘I/O
iotop

# 查看网络连接
netstat -tlnp
```

## 维护和更新

### 1. 定期维护

#### 1.1 数据库维护
```sql
-- 优化数据库
OPTIMIZE TABLE ai_scenario;
OPTIMIZE TABLE ai_scenario_step;
OPTIMIZE TABLE ai_step_template;
OPTIMIZE TABLE ai_child_learning_record;

-- 清理旧数据
DELETE FROM ai_child_learning_record WHERE created_at < DATE_SUB(NOW(), INTERVAL 1 YEAR);
```

#### 1.2 日志清理
```bash
# 清理旧日志
find /var/log/xiaozhi-ai-companion -name "*.log" -mtime +30 -delete

# 压缩日志
gzip /var/log/xiaozhi-ai-companion/*.log
```

### 2. 系统更新

#### 2.1 代码更新
```bash
# 拉取最新代码
git pull origin main

# 重新编译后端
cd main/manager-api
mvn clean package -DskipTests

# 重新构建前端
cd ../manager-web
npm run build

# 重启服务
sudo systemctl restart xiaozhi-api
sudo systemctl restart nginx
```

#### 2.2 数据库迁移
```bash
# 执行数据库迁移脚本
mysql -u root -p xiaozhi_ai_companion < migration_script.sql
```

## 安全考虑

### 1. 网络安全
```bash
# 配置防火墙
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw allow 8002/tcp
sudo ufw enable
```

### 2. 数据库安全
```sql
-- 创建专用数据库用户
CREATE USER 'xiaozhi_user'@'localhost' IDENTIFIED BY 'strong_password';
GRANT SELECT, INSERT, UPDATE, DELETE ON xiaozhi_ai_companion.* TO 'xiaozhi_user'@'localhost';
FLUSH PRIVILEGES;
```

### 3. API安全
```bash
# 配置HTTPS
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d your-domain.com
```

## 备份和恢复

### 1. 数据库备份
```bash
# 创建备份脚本
cat > backup.sh << 'EOF'
#!/bin/bash
BACKUP_DIR="/backup/xiaozhi-ai-companion"
DATE=$(date +%Y%m%d_%H%M%S)
mkdir -p $BACKUP_DIR

# 备份数据库
mysqldump -u root -p xiaozhi_ai_companion > $BACKUP_DIR/db_backup_$DATE.sql

# 备份配置文件
cp -r /etc/xiaozhi-ai-companion $BACKUP_DIR/config_$DATE

# 压缩备份
tar -czf $BACKUP_DIR/backup_$DATE.tar.gz $BACKUP_DIR/db_backup_$DATE.sql $BACKUP_DIR/config_$DATE

# 清理旧备份
find $BACKUP_DIR -name "backup_*.tar.gz" -mtime +7 -delete
EOF

chmod +x backup.sh
```

### 2. 系统恢复
```bash
# 恢复数据库
mysql -u root -p xiaozhi_ai_companion < backup/db_backup_20241201_120000.sql

# 恢复配置文件
cp -r backup/config_20241201_120000/* /etc/xiaozhi-ai-companion/
```

## 总结

通过以上步骤，您应该能够成功部署AI陪伴功能模块。部署完成后，请进行全面的功能测试和性能测试，确保系统正常运行。

如果遇到问题，请参考故障排除部分或联系技术支持团队。

---

**部署完成时间**: 2024年12月
**版本**: v1.0
**维护团队**: xiaozhi开发组
