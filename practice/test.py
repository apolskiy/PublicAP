
import sys


#and then changes internal hostname to the value of targethostname
from EstablishSSHConnection import *

hostname = str(sys.argv[1])
sshuser = str(sys.argv[2])
sshk = str(sys.argv[3])

sconn = EstablishSSHConn(hostname,sshuser,sshk)
time.sleep(10)
ipad6 = str(GetHostIP6SSH(sconn)).strip('\n')