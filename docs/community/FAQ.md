# NolQu-L FAQ

## What Is NolQu-L?

NolQu-L is a small experimental compiled language and toolchain focused on a
simple, readable surface with relatively direct low-level behavior.

## Is NolQu-L Stable?

The stable public baseline is `1.0.1`. Current `1.0.2a1` work is on the `dev`
track and includes active LLVM-related backend work.

## Which Backend Should I Use?

- use the default NASM backend for the most stable current path
- treat LLVM paths as experimental unless the relevant docs say otherwise

## Is NolQu-L Open Source?

Yes. The project is currently released under the MIT license. See
[LICENSE](/root/Nolqu/LICENSE).

## Are Locals Block-Scoped?

Not currently. Local variables are function-scoped in the current semantic
model.

## Are Function Arguments Named Or Variadic?

No. The current argument model is positional-only. There are no default,
named, or variadic arguments yet.

## In What Order Are Arguments Evaluated?

Arguments are currently evaluated from left to right.

## Are Arrays Passed By Copy?

No. In the current model, array values behave as shared mutable values across
ordinary function calls.

## Where Should I Start?

- [README.md](/root/Nolqu/README.md)
- [LANGUAGE.md](/root/Nolqu/docs/language/LANGUAGE.md)
- [SEMANTICS.md](/root/Nolqu/docs/language/SEMANTICS.md)
- [FEATURE_STATUS.md](/root/Nolqu/docs/language/FEATURE_STATUS.md)

## Where Do I Ask Questions?

See [SUPPORT.md](/root/Nolqu/docs/community/SUPPORT.md) and [CONTACT.md](/root/Nolqu/docs/community/CONTACT.md).
