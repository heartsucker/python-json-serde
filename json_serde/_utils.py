class AbsentType:

    """Type to represent a missing value where ``None`` would be ambiguous."""

    __INSTANCE = None

    def __new__(cls):
        if cls.__INSTANCE is None:
            cls.__INSTANCE = super().__new__(cls)
        return cls.__INSTANCE

    def __bool__(self) -> bool:
        return False

    def __repr__(self) -> str:
        return "Absent"

    def __str__(self) -> str:
        return repr(self)


Absent = AbsentType()
Absent.__doc__ = AbsentType.__doc__
