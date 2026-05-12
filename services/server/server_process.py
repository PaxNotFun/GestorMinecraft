import re
import subprocess
import sys
import threading
from collections import deque
from pathlib import Path

from .server_data import accept_eula, load_server_config

if sys.platform == "win32":
    import ctypes
    from ctypes import wintypes


    class IO_COUNTERS(ctypes.Structure):
        _fields_ = [('ReadOperationCount', ctypes.c_ulonglong), ('WriteOperationCount', ctypes.c_ulonglong),
                    ('OtherOperationCount', ctypes.c_ulonglong), ('ReadTransferCount', ctypes.c_ulonglong),
                    ('WriteTransferCount', ctypes.c_ulonglong), ('OtherTransferCount', ctypes.c_ulonglong)]


    class JOBOBJECT_EXTENDED_LIMIT_INFORMATION(ctypes.Structure):
        class _JOBOBJECT_BASIC_LIMIT_INFORMATION(ctypes.Structure):
            _fields_ = [('PerProcessUserTimeLimit', wintypes.LARGE_INTEGER),
                        ('PerJobUserTimeLimit', wintypes.LARGE_INTEGER), ('LimitFlags', wintypes.DWORD),
                        ('MinimumWorkingSetSize', ctypes.c_size_t), ('MaximumWorkingSetSize', ctypes.c_size_t),
                        ('ActiveProcessLimit', wintypes.DWORD), ('Affinity', ctypes.c_size_t),
                        ('PriorityClass', wintypes.DWORD), ('SchedulingClass', wintypes.DWORD)]

        _fields_ = [('BasicLimitInformation', _JOBOBJECT_BASIC_LIMIT_INFORMATION), ('IoInfo', IO_COUNTERS),
                    ('ProcessMemoryLimit', ctypes.c_size_t), ('JobMemoryLimit', ctypes.c_size_t),
                    ('PeakProcessMemoryUsed', ctypes.c_size_t), ('PeakJobMemoryUsed', ctypes.c_size_t)]
        JobObjectExtendedLimitInformation = 9


class ServerManager:
    def __init__(self, server_info, console_update_callback, status_update_callback, on_kill_ready_callback):
        self.server_info = server_info
        self.server_path = Path(server_info['path'])
        self.java_executable = server_info.get("java_executable", "java")
        self.jar_file = server_info.get("jar_file", "server.jar")
        self.history = deque(maxlen=2000)
        welcome_msg = f"━━━ Panel de Control: {self.server_info['name']} ━━━\n\n"
        self.history.append(welcome_msg)
        self._current_console_callback = console_update_callback
        self.status_update_callback = status_update_callback
        self.on_kill_ready_callback = on_kill_ready_callback
        self.process = None
        self.is_running = False
        self.kill_timer = None
        self.job_handle = None
        self.process_handle = None
        self._init_job_object()

    def _init_job_object(self):
        if sys.platform == "win32":
            try:
                self.job_handle = ctypes.windll.kernel32.CreateJobObjectW(None, None)
                info = JOBOBJECT_EXTENDED_LIMIT_INFORMATION()
                info.BasicLimitInformation.LimitFlags = 0x2000
                ctypes.windll.kernel32.SetInformationJobObject(self.job_handle, 9, ctypes.byref(info),
                                                               ctypes.sizeof(JOBOBJECT_EXTENDED_LIMIT_INFORMATION))
            except Exception:
                pass

    def log_output(self, text):
        self.history.append(text)
        if self._current_console_callback:
            try:
                self._current_console_callback(text)
            except Exception:
                pass

    def set_console_callback(self, new_callback):
        self._current_console_callback = new_callback

    def get_history(self):
        return "".join(self.history)

    def start(self):
        if self.is_running:
            self.log_output("El servidor ya está encendido.\n")
            return

        local_config = load_server_config(self.server_path)
        min_ram = local_config.get("min_ram", "2G")
        max_ram = local_config.get("max_ram", "4G")
        custom_args = local_config.get("jvm_args", "")
        use_aikar_flags = local_config.get("use_aikar_flags", False)

        try:
            if accept_eula(self.server_path):
                self.log_output("EULA Aceptado.\n")
        except Exception as e:
            self.log_output(f"❌ Error EULA: {e}\n")
            return

        # CONSTRUCCIÓN INTELIGENTE DEL COMANDO
        command = self._build_start_command(min_ram, max_ram, custom_args, use_aikar_flags)

        if not command:
            self.log_output("❌ Error: No se pudo construir el comando de inicio.\n")
            return

        try:
            full_cmd_str = " ".join(command)
            self.log_output(f"🚀 Ejecutando: {full_cmd_str}\n\n")

            creation_flags = 0
            if sys.platform == "win32":
                creation_flags = subprocess.CREATE_NO_WINDOW | subprocess.CREATE_NEW_PROCESS_GROUP

            self.process = subprocess.Popen(
                command,
                cwd=str(self.server_path),
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True, encoding='utf-8', errors='replace', bufsize=1,
                creationflags=creation_flags
            )
            self.is_running = True

            if self.job_handle and sys.platform == "win32":
                try:
                    p_handle = ctypes.windll.kernel32.OpenProcess(0x1F0FFF, False, self.process.pid)
                    ctypes.windll.kernel32.AssignProcessToJobObject(self.job_handle, p_handle)
                except:
                    pass

            self.status_update_callback(True)
            threading.Thread(target=self._read_output, daemon=True).start()

        except Exception as e:
            self.log_output(f"❌ Error al iniciar: {e}\n")
            self._cleanup_and_reset_status()

    def _build_start_command(self, min_ram, max_ram, custom_args, use_aikar_flags=False):
        """
        Construye el comando de inicio basándose en el tipo de servidor y lanzamiento.
        Returns: lista con el comando completo o None si hay error
        """
        server_type = self.server_info.get("type")
        forge_launch_type = self.server_info.get("forge_launch_type")
        forge_args_file = self.server_info.get("forge_args_file")

        # CASO ESPECIAL: Forge sin forge_launch_type (servidores antiguos)
        # Detectar en tiempo de ejecución
        if server_type == "Forge" and not forge_launch_type:
            forge_launch_type, forge_args_file = self._detect_forge_type_at_runtime()

        # CASO 1: FORGE MODERNO (1.17+)
        if server_type == "Forge" and forge_launch_type == "modern":
            return self._build_modern_forge_command(min_ram, max_ram, custom_args, forge_args_file, use_aikar_flags)

        # CASO 2: FORGE LEGACY (<=1.16.5) O CUALQUIER OTRO SERVIDOR
        else:
            return self._build_standard_jar_command(min_ram, max_ram, custom_args, use_aikar_flags)

    def _build_modern_forge_command(self, min_ram, max_ram, custom_args, forge_args_file, use_aikar_flags=False):
        """Construye el comando para Forge moderno (sistema de argumentos @)."""
        if not forge_args_file:
            self.log_output("❌ Error: Forge moderno detectado pero falta forge_args_file.\n")
            return None

        args_file_path = self.server_path / forge_args_file

        if not args_file_path.exists():
            self.log_output(f"❌ Error: No se encuentra el archivo de argumentos: {forge_args_file}\n")
            return None

        # Crear user_jvm_args.txt con los argumentos personalizados
        jvm_args_path = self.server_path / 'user_jvm_args.txt'

        try:
            with open(jvm_args_path, 'w', encoding='utf-8') as f:
                f.write(f"-Xms{min_ram}\n")
                f.write(f"-Xmx{max_ram}\n")

                if use_aikar_flags:
                    for flag in self._get_aikar_flags():
                        f.write(f"{flag}\n")

                if custom_args:
                    # Separar argumentos personalizados línea por línea
                    for arg in custom_args.split():
                        f.write(f"{arg}\n")
        except Exception as e:
            self.log_output(f"❌ Error al crear user_jvm_args.txt: {e}\n")
            return None

        # Construir comando con referencias @
        command = [
            self.java_executable,
            f"@{jvm_args_path.name}",  # @user_jvm_args.txt
            f"@{forge_args_file}",  # @libraries/.../win_args.txt
            "nogui"
        ]

        return command

    def _detect_forge_type_at_runtime(self):
        """
        Detecta el tipo de Forge en tiempo de ejecución para servidores ya instalados.
        Basado en el script de Pterodactyl.
        Returns: (forge_launch_type, forge_args_file) o (None, None)
        """
        args_filename = "win_args.txt" if sys.platform == "win32" else "unix_args.txt"

        # Buscar el archivo de argumentos en libraries/net/minecraftforge/forge/
        forge_libs_path = self.server_path / 'libraries' / 'net' / 'minecraftforge' / 'forge'

        if forge_libs_path.exists():
            # Buscar recursivamente el archivo de argumentos
            args_files = list(forge_libs_path.rglob(args_filename))

            if args_files:
                # Encontramos archivo de argumentos -> Forge Moderno
                args_file = args_files[0]  # Tomar el primero encontrado
                relative_path = args_file.relative_to(self.server_path)
                return ("modern", str(relative_path).replace('\\', '/'))

        # Si no encontramos archivo de argumentos, es Forge Legacy
        return ("legacy", None)

    def _build_standard_jar_command(self, min_ram, max_ram, custom_args, use_aikar_flags=False):
        """Construye el comando estándar con -jar para servidores normales o Forge legacy."""
        jar_file = self.jar_file

        # Si no hay jar_file especificado, intentar detectarlo
        if not jar_file:
            jar_file = self._find_server_jar()

            if not jar_file:
                self.log_output("❌ Error: No se pudo encontrar ningún archivo JAR en el directorio.\n")
                return None

        jar_path = self.server_path / jar_file

        if not jar_path.exists():
            self.log_output(f"❌ Error: No se encuentra el archivo JAR: {jar_file}\n")
            return None

        # Verificar que sea un archivo JAR válido
        if not jar_file.endswith('.jar'):
            self.log_output(f"❌ Error: '{jar_file}' no es un archivo JAR válido.\n")
            return None

        # Construir comando: RAM primero
        command = [
            self.java_executable,
            f'-Xms{min_ram}',
            f'-Xmx{max_ram}'
        ]

        # Aikar's flags van después de RAM (no incluyen -Xms/-Xmx para evitar duplicados)
        if use_aikar_flags:
            command.extend(self._get_aikar_flags())

        # Argumentos personalizados del usuario
        if custom_args:
            command.extend(custom_args.split())

        # JAR y modo nogui al final
        command.extend(['-jar', jar_file, 'nogui'])

        return command

    @staticmethod
    def _get_aikar_flags():
        """
        Retorna las Aikar's Flags optimizadas para servidores Minecraft.
        Fuente: https://aikar.co/mcflags.html
        No incluye -Xms/-Xmx ya que se pasan por separado.
        """
        return [
            '-XX:+UseG1GC',
            '-XX:+ParallelRefProcEnabled',
            '-XX:MaxGCPauseMillis=200',
            '-XX:+UnlockExperimentalVMOptions',
            '-XX:+DisableExplicitGC',
            '-XX:+AlwaysPreTouch',
            '-XX:G1NewSizePercent=30',
            '-XX:G1MaxNewSizePercent=40',
            '-XX:G1HeapRegionSize=8M',
            '-XX:G1ReservePercent=20',
            '-XX:G1HeapWastePercent=5',
            '-XX:G1MixedGCCountTarget=4',
            '-XX:InitiatingHeapOccupancyPercent=15',
            '-XX:G1MixedGCLiveThresholdPercent=90',
            '-XX:G1RSetUpdatingPauseTimePercent=5',
            '-XX:SurvivorRatio=32',
            '-XX:+PerfDisableSharedMem',
            '-XX:MaxTenuringThreshold=1',
            '-Dusing.aikars.flags=https://mcflags.emc.gs',
            '-Daikars.new.flags=true',
        ]

    def _find_server_jar(self):
        """
        Busca un archivo JAR de servidor en el directorio.
        Prioriza server.jar, luego forge-*.jar, luego cualquier .jar
        Returns: nombre del archivo o None
        """
        # Prioridad 1: server.jar
        if (self.server_path / 'server.jar').exists():
            return 'server.jar'

        # Prioridad 2: Buscar forge-*.jar (para Forge Legacy)
        server_type = self.server_info.get("type")
        mc_version = self.server_info.get("version", "")

        if server_type == "Forge" and mc_version:
            forge_jar_pattern = re.compile(rf"forge-.*{re.escape(mc_version)}-.*\.jar$", re.IGNORECASE)

            for jar_file in self.server_path.glob('*.jar'):
                if forge_jar_pattern.search(jar_file.name):
                    # Priorizar el que contiene "universal"
                    if "universal" in jar_file.name.lower():
                        return jar_file.name
                    # Si no hay universal, retornar el primero que encontremos
                    return jar_file.name

        # Prioridad 3: Cualquier JAR que no sea installer.jar
        for jar_file in self.server_path.glob('*.jar'):
            if jar_file.name not in ['installer.jar', 'forge-installer.jar']:
                return jar_file.name

        return None

    def _read_output(self):
        if not self.process: return
        for line in iter(self.process.stdout.readline, ''):
            self.log_output(line)
        self.process.wait()
        self.log_output("\n--- Servidor detenido ---\n")
        self.is_running = False
        if self.kill_timer: self.kill_timer.cancel()
        self.status_update_callback(False)
        self._cleanup_handles()

    def send_command(self, command):
        if self.is_running and self.process:
            try:
                self.log_output(f"> {command}\n")
                self.process.stdin.write(command + '\n')
                self.process.stdin.flush()
            except Exception as e:
                self.log_output(f"Error comando: {e}\n")

    def stop(self):
        if self.is_running:
            self.send_command("stop")
            self.kill_timer = threading.Timer(15.0, lambda: self.on_kill_ready_callback() if self.is_running else None)
            self.kill_timer.start()

    def kill(self):
        if self.process:
            self.process.kill()
        self.is_running = False

    def _cleanup_and_reset_status(self):
        self.is_running = False
        self.status_update_callback(False)
        self._cleanup_handles()

    def _cleanup_handles(self):
        if sys.platform == "win32" and self.process_handle:
            ctypes.windll.kernel32.CloseHandle(self.process_handle)
            self.process_handle = None