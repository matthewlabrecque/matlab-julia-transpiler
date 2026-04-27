# MATLAB to Julia Transpiler

A homemade Python application which allows full conversion of MATLAB scripts to their Julia equivalents.

### Why MATLAB sucks

I hate MATLAB. Simple as that. The fact that all values are stored as floats pisses me off to no end, and that alone should be damning enough to mean that nobody should use this horrid scripting language. However it has a massive head start on all other mathematical scripting languages and has widespread adoption.

### Why Julia is Better

Julia doesn't use floating point values for all numerical inputs. Because the devs aren't f*cking morons.

### What this application does

In short, this application allows you to take an existing MATLAB script or file and convert it to the corresponding output. There is both an interactive mode and a translation mode. By default it will run in interactive mode, which means that any MATLAB code pasted into the terminal will be displayed in the terminal as it's corresponding Julia code.

```bash
matjulia "foo = pi(); bar = exp(1);"
```

```
MATLAB input: foo = pi(); bar = exp(1);
JULIA EQUIVALENT: foo = π; bar = exp(1);

```

There is also a translatiom mode which can be activated using the `--translate` flag in our script call. The arguments that must be passed are the path to the MATLAB file and the name of the Julia file the code should be written to.

```bash
matjulia --translate matlabcode.m juliacode.jl
```
