# -*- python -*-
#
#       OpenAlea.OALab: Multi-Paradigm GUI
#
#       Copyright 2014 INRIA - CIRAD - INRA
#
#       File author(s): Julien Coste <julien.coste@inria.fr>
#
#       File contributor(s):
#
#       Distributed under the Cecill-C License.
#       See accompanying file LICENSE.txt or copy at
#           http://www.cecill.info/licences/Licence_CeCILL-C_V1-en.html
#
#       OpenAlea WebSite : http://openalea.gforge.inria.fr
#
###############################################################################
from openalea.core.model import Model
from openalea.oalab.model.parse import parse_docstring_r, get_docstring_r, parse_functions_r

# TODO : refactor (like class PythonModel in python.py)

class RModel(Model):
    default_name = "R"
    default_file_name = "script.r"
    pattern = "*.r"
    extension = "r"
    icon = ":/images/resources/RLogo.png"
    mimetype = "text/x-r"

    def __init__(self, **kwargs):
        super(RModel, self).__init__(**kwargs)
        self._step = None
        self._animate = None
        self._init = None
        self.has_run = False

        # If path doesn't exists, that means all content is in memory (passed in constructor for example)
        # So we need to parse it
        if not self.exists():
            self.parse()

    def get_documentation(self):
        """
        :return: a string with the documentation of the model
        """
        self.read()
        if self._doc:
            return self._doc
        else:
            return """
<H1><IMG SRC=%s
 ALT="icon"
 HEIGHT=25
 WIDTH=25
 TITLE="R logo">R language</H1>

more informations: http://www.r-project.org/
"""%str(self.icon)

    def repr_code(self):
        """
        :return: a string representation of model to save it on disk
        """
        return self.code

    def r_options(self, namespace):
        cmd = self.cmdline
        print self.inputs_info
        l = self.inputs_info
        input_names = [input.name for input in l]
        input_names= [name for name in input_names if name in namespace]
        #input_values = [input.split('=')[1] for input in l]

        if input_names:
            cmd+= ' -i %s'%(','.join(input_names))

        l = self.outputs_info
        output_names = [input.name for input in l]
        if output_names:
            cmd+= ' -o %s'%(','.join(output_names))

        print cmd

        return cmd

    def _universal_run(self,  code, *args, **kwargs):
        """ This method is used by others...
        """
        self.inputs = args
        user_ns = self._prepare_namespace()

        cmdline = self.r_options(user_ns)
        
        from openalea.core.service.ipython import interpreter
        interp = interpreter()
        if not self.has_run:
            try:
                interp.run_line_magic('load_ext','rpy2.ipython') #better as it solves display error but neeeds rpy2 > 2.4.2
            except ImportError:
                interp.run_line_magic('load_ext','rmagic')
            
        interp.run_cell_magic('R', cmdline, code)
        
        # Set outputs after execution
        self._set_output_from_ns(user_ns)


    def execute(self, code):
        """
        execute subpart of a model (only code *code*)
        """
        from openalea.core.service.ipython import interpreter
        interp = interpreter()

        user_ns = interp.user_ns
        user_ns.update(self.ns)
        try:
            shell = interp.shell
        except AttributeError:
            shell = interp

        cmdline = self.r_options(user_ns)
        if not self.has_run:
            try:
                shell.run_line_magic('load_ext','rpy2.ipython') #better as it solves display error but needs rpy2 > 2.4.2
            except ImportError:
                shell.run_line_magic('load_ext','rmagic')

        shell.run_cell_magic('R', cmdline, code)

    def run(self, *args, **kwargs):
        """
        execute entire model
        """
        # TODO: check if we can do by an other way for inputs, outputs (ex %%R -i inputs, -o outputs)

        self._universal_run(self.code,*args,**kwargs)
        self.has_run = True        
        return self.outputs

    def init(self, *args, **kwargs):
        """
        go back to initial step
        """
        if not self.has_run:
            self.run(*args, **kwargs)
        if self._init:
            code = '\ninit()\n'
            self._universal_run(code,*args,**kwargs)
            return self.outputs

    def step(self, *args, **kwargs):
        """
        execute only one step of the model
        """
        if not self.has_run:
            self.run(*args, **kwargs)
        code = '\nstep()\n'
        self._universal_run(code,*args,**kwargs)

        return self.outputs

    def stop(self, *args, **kwargs):
        """
        stop execution
        """
        pass

    def animate(self, *args, **kwargs):
        """
        run model step by step
        """
        if self._animate:
            if not self.has_run:
                self.run(*args, **kwargs)

            code = '\nanimate()\n'
            self._universal_run(code,*args,**kwargs)

            return self.outputs

    def parse(self):
        """
        Set the content and parse it to get docstring, inputs and outputs info, some methods
        """
        content = self._content
        # TODO define the 3 functions parse_docstring_r, parse_functions_r, get_docstring_r
        model, self.inputs_info, self.outputs_info, self.cmdline = parse_docstring_r(content)
        self._init, self._step, self._animate, self._run = parse_functions_r(content)
        self._doc = get_docstring_r(content)
        self.has_run = False

