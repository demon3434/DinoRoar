# 宝塔云 WAF 与 Nginx 流媒体代理优化配置规范

本项目大文件媒体资源（音频、视频等）由后端动态分发接口 `/api/attachments/download/{uuid}` 提供，并在外网通过 Nginx WAF 网关服务器进行 HTTPS 反向代理映射。

为了防止 Android 端在外网播放视频及语音时发生严重卡顿、无法加载的问题，反代服务器的 Nginx 必须做好流媒体优化与 WAF 豁免配置。本篇文档记录优化原理与详细的 Nginx 配置，以便未来查阅参考。

---

## 1. 核心优化原理

### 1.1 绕过全局 WAF 响应体过滤器 (关键性能点)
宝塔云 WAF（或其它基于 LuaJIT 的 Nginx 防火墙）通常会全局引入响应体审查过滤器（如 `body_filter_by_lua_file`），用于过滤敏感词、回显 SQL/XSS 攻击等。
* **危害**：当客户端请求大体积的流媒体（如几 MB 到几十 MB 的视频）时，所有的响应分包都会被传入 Lua 脚本在内存中进行全量正则扫描。这不仅会让服务器 CPU 跑满，还会造成巨大的网络阻断与传输卡顿。
* **解决办法**：在媒体相关的 `location` 块中，只声明空的 `header_filter_by_lua_block { }` 和 `body_filter_by_lua_block { }`，以覆盖并屏蔽全局的响应过滤，使流媒体直接"穿透"传输。

> ⚠️ **【已确认 BUG - 2026-07-20】禁止使用 `access_by_lua_block { ngx.exit(ngx.OK) }`**：
> 经 `curl -v` 实测，该指令在宝塔云 WAF 环境下会导致每次请求产生**两次 TLS 重协商（SSL Renegotiation）**，外网视频附件首字节延迟高达 10 多秒。
> **请只使用 `header_filter_by_lua_block { }` 和 `body_filter_by_lua_block { }` 来绕过响应过滤，严禁添加 `access_by_lua_block`。**

### 1.2 禁用代理缓冲区 (Proxy Buffering)
Nginx 默认会开启 `proxy_buffering on;`。在大文件下载或视频播放时，Nginx 会尝试将后端服务器返回的字节全量拉取并缓存到本地磁盘的临时文件夹中，然后由 Nginx 慢慢发送给客户端。
* **危害**：这会导致极大的首字节延迟，并且容易因磁盘 I/O 拥堵或临时文件写满而导致客户端连接超时中断。
* **解决办法**：对音视频分发接口强制配置 `proxy_buffering off;` 和 `proxy_request_buffering off;`，使数据实现零延迟直接转发。

### 1.3 支持 HTTP Range 范围请求 (206 断点续传)
Android 端播放器（如 MediaPlayer, ExoPlayer）拉取视频时，会自动发送带 `Range: bytes=0-` 的分片请求。
* **要求**：Nginx 反代必须正确将客户端的 `Range` 及 `If-Range` 头部透传给后端，且绝不能随意篡改或过滤后端的 `206 Partial Content` 状态，确保支持流媒体的进度条拖动与分块加载。

---

## 2. 优化后的虚拟主机配置明细

配置文件路径：`/www/cloud_waf/nginx/conf.d/vhost/dinoroar_your_domain_com_0.conf`
以下为对流媒体相关 `location` 的具体配置要求：

### 2.1 针对后端动态分发路由的配置
```nginx
# 媒体下载接口：进行 WAF 豁免及代理缓冲禁用
location /api/attachments/download/ {
    # 1. 覆盖并屏蔽全局的 WAF Lua 响应过滤器
    # ⚠️ 严禁使用 access_by_lua_block { ngx.exit(ngx.OK) }，已确认触发两次 TLS 重协商！
    header_filter_by_lua_block { }
    body_filter_by_lua_block { }

    # 2. 反向代理到后端容器
    proxy_pass http://dinoroar_backend_upstream;
    proxy_http_version 1.1;
    proxy_set_header Connection "";
    proxy_set_header Host $host_optimize;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
    proxy_set_header Cookie $http_cookie;

    # 3. 强力透传 Range 分片头部
    proxy_set_header Range $http_range;
    proxy_set_header If-Range $http_if_range;

    # 4. 关闭缓冲，实现数据实时下发
    proxy_buffering off;
    proxy_request_buffering off;

    # 5. 放宽大文件传输的超时限制，防止慢速网络下被 Nginx 强行斩断
    proxy_connect_timeout 600s;
    proxy_send_timeout 600s;
    proxy_read_timeout 600s;
    client_max_body_size 0;
}
```

### 2.2 针对静态音视频后缀的配置
若有客户端直接通过静态路径访问媒体文件，同样需要加入相同的覆盖策略：
```nginx
# 音频/视频 - 文件后缀匹配与优化
location ~* \.(mp4|webm|ogg|ogv|mov|avi|wmv|flv|m3u8|ts|mp3|wav|aac|flac|opus)$ {
    # 覆盖并绕过 WAF Lua 响应过滤器（禁止加 access_by_lua_block，会触发 TLS 重协商！）
    header_filter_by_lua_block { }
    body_filter_by_lua_block { }

    proxy_pass http://dinoroar_backend_upstream;
    proxy_http_version 1.1;
    proxy_set_header Connection "";
    proxy_set_header Host $host_optimize;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
    proxy_set_header Cookie $http_cookie;
    
    proxy_set_header Range $http_range;
    proxy_set_header If-Range $http_if_range;

    proxy_buffering off;
    proxy_request_buffering off;
    proxy_connect_timeout 600s;
    proxy_send_timeout 600s;
    proxy_read_timeout 600s;
    client_max_body_size 0;

    gzip off;
    expires 30d;
    add_header Cache-Control "public";
    add_header Accept-Ranges bytes;
}
```

### 2.3 重载生效命令
修改完成并确保语法测试通过后，重载容器内 Nginx 配置：
```bash
# 语法检测
docker exec cloudwaf_nginx nginx -t

# 重新加载
docker exec cloudwaf_nginx nginx -s reload
```
