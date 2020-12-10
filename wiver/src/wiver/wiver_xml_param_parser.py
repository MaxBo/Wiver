from lxml import etree
import os
from typing import List


class XMLParamParser:
    '''
    Parses an xml parameter file (gui_vm project-style) for the model
    '''
    # xml-tags of nodes of interest
    SCENARIO = "Szenario"
    INPUT = "Eingabe"
    RUN = "Ergebnis"
    RESOURCE_PATH = "Projektdatei"

    # map the names of the xml tags (values) to the injectables (keys)
    MAP_INPUT = {'params_file': 'params',
                 'matrix_file': 'matrices',
                 'zones_file': 'zonal_data'
                 }

    # map the names of the xml options (values)
    MAP_FLAGS = {}
    MAP_SPEC = {}

    # default values if params are not set in xml
    DEFAULTS = {}

    def __init__(self, filename: str, scenario_name: str, run_name: str):
        """
        Parameters
        ----------
        filename:
            the filename of the xml-file
        scenario_name:
            the name of the scenario to parse from the xml-file
        run_name:
            the name of the run to parse from the xml-file
        """
        tree = etree.parse(filename)
        self._filename = filename
        self._root = tree.getroot()
        self._scenario = self._get_scenario(self._root, scenario_name)
        if self._scenario is None:
            raise Exception('Kein Szenario mit dem Namen {} gefunden!'
                            .format(scenario_name))
        self._dict = self._build_dict(run_name)

    def __getitem__(self, key):
        return self._dict[key]

    def __iter__(self):
        return iter(self._dict)

    def _build_dict(self, run_name: str) -> dict:
        """
        Parameters
        ----------
        run_name:
            the name of the run

        Returns
        -------
        :
            the dict with the options of the run
        """
        inputs = self._get_inputs(self._scenario)
        run = self._get_run(self._scenario, run_name)
        if run is None:
            raise Exception('Kein Lauf mit dem Namen {} im Szenario {} gefunden!'
                            .format(run_name, self._scenario.attrib['name']))
        d = {}

        #Input files
        for key, value in self.MAP_INPUT.items():
            path = self._get_path(inputs, value)
            if path is None:
                path = self.DEFAULTS[key]
            d[key] = path

        #Flags (like calibrate)
        for key, value in self.MAP_FLAGS.items():
            flag = self._get_option(run, value)
            if flag is None:
                d[key] = self.DEFAULTS[key]
            elif flag and flag.strip().lower() == 'true':
                d[key] = True
            else:
                d[key] = False

        #Options (like groups)
        for key, value in self.MAP_SPEC.items():
            option = self._get_option(run, value)
            if option is not None:
                option = option.strip()
            else:
                option = self.DEFAULTS[key]
            d[key] = option

        # results file
        path = self._get_path([run], run_name)
        if path is None:
            path = scenario_name + '.h5'
        d['result_file'] = path

        return d

    def _get_scenario(self,
                      element: etree.Element,
                      scenario_name: str) -> List[etree.Element]:
        '''
        get scenario by name,

        Parameters
        ----------
        element:
            the etree-element to search in
        scenario_name:
            name of the scenario

        Returns
        -------
        :
            list of all inputs of given scenario or None if not found
        '''
        for scenario in element.findall('.//' + self.SCENARIO):
            scen_name = scenario.attrib['name']
            if scen_name == scenario_name:
                return scenario
        return None

    def _get_inputs(self, scenario: etree.Element) -> List[etree.Element]:
        '''
        get all inputs of given scenario node

        Parameters
        ----------
        scenario:
            describes scenario and it's configuration

        Returns
        -------
        :
            all inputs of given scenario
        '''
        return scenario.findall( './/' + self.INPUT)

    def _get_run(self, scenario: etree.Element, run_name: str) -> etree.Element:
        '''
        get a run of the given scenario with the given name

        Parameters
        ----------
        scenario:
            describes scenario and it's configuration

        Returns
        -------
        :
            the run
        '''
        for run in scenario.findall('.//' + self.RUN):
            r_name = run.attrib['name']
            if r_name == run_name:
                return run
        return None

    def _get_path(self, resources: List[etree.Element], resource_name: str) -> str:
        '''
        gets filepath of given resource (input or ), None if not found

        Parameters
        ----------
        resources:
            list of resources
        resource_name:
            name of the resource

        Returns
        -------
        :
            path to the resource file
        '''
        for res in resources:
            if res.attrib['name'] == resource_name:
                path = res.find(self.RESOURCE_PATH)
                if path.attrib.has_key('relative') and path.attrib['relative']:
                    return self._get_absolute_path(res)
                return path.text
        return None

    def _get_option(self, run: etree.Element, option_name: str) -> str:
        """
        Parameters
        ----------
        run:
            the run-Element
        option_name:
            the option to search in the run

        Returns
        -------
        :
            the value of the option
        """
        options = run.findall('Option')
        for opt in options:
            if opt.attrib['name'] == option_name:
                return opt.text
        return None

    def _get_absolute_path(self, resource: etree.Element) -> str:
        """
        Parameters
        ----------
        resource:
            a resource-Element

        Returns
        -------
        :
            the full path to the resource-file
        """
        typ = resource.tag
        rel_path = resource.find(self.RESOURCE_PATH).text
        project_path = os.path.split(self._filename)[0]
        scen_name = self._scenario.attrib['name']
        #ToDo: map this
        if typ == self.INPUT:
            sub = 'Eingaben'
        elif typ == self.RUN:
            sub = 'Ausgaben'
        else:
            sub = ''
        full_path = os.path.join(project_path, scen_name, sub, rel_path)
        return full_path