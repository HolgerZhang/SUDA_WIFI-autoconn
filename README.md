## SUDA_WIFI Automatically Connect

SUDA_WIFI 网关自动登录程序

#### 环境要求

- Windows | Linux 操作系统
- Python 3，装有 requests （若不存在，装有 pip 时会自动下载）
- Linux 系统装有 net-tools 

~~~shell
# 'ifconfig' can be installed with:
sudo apt install net-tools      # Ubuntu (Debian)
sudo yum install net-tools      # CentOS (Red Hat)
~~~

#### 配置 `config.json` 

格式要求：

~~~json
{
  "student_id": "填写网关账号",
  "password": "填写网关密码",
  "type": 0 | 1,  // 0 - 校园网；1 - 中国移动
  "index": 0  // 你的 IP 在“获得的IP地址”列表中的下标索引，默认为0可以满足大多数场景
}
~~~

#### 开始运行

运行 `main.py` 即可。

Windows 下可以将 `main.py` 扩展名更改为  `pyw` 来忽略运行时的黑框。

