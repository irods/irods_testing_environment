#! /bin/bash
set -e

setup_input_file=/irods_setup.input

if [ -e "${setup_input_file}" ]; then
    python /var/lib/irods/scripts/setup_irods.py < "${setup_input_file}"
    rm /irods_setup.input
fi

cd /usr/sbin
su irods -c 'bash -c "./irodsServer -u"'
