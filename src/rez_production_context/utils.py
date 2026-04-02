class NoInheritInstanceCheck(type):
    def __instancecheck__(cls, instance):
        return type(instance) is cls
