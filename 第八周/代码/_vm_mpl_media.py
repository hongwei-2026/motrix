#!/usr/bin/env python3
import io, paramiko
c=paramiko.SSHClient();c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect('42.123.114.169',32222,'root+vm-2GrY70fHwbyk1FTe',os.environ.get("MOTRIX_SSH_PASS", ""),timeout=45,allow_agent=False,look_for_keys=False)
_,o,e=c.exec_command('export PATH=/root/.local/bin:/usr/bin:/bin; cd /root/work/MotrixLab; uv pip install matplotlib pillow -i https://pypi.tuna.tsinghua.edu.cn/simple && .venv/bin/python /tmp/_make_media.py', timeout=300, get_pty=True)
print((o.read()+e.read()).decode(errors='replace')[-5000:])
print('exit', o.channel.recv_exit_status())
c.close()
