from . import install

class debian_installer(install.installer):
    def update_command(self):
        return "apt-get update"


    def install_local_packages_command(self):
        return "apt-get install -fy"


    def install_official_packages_command(self):
        return "apt-get install -y"


    def filename_extension(self):
        return 'deb'


    def version_joinery(self):
        return '='

