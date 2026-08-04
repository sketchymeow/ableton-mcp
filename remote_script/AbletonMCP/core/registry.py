"""Single source of truth for command dispatch."""


class CommandError(Exception):
    """Raised by handlers for expected failures. Reported to the client as-is."""

    def __init__(self, message, error_type="command_error"):
        super(CommandError, self).__init__(message)
        self.error_type = error_type


class Registry:
    def __init__(self):
        self._commands = {}

    def register(self, name, handler):
        if name in self._commands:
            raise ValueError("duplicate command: %s" % name)
        self._commands[name] = handler

    def register_all(self, handlers):
        for name, handler in handlers.items():
            self.register(name, handler)

    @property
    def command_names(self):
        return sorted(self._commands)

    def dispatch(self, name, params):
        try:
            handler = self._commands[name]
        except KeyError:
            raise CommandError(
                "unknown command %r; valid commands: %s"
                % (name, ", ".join(self.command_names)),
                error_type="unknown_command",
            )
        return handler(params or {})
