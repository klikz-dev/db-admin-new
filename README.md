# New DB Admin

## Prerequisites

### Django Setup

https://www.digitalocean.com/community/tutorials/how-to-install-the-django-web-framework-on-ubuntu-22-04

### Django Deployment

https://www.digitalocean.com/community/tutorials/how-to-serve-django-applications-with-apache-and-mod_wsgi-on-ubuntu-14-04

### Let's encrypt

https://www.digitalocean.com/community/tutorials/how-to-secure-apache-with-let-s-encrypt-on-ubuntu-20-04

### Apache Config

```
<VirtualHost *:80>
    ServerName www.decoratorsbestam.com
</VirtualHost>

<VirtualHost _default_:443>
    ServerAdmin murrell@decoratorsbest.com

    ErrorLog ${APACHE_LOG_DIR}/error.log
    CustomLog ${APACHE_LOG_DIR}/access.log combined

    ServerName www.decoratorsbestam.com

    Alias /static /home/ubuntu/admin/admin/static
    <Directory /home/ubuntu/admin/admin/static>
        Require all granted
    </Directory>

    <Directory /home/ubuntu/admin/admin/admin>
        <Files wsgi.py>
            Require all granted
        </Files>
    </Directory>

    WSGIDaemonProcess admin python-path=/home/ubuntu/admin/admin python-home=/home/ubuntu/admin/adminenv
    WSGIProcessGroup admin
    WSGIScriptAlias / /home/ubuntu/admin/admin/admin/wsgi.py

</VirtualHost>
```

## FTP Setup

### Create FTP User

1. sudo adduser username
2. sudo mkdir /var/sftp/username
3. sudo chown root: /var/sftp/username
4. Update /etc/ssh/sshd_config file
5. sudo service sshd restart
6. sudo mkdir /var/sftp/username/username
7. sudo chown username: /var/sftp/username/username

### SSH Config (/etc/ssh/sshd_config)

```
Match User username
ForceCommand internal-sftp
PasswordAuthentication yes
ChrootDirectory /var/sftp/username
PermitTunnel no
AllowAgentForwarding no
AllowTcpForwarding no
X11Forwarding no
```
