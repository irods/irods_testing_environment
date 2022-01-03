from . import install

class ubuntu_installer(install.installer):
    def update_command(self):
        return 'apt update'


    def install_local_packages_command(self):
        return 'apt install -fy'


    def install_official_packages_command(self):
        return 'apt install -y'


    def filename_extension(self):
        return 'deb'


    def version_joinery(self):
        return '='

