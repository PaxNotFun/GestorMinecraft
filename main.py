"""
Gestor de Servidores Minecraft
Punto de entrada de la aplicación
"""
from core.app import App


def main():
    """Función principal."""
    app = App()
    app.run()


if __name__ == "__main__":
    main()