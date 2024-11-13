from . import install


class centos_installer(install.installer):
    def update_command(self):
        return "yum update -y"

    def install_local_packages_command(self):
        return "yum --nogpgcheck -y install"

    def install_official_packages_command(self):
        return "yum -y install"

    def filename_extension(self):
        return "rpm"

    def version_joinery(self):
        return "-"
