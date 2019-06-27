# TADDI - Type Annotation Driven Dependency injection

How it works in a nutshell: An `Interface` (an abstract Python
base class) is registered with its `Implementation` (a concrete
Python class inheriting the `Interface` (or being an instance
thereof)) for an `Injector`.

The `Injector` can then resolve a given `Interface` by creating
(`Scoped`) or returning (`Singleton`) an `Implementation`. The
constructor of the `Implementation` is inspected and typed
parameters are recursively resolved.

To get a feel for how this works in practice take a look at the
tests - they will hopefully serve as acceptable examples.

This is probably not the best way to deal with DI in Python,
possibly not even a good one, but can still be of interest to
people who want a very simplistic DI library that prefers static
typing over duck typing.
