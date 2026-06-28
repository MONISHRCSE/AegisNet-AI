@load protocols/conn
@load protocols/http
@load protocols/dns
@load protocols/ssh
@load protocols/mysql
@load protocols/ftp

# Export logs in JSON format for easier parsing
redef LogAscii::use_json = T;
