# TADI - Type Annotation Dependency injection
# Copyright (c) 2019, Erik Edlund <erik.edlund@32767.se>
# 
# Redistribution and use in source and binary forms, with or without modification,
# are permitted provided that the following conditions are met:
# 
# * Redistributions of source code must retain the above copyright notice,
#   this list of conditions and the following disclaimer.
# 
# * Redistributions in binary form must reproduce the above copyright notice,
#   this list of conditions and the following disclaimer in the documentation
#   and/or other materials provided with the distribution.
# 
# * Neither the name of Erik Edlund, nor the names of its contributors may
#   be used to endorse or promote products derived from this software without
#   specific prior written permission.
# 
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR
# ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
# (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON
# ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

import inspect

from typing import (
    Any,
    Callable,
    Dict,
    List,
    Optional,
    Tuple
)

class InjectorError(Exception):
    pass

class CyclicDependencyError(InjectorError):
    def __init__(self, interface: str, stack: List[str]) -> None:
        super(CyclicDependencyError, self).__init__(
            "Cyclic dependency detected while resolving {} (resolved: {})".format(
                interface,
                stack
            )
        )

class ImplementedError(InjectorError):
    def __init__(self, interface: str) -> None:
        super(ImplementedError, self).__init__(
            "Interface {} is implemented".format(interface)
        )

class ImplementationInterfaceMismatchError(InjectorError):
    def __init__(self, implementation: str, interface: str) -> None:
        super(ImplementationInterfaceMismatchError, self).__init__(
            "Implementation {} does not inherit Interface {}".format(
                implementation,
                interface
            )
        )

class UnimplementedError(InjectorError):
    def __init__(self, interface: str) -> None:
        super(UnimplementedError, self).__init__(
            "Interface {} is not implemented".format(interface)
        )

class Injector(object):
    def __init__(self) -> None:
        self.interfaces = {} # type: Dict[str, type]
        self.scoped_services = [] # type: List[Tuple[type, type]]
        self.singleton_services = [] # type: List[Tuple[type, Any]]
    
    def implementation(self, interface: type) -> Any:
        for k, tv in self.scoped_services:
            if k == interface:
                return tv
        for k, av in self.singleton_services:
            if k == interface:
                return av
        raise UnimplementedError(interface.__name__)
    
    def interface(self, interface_id: Any) -> type:
        if not isinstance(interface_id, (str, type,)):
            raise TypeError("The interfaceid must be a str or type")
        if isinstance(interface_id, type):
            interface_id = interface_id.__name__
        if interface_id in self.interfaces:
            return self.interfaces[interface_id]
        raise UnimplementedError(interface_id)

    def _register_interface(self, interface: type) -> None:
        if interface.__name__ in self.interfaces:
            raise ImplementedError(interface.__name__)
        self.interfaces[interface.__name__] = interface
    
    def register_scoped(self, interface: type, implementation: type) -> None:
        if not issubclass(implementation, interface):
            raise ImplementationInterfaceMismatchError(
                implementation.__name__,
                interface.__name__
            )
        self._register_interface(interface)
        self.scoped_services.append((interface, implementation,))

    def register_singleton(self, interface: type, singleton: Any) -> None:
        if not isinstance(singleton, interface):
            raise ImplementationInterfaceMismatchError(
                singleton.__class__.__name__,
                interface.__name__
            )
        self._register_interface(interface)
        self.singleton_services.append((interface, singleton,))

    def resolve(self, interface: type, stack: Optional[List[type]]=None) -> Any:
        implementation = self.implementation(interface)
        if not isinstance(implementation, type):
            return implementation
        if stack is not None and interface in stack:
            raise CyclicDependencyError(
                interface.__name__,
                [x.__name__ for x in stack]
            )
        fullargspec = inspect.getfullargspec(implementation.__init__) # type: ignore
        kwargs = {} # type: Dict[str, Any]
        for parametername, parametertype in fullargspec.annotations.items():
            if parametername == "return":
                continue
            kwargs[parametername] = self.resolve(
                self.interface(parametertype),
                stack + [interface] if stack is not None else [interface]
            )
        return implementation(**kwargs)

    def resolve_callable(self, fn: Any) -> Callable[[], None]:
        if not callable(fn):
            raise ValueError("The argument must be callable")
        fullargspec = inspect.getfullargspec(fn)
        kwargs = {} # type: Dict[str, Any]
        for parametername, parametertype in fullargspec.annotations.items():
            if parametername == "return":
                continue
            kwargs[parametername] = self.resolve(self.interface(parametertype))
        return lambda: fn(**kwargs)
