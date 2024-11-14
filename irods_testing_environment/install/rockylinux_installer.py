from . import install


class rockylinux_installer(install.installer):
    def update_command(self):
        return "dnf update -y"

    def install_local_packages_command(self):
        return "dnf --nogpgcheck -y install"

    def install_official_packages_command(self):
        return "dnf -y install"

    def filename_extension(self):
        return "rpm"

    def version_joinery(self):
        return "-"
