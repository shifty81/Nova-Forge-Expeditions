"""
Installer Builder — stubs for Windows installers and portable packages.
"""
from pathlib import Path
from tools.zip_tools import ZipTools


class InstallerBuilder:
    """Stubs for creating Windows installers and portable packages."""

    def __init__(self):
        self._zip = ZipTools()

    def create_nsis_installer(self, app_name, version, source_dir, output_path):
        script = self.generate_nsis_script(app_name, version, source_dir,
                                           f"C:\\Program Files\\{app_name}")
        nsi_path = Path(output_path).with_suffix(".nsi")
        nsi_path.parent.mkdir(parents=True, exist_ok=True)
        nsi_path.write_text(script, encoding="utf-8")
        print(f"[InstallerBuilder] NSIS script -> {nsi_path}")
        return str(nsi_path)

    def create_portable_zip(self, source_dir, app_name, version, output_dir):
        out = self._zip.create_release_zip(source_dir, version, output_dir)
        print(f"[InstallerBuilder] portable zip -> {out}")
        return out

    def create_msi(self, app_name, version, source_dir, output_path):
        print(f"[InstallerBuilder] MSI {app_name} v{version} -> {output_path} (stub)")
        return output_path

    def sign_exe(self, exe_path, cert_path, cert_password=""):
        print(f"[InstallerBuilder] sign {exe_path} with {cert_path} (stub)")
        return exe_path

    def generate_nsis_script(self, app_name, version, source_dir, install_dir):
        return (
            f'; NSIS installer for {app_name} v{version}\n'
            f'!define APPNAME "{app_name}"\n'
            f'!define VERSION "{version}"\n'
            f'!define INSTALLDIR "{install_dir}"\n'
            f'\n'
            f'Name "${{APPNAME}} ${{VERSION}}"\n'
            f'OutFile "{app_name}-{version}-setup.exe"\n'
            f'InstallDir "${{INSTALLDIR}}"\n'
            f'\n'
            f'Section "MainSection" SEC01\n'
            f'  SetOutPath "$INSTDIR"\n'
            f'  File /r "{source_dir}\\*.*"\n'
            f'SectionEnd\n'
        )
