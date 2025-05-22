nssm stop SrvMonExporter
nssm remove SrvMonExporter confirm
netsh advfirewall firewall delete rule name="TCP_8911"
