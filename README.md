# C-DAC Compiler TUI


The C-DAC Compiler TUI is a Text User Interface for people interested in trying out GCC and LLVM compilers and for those learning about the different optimization passes available in these compilers. 


While working with compilers we realized that identifying the right optimization flags with GCC and LLVM compilers is very tedious. There are a lot of flags/options available with the compilers for optimization and it is very time consuming to explore all the flags and select the appropriate ones. Hence, we came up with the idea of developing a TUI for the compilers. 


The flags are organized into categories to make it easier to find them. The user can select their desired flags, compile and run any C program using those flags and view the output. It is also possible to generate dumps for different stages of compilation like CFG, AST etc. which can be viewed in our in-built editor. A separate screen is provided for viewing the warnings and errors.
We have also given the option to enable external projects like “POLLY”.




### Features of the C-DAC compiler TUI are listed below:
* Multiple compiler support (GCC & LLVM)
* Navigation and selection of program files
* Option for selecting any optimization level (eg. O2, Ofast etc.)
* Options for selecting optimization and transformation flags for compilation
* Provides information for each flag/Options
* Generate dump files
* Easy Compilation and execution
* View Errors & Warnings
* Built-in editor to modify any program files

