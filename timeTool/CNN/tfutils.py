"""
Script for tensorflow utility functions and classes 
"""
import logging
from functools import wraps

import tensorflow as tf

logger = logging.getLogger(__name__)

def doublewrap(function):
    """A decorator decorator, allowing to use the decorator to be used without
    parentheses if not arguments are provided. All arguments must be optional.
    """
    @wraps(function)
    def decorator(*args, **kwargs):
        if len(args) == 1 and len(kwargs) == 0 and callable(args[0]):
            return function(args[0])
        else:
            return lambda wrapee: function(wrapee, *args, **kwargs)
    return decorator

@doublewrap
def define_scope(function, scope=None, *args, **kwargs):
    """ The operations added by the function live within a tf.variable_scope().

    If this decorator is used with arguments, they will be forwarded to the
    variable scope. The scope name defaults to the name of the wrapped function.
    """
    name = scope or function.__name__
    @wraps(function)
    def decorator(self):
        with tf.variable_scope(name):
            return function(self, *args, **kwargs)
    return decorator

def lazy_property(function):
    """The wrapped method will only be executed once, and the result will be
    stored in a cache variable.

    Subsequent calls to it will directly return the result so that operations
    are added to the graph only once. 
    """
    attribute = '_cache_' + function.__name__
    @property
    @wraps(function)
    def decorator(self):
        if not hasattr(self, attribute):
            setattr(self, attribute, function(self))
        return getattr(self, attribute)
    return decorator
