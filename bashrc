# .bashrc

# Source global definitions
if [ -f /etc/bashrc ]; then
	. /etc/bashrc
fi

# User specific environment
PATH="$HOME/.local/bin:$HOME/bin:$PATH"
export PATH

# Uncomment the following line if you don't like systemctl's auto-paging feature:
# export SYSTEMD_PAGER=

# User specific aliases and functions

export PATH=$PATH:/home/admin/ansible-helper
export HELPER_PATH=/home/admin/db-host-prep/playbooks:/home/admin/couchbase-init/playbooks:/home/admin/general-admin/playbooks
export PS1="[\u@perfctl:\w]\$ "

# Check for interactive shell
if [ -z "$PS1" ]; then
   return
fi

eval "$(ssh-agent -s)"

ssh-add .ssh/adminkey
