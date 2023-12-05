#!/usr/bin/env python3
# encoding: utf-8


#import gc
import npyscreen
from npyscreen import wgwidget as widget
import npyscreen.wgmultiline as npsmultiline
import npyscreen.wgtitlefield as titlefield
import npyscreen.wgtextbox as textbox
from npyscreen import fmFileSelector
from npyscreen import fmPopup as Popup
from npyscreen.wgmultiline import MultiLine
from npyscreen import fmForm
from npyscreen import utilNotify


import weakref
import subprocess
import os
os.environ.setdefault('ESCDELAY', '25')
import curses
import sys

class TUIApp(npyscreen.NPSAppManaged):
    env = None
    def onStart(self):
        #npyscreen.setTheme(npyscreen.Themes.ElegantTheme)
        # When Application starts, set up the Forms that will be used.
        # These two forms are persistent between each edit.
        self.env = os.environ
        self.addForm("MAIN", MainForm, name="Screen 1", color="IMPORTANT",)
        self.addForm("LLVM", LLVMForm, name="Screen 2", color="WARNING",  )
        # This one will be re-created each time it is edited.
        self.addForm("EDIT", EditorForm, name="Screen 4", color="STANDOUT")
        self.addForm("ENV", EnvironmentForm, name="Screen 5", color="IMPORTANT")

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


class Form_OK_Button(npyscreen.wgbutton.MiniButtonPress):
    def handle_mouse_event(self, mouse_event):
        mouse_id, rel_x, rel_y, z, bstate = self.interpret_mouse_event(mouse_event)
        self.value = True


class EnvironmentForm(npyscreen.FormMultiPageAction):
    OKBUTTON_TYPE = Form_OK_Button
    width, height = 0, 0
    returnTo = ""
    _filter = ""
    variables = ["OMP_SCHEDULE", "OMP_NUM_THREADS", "OMP_DYNAMIC", "OMP_PROC_BIND", "OMP_PLACES", "OMP_STACKSIZE", "OMP_WAIT_POLICY", "OMP_MAX_ACTIVE_LEVELS",
                "OMP_NESTED", "OMP_THREAD_LIMIT", "OMP_CANCELLATION", "OMP_DISPLAY_ENV", "OMP_DISPLAY_AFFINITY", "OMP_AFFINITY_FORMAT", "OMP_DEFAULT_DEVICE",
                "OMP_MAX_TASK_PRIORITY", "OMP_TARGET_OFFLOAD", "OMP_TOOL", "OMP_TOOL_LIBRARIES", "OMP_DEBUG", "OMP_ALLOCATOR"]
    parameters = {
        "OMP_SCHEDULE": {
            "form" : "!modifier:kind,!chunk",
            "params" : ["modifier", "kind", "chunk"],
            "modifier" : ["monotonic", "nonmonotonic"],
            "kind" : ["static", "dynamic", "guided", "auto"],
            "chunk" : "int",
            "info" : "The OMP_SCHEDULE environment variable controls the schedule kind and chunk size of all loop directives that have the schedule "
                    "kind runtime, by setting the value of the run-sched-var ICV.\n\n"
                    "The value of this environment variable takes the form:\n"
                    "\t[modifier:]kind[, chunk]\n\n"
                    "where\n\n"
                    "\tmodifier is one of monotonic or nonmonotonic;\n"
                    "\tkind is one of static, dynamic, guided, or auto;\n"
                    "\tchunk is an optional positive integer that specifies the chunk size.\n"
        }, 
        "OMP_NUM_THREADS": {
            "form" : "str",
            "params" : ["str"],
            "str" : "str",
            "info" : "The OMP_NUM_THREADS environment variable sets the number of threads to use for parallel regions by setting the initial value of the nthreads-var ICV."
                    "The value of this environment variable must be a list of positive integer values. The values of the list set the number of threads to use for parallel"
                    "regions at the corresponding nested levels.\n\n"
                    "The behavior of the program is implementation defined if any value of the list specified in the OMP_NUM_THREADS environment variable leads to a number"
                    "of threads that is greater than an implementation can support, or if any value is not a positive integer.\n\n"
                    "Example:\n\n4,3,2"
        }, 
        "OMP_DYNAMIC": {
            "form" : "bool",
            "params" : ["bool"],
            "bool" : [True, False],
            "info" : "The OMP_DYNAMIC environment variable controls dynamic adjustment of the number of threads to use for executing parallel regions by setting the"
                    "initial value of the dyn-var ICV.\n\n"
                    "The value of this environment variable must be one of the following:\n\ntrue | false\n\n"
                    "If the environment variable is set to true, the OpenMP implementation may adjust the number of threads to use for executing parallel regions in"
                    "order to optimize the use of system resources. If the environment variable is set to false, the dynamic adjustment of the number of threads is disabled."
                    "The behavior of the program is implementation defined if the value of OMP_DYNAMIC is neither true nor false."
        }, 
        "OMP_PROC_BIND": {
            "form" : "bool|var1,var2,var3",
            "params" : ["bool", "var1", "var2", "var3"],
            "bool" : [True, False],
            "var1" : ["master", "close", "spread"],
            "var2" : ["master", "close", "spread"],
            "var3" : ["master", "close", "spread"],
            "info" : "The OMP_PROC_BIND environment variable sets the initial value of the bind-var ICV. The value of this environment variable is either true, false, "
                    "or a comma separated list of master, close, or spread. The values of the list set the thread affinity policy to be used for parallel regions at the"
                    "corresponding nested level.\n\n"
                    "If the environment variable is set to false, the execution environment may move OpenMP threads between OpenMP places, thread affinity is disabled,"
                    "and proc_bind clauses on parallel constructs are ignored.\n\n"
                    "Otherwise, the execution environment should not move OpenMP threads between OpenMP places, thread affinity is enabled, and the initial thread is "
                    "bound to the first place in the OpenMP place list prior to the first active parallel region.\n\n"
                    "The behavior of the program is implementation defined if the value in the OMP_PROC_BIND environment variable is not true, false, or a comma separated"
                    "list of master, close, or spread. The behavior is also implementation defined if an initial thread cannot be bound to the first place in the OpenMP"
                    "place list.\n\nExample: \n\nfalse\n\nspread, spread, close"
        }, 
        "OMP_PLACES": {
            "form" : "str",
            "params" : ["str"],
            "str" : "str",
            "info" : "A list of places can be specified in the OMP_PLACES environment variable. The place-partition-var ICV obtains its initial value from the OMP_PLACES value,"
                    "and makes the list available to the execution environment. The value of OMP_PLACES can be one of two types of values: either an abstract name that describes"
                    "a set of places or an explicit list of places described by non-negative numbers.\n\n"
                    "The OMP_PLACES environment variable can be defined using an explicit ordered list of comma-separated places. A place is defined by an unordered set"
                    "of comma-separated non-negative numbers enclosed by braces. The meaning of the numbers and how the numbering is done are implementation defined."
                    "Generally, the numbers represent the smallest unit of execution exposed by the execution environment, typically a hardware thread.\n\n"
                    "Intervals may also be used to define places. Intervals can be specified using the <lower-bound> : <length> : <stride> notation to represent the "
                    "following list of numbers: “<lower-bound>, <lower-bound> + <stride>, ..., <lower-bound> + (<length> - 1)*<stride>.” When <stride> is omitted, a "
                    "unit stride is assumed. Intervals can specify numbers within a place as well as sequences of places. \n\n"
                    "Example:\n\nthreads\n\nthreads(4)\n\n{0,1,2,3},{4,5,6,7},{8,9,10,11},{12,13,14,15}\n\n{0:4},{4:4},{8:4},{12:4}\n\n{0:4}:4:4"
        }, 
        "OMP_STACKSIZE": {
            "form" : "str",
            "params" : ["str"],
            "str" : "str",
            "info" : "The OMP_STACKSIZE environment variable controls the size of the stack for threads created by the OpenMP implementation, by setting the value of"
                    "the stacksize-var ICV. The environment variable does not control the size of the stack for an initial thread.\n\n"
                    "The value of this environment variable takes the form:\n\n"
                    "size | sizeB | sizeK | sizeM | sizeG \n\n"
                    "Example:\n\n2000500B\n\n3000 k\n\n10M\n\n\" 10 M \"\n\n\"20 m \"\n\n\" 1G\"\n\n20000"
        },
        "OMP_WAIT_POLICY": {
            "form" : "str",
            "params" : ["str"],
            "str" : "str",
            "info" : "The OMP_WAIT_POLICY environment variable provides a hint to an OpenMP implementation about the desired behavior of waiting threads by setting "
                    "the wait-policy-var ICV. A compliant OpenMP implementation may or may not abide by the setting of the environment variable.\n\n"
                    "The value of this environment variable must be one of the following:\n\n"
                    "ACTIVE | PASSIVE\n\n"
                    "The ACTIVE value specifies that waiting threads should mostly be active, consuming processor cycles, while waiting. An OpenMP implementation may,"
                    "for example, make waiting threads spin.\n\n"
                    "The PASSIVE value specifies that waiting threads should mostly be passive, not consuming processor cycles, while waiting. For example, an OpenMP" 
                    "implementation may make waiting threads yield the processor to other threads or go to sleep. "
        }, 
        "OMP_MAX_ACTIVE_LEVELS": {
            "form" : "str",
            "params" : ["str"],
            "str" : "str",
            "info" : "The OMP_MAX_ACTIVE_LEVELS environment variable controls the maximum number of nested active parallel regions by setting the initial value of" 
                    " the max-active-levels-var ICV.\n\n"
                    "The value of this environment variable must be a non-negative integer. The behavior of the program is implementation defined if the requested value of"
                    " OMP_MAX_ACTIVE_LEVELS is greater than the maximum number of nested active parallel levels an implementation can support, or if the value is not a "
                    "non-negative integer. "
        },
        "OMP_NESTED": {
            "form" : "str",
            "params" : ["str"],
            "str" : "str",
            "info" : "Deprecated\n\n" 
                    "The OMP_NESTED environment variable controls nested parallelism by setting the initial value of the max-active-levels-var ICV. "
                    "If the environment variable is set to true, the initial value of max-active-levels-var is set to the number of active levels of parallelism supported by the"
                    " implementation. If the environment variable is set to false, the initial value of max-active-levels-var is set to 1. The behavior of the program is "
                    "implementation defined if the value of OMP_NESTED is neither true nor false.\n\n"
                    "If both the OMP_NESTED and OMP_MAX_ACTIVE_LEVELS environment variables are set, the value of OMP_NESTED is false, and the value of OMP_MAX_ACTIVE_LEVELS is"
                    " greater than 1, the behavior is implementation defined. Otherwise, if both environment variables are set then the OMP_NESTED environment variable has no "
                    "effect.\n\n"
        }, 
        "OMP_THREAD_LIMIT": {
            "form" : "str",
            "params" : ["str"],
            "str" : "str",
            "info" : "The OMP_THREAD_LIMIT environment variable sets the maximum number of OpenMP threads to use in a contention group by setting the thread-limit-var ICV."
                    "\n\nThe value of this environment variable must be a positive integer. The behavior of the program is implementation defined if the requested value of "
                    "OMP_THREAD_LIMIT is greater than the number of threads an implementation can support, or if the value is not a positive integer."
        }, 
        "OMP_CANCELLATION": {
            "form" : "str",
            "params" : ["str"],
            "str" : "str",
            "info" : "The OMP_CANCELLATION environment variable sets the initial value of the cancel-var ICV.\n\n"
                    "The value of this environment variable must be one of the following:\n\n"
                    "true | false\n\n"
                    "If set to true, the effects of the cancel construct and of cancellation points are enabled and cancellation is activated. If set to false,"
                    " cancellation is disabled and the cancel construct and cancellation points are effectively ignored. The behavior of the program is implementation"
                    " defined if OMP_CANCELLATION is set to neither true nor false."
        }, 
        "OMP_DISPLAY_ENV": {
            "form" : "str",
            "params" : ["str"],
            "str" : "str",
            "info" : "The OMP_DISPLAY_ENV environment variable instructs the runtime to display the OpenMP version number and the value of the ICVs associated with the"
                    " environment variables described in Chapter 6, as name = value pairs. The runtime displays this information once, after processing the environment"
                    " variables and before any user calls to change the ICV values by any runtime routines.\n\n"
                    "The value of the OMP_DISPLAY_ENV environment variable may be set to one of these values:\n\n"
                    "TRUE | FALSE | VERBOSE"
        }, 
        "OMP_DISPLAY_AFFINITY": {
            "form" : "str",
            "params" : ["str"],
            "str" : "str",
            "info" : "The OMP_DISPLAY_AFFINITY environment variable instructs the runtime to display formatted affinity information for all OpenMP threads in the"
                    " parallel region upon entering the first parallel region and when any change occurs in the information accessible by format specifiers. "
                    "If affinity of any thread in a parallel region changes then thread affinity information for all threads in that region is displayed. "
                    "If the thread affinity for each respective parallel region at each nesting level has already been displayed and the thread affinity"
                    " has not changed, then the information is not displayed again. There is no specific order in displaying thread affinity information for all threads"
                    " in the same parallel region.\n\n"
                    "The value of the OMP_DISPLAY_AFFINITY environment variable may be set to one of these values:\n\n"
                    "TRUE | FALSE"
        }, 
        "OMP_AFFINITY_FORMAT": {
            "form" : "str",
            "params" : ["str"],
            "str" : "str",
            "info" : "The OMP_AFFINITY_FORMAT environment variable sets the initial value of the affinity-format-var ICV which defines the format when displaying "
                    "OpenMP thread affinity information.\n\n"
                    "The value of this environment variable is a character string that may contain as substrings one or more field specifiers, in addition to other characters."
                    " The format of each field specifier is  \n\n"
                    "%[[[0].] size ] type\n\n"
                    "where an individual field specifier must contain the percent symbol (%) and a type. The type can be a single character short name or its corresponding"
                    " long name delimited with curly braces, such as %n or %{thread_num}. A literal percent is specified as %%. Field specifiers can be provided in any order."
                    "The 0 modifier indicates whether or not to add leading zeros to the output, following any indication of sign or base. The . modifier indicates the output"
                    " should be right justified when size is specified. By default, output is left justified. The minimum field length is size, which is a decimal digit string"
                    " with a non-zero first digit. If no size is specified, the actual length needed to print the field will be used. If the 0 modifier is used with type of A,"
                    " {thread_affinity}, H, {host}, or a type that is not printed as a number, the result is unspecified. Any other characters in the format string that are not"
                    " part of a field specifier will be included literally in the output. "
        }, 
        "OMP_DEFAULT_DEVICE": {
            "form" : "str",
            "params" : ["str"],
            "str" : "str",
            "info" : "The OMP_DEFAULT_DEVICE environment variable sets the device number to use in device constructs by setting the initial value of the default-device-var"
                    " ICV.\n\n"
                    "The value of this environment variable must be a non-negative integer value."
        },
        "OMP_MAX_TASK_PRIORITY": {
            "form" : "str",
            "params" : ["str"],
            "str" : "str",
            "info" : "The OMP_MAX_TASK_PRIORITY environment variable controls the use of task priorities by setting the initial value of the max-task-priority-var ICV."
                    " The value of this environment variable must be a non-negative integer.\n\n"
                    # "Example:\n\n"
                    # "\%setenv OMP_MAX_TASK_PRIORITY 20"
        }, 
        "OMP_TARGET_OFFLOAD": {
            "form" : "str",
            "params" : ["str"],
            "str" : "str",
            "info" : "The OMP_TARGET_OFFLOAD environment variable sets the initial value of the target-offload-var ICV. The value of the OMP_TARGET_OFFLOAD "
                    "environment variable must be one of the following:\n\n"
                    "MANDATORY | DISABLED | DEFAULT\n\n"
                    "The MANDATORY value specifies that program execution is terminated if a device construct or device memory routine is encountered and the device is"
                    " not available or is not supported by the implementation. Support for the DISABLED value is implementation defined. If an implementation supports it,"
                    " the behavior is as if the only device is the host device."
        }, 
        "OMP_TOOL": {
            "form" : "str",
            "params" : ["str"],
            "str" : "str",
            "info" : "The OMP_TOOL environment variable sets the tool-var ICV, which controls whether an OpenMP runtime will try to register a first party tool.\n\n"
                    "The value of this environment variable must be one of the following:\n\n"
                    "enabled | disabled\n\n"
                    "If OMP_TOOL is set to any value other than enabled or disabled, the behavior is unspecified. If OMP_TOOL is not defined, the default value for tool-var"
                    " is enabled."
        }, 
        "OMP_TOOL_LIBRARIES": {
            "form" : "str",
            "params" : ["str"],
            "str" : "str",
            "info" : "The OMP_TOOL_LIBRARIES environment variable sets the tool-libraries-var ICV to a list of tool libraries that are considered for use on a device"
                    " on which an OpenMP implementation is being initialized. The value of this environment variable must be a list of names of dynamically-loadable"
                    " libraries, separated by an implementation specific, platform typical separator.\n\n"
                    "If the tool-var ICV is not enabled, the value of tool-libraries-var is ignored. Otherwise, if ompt_start_tool is not visible in the address space"
                    " on a device where OpenMP is being initialized or if ompt_start_tool returns NULL, an OpenMP implementation will consider libraries in the "
                    "tool-libraries-var list in a left to right order. The OpenMP implementation will search the list for a library that meets two criteria: it can "
                    "be dynamically loaded on the current device and it defines the symbol ompt_start_tool. If an OpenMP implementation finds a suitable library, "
                    "no further libraries in the list will be considered. "
        }, 
        "OMP_DEBUG": {
            "form" : "str",
            "params" : ["str"],
            "str" : "str",
            "info" : "The OMP_DEBUG environment variable sets the debug-var ICV, which controls whether an OpenMP runtime collects information that an OMPD library"
                    " may need to support a tool.\n\n"
                    "The value of this environment variable must be one of the following:\n\n"
                    "enabled | disabled\n\n"
                    "If OMP_DEBUG is set to any value other than enabled or disabled then the behavior is implementation defined."
        }, 
        "OMP_ALLOCATOR": {
            "form" : "str",
            "params" : ["str"],
            "str" : "str",
            "info" : "OMP_ALLOCATOR sets the def-allocator-var ICV that specifies the default allocator for allocation calls, directives and clauses that do not specify"
                    " an allocator. The value of this environment variable is a predefined allocator. The value of this environment variable is not case sensitive."
        }
    }
    
    def create(self):
        (self.height,self.width) = getTerminalDimensions()
        self.values = []
        for var in self.variables:
            self.values.append([var, self.parentApp.env[var] if var in self.parentApp.env.keys() else ""])
        self.name = "Environment Variables"
        self.shortcuts = "Save - Ctl+S\t|\tFind - Ctl+F\t|\tQuit - Ctl+Q"
        shortcutbar = self.add(npyscreen.TitleText, scroll_exit=True, name = self.shortcuts, max_height=2, max_width=len(self.shortcuts),
                relx=int((self.width/2)-len(self.shortcuts)/2), color=curses.COLOR_WHITE, editable=False)
        self.grid = self.add(CustomGridColTitles, columns=2, column_width=int(self.width/2)-4, width=self.width-4, select_whole_line=True,
                 col_titles=[" "*int((int(self.width/2)-4)/2-4) + "Variable", " "*int((int(self.width/2)-4)/2-3) + "Value"], values=self.values)

        def on_cancel():
            on_ok()

        def on_ok():
            self.parentApp.change_form(
                self.returnTo,
                resetHistory=True
            )

        def h_on_quit(arg):
            on_cancel()

        def h_on_save(args):
            on_ok()

        def h_on_search(arg):            
            P = EnvSearchPopup()
            P.owner_widget = weakref.proxy(self)
            P.display()
            P.edit()

        def set_env_value(variable, value):
            self.grid.selected_row()[1] = value
            self.parentApp.env[variable] = value

        def on_env_enter():
            self.P.ok_pressed = True
            self.P.exit_editing()
            var = self.grid.selected_row()
            val = self.P.value.value.strip()
            if val != var[1] and self.P.ok_pressed:
                set_env_value(var[0], val)

        def on_cell_clicked():
            var = self.grid.selected_row()
            self.P = EnvPopup()
            self.P.owner_widget = weakref.proxy(self)
            self.P.var_name.value = var[0]
            self.P.value.value = var[1]
            self.P.info.values = prepareList(self.P.columns-3, [self.parameters[var[0]]["info"]])
            self.P.value.on_enter_pressed = on_env_enter
            self.P.display()
            self.P.edit()
            val = self.P.value.value.strip()
            if val != var[1] and self.P.ok_pressed:
                set_env_value(var[0], val)

        key_bindings = {
            "^Q"             : h_on_quit,
            "^S"             : h_on_save,
            "^F"             : h_on_search,
        }

        self.add_handlers(key_bindings)
        self.edit_return_value = False
        self.grid.on_cell_clicked = on_cell_clicked
        self.on_cancel = on_cancel
        self.on_ok = on_ok

    def handle_selection(self, text):
        i = self.variables.index(text)
        self.grid.edit_cell[0] += i - self.grid.edit_cell[0]
        while self.grid.begin_row_display_at  + len(self.grid._my_widgets) - 1 < self.grid.edit_cell[0]:
            self.grid.h_scroll_display_down("")
        while self.grid.edit_cell[0] < self.grid.begin_row_display_at:
            self.grid.h_scroll_display_up("")

    def get_filtered_indexes(self):
        vars = self.variables
        filtered = list(filter(self.filter_element, vars))
        return filtered
    
    def filter_element(self,element):
        return True if self._filter.lower() in element.lower() else False

    def setArgs(self, args):
        if "compiler" in args:
            self.returnTo = args["compiler"]


class EditorForm(npyscreen.FormMultiPageAction):
    OKBUTTON_TYPE = Form_OK_Button
    contents = " "
    fname = ""
    warnings = []
    output = []
    isWarnings = False
    compiler = "MAIN"
    width, height = 0, 0
    def create(self):
        (self.height,self.width) = getTerminalDimensions()
        self.fn2 = self.add(NewTitleFilenameCombo, name="File:")
        self.nextrely+=1
        self.editor = self.add(MultiLineEditNew,scroll_exit=True , max_width=self.width-5, max_height=self.height-6,
                                name="File contents",color="GOOD")

        self.shortcuts = "Compiler - Ctl+E\t|\tSave - Ctl+S\t|\tWarnings - Ctl+W\t|\tQuit - Ctl+Q"
        self.name = "Text Editor ("+self.shortcuts+")"

        self.OK_BUTTON_TEXT = "Save"
        self.CANCEL_BUTTON_TEXT = "Back"

        def on_cancel():
            # TODO: If changes are made, Confirm if user wants to exit without saving
            # npyscreen.notify_yes_no("Exit without saving?")
            self.change_forms()

        def on_ok():
            h_on_save("")
            self.change_forms()

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
            if not self.isWarnings:
                curses.def_prog_mode() #Saves current terminal mode in curses state
                curses.endwin() # Probably causes a memory leak.

                if sys.version_info[0] == 2:
                    raw_input()
                else:
                    input()
                self.isWarnings = True
            else:
                self.isWarnings = False
            curses.reset_prog_mode() # Resets the terminal to the saved state

        key_bindings = {
            "^W"             : h_on_view_warnings,
            "^Q"             : h_on_quit,
            "^E"             : h_on_previous,
            "^S"             : h_on_save,
        }
        self.fn2.setChangeCallBack(self.h_on_file_change)
        self.add_handlers(key_bindings)
        self.edit_return_value = False
        self.on_cancel = on_cancel
        self.on_ok = on_ok

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
        self.add_line(self.height-2, 
                      2,
                      message,
                      self.make_attributes_list(message, curses.A_NORMAL),
                      len(message))

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
        # Tell the App object to change forms.
        self.parentApp.change_form(self.compiler)


class NewMenuListWithShortCuts(npyscreen.wgNMenuDisplay.wgMenuListWithSortCuts):
    _contained_widgets = npyscreen.wgNMenuDisplay.wgMenuLine
    clicked = False
    def handle_mouse_event(self, mouse_event):
        super().handle_mouse_event(mouse_event)
        if self.clicked:
            mouse_id, x, y, z, bstate = mouse_event
            self.h_select_exit("")
            self.clicked = False
        else:
            self.clicked = True


class NewMenuDisplayScreen(fmForm.Form):
    def __init__(self, *args, **keywords):
        super(NewMenuDisplayScreen, self).__init__(*args, **keywords)
        #self._menuListWidget = self.add(multiline.MultiLine, return_exit=True)
        self._menuListWidget = self.add(NewMenuListWithShortCuts, return_exit=True)
        self._menuListWidget.add_handlers({
            ord('q'):       self._menuListWidget.h_exit_down,
            ord('Q'):       self._menuListWidget.h_exit_down,
            ord('x'):       self._menuListWidget.h_select_exit,
            curses.ascii.SP:    self._menuListWidget.h_select_exit,
        })


class NewMenuDisplay(npyscreen.wgNMenuDisplay.MenuViewerController):
    def __init__(self, color='CONTROL', lines=15, columns=39, show_atx=5, show_aty=2, *args, **keywords):
        self._DisplayArea = NewMenuDisplayScreen(lines=lines, 
                                    columns=columns, 
                                    show_atx=show_atx, 
                                    show_aty=show_aty, 
                                    color=color)
        super(NewMenuDisplay, self).__init__(*args, **keywords)


class NewHasMenus(npyscreen.wgNMenuDisplay.HasMenus):
    MENU_DISPLAY_TYPE = NewMenuDisplay


class FormMultiPageActionWithMenusAndSections(npyscreen.FormMultiPageAction, NewHasMenus):
    OKBUTTON_TYPE = Form_OK_Button

    def __init__(self, *args, **keywords):
        super(FormMultiPageActionWithMenusAndSections, self).__init__(*args, **keywords)
        self.initialize_menus()

    def handle_exiting_widgets(self, condition):
        try:
            self.how_exited_handers[condition]()
        except:
            return True

    def new_section(self):
        if not hasattr(self, 'sections'):
            self.sections = [0]
        self.add_page()
        self.sections.append(self._active_page)

    def find_next_editable(self, *args):
        if self.editw != len(self._widgets__):
            value_changed = False
            if not self.cycle_widgets:
                r = list(range(self.editw+1, len(self._widgets__)))
            else:
                r = list(range(self.editw+1, len(self._widgets__))) + list(range(0, self.editw))
            for n in r:
                if self._widgets__[n].editable and not self._widgets__[n].hidden: 
                    self.editw = n
                    value_changed = True
                    break
            if not value_changed:
                if self._active_page < len(self._pages__)-1:
                    if not self._active_page + 1 in self.sections:
                        self.switch_page(self._active_page + 1)
                        self.editw = 0

        self.display()
    
    def find_previous_editable(self, *args):
        if self.editw == 0 or (self.editw > 0 and 
                               not any([self._widgets__[x].editable and not self._widgets__[x].hidden 
                                    for x in range(self.editw-1, -1, -1 )])):
            if self._active_page > 0:
                if not self._active_page in self.sections:
                    self.switch_page(self._active_page-1)
                    self.editw = len(self._widgets__) - 1
        
        if not self.editw == 0:     
            # remember that xrange does not return the 'last' value,
            # so go to -1, not 0! (fence post error in reverse)
            for n in range(self.editw-1, -1, -1 ):
                if self._widgets__[n].editable and not self._widgets__[n].hidden: 
                    self.editw = n
                    break

    def first_editable(self):
        r = list(range(0, len(self._widgets__)))
        for n in r:
            if self._widgets__[n].editable and not self._widgets__[n].hidden: 
                self.editw = n
                break

    def switch_page(self, page, display=True):
        ###
        try:
            if hasattr(self._widgets__[self.editw], 'entry_widget'):
                self._widgets__[self.editw].entry_widget.editing = False ###
        except: pass
        ###
        self._widgets__ = self._pages__[page]
        self._active_page = page
        self.editw = 0
        if display:
            self.display(clear=True)

    def add_line_persistant(self, realy, realx, 
                unicode_string, 
                attributes_list, max_columns, 
                force_ascii=False):
        self.add_line(realy, realx, 
                unicode_string, 
                attributes_list, max_columns, 
                force_ascii=False)



class MainForm(FormMultiPageActionWithMenusAndSections):#SplitForm):
    _filter = ""
    warnings = []
    output = []
    compiler = "gcc"
    CC = "gcc"
    CPP = "g++"
    version = ""
    outPrefix = "./"
    compile_click = None
    prevWidget = 0
    prevWidgetPos = 0
    width, height = 0, 0
    flagtype = "optimization"
    isWarnings = False
    page_index = {
        "optimization" : 0,
        "dumps" : 0,
        "omp" : 0
    }
    shell = "/bin/bash" if os.path.exists("/bin/bash") else "/bin/sh"
    def create(self):
        (self.height,self.width) = getTerminalDimensions()
        self.display_pages = False
        shortcuts = "LLVM - Ctl+T\t\t|\t\tFlag menu - Ctl + X\t\t|\t\tRun - F5\t\t|\t\tFind - Ctl + F\t\t|\t\tResults - Ctl+W\t\t|\t\tEditor - Ctl+E\t\t|\t\tQuit - Ctl+Q"
#LLVM - Ctl+T\t\t|\t\tFlag menu - Ctl + X\t\t|\t\tRun - F5\t\t|\t\tSearch - Ctl + F\t\t|Results - Ctl+W\t\t|\t\tEditor - Ctl+E\t\t|\t\tQuit - Ctl+Q
        def getCompilerVersion():
            proc = subprocess.Popen([self.compiler + " --version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True, env=self.parentApp.env)
            self.lines = 25 if self.height <= 25 else self.height
            r,e = proc.communicate()
            self.version = r if proc.returncode == 0 else e
            self.version = self.version.decode('utf-8').replace(u'\u2018',"'").replace(u'\u2019',"'")
            self.version = self.version[:self.version.find("\n")]
            self.name = "GCC UI " + "(" + self.version + ")"
        getCompilerVersion()

        self.optlevel = ["Os","Og","Oz","O1","O2","O3","Ofast"]

        optinfo = ["Optimize for size. -Os enables all -O2 optimizations except those that often increase code sizeIt also enables -finline-functions, causes the compiler to tune for code size rather than execution speed, and performs further optimizations designed to reduce code size. ",
                "Optimize debugging experience. -Og should be the optimization level of choice for the standard edit-compile-debug cycle, offering a reasonable level of optimization while maintaining fast compilation and a good debugging experience. It is a better choice than -O0 for producing debuggable code because some compiler passes that collect debug information are disabled at -O0.\n\nLike -O0, -Og completely disables a number of optimization passes so that individual options controlling them have no effect. Otherwise -Og enables all -O1 optimization flags except for those that may interfere with debugging",
                "Optimize aggressively for size rather than speed. This may increase the number of instructions executed if those instructions require fewer bytes to encode. -Oz behaves similarly to -Os including enabling most -O2 optimizations. ",
                "Optimize. Optimizing compilation takes somewhat more time, and a lot more memory for a large function.\n\nWith -O, the compiler tries to reduce code size and execution time, without performing any optimizations that take a great deal of compilation time. ",
            "Optimize even more. GCC performs nearly all supported optimizations that do not involve a space-speed tradeoff. As compared to -O, this option increases both compilation time and the performance of the generated code.\n\n-O2 turns on all optimization flags specified by -O1.",   "Optimize yet more. -O3 turns on all optimizations specified by -O2 and also turns on the following optimization flags:\n\n\t-fgcse-after-reload \t-fipa-cp-clone\t-floop-interchange \t-floop-unroll-and-jam \t-fpeel-loops \t-fpredictive-commoning \t-fsplit-loops \t-fsplit-paths \t-ftree-loop-distribution \t-ftree-partial-pre \t-funswitch-loops \t-fvect-cost-model=dynamic \t-fversion-loops-for-strides",                "Disregard strict standards compliance. -Ofast enables all -O3 optimizations. It also enables optimizations that are not valid for all standard-compliant programs. It turns on -ffast-math, -fallow-store-data-races and the Fortran-specific -fstack-arrays, unless -fmax-stack-var-size is specified, and -fno-protect-parens. It turns off -fsemantic-interposition. "]

        self.branching = ["-fthread-jumps", "-fif-conversion", "-fif-conversion2", "-fdelayed-branch","-fhoist-adjacent-loads", "-ftree-loop-if-convert", "-fno-guess-branch-probability", "-freorder-blocks"]

        branchinfo = ["This flag enables the compiler to generate code that takes advantage of conditional jumps to parallelize code that uses threads.",

"This flag enables the compiler to optimize if-else statements by converting them into switch statements or other equivalent code.",

"This flag is an extension of -fif-conversion and enables the compiler to perform more aggressive optimization of if-else statements.",

"This flag enables the compiler to reorder code to delay branching as much as possible, which can improve performance by reducing pipeline stalls.",

"This flag enables the compiler to move adjacent loads to the same address outside of loops to reduce memory access latency.",

"This flag enables the compiler to optimize loop conditions by converting them into if statements or other equivalent code.",

" This flag disables the compiler's branch probability guessing mechanism, which can improve performance by reducing the number of unnecessary branch instructions.",

"This flag enables the compiler to reorder basic blocks to improve the performance of the code."]


#__________________________________________________________


        self.loops = ["-funroll-loops","-floop-parallelize-all", "-ftree-loop-distribute-patterns", "-floop-interchange", "-ftree-loop-vectorize", "-floop-strip-mine", "-ftree-loop-im"]

        loopinfo = ["This option unrolls loops by replicating loop bodies and merging them together, reducing the overhead of loop control and improving instruction pipelining.",

"This option parallelizes all loops that are eligible for parallelization, using OpenMP to distribute the work across multiple cores or processors.",

"This option distributes loop iterations across multiple cores or processors, using a pattern matching algorithm to find and group together iterations that can be executed in parallel.",

"This option reorders loop nests to improve data locality and reduce cache misses.",

"This option vectorizes loops, converting scalar operations to SIMD (single instruction multiple data) instructions that can operate on multiple data elements in parallel",

"This option divides a loop into smaller, more manageable chunks that can fit into cache more efficiently.",

"This option uses induction variable recognition and elimination to simplify loop control and reduce overhead."]

#__________________________________________________________

        self.vectorization = ["-march=armv8.2-a+sve","-march=armv8.2-a+simd", "-ftree-vectorize", "-ftree-loop-vectorize", "-fassociative-math", "-ffast-math", "-ftree-vectorizer-verbose=2", "-freciprocal-math" ]

        vecorizeinfo = ["This option enables the use of the Arm Scalable Vector Extension (SVE) on A64FX.",

"This option enables the use of the NEON on A64FX.",

"This option enables tree-vectorization, which is a high-level vectorization optimization that operates on the abstract syntax tree (AST) representation of the code.",

"This option enables loop-vectorization, which is a lower-level vectorization optimization that operates on the machine code level.",

"This option allows the compiler to reassociate expressions involving floating-point operations, which can improve vectorization.",

"This option enables a set of aggressive floating-point optimizations, including vectorization, that can improve performance but may not be mathematically correct in all cases.",

"This option enables verbose output for the vectorizer, where n is an integer that specifies the level of verbosity (0-3).",

"This option allows the compiler to use reciprocal approximations for floating-point division, which can improve vectorization."]

#____________________________________________________________

        self.scheduling = ["-fschedule-fusion", "-fmodulo-sched", "-fmodulo-sched-allow-regmoves", "-fschedule-insns2", "-fno-sched-interblock", "-fno-sched-spec", "-fsched-pressure", "-fsched-spec-load", "-fsched-stalled-insns", "-fsched-stalled-insns-dep", "-fsched2-use-superblocks", "-fsched-group-heuristic", "-frename-registers"]

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


        self.memory = ["-fgcse", "-fgcse-lm", "-fgcse-sm", "-fgcse-las", "-fgcse-after-reload", "-fauto-inc-dec","-fstore-merging", "-fpredictive-commoning", "-fprefetch-loop-arrays", "-ffloat-store","-fallow-store-data-races", "-fmove-loop-stores"]


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


        self.mathops= ["-ffloat-store", "-ffast-math", "-fno-math-errno", "-funsafe-math-optimizations", "-ffinite-math-only", "-fno-rounding-math", "-fexcess-precision=fast", "-fassociative-math", "-fno-signed-zeros", "-fno-trapping-math"]

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


        self.dumps= ["-S -o asm.s","-g", "-fdump-tree-all", "-fdump-rtl-all", "-fdump-ipa-all", "-fdump-tree-optimized", "-fdump-final-insns", "-fopt-info-vec-all"]

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

        self.openmp = ["-fopenmp"]
        ompinfo = [" Enables recognition of OpenMP* features and tells the parallelizer to generate multi-threaded code based on OpenMP* directives."]

#_____________________________________________________________

        self.m1 = self.add_menu(name="Flag type", shortcut="^X")
        self.mopt = self.m1.addItemsFromList([
            ("Optimizations", self.show_opt_flags),
            ("Dumps", self.show_dump_flags),
            ("Open MP", self.show_omp_flags),
            ("Environment", self.set_environment)
        ])

        self.extLines = 0
        def showHeaderArea(flag_header):
            if self._active_page == 0:
                if len(shortcuts) > self.width-5:
                    bp = []
                    for i in range(0, len(shortcuts), self.width-5):
                        if shortcuts[i] != "|":
                            x = shortcuts[:i].rfind("|")
                            if x != -1:
                                i = x
                        bp.append(i)
                    bp += [None]
                    strs = [shortcuts[bp[i]:bp[i+1]].strip("|\t ") for i in range(len(bp)-1)]
                    # Problems
                    for st in strs:
                        self.add(npyscreen.TitleText, editable=False, name=st, max_height=2, 
                                       relx=int((self.width/2)-len(st)/2))
                        self.extLines += 2
                    self.lines += self.extLines
                else:
                    shortcutbar = self.add(npyscreen.TitleText, editable=False, name = shortcuts, width=len(shortcuts), max_height=2, 
                                       relx=int((self.width/2)-len(shortcuts)/2), labelColor='LABELBOLD')
                self.fn2 = self.add(NewTitleFilenameCombo, name="Filename:")
                self.divider = self.add(npyscreen.TitleText, editable=False, name="_"*(self.width-4), width=self.width-4, relx=2,  
                         labelColor='LABELBOLD')
                self.nextrely+=1
                self.ms = self.add(TitleSelectOneWithCallBack, value = [1,], max_height=4, max_width=int(self.width/2),name="Choose one Optimization Flag", 
                                   values = self.optlevel, scroll_exit=True)
            else:
                self._widgets__.extend(self._pages__[0][:4 + (self.extLines//2)])
            self.nextrely = 14
            self.ms3 = self.add(npyscreen.TitleText, max_height=3, max_width=int(self.width/2), name=flag_header,
                    scroll_exit=True, editable=False)
            
        def add_compile_btn():
            nxt = self.nextrely
            if not hasattr(self, "btn"):
                self.btn = self.add(NewMiniButtonPress, name="Compile", max_height=2,  max_width=int(self.width/2), rely=int(-self.height/7))
                self.btnW = self._widgets__[-1]
            else:
                self._widgets__.append(self.btnW)
                w_proxy = weakref.proxy(self.btnW)
                w_id = self._next_w_id
                self._next_w_id += 1
                self._widgets_by_id[w_id] = w_proxy
            self.nextrely = nxt

        showHeaderArea("Optimization Options:")
        multipage = False

        ms2 = self.add(TitleMultiSelectWithCallBack, max_height=3, max_width=int(self.width/2), value=[], name="Branching",
                values=self.branching, scroll_exit=True)
        if not self.height-5-self.nextrely >= 4:# and not multipage:
            add_compile_btn()
            self.add_page()
            showHeaderArea("Optimization Options:")
            multipage = True
        ms4 = self.add(TitleMultiSelectWithCallBack, max_height=3, max_width=int(self.width/2), value=[], name="Memory",
            values=self.memory, scroll_exit=True)
        if not self.height-5-self.nextrely >= 4:# and not multipage:
            add_compile_btn()
            self.add_page()
            showHeaderArea("Optimization Options:")
            multipage = True
        ms5 = self.add(TitleMultiSelectWithCallBack, max_height=3, max_width=int(self.width/2), value = [], name="vectorization",
                values = self.vectorization, scroll_exit=True)
        if not self.height-5-self.nextrely >= 4:# and not multipage:
            add_compile_btn()
            self.add_page()
            showHeaderArea("Optimization Options:")
            multipage = True
        ms6 = self.add(TitleMultiSelectWithCallBack, max_height=3, max_width=int(self.width/2), value = [], name="Loops",
                values = self.loops, scroll_exit=True)
        if not self.height-5-self.nextrely >= 4:# and not multipage:
            add_compile_btn()
            self.add_page()
            showHeaderArea("Optimization Options:")
            multipage = True
            
        if not self.height-5-self.nextrely >= 4:# and not multipage:
            add_compile_btn()
            self.add_page()
            showHeaderArea("Optimization Options:")
            multipage = True

        ms8 = self.add(TitleMultiSelectWithCallBack, max_height=3, max_width=int(self.width/2), value = [], name="Scheduling",
                values = self.scheduling, scroll_exit=True)
        if not self.height-5-self.nextrely >= 4:# and not multipage:
            add_compile_btn()
            self.add_page()
            showHeaderArea("Optimization Options:")
            multipage = True
        ms9 = self.add(TitleMultiSelectWithCallBack, max_height=3, max_width=int(self.width/2), value = [], name="Mathematical Ops",
                values = self.mathops, scroll_exit=True)
        add_compile_btn()
        #Dumps
        self.new_section()
        showHeaderArea("Dump Options:")
        self.page_index["dumps"] = self._active_page
        ms7 = self.add(TitleSelectOneWithCallBack, max_height=3, max_width=int(self.width/2), value = [], name="Dumps",
                        values = self.dumps, scroll_exit=True)
        add_compile_btn()

        #OpenMP
        self.new_section()
        showHeaderArea("OpenMP options:")
        self.page_index["omp"] = self._active_page
        ms10 = self.add(TitleMultiSelectWithCallBack, max_height=3, max_width=int(self.width/2), value = [], name="OpenMP",
                values = self.openmp, scroll_exit=True)
        add_compile_btn()

        self.switch_page(0)

        # btn = self.add(NewMiniButtonPress, name="Compile", max_height=2, max_width=int(self.width/2), rely=int(-self.height/7))
        #BoX
        self.t1 = self.add(npyscreen.BoxTitle, name = "Info", rely=int(self.divider.rely+self.height*0.1), relx=int(self.width/2+2),
                      max_height=int(self.height*0.6), max_width=int(self.width/2*0.89), scroll_exit=True)

        self.OK_BUTTON_TEXT = "Run"
        self.CANCEL_BUTTON_TEXT = "Quit"

        def on_ok():
            self.prevWidget = self.editw
            if self.fn2.value != None:
                npyscreen.notify_wait("Compiling...", wide=False)
                cmd = self.compiler+" -"+self.optlevel[self.ms.value[0]]+" "
                tmp = " ".join([self.branching[x] for x in ms2.value])+" "
                tmp = tmp + " ".join([self.vectorization[x] for x in ms5.value])+" "
                tmp = tmp + " ".join([self.memory[x] for x in ms4.value])+" "
                tmp = tmp + " ".join([self.loops[x] for x in ms6.value])+" "
                tmp = tmp + " ".join([self.dumps[x] for x in ms7.value])+" "
                tmp = tmp + " ".join([self.scheduling[x] for x in ms8.value])+" "
                tmp = tmp + " ".join([self.mathops[x] for x in ms9.value])+" "
                tmp = tmp + " ".join([self.openmp[x] for x in ms10.value])+" "
                cmd = cmd + tmp.strip()
                cmd = cmd + " " + self.fn2.value
                if len(ms7.value)==0:
                    cmdof = cmd+" -o "+self.outPrefix+"output"
                    run = True
                else:
                    run = False
                    cmdof = cmd
                
                # CallSubShell("clear", wait=False, env=self.parentApp.env)
                cwd = self.fn2.value[:self.fn2.value.rfind("/")]

                rc = CallSubShell(cmdof, wait=False, env=self.parentApp.env, cwd=cwd)
                if rc==0:
                    if run:
                        if self.warnings!=[]:
                            self.output = ["There are warnings"]
                            self.t1.values =  ["There are warnings"]
                            self.t1.update()
                        else:
                            self.t1.values = []
                            self.t1.update()
                        rc2 = CallSubShell(self.outPrefix+"output", env=self.parentApp.env, cwd=cwd)
                        subprocess.Popen(str("rm "+self.outPrefix+"output").split(), env=self.parentApp.env, cwd=cwd).wait()
            else:
                notify_confirm("No file selected!", wide=False)

        def on_cancel():
            self.parentApp.setNextForm(None)
            self.exit_editing()

        def h_on_ok(arg):
            on_ok()

        def h_on_quit(arg):
            on_cancel()

        def h_on_switch(arg):
            self.change_forms()

        def listNavChanged(cursor_line):
            if self.editw == self.prevWidget:
                if currentWidgetIsAList() and cursor_line == self.prevWidgetPos:
                    return False
                else:
                    return True
            else:
                return True
            
        def on_select_file():
            fname = self.fn2.value
            if fname and fname.strip() != "":
                ext_idx = fname.rfind(".") + 1
                if ext_idx > 0:
                    ext = str(fname[ext_idx:])
                    if ext.lower() == "c":
                        self.compiler = self.CC
                        getCompilerVersion()
                    elif ext.lower() == "cpp":
                        self.compiler = self.CPP
                        getCompilerVersion()
                    else:
                        notify_confirm("Only C and C++ programs are supported!", wide=False)
                    self.display()
                else:
                    notify_confirm("Could not recognize file type!", wide=False)
            

        def on_optlvl_change(cursor_line):
            if currentWidgetIsAList() and listNavChanged(cursor_line):
                self.t1.values = prepareList(self.t1.width,[optinfo[cursor_line]])
                self.t1.update()
            self.prevWidgetPos = cursor_line

        def on_branch_change(cursor_line):
            if currentWidgetIsAList() and listNavChanged(cursor_line):
                self.t1.values = prepareList(self.t1.width,[branchinfo[cursor_line]])
                self.t1.update()
            self.prevWidgetPos = cursor_line

        def on_memory_change(cursor_line):
            if currentWidgetIsAList() and listNavChanged(cursor_line):
                self.t1.values = prepareList(self.t1.width,[meminfo[cursor_line]])
                self.t1.update()
            self.prevWidgetPos = cursor_line

        def on_vect_change(cursor_line):
            if currentWidgetIsAList() and listNavChanged(cursor_line):
                self.t1.values = prepareList(self.t1.width,[vecorizeinfo[cursor_line]])
                self.t1.update()
            self.prevWidgetPos = cursor_line

        def on_loops_change(cursor_line):
            if currentWidgetIsAList() and listNavChanged(cursor_line):
                self.t1.values = prepareList(self.t1.width,[loopinfo[cursor_line]])
                self.t1.update()
            self.prevWidgetPos = cursor_line

        def on_dump_change(cursor_line):
            if currentWidgetIsAList() and listNavChanged(cursor_line):
                self.t1.values = prepareList(self.t1.width,[dumpinfo[cursor_line]])
                self.t1.update()
            self.prevWidgetPos = cursor_line

        def on_schedule_change(cursor_line):
            if currentWidgetIsAList() and listNavChanged(cursor_line):
                self.t1.values = prepareList(self.t1.width,[scheduleinfo[cursor_line]])
                self.t1.update()
            self.prevWidgetPos = cursor_line

        def on_math_change(cursor_line):
            if currentWidgetIsAList() and listNavChanged(cursor_line):
                self.t1.values = prepareList(self.t1.width,[mathinfo[cursor_line]])
                self.t1.update()
            self.prevWidgetPos = cursor_line

        def on_omp_change(cursor_line):
            if currentWidgetIsAList() and listNavChanged(cursor_line):
                self.t1.values = prepareList(self.t1.width,[ompinfo[cursor_line]])
                self.t1.update()
            self.prevWidgetPos = cursor_line

        def currentWidgetIsAList():
            wg = self._widgets__[self.editw]
            if type(wg) == TitleSelectOneWithCallBack or type(wg) == TitleMultiSelectWithCallBack:
                return True
            else:
                if self.t1.values == self.output:
                    return False
                self.t1.values = prepareList(self.t1.width, self.output)
                self.t1.update()
                return False

        def h_on_search(args):
            self.allselected = [self.optlevel[self.ms.value[0]]] + \
                [self.branching[x] for x in ms2.value] + \
                [self.vectorization[x] for x in ms5.value] + \
                [self.memory[x] for x in ms4.value] + \
                [self.loops[x] for x in ms6.value] + \
                [self.dumps[x] for x in ms7.value] + \
                [self.scheduling[x] for x in ms8.value] + \
                [self.mathops[x] for x in ms9.value] + \
                [self.openmp[x] for x in ms10.value]
            P = SearchPopup()
            P.owner_widget = weakref.proxy(self)
            P.display()
            P.edit()
            self.selected = [P.statusline.values[x] for x in P.statusline.value]
            notselected = [x for x in P.statusline.values if x not in self.selected]
            unselected = [x for x in notselected if x in self.allselected]
            for flag in self.selected:
                if flag in self.optlevel:
                    self.ms.value = [self.optlevel.index(flag)]
                    sorted(self.ms.value)
                    self.ms.update()
                elif flag in self.vectorization:
                    ms5.value.append(self.vectorization.index(flag))
                    sorted(ms5.value)
                    ms5.update()
                elif flag in self.memory:
                    ms4.value.append(self.memory.index(flag))
                    sorted(ms4.value)
                    ms4.update()
                elif flag in self.loops:
                    ms6.value.append(self.loops.index(flag))
                    sorted(ms6.value)
                    ms6.update()
                elif flag in self.branching:
                    ms2.value.append(self.branching.index(flag))
                    sorted(ms2.value)
                    ms2.update()
                elif flag in self.scheduling:
                    ms8.value.append(self.scheduling.index(flag))
                    sorted(ms8.value)
                    ms8.update()
                elif flag in self.mathops:
                    ms9.value.append(self.mathops.index(flag))
                    sorted(ms9.value)
                    ms9.update()
                elif flag in self.dumps:
                    ms7.value.append(self.dumps.index(flag))
                    sorted(ms7.value)
                    ms7.update()
                elif flag in self.openmp:
                    ms10.value.append(self.openmp.index(flag))
                    sorted(ms10.value)
                    ms10.update()

            for flag in unselected:
                if flag in self.optlevel:
                    self.ms.value.remove(self.optlevel.index(flag))
                    self.ms.update()
                elif flag in self.vectorization:
                    ms5.value.remove(self.vectorization.index(flag))
                    ms5.update()
                elif flag in self.memory:
                    ms4.value.remove(self.memory.index(flag))
                    ms4.update()
                elif flag in self.loops:
                    ms6.value.remove(self.loops.index(flag))
                    ms6.update()
                elif flag in self.branching:
                    ms2.value.remove(self.branching.index(flag))
                    ms2.update()
                elif flag in self.scheduling:
                    ms8.value.remove(self.scheduling.index(flag))
                    ms8.update()
                elif flag in self.mathops:
                    ms9.value.remove(self.mathops.index(flag))
                    ms9.update()
                elif flag in self.dumps:
                    ms7.value.remove(self.dumps.index(flag))
                    ms7.update()
                elif flag in self.openmp:
                    ms10.value.remove(self.openmp.index(flag))
                    ms10.update()

        def h_open_editor(arg):
            self.parentApp.change_form(
                    "EDIT",
                    formArgs = {
                            "fname"   : self.fn2.value if self.fn2.value!=None else "",
                            "warnings": self.warnings,
                            "output"  : self.output,
                            "compiler": "MAIN"
                    },
                    resetHistory=True
            )

        def h_on_view_warnings(args):
            if not self.isWarnings:
                curses.def_prog_mode() #Saves current terminal mode in curses state
                curses.endwin() # Probably causes a memory leak.

                if sys.version_info[0] == 2:
                    raw_input()
                else:
                    input()
                self.isWarnings = True
            else:
                self.isWarnings = False
            curses.reset_prog_mode() # Resets the terminal to the saved state


        def h_on_view_flag_info(args):
            if currentWidgetIsAList():
                self.t1.edit()

        def h_shell(arg): ###
            self.parentApp.change_form(
                    "SH",
                    formArgs = {
                            "compiler": "MAIN"
                    },
                    resetHistory=True
            )

        key_bindings = {
            curses.KEY_F5   : h_on_ok,
            "^Q"            : h_on_quit,
            "^T"            : self.change_forms,
            "^F"            : h_on_search,
            "^W"            : h_on_view_warnings,
            "^E"            : h_open_editor,
            ord('i')        : h_on_view_flag_info
        }

        self.fn2.setChangeCallBack(on_select_file)
        self.ms.entry_widget.setSelectionCallBack(on_optlvl_change)
        ms2.entry_widget.setSelectionCallBack(on_branch_change)
        ms4.entry_widget.setSelectionCallBack(on_memory_change)
        ms5.entry_widget.setSelectionCallBack(on_vect_change)
        ms6.entry_widget.setSelectionCallBack(on_loops_change)
        ms7.entry_widget.setSelectionCallBack(on_dump_change)
        ms8.entry_widget.setSelectionCallBack(on_schedule_change)
        ms9.entry_widget.setSelectionCallBack(on_math_change)
        ms10.entry_widget.setSelectionCallBack(on_omp_change)
        self.add_handlers(key_bindings)
        self.btn.setOnPressed(on_ok)
        self.on_cancel = on_cancel
        self.on_ok = on_ok
        self.edit_return_value = False

    def show_opt_flags(self):
        self.switch_page(self.page_index["optimization"])
        self.first_editable()

    def show_dump_flags(self):
        self.switch_page(self.page_index["dumps"])
        self.first_editable()

    def show_omp_flags(self):
        self.switch_page(self.page_index["omp"])
        self.first_editable()

    def set_environment(self):
        self.parentApp.change_form(
                    "ENV",
                    formArgs = {
                            "compiler": "MAIN"
                    },
                    resetHistory=True
            )

    def get_filtered_indexes(self, selection):
        allflags = self.optlevel + self.branching + self.loops + self.vectorization + self.scheduling \
                    + self.memory + self.mathops + self.dumps + self.openmp
        filtered = list(filter(self.filter_element, allflags))
        selectStatus = []
        if len(filtered) != len(selection):
            for x in filtered:
                selectStatus.append(True if x in self.allselected else False)
        else:
            selectStatus = selection
        return (filtered, selectStatus)
    
    def filter_element(self,element):
        return True if self._filter.lower() in element.lower() else False

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
class LLVMForm(FormMultiPageActionWithMenusAndSections):
    _filter = ""
    warnings = []
    output = []
    compiler = "clang"
    CC = "clang"
    CPP = "clang++"
    version = ""
    outPrefix = "./"
    prevWidget = 0
    prevWidgetPos = 0
    width, height = 0, 0
    isWarnings = False
    flagtype = "optimization"
    page_index = {
        "optimization" : 0,
        "dumps" : 0,
        "omp" : 0
    }
    shell = "/bin/bash" if os.path.exists("/bin/bash") else "/bin/sh"
    def create(self):
        (self.height,self.width) = getTerminalDimensions()
        self.display_pages = False
        shortcuts = "GCC - Ctl+T\t\t|\t\tFlag menu - Ctl + X\t\t|\t\tRun - F5\t\t|\t\tFind - Ctl + F\t\t|\t\tResults - Ctl+W\t\t|\t\tEditor - Ctl+E\t\t|\t\tQuit - Ctl+Q"
        def getCompilerVersion():
            proc = subprocess.Popen([self.compiler + " --version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True, env=self.parentApp.env)
            self.lines = 25 if self.height <= 25 else self.height
            r,e = proc.communicate()
            self.version = r if proc.returncode == 0 else e
            self.version = self.version.decode('utf-8').replace(u'\u2018',"'").replace(u'\u2019',"'")
            self.version = self.version[:self.version.find("\n")]
            self.name = "LLVM UI " + "(" + self.version + ")"
        getCompilerVersion()

#__________________________________________________________

        self.optlevel=["O0", "O1","O2","O3","Ofast","Os", "Oz"]

        optinfo= ["This level turns off all optimizations. It generates code that is easy to debug, but the resulting code may be slower and larger in size.",

"This level enables basic optimizations such as instruction scheduling and register allocation. It is generally safe to use and results in faster code.",

"This level enables more aggressive optimizations such as loop unrolling and function inlining. It can significantly improve performance but may also increase code size.",

"This level enables even more aggressive optimizations than -O2. It can result in faster code but may also increase compile time and code size.",

"This level enables all optimizations that do not violate strict standards compliance. It can result in very fast code but may not be safe to use in all cases.",

"This level optimizes for code size rather than performance. It can be useful for embedded systems or when code size is a primary concern.",

"This level performs even more aggressive optimizations for code size. It can result in significantly smaller code but may also increase compile time."]


#__________________________________________________________

        # self.vectorization = ["-march=armv8.2-a+sve -msve-vector-bits=512","-march=armv8.2-a+simd", "-ftree-vectorize", "-ftree-loop-vectorize", "-fassociative-math", "-ffast-math", "-ftree-vectorizer-verbose=2", "-freciprocal-math" ]
        self.vectorization = ["-march=armv8.2-a+sve -msve-vector-bits=512","-march=armv8.2-a+simd", "-ftree-vectorize", "-fassociative-math", "-ffast-math", "-freciprocal-math" ]

        vectorizeinfo = ["This option enables the use of the Arm Scalable Vector Extension (SVE) on A64FX.",

"This option enables the use of the NEON on A64FX.",

"This option enables tree-vectorization, which is a high-level vectorization optimization that operates on the abstract syntax tree (AST) representation of the code.",

# "This option enables loop-vectorization, which is a lower-level vectorization optimization that operates on the machine code level.",

"This option allows the compiler to reassociate expressions involving floating-point operations, which can improve vectorization.",

"This option enables a set of aggressive floating-point optimizations, including vectorization, that can improve performance but may not be mathematically correct in all cases.",

# "This option enables verbose output for the vectorizer, where n is an integer that specifies the level of verbosity (0-3).",

"This option allows the compiler to use reciprocal approximations for floating-point division, which can improve vectorization."]

#_____________________________________________________________

        self.polly= ["-mllvm -polly"]

        pollyinfo= ["Enables pollly"]


#_____________________________________________________________

        # self.loops=["-funroll-loops", "-floop-parallelize-all", "-floop-strip-mine", "-floop-interchange", "-floop-block"]
        self.loops=["-funroll-loops"]

        loopinfo= ["This option instructs the compiler to unroll loops, which can improve performance by reducing the overhead of loop iteration.",

# "This option enables automatic parallelization of all loops, which can improve performance on multi-core processors.",

# "This option enables loop strip-mining, which involves splitting a loop into smaller sub-loops to improve cache locality and reduce memory traffic.",

# "This option enables loop interchange, which involves swapping the order of nested loops to improve cache locality and reduce memory traffic.",

# "This option enables loop blocking, which involves partitioning a loop into smaller blocks to improve cache locality and reduce memory traffic"
        ]



#___________________________________________________________

        # self.branching =["-fbranch-probabilities", "-fstrict-aliasing", "-fno-branch-count-reg", "-fbranch-target-load-optimize", "-fbranch-target-load-optimize2", "-fno-tree-loop-distribute-patterns", "-fjump-tables", "-fswitch-tables", "-fomit-frame-pointer"]
        self.branching =["-fstrict-aliasing", "-fjump-tables", "-fomit-frame-pointer"]


        branchinfo= [
            # "This option enables the compiler to use profile-guided optimization (PGO) to optimize branches based on the probability of their outcomes. The compiler can use this information to generate code that minimizes the number of mispredicted branches.",

"This option enables the compiler to assume that pointers of different types do not alias, which can allow for more aggressive optimizations, including control-flow optimizations.",

# "This option disables the use of registers to count the number of times a loop has executed. While this can reduce code size, it can also limit the ability of the compiler to optimize control flow.",

# "This option enables an optimization that tries to predict branch targets using load instructions, which can be more accurate than traditional branch prediction.",

# "This option is a more aggressive version of -fbranch-target-load-optimize, which uses multiple load instructions to predict branch targets.",

# "This option disables loop distribution, which is a transformation that can reduce the number of branches in a loop.",

"This flag tells LLVM to use jump tables instead of if-else chains. This can reduce branching and improve performance.",

# "This flag tells LLVM to use switch tables instead of if-else chains. This can reduce branching and improve performance.",

"This flag tells LLVM to not generate a frame pointer for each function call. This can reduce branching and improve performance."]


#_____________________________________________________________


        self.scheduling= ["-mllvm -misched", "-mllvm -misched-early", "-mllvm -pre-RA-sched=fast" "-mllvm -enable-misched"]

        scheduleinfo= ["This flag enables machine instruction scheduling optimizations in LLVM. This can improve scheduling by reordering instructions to reduce stalls and increase the number of instructions that can be executed simultaneously.",

"This flag enables early machine instruction scheduling optimizations in LLVM. This can improve scheduling by scheduling instructions earlier in the pipeline to reduce stalls and increase the number of instructions that can be executed simultaneously.",

"This flag enables faster pre-register allocation machine instruction scheduling optimizations in LLVM. This can improve scheduling by scheduling instructions before register allocation to reduce stalls and increase the number of instructions that can be executed simultaneously.",

"This option enables machine instruction scheduling, which can improve performance by optimizing the order in which instructions are executed."]

#_____________________________________________________________


        # self.mathops = ["-ffloat-store", "-ffast-math", "-funsafe-math-optimizations", "-ffinite-math-only", "-fassociative-math"]
        self.mathops = ["-ffast-math", "-funsafe-math-optimizations", "-ffinite-math-only", "-fassociative-math"]

        mathinfo =[
            # "This flag disables the use of extended precision floating-point arithmetic and forces all intermediate floating-point values to be rounded and stored in memory.",

"This flag enables a set of aggressive floating-point optimizations, including the reordering of operations, the use of approximate math functions, and the removal of certain error checks. However, these optimizations can lead to inaccurate results in some cases.",

"This flag enables additional floating-point optimizations that can result in inaccurate results or undefined behavior in certain cases.",

"This flag restricts floating-point arithmetic to finite values only, excluding infinity and NaN values.",

"This flag enables reordering of floating-point operations that are associative, such as addition and multiplication."]

#____________________________________________________________


        self.dumps= ["-S -o asm.s", "-g", "-fdump-tree-all"]

        dumpinfo = ["This flag tells LLVM to generate an assembly language file (.s) instead of object code.",

"This flag tells LLVM to generate debugging information in the output files. This information can be used by debuggers to map the generated code back to the original source code.",

"Generates all Tree dumps"]

#_____________________________________________________________


        self.openmp = ["-fopenmp"]
        ompinfo = [" Enables recognition of OpenMP* features and tells the parallelizer to generate multi-threaded code based on OpenMP* directives."]

#_____________________________________________________________

        self.m1 = self.add_menu(name="Flag type", shortcut="^X")
        self.mopt = self.m1.addItemsFromList([
            ("Optimizations", self.show_opt_flags),
            ("Dumps", self.show_dump_flags),
            ("Open MP", self.show_omp_flags),
            ("Environment", self.set_environment)
        ])

        self.extLines = 0
        def showHeaderArea(flag_header):
            if self._active_page == 0:
                if len(shortcuts) > self.width-5:
                    bp = []
                    for i in range(0, len(shortcuts), self.width-5):
                        if shortcuts[i] != "|":
                            x = shortcuts[:i].rfind("|")
                            if x != -1:
                                i = x
                        bp.append(i)
                    bp += [None]
                    strs = [shortcuts[bp[i]:bp[i+1]].strip("|\t ") for i in range(len(bp)-1)]
                    for st in strs:
                        self.add(npyscreen.TitleText, editable=False, name=st, max_height=2, 
                                       relx=int((self.width/2)-len(st)/2))
                        self.extLines += 2
                    self.lines += self.extLines
                else:
                    shortcutbar = self.add(npyscreen.TitleText, scroll_exit=True, name = shortcuts, max_height=2, max_width=len(shortcuts),
                        relx=int((self.width/2)-len(shortcuts)/2), labelColor='LABELBOLD', use_two_lines=True, editable=False)
                self.fn2 = self.add(NewTitleFilenameCombo, name="Filename:")
                self.divider = self.add(npyscreen.TitleText, editable=False, name="_"*(self.width-4), width=self.width-4, relx=2,  
                         labelColor='LABELBOLD')
                self.nextrely+=1
                self.ms = self.add(TitleSelectOneWithCallBack, value = [1,], max_height=4, max_width=int(self.width/2),
                                   name="Choose one Optimization Flag", values = self.optlevel, scroll_exit=True)
            else:
                self._widgets__.extend(self._pages__[0][:4 + self.extLines//2])
            self.nextrely = 14
            self.ms3= self.add(npyscreen.TitleText, max_height=3, max_width=int(self.width/2), name=flag_header,
                    editable=False)
        
        def add_compile_btn():
            nxt = self.nextrely
            if not hasattr(self, "btn"):
                self.btn = self.add(NewMiniButtonPress, name="Compile", max_height=2,  max_width=int(self.width/2), rely=int(-self.height/7))
                self.btnW = self._widgets__[-1]
            else:
                self._widgets__.append(self.btnW)
                w_proxy = weakref.proxy(self.btnW)
                w_id = self._next_w_id
                self._next_w_id += 1
                self._widgets_by_id[w_id] = w_proxy
            self.nextrely = nxt

        showHeaderArea("Optimization Options:")
        multipage = False

        ms4= self.add(TitleSelectOneWithCallBack, max_height=3, max_width=int(self.width/2), value = [], name="ENABLE POLLY",
                values = self.polly, scroll_exit=True)
        if not self.height-5-self.nextrely >= 4:# and not multipage:
            add_compile_btn()
            self.add_page()
            showHeaderArea("Optimization Options:")
            multipage = True
        ms2= self.add(TitleMultiSelectWithCallBack, max_height=3, max_width=int(self.width/2), value = [], name="Branching",
                values = self.branching, scroll_exit=True)
        if not self.height-5-self.nextrely >= 4:# and not multipage:
            add_compile_btn()
            self.add_page()
            showHeaderArea("Optimization Options:")
            multipage = True
        ms5= self.add(TitleMultiSelectWithCallBack, max_height=3, max_width=int(self.width/2), value = [], name="vectorization",
                values = self.vectorization, scroll_exit=True)
        if not self.height-5-self.nextrely >= 4:# and not multipage:
            add_compile_btn()
            self.add_page()
            showHeaderArea("Optimization Options:")
            multipage = True
        ms6= self.add(TitleMultiSelectWithCallBack, max_height=3, max_width=int(self.width/2), value = [], name="Loops",
                values = self.loops, scroll_exit=True)
        if not self.height-5-self.nextrely >= 4:# and not multipage:
            add_compile_btn()
            self.add_page()
            showHeaderArea("Optimization Options:")
            multipage = True
        ms8= self.add(TitleSelectOneWithCallBack, max_height=3, max_width=int(self.width/2), value = [], name="Scheduling",
                values = self.scheduling, scroll_exit=True)
        if not self.height-5-self.nextrely >= 4:# and not multipage:
            add_compile_btn()
            self.add_page()
            showHeaderArea("Optimization Options:")
            multipage = True
        ms9= self.add(TitleMultiSelectWithCallBack, max_height=3, max_width=int(self.width/2), value = [], name="Mathematical OPs",
                values = self.mathops, scroll_exit=True)
        add_compile_btn()

        #Dumps
        self.new_section()
        showHeaderArea("Dump Options:")
        self.page_index["dumps"] = self._active_page
        ms7= self.add(TitleSelectOneWithCallBack, max_height=3, max_width=int(self.width/2), value = [], name="Dumps",
                values = self.dumps, scroll_exit=True)
        add_compile_btn()

        #OpenMP
        self.new_section()
        showHeaderArea("OpenMP options:")
        self.page_index["omp"] = self._active_page
        ms10 = self.add(TitleMultiSelectWithCallBack, max_height=3, max_width=int(self.width/2), value = [], name="OpenMP",
                values = self.openmp, scroll_exit=True)
        add_compile_btn()
        
        self.switch_page(0)

        # btn = self.add(NewMiniButtonPress, name="Compile", max_height=2, max_width=int(self.width/2), rely=int(-self.height/7))

        #BoX
        self.t1 = self.add(npyscreen.BoxTitle, name = "Info", rely=int(self.divider.rely+self.height*0.1), relx=int(self.width/2+2),
                      max_height=int(self.height*0.6), max_width=int(self.width/2*0.89), scroll_exit=True)

        self.OK_BUTTON_TEXT = "Run"
        self.CANCEL_BUTTON_TEXT = "Quit"

        def on_ok():
            self.prevWidget = self.editw
            if self.fn2.value != None:
                npyscreen.notify_wait("Compiling...", wide=False)
                cmd = self.compiler+" -"+self.optlevel[self.ms.value[0]]+" "
                tmp = " ".join([self.branching[x] for x in ms2.value])+" "
                tmp = tmp + " ".join([self.vectorization[x] for x in ms5.value])+" "
                tmp = tmp + " ".join([self.polly[x] for x in ms4.value])+" "
                tmp = tmp + " ".join([self.loops[x] for x in ms6.value])+" "
                tmp = tmp + " ".join([self.scheduling[x] for x in ms8.value])+" "
                tmp = tmp + " ".join([self.mathops[x] for x in ms9.value])+" "
                tmp = tmp + " ".join([self.dumps[x] for x in ms7.value])+" "
                tmp = tmp + " ".join([self.openmp[x] for x in ms10.value])+" "
                cmd = cmd + tmp.strip() + " " + self.fn2.value
                if len(ms7.value)==0:
                    cmdof = cmd+" -o "+self.outPrefix+"output"
                    run = True
                else:
                    run = False
                    cmdof = cmd

                cwd = self.fn2.value[:self.fn2.value.rfind("/")]
                # CallSubShell("clear", wait=False, env=self.parentApp.env)
                rc = CallSubShell(cmdof, wait=False, env=self.parentApp.env, cwd=cwd)
                if rc==0:
                    if run:
                        if self.warnings!=[]:
                            self.output = ["There are warnings"]
                            self.t1.values =  ["There are warnings"]
                            self.t1.update()
                        else:
                            self.t1.values = []
                            self.t1.update()
                        rc2 = CallSubShell(self.outPrefix+"output", env=self.parentApp.env, cwd=cwd)
                        subprocess.Popen("rm "+self.outPrefix+"output", shell=True, cwd=cwd).wait()
            else:
                notify_confirm("No file selected!", wide=False)

        def on_cancel():
            self.parentApp.setNextForm(None)
            self.exit_editing()

        def h_on_ok(arg):
            on_ok()

        def h_on_quit(arg):
            on_cancel()

        def h_on_switch(arg):
            self.change_forms()

        def listNavChanged(cursor_line):
            if self.editw == self.prevWidget:
                if currentWidgetIsAList() and cursor_line == self.prevWidgetPos:
                    return False
                else:
                    return True
            else:
                return True
            
        def on_select_file():
            fname = self.fn2.value
            ext_idx = fname.rfind(".") + 1
            if ext_idx > 0:
                ext = str(fname[ext_idx:])
                if ext.lower() == "c":
                    self.compiler = self.CC
                    getCompilerVersion()
                elif ext.lower() == "cpp":
                    self.compiler = self.CPP
                    getCompilerVersion()
                else:
                    notify_confirm("Only C and C++ programs are supported!", wide=False)
                self.display()
            else:
                notify_confirm("Could not recognize file type!", wide=False)

        def on_optlvl_change(cursor_line):
            if currentWidgetIsAList() and listNavChanged(cursor_line):
                self.t1.values = prepareList(self.t1.width,[optinfo[cursor_line]])
                self.t1.update()
            self.prevWidgetPos = cursor_line

        def on_branch_change(cursor_line):
            if currentWidgetIsAList() and listNavChanged(cursor_line):
                self.t1.values = prepareList(self.t1.width,[branchinfo[cursor_line]])
                self.t1.update()
            self.prevWidgetPos = cursor_line

        def on_polly_change(cursor_line):
            if currentWidgetIsAList() and listNavChanged(cursor_line):
                self.t1.values = prepareList(self.t1.width,[pollyinfo[cursor_line]])
                self.t1.update()
            self.prevWidgetPos = cursor_line

        def on_vect_change(cursor_line):
            if currentWidgetIsAList() and listNavChanged(cursor_line):
                self.t1.values = prepareList(self.t1.width,[vectorizeinfo[cursor_line]])
                self.t1.update()
            self.prevWidgetPos = cursor_line

        def on_loops_change(cursor_line):
            if currentWidgetIsAList() and listNavChanged(cursor_line):
                self.t1.values = prepareList(self.t1.width,[loopinfo[cursor_line]])
                self.t1.update()
            self.prevWidgetPos = cursor_line

        def on_dump_change(cursor_line):
            if currentWidgetIsAList() and listNavChanged(cursor_line):
                self.t1.values = prepareList(self.t1.width,[dumpinfo[cursor_line]])
                self.t1.update()
            self.prevWidgetPos = cursor_line

        def on_schedule_change(cursor_line):
            if currentWidgetIsAList() and listNavChanged(cursor_line):
                self.t1.values = prepareList(self.t1.width,[scheduleinfo[cursor_line]])
                self.t1.update()
            self.prevWidgetPos = cursor_line

        def on_math_change(cursor_line):
            if currentWidgetIsAList() and listNavChanged(cursor_line):
                self.t1.values = prepareList(self.t1.width,[mathinfo[cursor_line]])
                self.t1.update()
            self.prevWidgetPos = cursor_line

        def on_omp_change(cursor_line):
            if currentWidgetIsAList() and listNavChanged(cursor_line):
                self.t1.values = prepareList(self.t1.width,[ompinfo[cursor_line]])
                self.t1.update()
            self.prevWidgetPos = cursor_line

        def currentWidgetIsAList():
            wg = self._widgets__[self.editw]
            if type(wg) == TitleSelectOneWithCallBack or type(wg) == TitleMultiSelectWithCallBack:
                return True
            else:
                self.t1.values = prepareList(self.t1.width, self.output)
                self.t1.update()
                return False

        def h_on_search(args):
            self.allselected = [self.optlevel[self.ms.value[0]]] + \
                [self.branching[x] for x in ms2.value] + \
                [self.vectorization[x] for x in ms5.value] + \
                [self.polly[x] for x in ms4.value] + \
                [self.loops[x] for x in ms6.value] + \
                [self.dumps[x] for x in ms7.value] + \
                [self.scheduling[x] for x in ms8.value] + \
                [self.mathops[x] for x in ms9.value] + \
                [self.openmp[x] for x in ms10.value]
            P = SearchPopup()
            P.owner_widget = weakref.proxy(self)
            P.display()
            P.edit()
            self.selected = [P.statusline.values[x] for x in P.statusline.value]
            notselected = [x for x in P.statusline.values if x not in self.selected]
            unselected = [x for x in notselected if x in self.allselected]
            for flag in self.selected:
                if flag in self.optlevel:
                    self.ms.value.append(self.optlevel.index(flag))
                    sorted(self.ms.value)
                    self.ms.update()
                elif flag in self.vectorization:
                    ms5.value.append(self.vectorization.index(flag))
                    sorted(ms5.value)
                    ms5.update()
                elif flag in self.polly:
                    ms4.value.append(self.polly.index(flag))
                    sorted(ms4.value)
                    ms4.update()
                elif flag in self.loops:
                    ms6.value.append(self.loops.index(flag))
                    sorted(ms6.value)
                    ms6.update()
                elif flag in self.branching:
                    ms2.value.append(self.branching.index(flag))
                    sorted(ms2.value)
                    ms2.update()
                elif flag in self.scheduling:
                    ms8.value.append(self.scheduling.index(flag))
                    sorted(ms8.value)
                    ms8.update()
                elif flag in self.mathops:
                    ms9.value.append(self.mathops.index(flag))
                    sorted(ms9.value)
                    ms9.update()
                elif flag in self.dumps:
                    ms7.value.append(self.dumps.index(flag))
                    sorted(ms7.value)
                    ms7.update()
                elif flag in self.openmp:
                    ms10.value.append(self.openmp.index(flag))
                    sorted(ms10.value)
                    ms10.update()

            for flag in unselected:
                if flag in self.optlevel:
                    self.ms.value.remove(self.optlevel.index(flag))
                    self.ms.update()
                elif flag in self.vectorization:
                    ms5.value.remove(self.vectorization.index(flag))
                    ms5.update()
                elif flag in self.polly:
                    ms4.value.remove(self.polly.index(flag))
                    ms4.update()
                elif flag in self.loops:
                    ms6.value.remove(self.loops.index(flag))
                    ms6.update()
                elif flag in self.branching:
                    ms2.value.remove(self.branching.index(flag))
                    ms2.update()
                elif flag in self.scheduling:
                    ms8.value.remove(self.scheduling.index(flag))
                    ms8.update()
                elif flag in self.mathops:
                    ms9.value.remove(self.mathops.index(flag))
                    ms9.update()
                elif flag in self.dumps:
                    ms7.value.remove(self.dumps.index(flag))
                    ms7.update()
                elif flag in self.openmp:
                    ms10.value.remove(self.openmp.index(flag))
                    ms10.update()

        def h_open_editor(arg):
            self.parentApp.change_form(
                    "EDIT",
                    formArgs = {
                            "fname"   : self.fn2.value if self.fn2.value!=None else "",
                            "warnings": self.warnings,
                            "output"  : self.output,
                            "compiler": "LLVM"
                    },
                    resetHistory=True
            )

        def h_on_view_warnings(args):
            if not self.isWarnings:
                curses.def_prog_mode() #Saves current terminal mode in curses state
                curses.endwin() # Probably causes a memory leak.

                if sys.version_info[0] == 2:
                    raw_input()
                else:
                    input()
                self.isWarnings = True
            else:
                self.isWarnings = False
            curses.reset_prog_mode() # Resets the terminal to the saved state

        def h_on_view_flag_info(args):
            if currentWidgetIsAList():
                self.t1.edit()

        key_bindings = {
            curses.KEY_F5   : h_on_ok,
            "^Q"            : h_on_quit,
            "^T"            : self.change_forms,
            "^F"            : h_on_search,
            "^W"            : h_on_view_warnings,
            "^E"            : h_open_editor,
            ord('i')        : h_on_view_flag_info
        }

        self.fn2.setChangeCallBack(on_select_file)
        self.ms.entry_widget.setSelectionCallBack(on_optlvl_change)
        ms2.entry_widget.setSelectionCallBack(on_branch_change)
        ms4.entry_widget.setSelectionCallBack(on_polly_change)
        ms5.entry_widget.setSelectionCallBack(on_vect_change)
        ms6.entry_widget.setSelectionCallBack(on_loops_change)
        ms7.entry_widget.setSelectionCallBack(on_dump_change)
        ms8.entry_widget.setSelectionCallBack(on_schedule_change)
        ms9.entry_widget.setSelectionCallBack(on_math_change)
        ms10.entry_widget.setSelectionCallBack(on_omp_change)
        self.add_handlers(key_bindings)
        self.btn.whenPressed = on_ok
        self.on_cancel = on_cancel
        self.on_ok = on_ok
        self.edit_return_value = False

    def show_opt_flags(self):
        self.switch_page(self.page_index["optimization"])
        self.first_editable()

    def show_dump_flags(self):
        self.switch_page(self.page_index["dumps"])
        self.first_editable()

    def show_omp_flags(self):
        self.switch_page(self.page_index["omp"])
        self.first_editable()

    def set_environment(self):
        self.parentApp.change_form(
                    "ENV",
                    formArgs = {
                            "compiler": "LLVM"
                    },
                    resetHistory=True
            )

    def get_filtered_indexes(self, selection):
        allflags = self.optlevel + self.branching + self.loops + self.vectorization + self.scheduling \
                    + self.polly + self.mathops + self.dumps + self.openmp
        filtered = list(filter(self.filter_element, allflags))
        selectStatus = []
        if len(filtered) != len(selection):
            for x in filtered:
                selectStatus.append(True if x in self.allselected else False)
        else:
            selectStatus = selection
        return (filtered, selectStatus)
    
    def filter_element(self,element):
        return True if self._filter.lower() in element.lower() else False

    def _remake_filter_cache(self):
        pass

    def change_forms(self, *args, **keywords):
        # Tell the MyTestApp object to change forms.
        self.parentApp.change_form("MAIN")

    def afterEditing(self):
        pass

    def while_editing(self,widget):
        self.prevWidget = self.editw+1


###Utility functions

def getTerminalDimensions():
    return curses.initscr().getmaxyx()

def prepareList(width, ls, trimItems=True):
    ls1 = []
    for x in ls:
        ls1 = ls1 + x.split("\n")

    ls2 = []
    for ind in range(0, len(ls1)):
        s = ls1[ind]
        if len(s)>width-5:
            indices = [x for x in range(0,len(s),width-5)] + [None]
            
            for ind in range(0, len(indices)):
                index = indices[ind]
                if index == 0 or index == None:
                    continue
                prev = indices[ind-1]
                next = indices[ind+1]
                currStr = s[prev:index]
                nxtStr = s[index:next]
                if currStr.strip()!="" and (currStr[-1] != " " or nxtStr[-1] != " "):
                    x = currStr.rfind(" ") 
                    indices[ind] = indices[ind-1] + x  if x > 0 else width-5
                    if indices[ind + 1] != None and indices[ind + 1] - indices[ind] > width-5:
                        indices[ind + 1] -= indices[ind + 1] - indices[ind] - (width-5)
            if len(indices) > 2 and len(s) - indices[-2] > (width-5):
                s2 = s[indices[-2]:indices[-2]+(width-5)]
                x = s2.rfind(" ")
                if x > 0:
                    indices.insert(len(indices) - 1, indices[-2] + x)
                else:
                    indices.insert(len(indices) - 1, indices[-2] + (width-5))

            sublist = [s[indices[i]:indices[i+1]] for i in range(len(indices)-1)]
            ls2 = ls2 + sublist
        else:
            ls2.append(s)
    if trimItems:
        ls2 = [x.strip() for x in ls2]
    return [" "] + ls2

def find_nth(haystack, needle, n):
    start = haystack.find(needle)
    while start >= 0 and n > 1:
        start = haystack.find(needle, start+len(needle))
        n -= 1
    return start


def CallSubShell(subshell, clear=False, wait=True, env=None, cwd="."): # , env=None):
    """Call this function if you need to execute an external command in a subshell (os.system).  All the usual warnings apply -- the command line will be
    expanded by the shell, so make sure it is safe before passing it to this function."""
    curses.def_prog_mode() #Saves current terminal mode in curses state
    curses.endwin() # Probably causes a memory leak.

    if clear:
        subprocess.Popen("clear", env=env).wait()
    subprocess.Popen(str("echo $ %s\n" % (subshell)).split(), env=env).wait()
    rtn = subprocess.Popen(str("%s" % (subshell)).split(), stderr=sys.stdout.buffer, env=env, cwd=cwd).wait()

    if wait or rtn != 0:
        if sys.version_info[0] == 2:
            raw_input("\n\nPress enter to continue...")
        else:
            input("\n\nPress enter to continue...")
    curses.reset_prog_mode() # Resets the terminal to the saved state

    return rtn

###Custom Widgets

class NewMiniButtonPress(npyscreen.MiniButtonPress):
    when_pressed_function = None
    def __init__(self, screen, when_pressed_function=None, *args, **keywords):
        super(NewMiniButtonPress, self).__init__(screen, when_pressed_function, *args, **keywords)
        if when_pressed_function:
            self.when_pressed_function = when_pressed_function

    def handle_mouse_event(self, mouse_event):
        mouse_id, rel_x, rel_y, z, bstate = self.interpret_mouse_event(mouse_event)
        self.whenPressed()

    def whenPressed(self):
        super().whenPressed()
        if self.when_pressed_function:
            self.when_pressed_function()

    def setOnPressed(self, onPressed):
        self.when_pressed_function = onPressed

class NewMiniButton(npyscreen.MiniButton):
    clicked = False
    def __init__(self, screen, name='Button', cursor_color=None, *args, **keywords):
        super().__init__(screen, name, cursor_color, *args, **keywords)
        self.parent.editw = len(self.parent._widgets__)

    def handle_mouse_event(self, mouse_event):
        if self.clicked:
            self.clicked = False
            mouse_id, rel_x, rel_y, z, bstate = self.interpret_mouse_event(mouse_event)
            self.h_select_exit("")
        else:
            self.clicked = True


class MultiLineEditNew(npyscreen.MultiLineEdit):
    clicked = False
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
    
    def handle_mouse_event(self, mouse_event):
        if not self.clicked and self.value != "":
            self.clicked = True
            mouse_id, x, y, z, bstate = mouse_event
            ls = self.get_value_as_list()
            pos = len("".join([s + " " for s in ls[:self.start_display_at + y - 4]]))
            pos += x - 2 if x - 2 <= len(ls[self.start_display_at + y-4]) else len(ls[self.start_display_at + y-4])
            self.cursor_position = pos
            self.display()
        else:
            self.clicked = False

## File selector

class CustomFileGrid(fmFileSelector.FileGrid):
    clicked = False
    def set_up_handlers(self):
        super(fmFileSelector.FileGrid, self).set_up_handlers()
        self.handlers.update ({
            curses.ascii.NL:    self.h_select_file,
            curses.ascii.CR:    self.h_select_file,
            curses.ascii.SP:    self.h_select_file,
        })
        self.handlers.pop(curses.ascii.ESC)

    def handle_mouse_event(self, mouse_event):
        super().handle_mouse_event(mouse_event)
        if not self.clicked:
            self.h_select_file("")
            self.clicked = True
        else: 
            self.clicked = False
        

class CustomFileCommand(fmFileSelector.FileCommand):
    def set_up_handlers(self):
        super(CustomFileCommand, self).set_up_handlers()
        self.handlers.pop(curses.ascii.ESC)


class ClickFileSelector(fmFileSelector.FileSelector):
    MAIN_WIDGET_CLASS   = CustomFileGrid
    COMMAND_WIDGET_CLASS= fmFileSelector.FileCommand
    def __init__(self,
    select_dir=False, #Select a dir, not a file
    must_exist=False, #Selected File must already exist
    confirm_if_exists=True,
    sort_by_extension=True,
    *args, **keywords):
        self.select_dir = select_dir
        self.must_exist = must_exist
        self.confirm_if_exists = confirm_if_exists
        self.sort_by_extension = sort_by_extension

        super(ClickFileSelector, self).__init__(
            select_dir, must_exist,
            confirm_if_exists,
            sort_by_extension,
            *args, **keywords)
    
    def set_up_handlers(self):
        super().set_up_handlers()
        self.handlers.update({curses.ascii.ESC: self.h_exit_escape2})
        self.handlers.update({curses.ascii.ESC: self.h_exit_escape2})

    def h_exit_escape2(self, _input):
        # super().h_exit_escape(_input)
        self.exit_editing()


def selectFile(starting_value=None, *args, **keywords):
    F = ClickFileSelector(*args, **keywords)
    F.set_colors()
    F.wCommand.show_bold = True
    if starting_value:
        if not os.path.exists(os.path.abspath(os.path.expanduser(starting_value))):
            F.value = os.getcwd()
        else:
            F.value = starting_value
            F.wCommand.value = starting_value
    else:
        F.value = os.getcwd()
    F.update_grid()
    F.display()
    F.edit()    
    return F.wCommand.value

class NewFilenameCombo(npyscreen.FilenameCombo):
    onChangeCallBack = None
    clicked = False
    def h_change_value(self, *args, **keywords):
        self.value = selectFile(
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
    
    def handle_mouse_event(self, mouse_event):
        #mouse_id, x, y, z, bstate = mouse_event
        #rel_mouse_x = x - self.relx - self.parent.show_atx
        if not self.clicked:
            self.clicked = True
            mouse_id, rel_x, rel_y, z, bstate = self.interpret_mouse_event(mouse_event)
            self.cursor_position = rel_x + self.begin_at

            self.display()
            self.h_change_value()
        else:
            self.clicked = False
            


class NewTitleFilenameCombo(npyscreen.TitleFilenameCombo):
    _entry_type = NewFilenameCombo

    def setChangeCallBack(self, callback):
        self.entry_widget.onChangeCallBack = callback

##
    
class SelectOneWithCallBack(npyscreen.SelectOne):
     selectionCallBack = None

     def _before_print_lines(self):
         if self.selectionCallBack!=None:
            self.selectionCallBack(self.cursor_line)

     def setSelectionCallBack(self,callBack=None):
         self.selectionCallBack = callBack

     def handle_mouse_event(self, mouse_event):
         # unfinished
         #mouse_id, x, y, z, bstate = mouse_event
         #self.cursor_line = y - self.rely - self.parent.show_aty + self.start_display_at
         old_cl = self.cursor_line ###
         
         mouse_id, rel_x, rel_y, z, bstate = self.interpret_mouse_event(mouse_event)
         self.cursor_line = rel_y // self._contained_widget_height + self.start_display_at
         
         # Check if the checkbox is the area that was clicked
         isCheckBox = rel_x >= 0 and rel_x < 3
         if old_cl == self.cursor_line and bstate == 1 and isCheckBox: ###
             if not old_cl in self.value:
                 self.value = [old_cl]
         ##if self.cursor_line > len(self.values):
         ##    self.cursor_line = len(self.values)
         self.display()


class TitleSelectOneWithCallBack(npyscreen.TitleSelectOne):
    _entry_type = SelectOneWithCallBack


class MultiSelectWithCallBack(npyscreen.MultiSelect):
     selectionCallBack = None

     def _before_print_lines(self):
         if self.selectionCallBack!=None:
            self.selectionCallBack(self.cursor_line)

     def setSelectionCallBack(self,callBack=None):
         self.selectionCallBack = callBack

     def handle_mouse_event(self, mouse_event):
         # unfinished
         #mouse_id, x, y, z, bstate = mouse_event
         #self.cursor_line = y - self.rely - self.parent.show_aty + self.start_display_at
         old_cl = self.cursor_line ###
         
         mouse_id, rel_x, rel_y, z, bstate = self.interpret_mouse_event(mouse_event)
         self.cursor_line = rel_y // self._contained_widget_height + self.start_display_at
         
         # Check if the checkbox is the area that was clicked
         isCheckBox = rel_x >= 0 and rel_x < 3
         if old_cl == self.cursor_line and bstate == 1 and isCheckBox: ###
             if old_cl in self.value:
                 self.value.remove(old_cl)
             else:
                 self.value.append(old_cl)
         ##if self.cursor_line > len(self.values):
         ##    self.cursor_line = len(self.values)
         self.display()


class TitleMultiSelectWithCallBack(npyscreen.TitleMultiSelect):
    _entry_type = MultiSelectWithCallBack


class ResizableMultiLine(MultiLine):
    MORE_LABEL = "- more -"

    def resize(self):
        super(MultiLine, self).resize()
        self.make_contained_widgets2()
        self.reset_display_cache()
        self.display()

    def make_contained_widgets2(self, ):
        self.parent_widget.make_contained_widget(contained_widget_arguments=self.parent_widget.contained_widget_arguments)


class ResizableBoxTitle(npyscreen.wgboxwidget.BoxTitle):
    _contained_widget = ResizableMultiLine

    def __init__(self, screen, contained_widget_arguments=None, *args, **keywords):
        super(npyscreen.wgboxwidget.BoxTitle, self).__init__(screen, *args, **keywords)
        self.contained_widget_arguments = None
        self.key_words = keywords
        if contained_widget_arguments:
            self.contained_widget_arguments = contained_widget_arguments
            self.make_contained_widget(contained_widget_arguments=contained_widget_arguments)
        else:
            self.make_contained_widget()
        if 'editable' in keywords:
            self.entry_widget.editable=keywords['editable']
        if 'value' in keywords:
            self.value = keywords['value']
        if 'values' in keywords:
            self.values = keywords['values']
        if 'scroll_exit' in keywords:
            self.entry_widget.scroll_exit = keywords['scroll_exit']
        if 'slow_scroll' in keywords:
            self.entry_widget.scroll_exit = keywords['slow_scroll']

    def make_contained_widget(self, contained_widget_arguments=None):
        self._my_widgets = []
        width = self.width-4
        if width < 3: width = 3
        height = self.height-2
        if height < 4: height = 4
        if contained_widget_arguments:
            self._my_widgets.append(self._contained_widget(self.parent, 
                                rely=self.rely+1, relx = self.relx+2, 
                                max_width=width,
                                max_height=height,
                                height=height,
                                values=self.values,
                                **contained_widget_arguments
                            ))
        else:
            self._my_widgets.append(self._contained_widget(self.parent, 
                                rely=self.rely+1, relx = self.relx+2, 
                                max_width=width,
                                max_height=height,
                                height=height,
                                values=self.values,
                            ))
        self.entry_widget = weakref.proxy(self._my_widgets[0])
        self.entry_widget.parent_widget = weakref.proxy(self)


class CustomGridColTitles(npyscreen.wggridcoltitles.GridColTitles, npyscreen.SimpleGrid):
    mouse_clicked = False
    mouse_click_active = False
    def __init__(self, screen, col_titles = None, *args, **keywords):
        self.on_cell_clicked = None
        super(CustomGridColTitles, self).__init__(screen,  col_titles, *args, **keywords)

    def display_value(self, vl):
        padding = int(self._column_width/2 - len(vl)/2) 
        if padding < 0: padding = 0
        return str(5*" " + vl)
    
    def make_contained_widgets(self):
        self.row_height = 3
        super(CustomGridColTitles, self).make_contained_widgets()

    def set_up_handlers(self):
        super(npyscreen.SimpleGrid, self).set_up_handlers()
        self.handlers = {
                    curses.KEY_UP:      self.h_move_line_up,
                    curses.KEY_LEFT:    self.h_move_cell_left,
                    curses.KEY_DOWN:    self.h_move_line_down,
                    curses.KEY_RIGHT:   self.h_move_cell_right,
                    "k":                self.h_move_line_up,
                    "h":                self.h_move_cell_left,
                    "j":                self.h_move_line_down,
                    "l":                self.h_move_cell_right,
                    curses.KEY_NPAGE:   self.h_move_page_down,
                    curses.KEY_PPAGE:   self.h_move_page_up,
                    curses.KEY_HOME:    self.h_show_beginning,
                    curses.KEY_END:     self.h_show_end,
                    ord('g'):           self.h_show_beginning,
                    ord('G'):           self.h_show_end,
                    curses.ascii.TAB:   self.h_exit,
                    curses.KEY_BTAB:     self.h_exit_up,
                    '^P':               self.h_exit_up,
                    '^N':               self.h_exit_down,
                    ord('q'):       self.h_exit,
                    curses.ascii.ESC:   self.h_exit,
                    curses.KEY_MOUSE:    self.h_exit_mouse,
                    curses.ascii.SP: self.cell_clicked,
                    curses.ascii.CR: self.cell_clicked,
                    curses.ascii.NL: self.cell_clicked
                }

        self.complex_handlers = [
                    ]

    def cell_clicked(self, arg=""):
        if self.on_cell_clicked:
            self.on_cell_clicked()

    def handle_mouse_event(self, mouse_event):
        super().handle_mouse_event(mouse_event)
        if self.mouse_clicked and not self.mouse_click_active:
            self.mouse_click_active = True
            self.cell_clicked()
            self.mouse_clicked = False
            self.mouse_click_active = False
        else:
            self.mouse_clicked = True


class SearchPopup(Popup.Popup):
    OKBUTTON_TYPE = NewMiniButton
    def create(self):
        super(SearchPopup, self).create()
        self.filterbox = self.add(titlefield.TitleText, name='Find:', )
        self.nextrely += 1
        self.statusline = self.add(TitleMultiSelectWithCallBack, color='LABEL',name="Results")
	
    def updatestatusline(self):
        self.owner_widget._filter   = self.filterbox.value
        filter_result = self.owner_widget.get_filtered_indexes([(x in self.statusline.value) for x in range(0, len(self.statusline.values))])
        filtered_lines = filter_result[0]
        filtered_selected = filter_result[1]
        self.statusline.values = filtered_lines
        self.statusline.value = [x for x in range(0, len(filtered_selected)) if filtered_selected[x]]

    def adjust_widgets(self):
        self.updatestatusline()
        self.statusline.display()


class EnvPopup(Popup.ActionPopup):
    class OK_Button(npyscreen.wgbutton.MiniButtonPress):
        def whenPressed(self):
            return self.parent._on_ok()

        def handle_mouse_event(self, mouse_event):
            mouse_id, rel_x, rel_y, z, bstate = self.interpret_mouse_event(mouse_event)
            self.whenPressed()
    
    class Cancel_Button(npyscreen.wgbutton.MiniButtonPress):
        def whenPressed(self):
            return self.parent._on_cancel()
        
        def handle_mouse_event(self, mouse_event):
            mouse_id, rel_x, rel_y, z, bstate = self.interpret_mouse_event(mouse_event)
            self.whenPressed()
    
    OKBUTTON_TYPE = OK_Button
    CANCELBUTTON_TYPE = Cancel_Button

    ok_pressed = False
    (height, width) = getTerminalDimensions()
    DEFAULT_LINES = 25
    def create(self):
        super(EnvPopup, self).create()
        (self.height, self.width) = getTerminalDimensions()
        self.var_name = self.add(TitleTextEnterAction, name="Variable", editable=False)
        self.nextrely += 1
        self.value = self.add(TitleTextEnterAction, name="Value")
        self.nextrely += 1
        self.info = self.add(npyscreen.BoxTitle, name="Info", editable=True)

    def adjust_widgets(self):
        pass

    def on_ok(self):
        self.ok_pressed = True
        return super().on_ok()
    
    def on_cancel(self):
        self.ok_pressed = False
        return super().on_cancel()


class EnvSearchPopup(Popup.Popup):
    OKBUTTON_TYPE = NewMiniButton
    def create(self):
        super(EnvSearchPopup, self).create()
        self.filterbox = self.add(titlefield.TitleText, name='Find:', )
        self.nextrely += 1
        self.statusline = self.add(npyscreen.BoxTitle, color='LABEL',name="Results")
        self.statusline.entry_widget.add_handlers({
            curses.ascii.SP: self.result_selected,
            curses.ascii.CR: self.result_selected,
            curses.ascii.NL: self.result_selected
        })

    def result_selected(self, arg):
        txt = self.statusline.entry_widget.values[self.statusline.entry_widget.cursor_line]
        self.on_ok()
        self.owner_widget.handle_selection(txt)
	
    def updatestatusline(self):
        self.owner_widget._filter   = self.filterbox.value
        filter_result = self.owner_widget.get_filtered_indexes()
        filtered_indices = filter_result
        self.statusline.values = filtered_indices

    def adjust_widgets(self):
        self.updatestatusline()
        self.statusline.display()

    def on_ok(self):
        self.exit_editing()
        

class Popup2(Popup.Popup):
    OKBUTTON_TYPE = NewMiniButton


class PopupWide2(Popup2):
    OKBUTTON_TYPE = NewMiniButton
    DEFAULT_LINES      = 14
    DEFAULT_COLUMNS    = None
    SHOW_ATX           = 0
    SHOW_ATY           = 0


def notify_confirm(message, title="Message", form_color='STANDOUT', wrap=True, wide=False,
                    editw = 0,):
    message = utilNotify._prepare_message(message)
    if wide:
        F = PopupWide2(name=title, color=form_color)
    else:
        F   = Popup2(name=title, color=form_color)
    F.preserve_selected_widget = True
    mlw = F.add(npyscreen.Pager,)
    mlw_width = mlw.width-1
    if wrap:
        message = utilNotify._wrap_message_lines(message, mlw_width)
    else:
        message = message.split("\n")
    mlw.values = message
    F.editw = editw
    F.edit()


class TitleTextEnterAction(npyscreen.TitleText):
    def __init__(self, screen, 
        begin_entry_at = 16, 
        field_width = None,
        value = None,
        use_two_lines = None,
        hidden=False,
        labelColor='LABEL',
        allow_override_begin_entry_at=True,
        **keywords):
        super(TitleTextEnterAction, self).__init__(screen, 
                                            begin_entry_at, 
                                            field_width,
                                            value,
                                            use_two_lines,
                                            hidden,
                                            labelColor,
                                            allow_override_begin_entry_at,
                                            **keywords)
        self.on_enter_pressed = None
        self.set_handlers()

    def set_handlers(self):
        handlers = {
            curses.ascii.NL:     self.enter_action,
            curses.ascii.CR:     self.enter_action,
        }
        self.add_handlers(handlers)

    def enter_action(self, arg):
        if self.on_enter_pressed:
            self.on_enter_pressed()

###


####

if __name__=="__main__":
    App = TUIApp()
    App.run()

