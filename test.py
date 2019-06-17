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

import unittest

from tadi import (
    CyclicDependencyError,
    ImplementedError,
    ImplementationInterfaceMismatchError,
    UnimplementedError,
    Injector
)
from typing import cast

class ComplexService(object):
    pass

class ComplexServiceImpl(ComplexService):
    def __init__(
        self,
        simpleone_service: "SimpleOneService",
        simpletwo_service: "SimpleTwoService"
    ) -> None:
        self.simpleone_service = simpleone_service
        self.simpletwo_service = simpletwo_service

class Config(object):
    def __init__(self) -> None:
        self.a = 0
        self.b = 1
        self.c = "foo"
        self.d = "bar"

class CyclicService(object):
    pass

class CyclicServiceImpl(CyclicService):
    def __init__(self, cyclic_service: "CyclicService") -> None:
        self.cyclic_service = cyclic_service

class SimpleOneService(object):
    def transmogrify(self, x: int, y: int) -> int:
        raise NotImplementedError()

class SimpleOneServiceImpl(SimpleOneService):
    def transmogrify(self, x: int, y: int) -> int:
        return x + y

class SimpleTwoService(object):
    def fiddle(self, x: int) -> int:
        raise NotImplementedError()

class SimpleTwoServiceImpl(SimpleTwoService):
    def fiddle(self, x: int) -> int:
        return (x + 1) ** 2

class SuperComplexService(object):
    pass

class SuperComplexServiceImpl(SuperComplexService):
    def __init__(
        self,
        config: "Config",
        simpleone_service: "SimpleOneService",
        simpletwo_service: "SimpleTwoService"
    ) -> None:
        self.config = config
        self.simpleone_service = simpleone_service
        self.simpletwo_service = simpletwo_service

class InjectorTestCase(unittest.TestCase):
    def testResolveComplexService(self) -> None:
        injector = Injector()
        injector.register_scoped(ComplexService, ComplexServiceImpl)
        injector.register_scoped(SimpleOneService, SimpleOneServiceImpl)
        injector.register_scoped(SimpleTwoService, SimpleTwoServiceImpl)
        complex_service = injector.resolve(ComplexService)
        self.assertIsInstance(complex_service, ComplexServiceImpl)
        self.assertIsInstance(complex_service.simpleone_service, SimpleOneServiceImpl)
        self.assertIsInstance(complex_service.simpletwo_service, SimpleTwoServiceImpl)
    
    def testResolveConfig(self) -> None:
        injector = Injector()
        injector.register_singleton(Config, Config())
        config = injector.resolve(Config)
        self.assertIsInstance(config, Config)
    
    def testResolveSuperComplexService(self) -> None:
        injector = Injector()
        injector.register_singleton(Config, Config())
        injector.register_scoped(SuperComplexService, SuperComplexServiceImpl)
        injector.register_scoped(SimpleOneService, SimpleOneServiceImpl)
        injector.register_scoped(SimpleTwoService, SimpleTwoServiceImpl)
        supercomplex_service = injector.resolve(SuperComplexService)
        self.assertIsInstance(supercomplex_service, SuperComplexServiceImpl)
        self.assertIsInstance(supercomplex_service.config, Config)
        self.assertIsInstance(supercomplex_service.simpleone_service, SimpleOneServiceImpl)
        self.assertIsInstance(supercomplex_service.simpletwo_service, SimpleTwoServiceImpl)
    
    def testResolveCallable(self) -> None:
        def inner(supercomplex_service: SuperComplexService) -> None:
            self.assertIsInstance(supercomplex_service, SuperComplexServiceImpl)
            # Mypy does not pick up on the assertIsInstance() here.
            supercomplex_serviceimpl = cast(SuperComplexServiceImpl, supercomplex_service)
            self.assertIsInstance(supercomplex_serviceimpl.config, Config)
            self.assertIsInstance(supercomplex_serviceimpl.simpleone_service, SimpleOneServiceImpl)
            self.assertIsInstance(supercomplex_serviceimpl.simpletwo_service, SimpleTwoServiceImpl)
        injector = Injector()
        injector.register_singleton(Config, Config())
        injector.register_scoped(SuperComplexService, SuperComplexServiceImpl)
        injector.register_scoped(SimpleOneService, SimpleOneServiceImpl)
        injector.register_scoped(SimpleTwoService, SimpleTwoServiceImpl)
        inner_wrap = injector.resolve_callable(inner)
        self.assertTrue(callable(inner_wrap))
        inner_wrap()
    
    def testImplementedError(self) -> None:
        with self.assertRaises(ImplementedError) as context:
            injector = Injector()
            injector.register_scoped(SimpleOneService, SimpleOneServiceImpl)
            injector.register_scoped(SimpleOneService, SimpleOneServiceImpl)
        self.assertEqual(str(context.exception), "Interface SimpleOneService is implemented")

    def testImplementationInterfaceMismatchError(self) -> None:
        with self.assertRaises(ImplementationInterfaceMismatchError) as context:
            injector = Injector()
            injector.register_scoped(SimpleOneService, SimpleTwoServiceImpl)
        self.assertEqual(
            str(context.exception),
            "Implementation SimpleTwoServiceImpl does not inherit Interface SimpleOneService"
        )

    def testUnimplementedError(self) -> None:
        with self.assertRaises(UnimplementedError) as context:
            injector = Injector()
            injector.resolve(ComplexService)
        self.assertEqual(str(context.exception), "Interface ComplexService is not implemented")
        with self.assertRaises(UnimplementedError) as context:
            injector = Injector()
            injector.register_scoped(ComplexService, ComplexServiceImpl)
            injector.resolve(ComplexService)
        self.assertEqual(str(context.exception), "Interface SimpleOneService is not implemented")
        with self.assertRaises(UnimplementedError) as context:
            injector = Injector()
            injector.register_scoped(ComplexService, ComplexServiceImpl)
            injector.register_scoped(SimpleOneService, SimpleOneServiceImpl)
            injector.resolve(ComplexService)
        self.assertEqual(str(context.exception), "Interface SimpleTwoService is not implemented")
    
    def testCyclicDependencyError(self) -> None:
        with self.assertRaises(CyclicDependencyError) as context:
            injector = Injector()
            injector.register_scoped(CyclicService, CyclicServiceImpl)
            injector.resolve(CyclicService)
        self.assertEqual(
            str(context.exception),
            "Cyclic dependency detected while resolving CyclicService"
            " (resolved: ['CyclicService'])"
        )

if __name__ == "__main__":
    unittest.main()
