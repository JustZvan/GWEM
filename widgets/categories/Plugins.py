from PySide6 import QtWidgets
from widgets.installable_widget import InstallableWidget
from widgets.version_manager_widget import VersionManagerWidget
from plugin_manager import plugin_manager
from ..FlowLayout import FlowLayout


class Plugins(QtWidgets.QStackedWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.container = QtWidgets.QWidget()
        self.layout = FlowLayout()
        self.container.setLayout(self.layout)
        self.addWidget(self.container)

        self.plugin_widgets = {}
        self.plugin_version_managers = {}

        self._load_plugin_widgets()

    def _load_plugin_widgets(self):
        """Load widgets for all available plugins"""
        plugin_apps = plugin_manager.get_plugin_apps()

        for plugin_name, apps in plugin_apps.items():
            for app_instance in apps:
                self._create_widget_for_app(app_instance, plugin_name)

    def _create_widget_for_app(self, app_instance, plugin_name):
        """Create a widget for a plugin app instance"""
        # Try to get a readable name for the app
        app_display_name = getattr(app_instance, "display_name", None)
        if not app_display_name:
            app_display_name = getattr(
                app_instance, "app_name", app_instance.__class__.__name__
            )

        # Try to get a description for the app
        app_description = getattr(
            app_instance, "description", f"Plugin from {plugin_name}"
        )

        widget_key = f"{plugin_name}_{app_instance.__class__.__name__}"

        # Check if this is a ManagedApp or NonManagedApp
        is_managed_app = hasattr(app_instance, "is_installed")

        if is_managed_app:
            # ManagedApp - has version management
            widget = InstallableWidget(
                title=app_display_name,
                description=app_description,
                installed=app_instance.is_installed,
                on_install=lambda app=app_instance, widget_key=widget_key: self._handle_managed_app_install(
                    app, widget_key
                ),
                on_manage_versions=lambda app=app_instance, name=app_display_name: self._handle_manage_versions(
                    app, name
                ),
                show_success_message=False,
            )

            # Create version manager for managed apps
            version_manager = VersionManagerWidget(
                app_instance, app_display_name, parent=self
            )
            self.plugin_version_managers[widget_key] = version_manager

        else:
            # NonManagedApp - simple install only
            widget = InstallableWidget(
                title=app_display_name,
                description=app_description,
                installed=False,  # NonManagedApps don't track installation state
                on_install=lambda app=app_instance: self._handle_non_managed_app_install(
                    app
                ),
                show_success_message=True,
            )

        self.plugin_widgets[widget_key] = {
            "widget": widget,
            "app_instance": app_instance,
            "plugin_name": plugin_name,
            "is_managed": is_managed_app,
        }

        self.layout.addWidget(widget)

    def _handle_managed_app_install(self, app_instance, widget_key):
        """Handle installation for managed apps"""
        try:
            app_instance.install()
            # Update widget state
            if widget_key in self.plugin_widgets:
                widget_info = self.plugin_widgets[widget_key]
                widget_info["widget"].set_installed(app_instance.is_installed)
        except Exception as e:
            print(f"Error installing {app_instance.__class__.__name__}: {e}")

    def _handle_non_managed_app_install(self, app_instance):
        """Handle installation for non-managed apps"""
        try:
            app_instance.install()
        except Exception as e:
            print(f"Error installing {app_instance.__class__.__name__}: {e}")

    def _handle_manage_versions(self, app_instance, app_name):
        """Show version manager for managed apps"""
        for widget_key, version_manager in self.plugin_version_managers.items():
            widget_info = self.plugin_widgets.get(widget_key)
            if widget_info and widget_info["app_instance"] == app_instance:
                version_manager.show_manager()
                break

    def _handle_app_install(self, app_instance, widget, app_name):
        """Generic handler for app installation with version selection"""
        try:
            app_instance.install()
            widget.set_installed(app_instance.is_installed)
            widget.show_success(f"{app_name} installed successfully!")
        except Exception as e:
            print(f"Error installing {app_name}: {e}")
            widget.show_error(f"Failed to install {app_name}: {str(e)}")

    def _handle_app_uninstall(self, app_instance, widget, description):
        """Generic handler for app uninstallation"""
        try:
            app_instance.uninstall()
            widget.set_installed(False)
            widget.description_label.setText(description)
        except Exception as e:
            print(f"Error uninstalling {app_instance.__class__.__name__}: {e}")

    def refresh_plugins(self):
        """Refresh the plugin widgets by reloading plugins"""
        # Clear existing widgets
        for widget_info in self.plugin_widgets.values():
            widget_info["widget"].setParent(None)

        self.plugin_widgets.clear()
        self.plugin_version_managers.clear()

        # Reload plugins
        plugin_manager.reload_plugins()

        # Recreate widgets
        self._load_plugin_widgets()

    def get_plugin_info(self):
        """Get information about loaded plugins"""
        return plugin_manager.get_plugin_info()
