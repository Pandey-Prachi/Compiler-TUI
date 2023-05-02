#!/usr/bin/env python
# encoding: utf-8


#import gc
import npyscreen
import npyscreen.wgmultiline as npsmultiline
import npyscreen.wgtitlefield as titlefield
import npyscreen.wgtextbox as textbox
from npyscreen import fmFileSelector

import weakref
import subprocess
import curses
import os

class TUIApp(npyscreen.NPSAppManaged):
    def onStart(self):
        #npyscreen.setTheme(npyscreen.Themes.ElegantTheme)
        # When Application starts, set up the Forms that will be used.
        # These two forms are persistent between each edit.
        self.addForm("MAIN", MainForm, name="Screen 1", color="IMPORTANT",)
        self.addForm("LLVM", LLVMForm, name="Screen 2", color="WARNING",  )
        # This one will be re-created each time it is edited.
        self.addForm("WARN", WarningForm, name="Screen 3", color="IMPORTANT",)#"CRITICAL",)
        self.addForm("EDIT", EditorForm, name="Screen 4", color="STANDOUT")

    #def onCleanExit(self):
        #npyscreen.notify_wait("Goodbye!")

    def change_form(self, name, formArgs={}, resetHistory=True):
        # Switch forms.  NB. Do *not* call the .edit() method directly (which
        # would lead to a memory leak and ultimately a recursion error).
        # Instead, use the method .switchForm to change forms.
        if formArgs!={}:
            f = self.getForm(name)
            f.setArgs(formArgs)
        self.switchForm(name)

        # By default the application keeps track of every form visited.
        # There's no harm in this, but we don't need it so:
        if resetHistory:
            self.resetHistory()


class EditorForm(npyscreen.FormMultiPageAction):
    contents = " "
    fname = ""
    warnings = []
    output = []
    compiler = "MAIN"
    width, height = 0, 0
    def create(self):
        (self.height,self.width) = getTerminalDimensions()
        self.fn2 = self.add(NewTitleFilenameCombo, name="File:")
        self.nextrely+=1
        self.editor = self.add(npyscreen.MultiLineEdit,scroll_exit=True , max_width=self.width-5, max_height=self.height-8, name="File contents",color="GOOD")
        self.statusline = self.add(npyscreen.Pager, max_width=self.width-5,max_height=2,values=[self.fn2.value],scroll_exit=True)

        self.shortcuts = "Compiler - Ctl+E\t|\tSave - Ctl+S\t|\tWarnings - Ctl+W\t|\tQuit - Ctl+Q"
        self.name = "Text Editor ("+self.shortcuts+")"#*(int(self.width*0.80)-len(self.shortcuts))+self.shortcuts+")"#"Text Editor"

        def on_cancel():
            self.parentApp.setNextForm(None)
            self.exit_editing()


        def h_on_quit(arg):
            on_cancel()

        def h_on_previous(args):
            self.change_forms()

        def h_on_save(args):
            self.showStatus("")
            try:
                f = open(self.fname,"w")
                f.write(self.editor.value)
                f.close()
                f = open(self.fname, "r")
                self.contents = f.read()
                f.close()
                self.editor.value = self.contents
                self.editor.update()
                self.editor.display()
                self.showStatus("File saved")
            except:
                pass

        def h_on_view_warnings(args):
            self.parentApp.change_form(
                    "WARN",
                    formArgs = {
                            "warnings" : prepareList(self.width-5, self.warnings, trimItems=False),
                            "compiler" : self.compiler,
                            "output"   : self.output,
                            "fname"    : self.fname
                    },
                    resetHistory=True
            )

        key_bindings = {
            "^W"             : h_on_view_warnings,
            "^Q"             : h_on_quit,
            "^E"             : h_on_previous,
            "^S"             : h_on_save,
        }
        self.fn2.setChangeCallBack(self.h_on_file_change)
        self.add_handlers(key_bindings)
        self.edit_return_value = False

    def h_on_file_change(self):
        try:
            self.fname = self.fn2.value
            f = open(self.fname, "r")
            self.contents = f.read()
            f.close()
            self.editor.value = self.contents
            self.editor.update()
            self.showStatus(self.fname)
        except Exception as e:
            pass

    def showStatus(self, message):
        self.statusline.values = [message]
        self.statusline.update()

    def setArgs(self, args):
        if "fname" in args:
            self.fn2.value = args["fname"]
            self.h_on_file_change()
        if "warnings" in args:
            self.warnings = args["warnings"]
        if "compiler" in args:
            self.compiler = args["compiler"]
        if "output" in args:
            self.output = args["output"]

    def change_forms(self, *args, **keywords):
        # Tell the MyTestApp object to change forms.
        self.parentApp.change_form(self.compiler)



class WarningForm(npyscreen.FormMultiPageActionWithMenus):#SplitForm):
    contents = None
    warnings = []
    output = []
    compiler = ""
    fname = ""
    width, height = 0, 0
    def create(self):
        (self.height,self.width) = getTerminalDimensions()

        shortcuts = "Compiler - Ctl+W\t\t|\t\tEditor - Ctl+E\t\t|\t\tQuit - Ctl+Q"
        shortcutbar = self.add(npyscreen.TitleText, scroll_exit=True, name = shortcuts, max_height=2, max_width=len(shortcuts),
                relx=int((self.width/2)-len(shortcuts)/2), color=curses.COLOR_WHITE)

        self.name = "Output"
        self.result = self.add(npyscreen.BoxTitle, max_height=int(self.height/2-4), name="Output", values = self.output)
        self.nextrely+=1
        self.contents = self.add(npyscreen.BoxTitle, max_height=int(self.height/2-3), name="Errors & Warnings", values = self.warnings)

        def on_cancel():
            self.parentApp.setNextForm(None)
            self.exit_editing()

        def h_on_quit(arg):
            on_cancel()

        def h_on_previous(args):
            self.change_forms()

        def h_on_edit(args):
            self.parentApp.change_form(
                    "EDIT",
                    formArgs = {
                            "warnings" : prepareList(self.width-5, self.warnings, trimItems=False),
                            "compiler" : self.compiler,
                            "output"   : self.output,
                            "fname"    : self.fname
                    },
                    resetHistory=True
            )

        key_bindings = {
            "^Q"             : h_on_quit,
            "^W"             : h_on_previous,
            "^E"             : h_on_edit,
        }
        self.add_handlers(key_bindings)
        self.edit_return_value = False

    def updateDisplay(self):
        self.contents.values = self.warnings
        self.result.values = self.output

    # args is a dictionary containing the arguments for this form
    def setArgs(self, args):
        if "warnings" in args and "output" in args:
            self.warnings = [str(len(args["warnings"]))+" lines"]+args["warnings"]
            self.output = args["output"]
            self.updateDisplay()
        if "fname" in args:
            self.fname = args["fname"]
        if "compiler" in args:
            self.compiler = args["compiler"]

    def change_forms(self, *args, **keywords):
        # Tell the MyTestApp object to change forms.
        self.parentApp.change_form(self.compiler)


class MainForm(npyscreen.FormMultiPageActionWithMenus):#SplitForm):
    _filter = ""
    warnings = []
    output = []
    outPrefix = "./"
    prevWidget = 0
    prevWidgetPos = 0
    width, height = 0, 0
    shell = "/bin/bash" if os.path.exists("/bin/bash") else "/bin/sh"
    def create(self):
        (self.height,self.width) = getTerminalDimensions()

        optlevel = ["Os","Og","Oz","O1","O2","O3","Ofast"]

        optinfo = ["Optimize for size. -Os enables all -O2 optimizations except those that often increase code sizeIt also enables -finline-functions, causes the compiler to tune for code size rather than execution speed, and performs further optimizations designed to reduce code size. ",
                "Optimize debugging experience. -Og should be the optimization level of choice for the standard edit-compile-debug cycle, offering a reasonable level of optimization while maintaining fast compilation and a good debugging experience. It is a better choice than -O0 for producing debuggable code because some compiler passes that collect debug information are disabled at -O0.\n\nLike -O0, -Og completely disables a number of optimization passes so that individual options controlling them have no effect. Otherwise -Og enables all -O1 optimization flags except for those that may interfere with debugging",
                "Optimize aggressively for size rather than speed. This may increase the number of instructions executed if those instructions require fewer bytes to encode. -Oz behaves similarly to -Os including enabling most -O2 optimizations. ",
                "Optimize. Optimizing compilation takes somewhat more time, and a lot more memory for a large function.\n\nWith -O, the compiler tries to reduce code size and execution time, without performing any optimizations that take a great deal of compilation time. ",
            "Optimize even more. GCC performs nearly all supported optimizations that do not involve a space-speed tradeoff. As compared to -O, this option increases both compilation time and the performance of the generated code.\n\n-O2 turns on all optimization flags specified by -O1.",   "Optimize yet more. -O3 turns on all optimizations specified by -O2 and also turns on the following optimization flags:\n\n\t-fgcse-after-reload \t-fipa-cp-clone\t-floop-interchange \t-floop-unroll-and-jam \t-fpeel-loops \t-fpredictive-commoning \t-fsplit-loops \t-fsplit-paths \t-ftree-loop-distribution \t-ftree-partial-pre \t-funswitch-loops \t-fvect-cost-model=dynamic \t-fversion-loops-for-strides",                "Disregard strict standards compliance. -Ofast enables all -O3 optimizations. It also enables optimizations that are not valid for all standard-compliant programs. It turns on -ffast-math, -fallow-store-data-races and the Fortran-specific -fstack-arrays, unless -fmax-stack-var-size is specified, and -fno-protect-parens. It turns off -fsemantic-interposition. "]

        branching = ["-fthread-jumps", "-fif-conversion", "-fif-conversion2", "-fdelayed-branch","-fhoist-adjacent-loads", "-ftree-loop-if-convert", "-fno-guess-branch-probability", "-freorder-blocks"]

        branchinfo = ["This flag enables the compiler to generate code that takes advantage of conditional jumps to parallelize code that uses threads.",

"This flag enables the compiler to optimize if-else statements by converting them into switch statements or other equivalent code.",

"This flag is an extension of -fif-conversion and enables the compiler to perform more aggressive optimization of if-else statements.",

"This flag enables the compiler to reorder code to delay branching as much as possible, which can improve performance by reducing pipeline stalls.",

"This flag enables the compiler to move adjacent loads to the same address outside of loops to reduce memory access latency.",

"This flag enables the compiler to optimize loop conditions by converting them into if statements or other equivalent code.",

" This flag disables the compiler's branch probability guessing mechanism, which can improve performance by reducing the number of unnecessary branch instructions.",

"This flag enables the compiler to reorder basic blocks to improve the performance of the code."]


#__________________________________________________________


        loops = ["-funroll-loops","-floop-parallelize-all", "-ftree-loop-distribute-patterns", "-floop-interchange", "-ftree-loop-vectorize", "-floop-strip-mine", "-ftree-loop-im"]

        loopinfo = ["This option unrolls loops by replicating loop bodies and merging them together, reducing the overhead of loop control and improving instruction pipelining.",

"This option parallelizes all loops that are eligible for parallelization, using OpenMP to distribute the work across multiple cores or processors.",

"This option distributes loop iterations across multiple cores or processors, using a pattern matching algorithm to find and group together iterations that can be executed in parallel.",

"This option reorders loop nests to improve data locality and reduce cache misses.",

"This option vectorizes loops, converting scalar operations to SIMD (single instruction multiple data) instructions that can operate on multiple data elements in parallel",

"This option divides a loop into smaller, more manageable chunks that can fit into cache more efficiently.",

"This option uses induction variable recognition and elimination to simplify loop control and reduce overhead."]

#__________________________________________________________

        vectorization = ["-march=armv8.2-a+sve","-march=armv8.2-a+simd", "-ftree-vectorize", "-ftree-loop-vectorize", "-fassociative-math", "-ffast-math", "-ftree-vectorizer-verbose=2", "-freciprocal-math" ]

        vecorizeinfo = ["This option enables the use of the Arm Scalable Vector Extension (SVE) on A64FX.",

"This option enables the use of the NEON on A64FX.",

"This option enables tree-vectorization, which is a high-level vectorization optimization that operates on the abstract syntax tree (AST) representation of the code.",

"This option enables loop-vectorization, which is a lower-level vectorization optimization that operates on the machine code level.",

"This option allows the compiler to reassociate expressions involving floating-point operations, which can improve vectorization.",

"This option enables a set of aggressive floating-point optimizations, including vectorization, that can improve performance but may not be mathematically correct in all cases.",

"This option enables verbose output for the vectorizer, where n is an integer that specifies the level of verbosity (0-3).",

"This option allows the compiler to use reciprocal approximations for floating-point division, which can improve vectorization."]

#____________________________________________________________

        scheduling= ["-fschedule-fusion", "-fmodulo-sched", "-fmodulo-sched-allow-regmoves", "-fschedule-insns2", "-fno-sched-interblock", "-fno-sched-spec", "-fsched-pressure", "-fsched-spec-load", "-fsched-stalled-insns", "-fsched-stalled-insns-dep", "-fsched2-use-superblocks", "-fsched-group-heuristic", "-frename-registers"]

        scheduleinfo = ["This flag enables instruction fusion, which merges multiple instructions into a single instruction to reduce the number of instructions executed and improve performance.",

"This flag enables modulo scheduling, which is a scheduling technique that tries to minimize pipeline stalls caused by dependencies.",

"This flag allows GCC to move register assignments across loop boundaries when using modulo scheduling.",

"This flag enables a more advanced instruction scheduler that considers the interactions between multiple instructions to reduce pipeline stalls.",

"This flag disables interblock scheduling, which is a technique that reorders instructions between basic blocks to improve performance.",

"This flag disables speculation scheduling, which is a technique that tries to guess the outcome of a conditional branch and schedule instructions accordingly to reduce pipeline stalls.",

"This flag enables pressure scheduling, which tries to minimize the number of register spills by scheduling instructions that have a low register pressure first.",

"This flag enables speculation scheduling for loads, which is a technique that tries to guess the value of a load before it is actually executed and schedule instructions accordingly to reduce pipeline stalls.",

"This flag enables scheduling of stalled instructions, which are instructions that cannot execute because they are waiting for a resource or data.",

"This flag enables scheduling of stalled instructions based on data dependencies.",

"This flag enables superblock scheduling, which is a technique that groups together multiple basic blocks into larger blocks to improve instruction scheduling.",

"This flag enables a heuristic for instruction grouping that tries to minimize the number of pipeline stalls caused by data dependencies.",

"This flag allows GCC to rename registers to minimize register usage and improve performance."]


#_____________________________________________________________


        memory = ["-fgcse", "-fgcse-lm", "-fgcse-sm", "-fgcse-las", "-fgcse-after-reload", "-fauto-inc-dec","-fstore-merging", "-fpredictive-commoning", "-fprefetch-loop-arrays", "-ffloat-store","-fallow-store-data-races", "-fmove-loop-stores"]


        meminfo = ["This option enables global common subexpression elimination, which eliminates redundant calculations by reusing the results of previously computed expressions.",

"This option enables local common subexpression elimination with memory operands, which eliminates redundant calculations involving memory operands.",

"This option enables statement-level common subexpression elimination, which eliminates redundant calculations within a single statement.",

"This option enables loop-invariant code motion and strength reduction, which moves loop-invariant calculations outside the loop and replaces expensive operations with cheaper ones.",

"This option enables global common subexpression elimination after the register allocation phase.",

"This option enables the use of increment and decrement instructions instead of add and subtract instructions, which can be faster on some processors.",

"This option merges multiple stores to adjacent memory locations into a single operation, reducing memory traffic and improving cache performance.",

"This option enables predictive common subexpression elimination, which identifies expressions that are likely to be computed repeatedly and eliminates them.",

"This option inserts prefetch instructions to load data into cache before it is needed, improving cache hit rates and reducing access latency.",

"This option forces floating-point values to be stored in memory, even if they could be kept in registers, to ensure consistent behavior across different processors.",

"This option allows stores to overlapping memory locations in multi-threaded programs, which can improve performance at the expense of data integrity.",

"This option moves loop-invariant stores outside the loop, reducing the number of memory accesses and improving cache performance."]


#____________________________________________________________


        mathops= ["-ffloat-store", "-ffast-math", "-fno-math-errno", "-funsafe-math-optimizations", "-ffinite-math-only", "-fno-rounding-math", "-fexcess-precision=fast", "-fassociative-math", "-fno-signed-zeros", "-fno-trapping-math"]

        mathinfo =["This flag disables the use of extended precision floating-point arithmetic and forces all intermediate floating-point values to be rounded and stored in memory.",

"This flag enables a set of aggressive floating-point optimizations, including the reordering of operations, the use of approximate math functions, andthe removal of certain error checks. However, these optimizations can lead to inaccurate results in some cases.",

"This flag disables the setting of the errno variable for certain math functions that can generate error conditions. This can result in faster code but can also make it harder to diagnose errors.",

"This flag enables additional floating-point optimizations that can result in inaccurate results or undefined behavior in certain cases.",

"This flag restricts floating-point arithmetic to finite values only, excluding infinity and NaN values.",

"This flag disables the rounding of floating-point results to the nearest representable value.",

"This flag enables excess precision arithmetic optimizations that can improve performance but may result in slightly different results compared to strict IEEE 754 compliance.",

"This flag enables reordering of floating-point operations that are associative, such as addition and multiplication.",

"This flag disables the use of signed zeros in floating-point arithmetic.",

"This flag disables trapping for certain floating-point exceptions, such as division by zero or overflow, which can improve performance but may also result in undefined behavior."]

#____________________________________________________________


        dumps= ["-S -o asm.s","-g", "-fdump-tree-all", "-fdump-rtl-all", "-fdump-ipa-all", "-fdump-tree-optimized", "-fdump-final-insns", "-fopt-info-vec-all"]

        dumpinfo = ["This flag tells GCC to generate an assembly language file (.s) instead of object code.",
"This flag tells GCC to generate debugging information in the output files. This information can be used by debuggers to map the generated code back to the original source code.",
"This flag generates a dump of all the internal representations of the code after each stage of the optimization process.",
"This flag generates a dump of the register transfer language (RTL) representation of the code after each stage of the optimization process.",
"This flag generates a dump of the interprocedural optimization (IPA) information after each stage of the optimization process.",
"This flag generates a dump of the final optimized code in the form of an abstract syntax tree (AST).",
"This flag generates a dump of the final optimized code in RTL format.",
"This flag generates a dump of the final optimized code in assembly language format.",
"This flag generates a report on the vectorization optimization process."]

#_____________________________________________________________

        self.name = "GCC UI"

        shortcuts = "LLVM - Ctl+T\t\t|\t\tRun - F5\t\t|\t\tResults - Ctl+W\t\t|\t\tEditor - Ctl+E\t\t|\t\tQuit - Ctl+Q"

        shortcutbar = self.add(npyscreen.TitleText, scroll_exit=True, name = shortcuts, max_height=2, max_width=len(shortcuts),
                relx=int((self.width/2)-len(shortcuts)/2), color=curses.COLOR_WHITE)

        fn2 = self.add(npyscreen.TitleFilenameCombo, name="Filename:")
        s  = self.add(npyscreen.TitleSliderPercent, accuracy=0, out_of=12, name=" ", editable=False)

        ms= self.add(TitleSelectOneWithCallBack, value = [1,], max_height=4, max_width=int(self.width/2),name="Choose one Optimization Flag", values = optlevel, scroll_exit=True)
        self.nextrely+=1
        ms3= self.add(npyscreen.TitleText, max_height=3, max_width=int(self.width/2), name="Optimization Options:",
                scroll_exit=True)

        relyflags = self.nextrely

        self.nextrely = relyflags
        multipage = False

        ms2 = self.add(TitleMultiSelectWithCallBack, max_height=3, max_width=int(self.width/2), value=[], name="Branching",
                values=branching, scroll_exit=True)
        if not self.height-10-self.nextrely >= 4 and not multipage:
            self.add_page()
            multipage = True
        ms4 = self.add(TitleMultiSelectWithCallBack, max_height=3, max_width=int(self.width/2), value=[], name="Memory",
               values=memory, scroll_exit=True)
        if not self.height-10-self.nextrely >= 4 and not multipage:
            self.add_page()
            multipage = True
        ms5 = self.add(TitleMultiSelectWithCallBack, max_height=3, max_width=int(self.width/2), value = [], name="vectorization",
                values = vectorization, scroll_exit=True)
        if not self.height-10-self.nextrely >= 4 and not multipage:
            self.add_page()
            multipage = True
        ms6 = self.add(TitleMultiSelectWithCallBack, max_height=3, max_width=int(self.width/2), value = [], name="Loops",
                values = loops, scroll_exit=True)
        if not self.height-10-self.nextrely >= 4 and not multipage:
            self.add_page()
            multipage = True
        ms7 = self.add(TitleSelectOneWithCallBack, max_height=3, max_width=int(self.width/2), value = [], name="Dumps",
                values = dumps, scroll_exit=True)
        if not self.height-10-self.nextrely >= 4 and not multipage:
            self.add_page()
            multipage = True
        ms8 = self.add(TitleMultiSelectWithCallBack, max_height=3, max_width=int(self.width/2), value = [], name="Scheduling",
                values = scheduling, scroll_exit=True)
        if not self.height-10-self.nextrely >= 4 and not multipage:
            self.add_page()
            multipage = True
        ms9 = self.add(TitleMultiSelectWithCallBack, max_height=3, max_width=int(self.width/2), value = [], name="Mathematical Ops",
                values = mathops, scroll_exit=True)

        self.switch_page(0)

        btn = self.add(npyscreen.MiniButtonPress, name="Compile", max_height=2, max_width=int(self.width/2), rely=int(-self.height/7))
        #BoX
        t1 = self.add(npyscreen.BoxTitle, name = "Info", rely=8, relx=int(self.width/2+2),
                      max_height=int(self.height*0.6), max_width=int(self.width/2*0.9), scroll_exit=True)
        #t1 = self.add(npyscreen.BoxTitle, name = "Info", rely=8, relx=-5#self.width/2+2,
         #            max_height=int(self.height*0.6), max_width=self.width/2-12, scroll_exit=True)

        self.OK_BUTTON_TEXT = "Run"
        self.CANCEL_BUTTON_TEXT = "Quit"

        def on_ok():
            self.prevWidget = self.editw
            if fn2.value != None:
                npyscreen.notify_wait("Compiling...", wide=False)
                cmd = "gcc "+"-"+optlevel[ms.value[0]]+" "
                tmp = " ".join([branching[x] for x in ms2.value])+" "
                tmp = tmp + " ".join([vectorization[x] for x in ms5.value])+" "
                tmp = tmp + " ".join([memory[x] for x in ms4.value])+" "
                tmp = tmp + " ".join([loops[x] for x in ms6.value])+" "
                tmp = tmp + " ".join([dumps[x] for x in ms7.value])+" "
                tmp = tmp + " ".join([scheduling[x] for x in ms8.value])+" "
                tmp = tmp + " ".join([mathops[x] for x in ms9.value])+" "
                cmd = cmd + tmp.strip()
                cmd = cmd + " " + fn2.value
                if len(ms7.value)==0:
                    cmdof = cmd+" -o "+self.outPrefix+"output"
                    run = True
                else:
                    run = False
                    cmdof = cmd
                proc = subprocess.Popen([cmdof], stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
                res,err = proc.communicate()
                res = res.decode('utf-8').replace(u'\u2018',"'").replace(u'\u2019',"'")
                err = err.decode('utf-8').replace(u'\u2018',"'").replace(u'\u2019',"'")
                if err == b'' or err == "":
                    #No warnings, so clear warnings
                    self.warnings = []
                else: 
                    #Warnings
                    self.warnings = [err]
                self.output = []
                t1.values = []
                if proc.returncode==0:
                    if run:
                        if self.warnings!=[]:
                            self.output = ["There are warnings"]
                            t1.values =  ["There are warnings"]
                            t1.update()
                        else:
                            t1.values = []
                            t1.update()
                        proc = subprocess.Popen([self.outPrefix+"output"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
                        res,err = proc.communicate()
                        res=res.decode('utf-8').replace(u'\u2018',"'").replace(u'\u2019',"'")
                        err=err.decode('utf-8').replace(u'\u2018',"'").replace(u'\u2019',"'")
                        t1.values+=prepareList(t1.width,["$ "+cmd])+prepareList(t1.width,res.split("\n"))
                        self.output+=prepareList(self.width-5,["$ "+cmd])+prepareList(self.width-5,res.split("\n"))
                        t1.update()
                        npyscreen.notify_confirm("$ "+cmd+"\n\n"+res, wide=True)
                        os.system("rm "+self.outPrefix+"output")
                    else:
                        self.output = ["Dump created"]
                        if self.warnings!=[]:
                            self.output.append("There are warnings")
                        t1.values = self.output
                        t1.update()
                else:
                    self.output = ["There are errors"]
                    t1.values = self.output
                    t1.update()
            else:
                npyscreen.notify_confirm("No file selected!", wide=False)

        def on_cancel():
            self.parentApp.setNextForm(None)
            self.exit_editing()

        def h_on_ok(arg):
            on_ok()

        def h_on_quit(arg):
            on_cancel()

        def h_on_switch(arg):
            change_forms()

        def listNavChanged(cursor_line):
            if self.editw == self.prevWidget:
                if currentWidgetIsAList() and cursor_line == self.prevWidgetPos:
                    return False
                else:
                    return True
            else:
                return True

        def on_optlvl_change(cursor_line):
            if currentWidgetIsAList() and listNavChanged(cursor_line):
                t1.values = prepareList(t1.width,[optinfo[cursor_line]])
                t1.update()
            self.prevWidgetPos = cursor_line

        def on_branch_change(cursor_line):
            if currentWidgetIsAList() and listNavChanged(cursor_line):
                t1.values = prepareList(t1.width,[branchinfo[cursor_line]])
                t1.update()
            self.prevWidgetPos = cursor_line

        def on_memory_change(cursor_line):
            if currentWidgetIsAList() and listNavChanged(cursor_line):
                t1.values = prepareList(t1.width,[meminfo[cursor_line]])
                t1.update()
            self.prevWidgetPos = cursor_line

        def on_vect_change(cursor_line):
            if currentWidgetIsAList() and listNavChanged(cursor_line):
                t1.values = prepareList(t1.width,[vecorizeinfo[cursor_line]])
                t1.update()
            self.prevWidgetPos = cursor_line

        def on_loops_change(cursor_line):
            if currentWidgetIsAList() and listNavChanged(cursor_line):
                t1.values = prepareList(t1.width,[loopinfo[cursor_line]])
                t1.update()
            self.prevWidgetPos = cursor_line

        def on_dump_change(cursor_line):
            if currentWidgetIsAList() and listNavChanged(cursor_line):
                t1.values = prepareList(t1.width,[dumpinfo[cursor_line]])
                t1.update()
            self.prevWidgetPos = cursor_line

        def on_schedule_change(cursor_line):
            if currentWidgetIsAList() and listNavChanged(cursor_line):
                t1.values = prepareList(t1.width,[scheduleinfo[cursor_line]])
                t1.update()
            self.prevWidgetPos = cursor_line

        def on_math_change(cursor_line):
            if currentWidgetIsAList() and listNavChanged(cursor_line):
                t1.values = prepareList(t1.width,[mathinfo[cursor_line]])
                t1.update()
            self.prevWidgetPos = cursor_line

        def currentWidgetIsAList():
            wg = self._widgets__[self.editw]
            if type(wg) == TitleSelectOneWithCallBack or type(wg) == TitleMultiSelectWithCallBack:
                return True
            else:
                t1.values = prepareList(t1.width, self.output)
                t1.update()
                return False

        def h_on_search(args):
            P = SearchPopUp()
            P.owner_widget = weakref.proxy(self)
            P.display()
            P.filterbox.edit()

        def h_open_editor(arg):
            self.parentApp.change_form(
                    "EDIT",
                    formArgs = {
                            "fname"   : fn2.value if fn2.value!=None else "",
                            "warnings": self.warnings,
                            "output"  : self.output,
                            "compiler": "MAIN"
                    },
                    resetHistory=True
            )

        def h_on_view_warnings(args):
            self.parentApp.change_form(
                    "WARN",
                    formArgs = {
                            "warnings" : prepareList(self.width-5, self.warnings, trimItems=False),
                            "output"   : self.output,
                            "fname"   : fn2.value if fn2.value!=None else "",
                            "compiler": "MAIN"
                    },
                    resetHistory=True
            )

        def h_on_view_flag_info(args):
            if currentWidgetIsAList():
                t1.edit()

        key_bindings = {
            curses.KEY_F5   : h_on_ok,
            "^Q"            : h_on_quit,
            "^T"            : self.change_forms,
            "^F"            : h_on_search,
            "^W"            : h_on_view_warnings,
            "^E"            : h_open_editor,
            ord('i')        : h_on_view_flag_info
        }
        ms.entry_widget.setSelectionCallBack(on_optlvl_change)
        ms2.entry_widget.setSelectionCallBack(on_branch_change)
        ms4.entry_widget.setSelectionCallBack(on_memory_change)
        ms5.entry_widget.setSelectionCallBack(on_vect_change)
        ms6.entry_widget.setSelectionCallBack(on_loops_change)
        ms7.entry_widget.setSelectionCallBack(on_dump_change)
        ms8.entry_widget.setSelectionCallBack(on_schedule_change)
        ms9.entry_widget.setSelectionCallBack(on_math_change)
        self.add_handlers(key_bindings)
        btn.whenPressed = on_ok
        self.on_cancel = on_cancel
        self.on_ok = on_ok
        self.edit_return_value = False


    def get_filtered_indexes(self):
        return ["not", "the", "real", "results"]

    def _remake_filter_cache(self):
        pass

    def change_forms(self, *args, **keywords):
        # Tell the MyTestApp object to change forms.
        self.parentApp.change_form("LLVM")

    def afterEditing(self):
        pass

    def while_editing(self,widget):
        self.prevWidget = self.editw+1




#LLVM
class LLVMForm(npyscreen.FormMultiPageActionWithMenus):
    _filter = ""
    warnings = []
    output = []
    outPrefix = "./"
    prevWidget = 0
    prevWidgetPos = 0
    width, height = 0, 0
    shell = "/bin/bash" if os.path.exists("/bin/bash") else "/bin/sh"
    def create(self):
        (self.height,self.width) = getTerminalDimensions()


#__________________________________________________________

        optlevel=["O0", "O1","O2","O3","Ofast","Os", "Oz"]

        optinfo= ["This level turns off all optimizations. It generates code that is easy to debug, but the resulting code may be slower and larger in size.",

"This level enables basic optimizations such as instruction scheduling and register allocation. It is generally safe to use and results in faster code.",

"This level enables more aggressive optimizations such as loop unrolling and function inlining. It can significantly improve performance but may also increase code size.",

"This level enables even more aggressive optimizations than -O2. It can result in faster code but may also increase compile time and code size.",

"This level enables all optimizations that do not violate strict standards compliance. It can result in very fast code but may not be safe to use in all cases.",

"This level optimizes for code size rather than performance. It can be useful for embedded systems or when code size is a primary concern.",

"This level performs even more aggressive optimizations for code size. It can result in significantly smaller code but may also increase compile time."]


#__________________________________________________________

        vectorization = ["-march=armv8.2-a+sve -msve-vector-bits=512","-march=armv8.2-a+simd", "-ftree-vectorize", "-ftree-loop-vectorize", "-fassociative-math", "-ffast-math", "-ftree-vectorizer-verbose=2", "-freciprocal-math" ]

        vectorizeinfo = ["This option enables the use of the Arm Scalable Vector Extension (SVE) on A64FX.",

"This option enables the use of the NEON on A64FX.",

"This option enables tree-vectorization, which is a high-level vectorization optimization that operates on the abstract syntax tree (AST) representation of the code.",

"This option enables loop-vectorization, which is a lower-level vectorization optimization that operates on the machine code level.",

"This option allows the compiler to reassociate expressions involving floating-point operations, which can improve vectorization.",

"This option enables a set of aggressive floating-point optimizations, including vectorization, that can improve performance but may not be mathematically correct in all cases.",

"This option enables verbose output for the vectorizer, where n is an integer that specifies the level of verbosity (0-3).",

"This option allows the compiler to use reciprocal approximations for floating-point division, which can improve vectorization."]

#_____________________________________________________________

        polly= ["-mllvm -polly"]

        pollyinfo= ["Enables pollly"]


#_____________________________________________________________

        loops=["-funroll-loops", "-floop-parallelize-all", "-floop-strip-mine", "-floop-interchange", "-floop-block"]


        loopinfo= ["This option instructs the compiler to unroll loops, which can improve performance by reducing the overhead of loop iteration.",

"This option enables automatic parallelization of all loops, which can improve performance on multi-core processors.",

"This option enables loop strip-mining, which involves splitting a loop into smaller sub-loops to improve cache locality and reduce memory traffic.",

"This option enables loop interchange, which involves swapping the order of nested loops to improve cache locality and reduce memory traffic.",

"This option enables loop blocking, which involves partitioning a loop into smaller blocks to improve cache locality and reduce memory traffic"]



#___________________________________________________________

        branching =["-fbranch-probabilities", "-fstrict-aliasing", "-fno-branch-count-reg", "-fbranch-target-load-optimize", "-fbranch-target-load-optimize2", "-fno-tree-loop-distribute-patterns", "-fjump-tables", "-fswitch-tables", "-fomit-frame-pointer"]

        branchinfo= ["This option enables the compiler to use profile-guided optimization (PGO) to optimize branches based on the probability of their outcomes. The compiler can use this information to generate code that minimizes the number of mispredicted branches.",

"This option enables the compiler to assume that pointers of different types do not alias, which can allow for more aggressive optimizations, including control-flow optimizations.",

"This option disables the use of registers to count the number of times a loop has executed. While this can reduce code size, it can also limit the ability of the compiler to optimize control flow.",

"This option enables an optimization that tries to predict branch targets using load instructions, which can be more accurate than traditional branch prediction.",

"This option is a more aggressive version of -fbranch-target-load-optimize, which uses multiple load instructions to predict branch targets.",

"This option disables loop distribution, which is a transformation that can reduce the number of branches in a loop.",

"This flag tells LLVM to use jump tables instead of if-else chains. This can reduce branching and improve performance.",

"This flag tells LLVM to use switch tables instead of if-else chains. This can reduce branching and improve performance.",

"This flag tells LLVM to not generate a frame pointer for each function call. This can reduce branching and improve performance."]


#_____________________________________________________________


        scheduling= ["-mllvm -misched", "-mllvm -misched-early", "-mllvm -pre-RA-sched=fast" "-mllvm -enable-misched"]

        scheduleinfo= ["This flag enables machine instruction scheduling optimizations in LLVM. This can improve scheduling by reordering instructions to reduce stalls and increase the number of instructions that can be executed simultaneously.",

"This flag enables early machine instruction scheduling optimizations in LLVM. This can improve scheduling by scheduling instructions earlier in the pipeline to reduce stalls and increase the number of instructions that can be executed simultaneously.",

"This flag enables faster pre-register allocation machine instruction scheduling optimizations in LLVM. This can improve scheduling by scheduling instructions before register allocation to reduce stalls and increase the number of instructions that can be executed simultaneously.",

"This option enables machine instruction scheduling, which can improve performance by optimizing the order in which instructions are executed."]

#_____________________________________________________________


        mathops = ["-ffloat-store", "-ffast-math", "-funsafe-math-optimizations", "-ffinite-math-only", "-fassociative-math"]

        mathinfo =["This flag disables the use of extended precision floating-point arithmetic and forces all intermediate floating-point values to be rounded and stored in memory.",

"This flag enables a set of aggressive floating-point optimizations, including the reordering of operations, the use of approximate math functions, and the removal of certain error checks. However, these optimizations can lead to inaccurate results in some cases.",

"This flag enables additional floating-point optimizations that can result in inaccurate results or undefined behavior in certain cases.",

"This flag restricts floating-point arithmetic to finite values only, excluding infinity and NaN values.",

"This flag enables reordering of floating-point operations that are associative, such as addition and multiplication."]

#____________________________________________________________


        dumps= ["-S -o asm.s", "-g", "-fdump-tree-all"]

        dumpinfo = ["This flag tells LLVM to generate an assembly language file (.s) instead of object code.",

"This flag tells LLVM to generate debugging information in the output files. This information can be used by debuggers to map the generated code back to the original source code.",

"Generates all Tree dumps"]

#_____________________________________________________________




        self.name = "LLVM UI"

        shortcuts = "GCC - Ctl+T\t\t|\t\tRun - F5\t\t|\t\tResults - Ctl+W|\t\tEditor - Ctl+E\t\t|\t\tQuit - Ctl+Q"

        shortcutbar = self.add(npyscreen.TitleText, scroll_exit=True, name = shortcuts, max_height=2, max_width=len(shortcuts),
                relx=int((self.width/2)-len(shortcuts)/2), color="DEFAULT")

        fn2 = self.add(npyscreen.TitleFilenameCombo, name="Filename:")
        s  = self.add(npyscreen.TitleSliderPercent, accuracy=0, out_of=12, name="Slider")

        ms= self.add(TitleSelectOneWithCallBack, value = [1,], max_height=4, max_width=int(self.width/2),name="Choose one Optimization Flag"            ,values = optlevel, scroll_exit=True)
        self.nextrely+=1
        ms3= self.add(npyscreen.TitleText, max_height=3, max_width=int(self.width/2), name="Optimization Options:",
                scroll_exit=True)

        relyflags = self.nextrely

        self.nextrely = relyflags
        multipage = False

        ms4= self.add(TitleSelectOneWithCallBack, max_height=3, max_width=int(self.width/2), value = [], name="ENABLE POLLY",
                values = polly, scroll_exit=True)
        if not self.height-10-self.nextrely >= 4 and not multipage:
            self.add_page()
            multipage = True
        ms2= self.add(TitleMultiSelectWithCallBack, max_height=3, max_width=int(self.width/2), value = [], name="Branching",
                values = branching, scroll_exit=True)
        if not self.height-10-self.nextrely >= 4 and not multipage:
            self.add_page()
            multipage = True
        ms5= self.add(TitleMultiSelectWithCallBack, max_height=3, max_width=int(self.width/2), value = [], name="vectorization",
                values = vectorization, scroll_exit=True)
        if not self.height-10-self.nextrely >= 4 and not multipage:
            self.add_page()
            multipage = True
        ms6= self.add(TitleMultiSelectWithCallBack, max_height=3, max_width=int(self.width/2), value = [], name="Loops",
                values = loops, scroll_exit=True)
        if not self.height-10-self.nextrely >= 4 and not multipage:
            self.add_page()
            multipage = True
        ms7= self.add(TitleSelectOneWithCallBack, max_height=3, max_width=int(self.width/2), value = [], name="Dumps",
                values = dumps, scroll_exit=True)
        if not self.height-10-self.nextrely >= 4 and not multipage:
            self.add_page()
            multipage = True
        ms8= self.add(TitleSelectOneWithCallBack, max_height=3, max_width=int(self.width/2), value = [], name="Scheduling",
                values = scheduling, scroll_exit=True)
        if not self.height-10-self.nextrely >= 4 and not multipage:
            self.add_page()
            multipage = True
        ms9= self.add(TitleSelectOneWithCallBack, max_height=3, max_width=int(self.width/2), value = [], name="Mathematical OPs",
                values = mathops, scroll_exit=True)

        self.switch_page(0)

        btn = self.add(npyscreen.MiniButtonPress, name="Compile", max_height=2, max_width=int(self.width/2), rely=int(-self.height/7))

        #BoX
        t1 = self.add(npyscreen.BoxTitle, name = "Info", rely=8, relx=int(self.width/2+2),max_height=int(self.height*0.6), max_width=int(self.width/2*0.9), scroll_exit=True)
        #t1 = self.add(npyscreen.BoxTitle, name = "Info", rely=8, relx=self.width/2+2,
         #            max_height=int(self.height*0.6), max_width=self.width/2-12, scroll_exit=True)

        self.OK_BUTTON_TEXT = "Run"
        self.CANCEL_BUTTON_TEXT = "Quit"

        def on_ok():
            self.prevWidget = self.editw
            if fn2.value != None:
                npyscreen.notify_wait("Compiling...")
                t1.values = ["Compiling..."]
                t1.update()
                cmd = "clang "+"-"+optlevel[ms.value[0]]+" "
                tmp = " ".join([branching[x] for x in ms2.value])+" "
                tmp = tmp + " ".join([vectorization[x] for x in ms5.value])+" "
                tmp = tmp + " ".join([polly[x] for x in ms4.value])+" "
                tmp = tmp + " ".join([loops[x] for x in ms6.value])+" "
                tmp = tmp + " ".join([scheduling[x] for x in ms8.value])+" "
                tmp = tmp + " ".join([mathops[x] for x in ms9.value])+" "
                tmp = tmp + " ".join([dumps[x] for x in ms7.value])+" "
                cmd = cmd + tmp.strip() + " " + fn2.value

                if len(ms7.value)==0:
                    cmdof = cmd+" -o "+self.outPrefix+"output"
                    run = True
                else:
                    run = False
                    cmdof = cmd

                proc = subprocess.Popen([cmd+" -o "+self.outPrefix+"output"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
                res,err = proc.communicate()
                res=res.decode('utf-8').replace(u'\u2018',"'").replace(u'\u2019',"'")
                err=err.decode('utf-8').replace(u'\u2018',"'").replace(u'\u2019',"'")
                if err == b'' or err == "":
                    #No warnings, so clear warnings
                    self.warnings = []
                else: 
                    #Warnings
                    self.warnings = [err]
                self.output = []
                t1.values=[]
                if proc.returncode==0:
                    if run:
                        if self.warnings!=[]:
                            self.output = ["There are warnings"]
                            t1.values =  ["There are warnings"]
                            t1.update()
                        else:
                            t1.values = []
                            t1.update()
                        proc = subprocess.Popen([self.outPrefix+"output"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
                        res,err = proc.communicate()
                        res=res.decode('utf-8').replace(u'\u2018',"'").replace(u'\u2019',"'")
                        err=err.decode('utf-8').replace(u'\u2018',"'").replace(u'\u2019',"'")
                        t1.values+=prepareList(t1.width,["$ "+cmd])+prepareList(t1.width,res.split("\n"))
                        self.output+=prepareList(self.width-5,["$ "+cmd])+prepareList(self.width-5,res.split("\n"))
                        t1.update()
                        npyscreen.notify_confirm("$ "+cmd+"\n\n"+res, wide=True)
                        os.system("rm "+self.outPrefix+"output")
                    else:
                        self.output = ["Dump created"]
                        if self.warnings!=[]:
                            self.output.append("There are warnings")
                        t1.values = self.output
                        t1.update()
                else:
                    self.output = ["There are errors"]
                    t1.values = self.output
                    t1.update()
            else:
                npyscreen.notify_confirm("No file selected!", wide=False)

        def on_cancel():
            self.parentApp.setNextForm(None)
            self.exit_editing()

        def h_on_ok(arg):
            on_ok()

        def h_on_quit(arg):
            on_cancel()

        def h_on_switch(arg):
            change_forms()

        def listNavChanged(cursor_line):
            if self.editw == self.prevWidget:
                if currentWidgetIsAList() and cursor_line == self.prevWidgetPos:
                    return False
                else:
                    return True
            else:
                return True

        def on_optlvl_change(cursor_line):
            if currentWidgetIsAList() and listNavChanged(cursor_line):
                t1.values = prepareList(t1.width,[optinfo[cursor_line]])
                t1.update()
            self.prevWidgetPos = cursor_line

        def on_branch_change(cursor_line):
            if currentWidgetIsAList() and listNavChanged(cursor_line):
                t1.values = prepareList(t1.width,[branchinfo[cursor_line]])
                t1.update()
            self.prevWidgetPos = cursor_line

        def on_polly_change(cursor_line):
            if currentWidgetIsAList() and listNavChanged(cursor_line):
                t1.values = prepareList(t1.width,[pollyinfo[cursor_line]])
                t1.update()
            self.prevWidgetPos = cursor_line

        def on_vect_change(cursor_line):
            if currentWidgetIsAList() and listNavChanged(cursor_line):
                t1.values = prepareList(t1.width,[vectorizeinfo[cursor_line]])
                t1.update()
            self.prevWidgetPos = cursor_line

        def on_loops_change(cursor_line):
            if currentWidgetIsAList() and listNavChanged(cursor_line):
                t1.values = prepareList(t1.width,[loopinfo[cursor_line]])
                t1.update()
            self.prevWidgetPos = cursor_line

        def on_dump_change(cursor_line):
            if currentWidgetIsAList() and listNavChanged(cursor_line):
                t1.values = prepareList(t1.width,[dumpinfo[cursor_line]])
                t1.update()
            self.prevWidgetPos = cursor_line

        def on_schedule_change(cursor_line):
            if currentWidgetIsAList() and listNavChanged(cursor_line):
                t1.values = prepareList(t1.width,[scheduleinfo[cursor_line]])
                t1.update()
            self.prevWidgetPos = cursor_line

        def on_math_change(cursor_line):
            if currentWidgetIsAList() and listNavChanged(cursor_line):
                t1.values = prepareList(t1.width,[mathinfo[cursor_line]])
                t1.update()
            self.prevWidgetPos = cursor_line

        def currentWidgetIsAList():
            wg = self._widgets__[self.editw]
            if type(wg) == TitleSelectOneWithCallBack or type(wg) == TitleMultiSelectWithCallBack:
                return True
            else:
                t1.values = prepareList(t1.width, self.output)
                t1.update()
                return False

        def h_on_search(args):
            P = SearchPopUp()
            P.owner_widget = weakref.proxy(self)
            P.display()
            P.filterbox.edit()

        def h_open_editor(arg):
            self.parentApp.change_form(
                    "EDIT",
                    formArgs = {
                            "fname"   : fn2.value if fn2.value!=None else "",
                            "warnings": self.warnings,
                            "output"  : self.output,
                            "compiler": "LLVM"
                    },
                    resetHistory=True
            )

        def h_on_view_warnings(args):
            self.parentApp.change_form(
                    "WARN",
                    formArgs = {
                            "warnings" : prepareList(self.width-5, self.warnings, trimItems=False),
                            "output"   : self.output,
                            "fname"   : fn2.value if fn2.value!=None else "",
                            "compiler": "LLVM"
                    },
                    resetHistory=True
            )

        def h_on_view_flag_info(args):
            if currentWidgetIsAList():
                t1.edit()

        key_bindings = {
            curses.KEY_F5   : h_on_ok,
            "^Q"            : h_on_quit,
            "^T"            : self.change_forms,
            "^F"            : h_on_search,
            "^W"            : h_on_view_warnings,
            "^E"            : h_open_editor,
            ord('i')        : h_on_view_flag_info
        }
        ms.entry_widget.setSelectionCallBack(on_optlvl_change)
        ms2.entry_widget.setSelectionCallBack(on_branch_change)
        ms4.entry_widget.setSelectionCallBack(on_polly_change)
        ms5.entry_widget.setSelectionCallBack(on_vect_change)
        ms6.entry_widget.setSelectionCallBack(on_loops_change)
        ms7.entry_widget.setSelectionCallBack(on_dump_change)
        ms8.entry_widget.setSelectionCallBack(on_schedule_change)
        ms9.entry_widget.setSelectionCallBack(on_math_change)
        self.add_handlers(key_bindings)
        btn.whenPressed = on_ok
        self.on_cancel = on_cancel
        self.on_ok = on_ok
        self.edit_return_value = False


    def get_filtered_indexes(self):
        return ["not", "the", "real", "results"]

    def _remake_filter_cache(self):
        pass

    def change_forms(self, *args, **keywords):
        # Tell the MyTestApp object to change forms.
        self.parentApp.change_form("MAIN")

    def afterEditing(self):
        pass

    def while_editing(self,widget):
        self.prevWidget = self.editw+1

###Custom Widgets

class MultiLineEditNew(npyscreen.MultiLineEdit):
    def _print_unicode_char(self, ch):
        try:
            #super(MultiLineEditNew,self)._print_unicode_char(ch)
            if self._force_ascii:
                return ch.encode('ascii', 'replace')
            elif sys.version_info[0] >= 3:
                return ch
            else:
                return ch.encode('utf-8', 'strict')
        except Exception as e:
            pass

class NewFilenameCombo(npyscreen.FilenameCombo):
    onChangeCallBack = None
    def h_change_value(self, *args, **keywords):
        self.value = fmFileSelector.selectFile(
            starting_value = self.value,
            select_dir = self.select_dir,
            must_exist = self.must_exist,
            confirm_if_exists = self.confirm_if_exists,
            sort_by_extension = self.sort_by_extension
        )
        if self.value == '':
            self.value = None
        self.display()
        if self.onChangeCallBack!=None:
            self.onChangeCallBack()


class NewTitleFilenameCombo(npyscreen.TitleFilenameCombo):
    _entry_type = NewFilenameCombo

    def setChangeCallBack(self, callback):
        self.entry_widget.onChangeCallBack = callback


class SelectOneWithCallBack(npyscreen.SelectOne):
     selectionCallBack = None

     def _before_print_lines(self):
         if self.selectionCallBack!=None:
            self.selectionCallBack(self.cursor_line)

     def setSelectionCallBack(self,callBack=None):
         self.selectionCallBack = callBack


class TitleSelectOneWithCallBack(npyscreen.TitleSelectOne):
    _entry_type = SelectOneWithCallBack


class MultiSelectWithCallBack(npyscreen.MultiSelect):
     selectionCallBack = None

     def _before_print_lines(self):
         if self.selectionCallBack!=None:
            self.selectionCallBack(self.cursor_line)

     def setSelectionCallBack(self,callBack=None):
         self.selectionCallBack = callBack


class TitleMultiSelectWithCallBack(npyscreen.TitleMultiSelect):
    _entry_type = MultiSelectWithCallBack


class SearchPopUp(npsmultiline.FilterPopupHelper):

    def create(self):
        super(npsmultiline.FilterPopupHelper, self).create()
        self.filterbox = self.add(titlefield.TitleText, name='Find what: ', )
        self.nextrely += 1
        self.statusline = self.add(textbox.Textfield, color = 'LABEL TEXT', editable = False)

    def updatestatusline(self):
        self.owner_widget._filter   = self.filterbox.value
        filtered_lines = self.owner_widget.get_filtered_indexes()
        len_f = len(filtered_lines)
        if self.filterbox.value == None or self.filterbox.value == '':
            self.statusline.value = ''
        elif len_f == 0:
            self.statusline.value = '(No Matches)'
        elif len_f == 1:
            self.statusline.value = '(1 Match)'
        else:
            self.statusline.value = '(%s Matches)' % len_f

    def adjust_widgets(self):
        self.updatestatusline()
        self.statusline.display()

###

###Utility functions

def getTerminalDimensions():
    return curses.initscr().getmaxyx()

def prepareList(width, ls, trimItems=False):
    ls1 = []
    for x in ls:
        ls1 = ls1 + x.split("\n")
    i=0
    ls2 = []
    for s in ls1:
        if len(s)>width-5:
            indices = [0]+[x for x in range(0,len(s),width-5)]+[None]
            sublist = [s[indices[i]:indices[i+1]] for i in range(len(indices)-1)]
            ls2 = ls2 + sublist
        else:
            ls2.append(s)
        i+=1
    if trimItems:
        ls2 = [x.strip() for x in ls2]

    return ls2

####

if __name__=="__main__":
    App = TUIApp()
    App.run()
