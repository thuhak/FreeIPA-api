#Free IPA api

> 对Free IPA的进一步封装


## 认证

使用Http Basic认证，填入用户名密码


## 配置

默认的配置文件是/etc/ipa/api.yml

```yaml
ipa:
  domain: abc.com
  default_server: ldap
  user: ipa.useradm@ABC.COM
  keytab: /etc/ipa/useradmin.keytab

api:
  user: test
  password: test
```

### 配置解释

- ipa
    - domain: ipa的域名
    - default_server: 默认连接的ipa服务器，如果该服务器无法访问，则会自动切换至/etc/ipa/default.conf中xmlrpc_uri所指向的服务器
    - user: api所使用的ipa用户名，需要有对应的权限
    - keytab: 用户对应的keytab, 可以使用`ipa-getkeytab -p user@domain -k keytab -e aes256-cts-hmac-sha1-96`
导出用户的keytab,导出以后，用户的密码会被随机重置而不可用
- api
    - user: basic auth的用户
    - password: basic auth的密码



## API

### User

#### 查询用户的属性

- URL: /user/<string: username>
- 方法: GET

##### 举例

```cmd
curl -u user:pass 127.0.0.1:5000/user/username
```

##### 返回

- 200: 成功，并包含用户信息
- 403：用户不存在
- 500：其他类型异常

#### 添加用户或重置密码

如果不存在用户，添加并设置密码，如果存在用户，则直接重置密码

- URL: /user/<string: username>
- 方法: POST
- 参数(json)：
    - password(str): 密码

##### 举例

```cmd
curl -H "Content-Type: application/json" -XPOST 127.0.0.1:5000/user/username --data '{"password":"12345678"}'
```

##### 返回

- 200: 成功
- 400：json的参数异常
- 500：ipa后端调用失败或者其他异常

#### 删除

- URL: /user/<string: username>
- 方法: DELETE

##### 举例

```cmd
curl -u user:pass -XDELETE 127.0.0.1:5000/user/username
```

##### 返回

- 200: 成功，并包含用户信息
- 403：用户不存在
- 500：其他类型异常
