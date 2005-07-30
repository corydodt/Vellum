"""Utility class for the controller"""
from gtkmvc import controller

class SilentController(controller.Controller):
    """Controller that auto-implements change_notification
    handlers and discards the changes.
    """
    def __getattr__(self, name):
        if (name.startswith("property_") and
            name.endswith("_change_notification")):
            return self.eatNotification
        raise AttributeError(name)

    def eatNotification(self, model, old, new):
        pass


