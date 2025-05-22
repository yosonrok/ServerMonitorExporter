nssm install SrvMonExporter "D:\SrvMonExporter\SrvMonExporter.exe"
netsh advfirewall firewall add rule name="TCP_8911" dir=in action=allow protocol=TCP localport=8911 remoteip=210.242.75.66,210.242.75.77,210.242.171.0/24
nssm start SrvMonExporter